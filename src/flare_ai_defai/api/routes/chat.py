"""
Chat Router Module

This module implements the main chat routing system for the AI Agent API.
It handles message routing, blockchain interactions, attestations, and AI responses.

The module provides a ChatRouter class that integrates various services:
- AI capabilities through GeminiProvider
- Blockchain operations through FlareProvider
- Attestation services through Vtpm
- Prompt management through PromptService
"""

import json
import re

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import Web3RPCError, ContractLogicError

from datetime import datetime, timedelta
import asyncio
import aiohttp


from flare_ai_defai.ai import GeminiProvider
from flare_ai_defai.attestation import Vtpm, VtpmAttestationError
from flare_ai_defai.blockchain import FlareProvider
from flare_ai_defai.prompts import PromptService, SemanticRouterResponse
from flare_ai_defai.settings import settings

logger = structlog.get_logger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    """
    Pydantic model for chat message validation.

    Attributes:
        message (str): The chat message content, must not be empty
    """

    message: str = Field(..., min_length=1)


class ChatRouter:
    """
    Main router class handling chat messages and their routing to appropriate handlers.

    This class integrates various services and provides routing logic for different
    types of chat messages including blockchain operations, attestations, and general
    conversation.

    Attributes:
        ai (GeminiProvider): Provider for AI capabilities
        blockchain (FlareProvider): Provider for blockchain operations
        attestation (Vtpm): Provider for attestation services
        prompts (PromptService): Service for managing prompts
        logger (BoundLogger): Structured logger for the chat router
    """

    def __init__(
        self,
        ai: GeminiProvider,
        blockchain: FlareProvider,
        attestation: Vtpm,
        prompts: PromptService,
    ) -> None:
        """
        Initialize the ChatRouter with required service providers.

        Args:
            ai: Provider for AI capabilities
            blockchain: Provider for blockchain operations
            attestation: Provider for attestation services
            prompts: Service for managing prompts
        """
        self._router = APIRouter()
        self.ai = ai
        self.blockchain = blockchain
        self.attestation = attestation
        self.prompts = prompts
        self.logger = logger.bind(router="chat")
        self._setup_routes()

        self.flare_api_base = "https://flr-data-availability.flare.network/api/v0"

        self.session = None

        self.context = ""

    def _setup_routes(self) -> None:
        """
        Set up FastAPI routes for the chat endpoint.
        Handles message routing, command processing, and transaction confirmations.
        """

        @self._router.post("/")
        async def chat(message: ChatMessage) -> dict[str, str]:  # pyright: ignore [reportUnusedFunction]
            """
            Process incoming chat messages and route them to appropriate handlers.

            Args:
                message: Validated chat message

            Returns:
                dict[str, str]: Response containing handled message result

            Raises:
                HTTPException: If message handling fails
            """
            try:
                self.logger.debug("received_message", message=message.message)

                if message.message.startswith("/"):
                    return await self.handle_command(message.message)
                if (
                    self.blockchain.tx_queue
                    and message.message == self.blockchain.tx_queue[-1].msg
                ):
                    try:
                        tx_hash = self.blockchain.send_tx_in_queue()
                    except Web3RPCError as e:
                        self.logger.exception("send_tx_failed", error=str(e))
                        msg = (
                            f"Unfortunately the tx failed with the error:\n{e.args[0]}"
                        )
                        return {"response": msg}

                    prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                        "tx_confirmation",
                        tx_hash=tx_hash,
                        block_explorer=settings.web3_explorer_url,
                    )
                    tx_confirmation_response = self.ai.generate(
                        prompt=prompt,
                        response_mime_type=mime_type,
                        response_schema=schema,
                    )
                    return {"response": tx_confirmation_response.text}
                if self.attestation.attestation_requested:
                    try:
                        resp = self.attestation.get_token([message.message])
                    except VtpmAttestationError as e:
                        resp = f"The attestation failed with  error:\n{e.args[0]}"
                    self.attestation.attestation_requested = False
                    return {"response": resp}

                self.context += message.message + "\n"

                route = await self.get_semantic_route(message.message)
                return await self.route_message(route, message.message)

            except Exception as e:
                self.logger.exception("message_handling_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

    @property
    def router(self) -> APIRouter:
        """Get the FastAPI router with registered routes."""
        return self._router

    async def handle_command(self, command: str) -> dict[str, str]:
        """
        Handle special command messages starting with '/'.

        Args:
            command: Command string to process

        Returns:
            dict[str, str]: Response containing command result
        """
        if command == "/reset":
            self.blockchain.reset()
            self.ai.reset()
            return {"response": "Reset complete"}
        return {"response": "Unknown command"}

    async def get_semantic_route(self, message: str) -> SemanticRouterResponse:
        """
        Determine the semantic route for a message using AI provider.

        Args:
            message: Message to route

        Returns:
            SemanticRouterResponse: Determined route for the message
        """
        try:
            prompt, mime_type, schema = self.prompts.get_formatted_prompt(
                "semantic_router", user_input=message
            )
            route_response = self.ai.generate(
                prompt=prompt, response_mime_type=mime_type, response_schema=schema
            )
            return SemanticRouterResponse(route_response.text)
        except Exception as e:
            self.logger.exception("routing_failed", error=str(e))
            return SemanticRouterResponse.CONVERSATIONAL

    async def route_message(
        self, route: SemanticRouterResponse, message: str
    ) -> dict[str, str]:
        """
        Route a message to the appropriate handler based on semantic route.

        Args:
            route: Determined semantic route
            message: Original message to handle

        Returns:
            dict[str, str]: Response from the appropriate handler
        """
        handlers = {
            SemanticRouterResponse.GENERATE_ACCOUNT: self.handle_generate_account,
            SemanticRouterResponse.SEND_TOKEN: self.handle_send_token,
            SemanticRouterResponse.SWAP_TOKEN: self.handle_swap_token,
            SemanticRouterResponse.REQUEST_ATTESTATION: self.handle_attestation,
            SemanticRouterResponse.CONVERSATIONAL: self.handle_conversation,
            SemanticRouterResponse.COIN_INFO: self.get_coin_info,
            SemanticRouterResponse.MARKET_WATCH: self.handle_market_watch,
        }

        handler = handlers.get(route)
        if not handler:
            return {"response": "Unsupported route"}

        return await handler(message)

    async def handle_generate_account(self, _: str) -> dict[str, str]:
        """
        Handle account generation requests.

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response containing new account information
                or existing account
        """
        if self.blockchain.address:
            return {"response": f"Account exists - {self.blockchain.address}"}
        address = self.blockchain.generate_account()
        prompt, mime_type, schema = self.prompts.get_formatted_prompt(
            "generate_account", address=address
        )
        gen_address_response = self.ai.generate(
            prompt=prompt, response_mime_type=mime_type, response_schema=schema
        )
        self.context += gen_address_response.text + "\n"
        return {"response": gen_address_response.text}

    async def handle_send_token(self, message: str) -> dict[str, str]:
        """
        Handle token sending requests.

        Args:
            message: Message containing token sending details

        Returns:
            dict[str, str]: Response containing transaction preview or follow-up prompt
        """
        if not self.blockchain.address:
            await self.handle_generate_account(message)

        # Extract the first number in the message for amount
        amount_match = re.search(r'\d+(?:\.\d+)?', message)
        if not amount_match:
            raise ValueError("No valid amount found in message")
        
        # Find Ethereum address (0x followed by 40 hex chars)
        address_match = re.search(r'0x[0-9a-fA-F]{40}\b', message)
        if not address_match:
            raise ValueError("No valid Ethereum address found in message")
        
        send_token_json = {
            "to_address": address_match.group(),
            "amount": float(amount_match.group()),
        }
        # send_token_response = self.ai.generate(
        #     prompt=prompt, response_mime_type=mime_type, response_schema=schema
        # )

        expected_json_len = 2
        self.logger.debug("send_token_json", json=send_token_json)
        if (
            len(send_token_json) != expected_json_len
            or send_token_json.get("amount") == 0.0
        ):
            prompt, _, _ = self.prompts.get_formatted_prompt("follow_up_token_send")
            follow_up_response = self.ai.generate(prompt)
            return {"response": follow_up_response.text}

        tx = self.blockchain.create_send_flr_tx(
            to_address=send_token_json.get("to_address"),
            amount=send_token_json.get("amount"),
        )
        self.logger.debug("send_token_tx", tx=tx)
        self.blockchain.add_tx_to_queue(msg=message, tx=tx)
        formatted_preview = (
            "Transaction Preview: "
            + f"Sending {Web3.from_wei(tx.get('value', 0), 'ether')} "
            + f"FLR to {tx.get('to')}\nType CONFIRM to proceed."
        )
        self.context += formatted_preview + "\n"
        return {"response": formatted_preview}

    async def handle_swap_token(self, message: str) -> dict[str, str]:
        """
        Handle token swap requests. Expected format:
        'Swap X TokenA for Y TokenB'
        where X and Y are amounts and TokenA/TokenB are token symbols.

        Args:
            message: User message containing swap request

        Returns:
            dict[str, str]: Response with swap preview or error
        """
        if not self.blockchain.address:
            await self.handle_generate_account(message)

        # Extract amount and tokens using regex
        swap_pattern = r"^.*?(\d+)\s+([A-Z]+).*?([A-Z]+).*"
        match = re.search(swap_pattern, message)
        
        if not match:
            return {"response": "Invalid swap format. Please use: 'Swap X TokenA for TokenB case sensitive'"}
            
        from_amount = float(match.group(1))
        from_token = match.group(2).upper()
        to_token = match.group(3).upper()
        
        # Validate tokens are supported
        supported_tokens = ["FLR", "USDC", "JOULE", "WFLR", "USDT", "WETH"]  # Add more supported tokens as needed
        if from_token not in supported_tokens or to_token not in supported_tokens:
            return {
                "response": f"Unsupported tokens. Currently supported tokens: {', '.join(supported_tokens)}"
            }
            

        # Create swap transaction
        swap_tx = self.blockchain.handle_swap_token(
            from_token=from_token,
            to_token=to_token,
            amount=from_amount
        )

        # self.blockchain.add_tx_to_queue(
        #     msg=f"Swap {from_amount} {from_token} to {to_token}",
        #     tx=swap_tx
        # )

        # Return preview with approval notice if needed
        approval_notice = "\n(Note: You'll need to approve the token spend first)" if from_token != "FLR" else ""
        formatted_preview = (
            f"Swap transaction:\n"
            f"Token In: {from_token}\n"
            f"Token Out: {to_token}\n"
            f"Amount: {from_amount}{approval_notice}\n"
            f"Transaction hash: {swap_tx[:10]}\n"
            f"{swap_tx[10:]}"
            # f"Type CONFIRM SWAP to proceed."
        )
        self.context += formatted_preview + "\n"
        
        return {"response": formatted_preview}

    async def handle_attestation(self, _: str) -> dict[str, str]:
        """
        Handle attestation requests.

        Args:
            _: Unused message parameter

        Returns:
            dict[str, str]: Response containing attestation request
        """
        prompt = self.prompts.get_formatted_prompt("request_attestation")[0]
        request_attestation_response = self.ai.generate(prompt=prompt)
        self.attestation.attestation_requested = True

        self.context += request_attestation_response.text + "\n"

        return {"response": request_attestation_response.text}

    async def handle_conversation(self, message: str) -> dict[str, str]:
        """
        Handle general conversation messages.

        Args:
            message: Message to process

        Returns:
            dict[str, str]: Response from AI provider
        """
        response = self.ai.send_message(self.context + "\n" + message)
        self.context += response.text + "\n"
        return {"response": response.text}

    def create_ascii_chart(self, prices: list[float], max_width: int = 20, max_height: int = 10) -> list[str]:

        """Create an ASCII scatter plot from a list of prices."""

        if not prices:

            return []

            

        # Calculate price range with dynamic padding based on volatility

        min_price = min(prices)

        max_price = max(prices)

        price_range = max_price - min_price

        

        # Use more padding (up to 15%) for low volatility to make changes more visible

        padding_percent = min(0.15, max(0.05, 1 - (price_range / max_price)))

        padding = price_range * padding_percent

        

        min_price = min_price - padding

        max_price = max_price + padding

        price_range = max_price - min_price if max_price != min_price else 1

        

        # Initialize the chart grid with spaces

        grid = [[" " for _ in range(max_width)] for _ in range(max_height)]

        

        # Add y-axis line

        for i in range(max_height):

            grid[i][0] = "│"

            

        # Add x-axis line

        for i in range(max_width):

            grid[max_height-1][i] = "─"

            

        # Add corner

        grid[max_height-1][0] = "└"

        

        # Plot data points

        for i, price in enumerate(reversed(prices)):  # Reverse to show oldest to newest (left to right)

            x = 1 + int(((i / (len(prices) - 1)) * (max_width - 2)))  # Leave space for y-axis

            y = int(((price - min_price) / price_range) * (max_height - 2))  # Leave space for x-axis

            if 0 <= y < max_height-1 and x < max_width:  # Ensure we don't overwrite axes

                grid[y][x] = "•"

        

        # Format price labels based on price magnitude

        def format_price(price: float) -> str:

            if abs(price) >= 1_000_000:

                return f"${price/1_000_000:.1f}M"

            elif abs(price) >= 1000:

                return f"${price/1000:.1f}K"

            else:

                return f"${price:.2f}"

        

        # Convert grid to strings and add axis labels

        chart = []

        price_interval = price_range / (max_height - 2)  # Adjust for axis space

        

        # Add price labels on y-axis

        for i in range(max_height - 1):  # Don't label x-axis line

            price_value = max_price - (i * price_interval)

            price_label = format_price(price_value)

            row = f"{price_label:>8} {''.join(grid[i])}"

            chart.append(row)

        

        # Add x-axis line

        chart.append("         " + "".join(grid[max_height-1]))

        

        # Add time labels

        time_labels = ["5d", "3d", "1d", "Now"]

        label_line = "         "  # Align with price labels

        spacing = (max_width - 1) // (len(time_labels))

        

        for i, label in enumerate(time_labels):

            pos = 1 + i * spacing  # Start after y-axis

            while len(label_line) < pos + 9:

                label_line += " "

            label_line += label

        chart.append(label_line)

        
        self.context += "\n".join(chart) + "\n"
        return chart



    async def get_historical_prices(self, feed_id: str, latest_round_id: int, latest_timestamp: int) -> list[tuple[float, str, int]]:

        """Get historical price data for multiple voting rounds."""

        if not self.session:

            self.session = aiohttp.ClientSession()

            

        rounds_per_day = int((24 * 60 * 60) / 90)  # 90 seconds per round

        historical_data = []

        

        for days_ago in range(5):

            historical_round_id = latest_round_id - (rounds_per_day * (days_ago + 1))

            payload = {"feed_ids": [feed_id]}

            url = f"{self.flare_api_base}/ftso/anchor-feeds-with-proof"

            params = {"voting_round_id": historical_round_id}

            

            async with self.session.post(url, params=params, json=payload) as response:

                if response.status != 200:

                    raise HTTPException(status_code=response.status, detail=f"Failed to fetch historical price for {days_ago + 1} days ago")

                data = await response.json()

                if not data:

                    raise ValueError(f"No historical price data available for {days_ago + 1} days ago")

                    

                feed_data = data[0]["body"]

                price = feed_data["value"] / (10 ** abs(feed_data["decimals"]))

                

                # Calculate timestamp based on latest timestamp and rounds difference

                rounds_diff = latest_round_id - historical_round_id

                historical_timestamp = latest_timestamp - (rounds_diff * 90)  # 90 seconds per round

                timestamp = datetime.fromtimestamp(historical_timestamp)

                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

                historical_data.append((price, formatted_time, days_ago + 1))

        
        self.context += "\n" + str(historical_data) + "\n"

        return historical_data



    async def get_coin_info(self, message: str) -> dict[str, str]:

        """

        Get current and historical price information for a Flare token from FTSO.



        Args:

            message: Message containing token symbol



        Returns:

            dict[str, str]: Response containing current and historical token price information

        """

        try:

            # Parse the message to get token

            prompt, mime_type, schema = self.prompts.get_formatted_prompt(

                "coin_info", user_input=message

            )

            coin_info_response = self.ai.generate(

                prompt=prompt,

                response_mime_type=mime_type,

                response_schema=schema,

            )

            

            coin_info = json.loads(coin_info_response.text)

            token = coin_info["token"]

            

            # Normalize token name (remove /USD, convert to uppercase, strip spaces)

            normalized_token = token.upper().replace("/USD", "").strip()

            

            # Get the FTSO symbol

            ftso_symbol = settings.FTSO_SYMBOLS.get(normalized_token)

            if not ftso_symbol:

                supported_variations = [

                    k for k, v in settings.FTSO_SYMBOLS.items() 

                    if v in settings.FTSO_SUPPORTED_TOKENS

                ]

                return {

                    "response": (

                        f"Sorry, I cannot get the price for {token}. "

                        f"Supported tokens are: {', '.join(sorted(set(supported_variations)))}\n"

                        "You can use any common variation of these tokens (e.g., 'BTC' or 'Bitcoin')."

                    )

                }

            

            # Get the feed ID for the token

            feed_id = settings.FTSO_FEED_IDS.get(ftso_symbol)

            if not feed_id:

                return {

                    "response": (

                        f"Sorry, while I recognize {token}, its price feed "

                        f"({ftso_symbol}) is not currently supported by the FTSO."

                    )

                }

            

            try:

                # Check Web3 connection

                if not self.blockchain.w3.is_connected():

                    return {

                        "response": "Sorry, I cannot connect to the Flare network at the moment. "

                                  "Please try again later."

                    }

                

                # Get current price from FTSO contract

                ftsov2 = self.blockchain.w3.eth.contract(

                    address=settings.FTSOV2_ADDRESS,

                    abi=settings.FTSOV2_ABI

                )

                

                # Convert feed ID from hex string to bytes21

                feed_id_bytes = bytes.fromhex(feed_id[2:])  # Remove '0x' prefix

                

                # Get current price data from FTSO

                price, decimals, timestamp = ftsov2.functions.getFeedById(feed_id_bytes).call()

                

                if price == 0:

                    return {

                        "response": f"No price data available for {token} at the moment."

                    }

                

                # Calculate actual price (price is returned with decimals)

                current_price = price / (10 ** abs(decimals))

                

                # Format human readable timestamp

                current_dt = datetime.fromtimestamp(timestamp)

                formatted_current_time = current_dt.strftime("%Y-%m-%d %H:%M:%S UTC")



                # Get latest voting round and calculate historical rounds

                latest_round_id, latest_timestamp = await self.get_latest_voting_round()

                

                # Get historical prices

                try:

                    historical_data = await self.get_historical_prices(feed_id, latest_round_id, latest_timestamp)

                    

                    # Calculate price changes

                    oldest_price = historical_data[-1][0]

                    total_change = -1 * ((current_price - oldest_price) / oldest_price) * 100

                    change_symbol = "📉" if total_change < 0 else "📈"  # Flipped comparison due to flipped sign

                    

                    # Create ASCII chart

                    all_prices = [current_price] + [price for price, _, _ in historical_data]

                    chart = self.create_ascii_chart(all_prices)

                    

                    # Build response with current, historical data and chart

                    response = [

                        f"Current {token}/USD Price: **${current_price:.4f}** {change_symbol} {total_change:+.2f}% (5d)",

                        f"Last Updated: {formatted_current_time} (via Flare Time Series Oracle)",

                        "",

                        "```",

                        *chart,

                        "```"

                    ]

                    

                except Exception as e:

                    # Fallback to just current price if historical data fails

                    self.logger.error("Failed to fetch historical prices", error=str(e))

                    response = [

                        f"Current {token}/USD Price: **${current_price:.4f}**",

                        f"Last Updated: {formatted_current_time} (via Flare Time Series Oracle)",

                        "",

                        "Note: Historical price data is temporarily unavailable."

                    ]

                
                self.context += "\n" + str(response) + "\n"
                return {"response": "\n".join(response)}

                

            except ContractLogicError as e:

                self.logger.error(

                    "FTSO contract call failed",

                    error=str(e),

                    symbol=ftso_symbol,

                    feed_id=feed_id,

                    original_token=token

                )

                return {

                    "response": f"Sorry, I couldn't fetch the price for {token}. "

                               f"The FTSO service might be temporarily unavailable."

                }

            except Exception as e:

                self.logger.error(

                    "Unexpected error in FTSO interaction",

                    error=str(e),

                    symbol=ftso_symbol,

                    feed_id=feed_id,

                    original_token=token

                )

                return {

                    "response": f"Sorry, an unexpected error occurred while "

                               f"fetching the price for {token}."

                }

                

        except Exception as e:

            self.logger.error("Error processing coin info request", error=str(e))

            raise HTTPException(

                status_code=500,

                detail=f"Error processing request: {str(e)}"

            )



    async def get_latest_voting_round(self) -> tuple[int, int]:

        """Get the latest voting round ID and its timestamp."""

        if not self.session:

            self.session = aiohttp.ClientSession()

            

        async with self.session.get(f"{self.flare_api_base}/fsp/latest-voting-round") as response:

            if response.status != 200:

                raise HTTPException(status_code=response.status, detail="Failed to fetch latest voting round")

            data = await response.json()

            return data["voting_round_id"], data["start_timestamp"]



    async def handle_market_watch(self, _: str) -> dict[str, str]:

        """

        Get market trend analysis for all supported FTSO tokens.



        Args:

            _: Unused message parameter



        Returns:

            dict[str, str]: Response containing market trend analysis

        """

        try:

            tokens = settings.FTSO_SUPPORTED_TOKENS

            token_data = []



            latest_round_id, latest_timestamp = await self.get_latest_voting_round()



            for token in tokens:

                try:

                    feed_id = settings.FTSO_FEED_IDS.get(token)

                    if not feed_id:

                        continue



                    # Get current price from FTSO contract first

                    feed_id_bytes = bytes.fromhex(feed_id[2:])  # Remove '0x' prefix

                    ftsov2 = self.blockchain.w3.eth.contract(

                        address=settings.FTSOV2_ADDRESS,

                        abi=settings.FTSOV2_ABI

                    )

                    price, decimals, timestamp = ftsov2.functions.getFeedById(feed_id_bytes).call()

                    if price == 0:

                        continue

                    

                    current_price = price / (10 ** abs(decimals))



                    # Get historical prices for comparison

                    historical_data = await self.get_historical_prices(feed_id, latest_round_id, latest_timestamp)

                    if not historical_data:

                        continue



                    five_day_price = historical_data[-1][0]  # 5 days ago price

                    price_change = -1 * ((current_price - five_day_price) / five_day_price) * 100



                    token_data.append({

                        'token': token,

                        'current_price': current_price,

                        'price_change': price_change

                    })



                except Exception as e:

                    self.logger.error(f"Error processing {token}", error=str(e))

                    continue



            token_data.sort(key=lambda x: abs(x['price_change']), reverse=True)

            top_movers = token_data[:3]  



            response_lines = ["📊 Market Overview (5-Day Change) via Flare Time Series Oracle", ""]

            

            for data in top_movers:

                change_symbol = "📉" if data['price_change'] < 0 else "📈"  # Flipped comparison due to flipped sign

                response_lines.append(

                    f"{data['token']}: ${data['current_price']:.4f} "

                    f"{change_symbol} {data['price_change']:+.2f}%"

                )



            response_lines.extend([

                "",

                "These are the tokens with the most significant price movements in the last 5 days.",

                "All price data is sourced from the Flare Time Series Oracle (FTSO) for accurate, decentralized market information.",

                "Use the coin info command for detailed price charts of specific tokens."

            ])


            self.context += "\n" + "\n".join(response_lines) + "\n"

            return {"response": "\n".join(response_lines)}



        except Exception as e:

            self.logger.error("Error in market watch", error=str(e))

            raise HTTPException(

                status_code=500,

                detail=f"Error processing market watch request: {str(e)}"

            )
