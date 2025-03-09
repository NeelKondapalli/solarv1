"""
Settings Configuration Module

This module defines the configuration settings for the AI Agent API
using Pydantic's BaseSettings. It handles environment variables and
provides default values for various service configurations.

The settings can be overridden by environment variables or through a .env file.
Environment variables take precedence over values defined in the .env file.
"""

import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict
from web3 import Web3
logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """
    Application settings model that provides configuration for all components.
    """

    # Flag to enable/disable attestation simulation
    simulate_attestation: bool = False
    # Restrict backend listener to specific IPs
    cors_origins: list[str] = ["*"]
    # API key for accessing Google's Gemini AI service
    gemini_api_key: str = ""
    # The Gemini model identifier to use
    gemini_model: str = "gemini-1.5-flash"
    # API version to use at the backend
    api_version: str = "v1"
    # URL for the Flare Network RPC provider
    web3_provider_url: str = "https://flare-api.flare.network/ext/C/rpc"
    # URL for the Flare Network block explorer
    web3_explorer_url: str = "https://flare-explorer.flare.network/"

    # FTSO Contract Settings

    FTSOV2_ADDRESS: str = Web3.to_checksum_address("0xB18d3A5e5A85C65cE47f977D7F486B79F99D3d32")  # Coston2 FTSO contract

    FTSOV2_ABI: list = [

        {

            "inputs": [{"internalType": "bytes21","name": "_feedId","type": "bytes21"}],

            "name": "getFeedById",

            "outputs": [

                {"internalType": "uint256","name": "","type": "uint256"},

                {"internalType": "int8","name": "","type": "int8"},

                {"internalType": "uint64","name": "","type": "uint64"}

            ],

            "stateMutability": "payable",

            "type": "function"

        },

        {

            "inputs": [{"internalType": "bytes21[]","name": "_feedIds","type": "bytes21[]"}],

            "name": "getFeedsById",

            "outputs": [

                {"internalType": "uint256[]","name": "","type": "uint256[]"},

                {"internalType": "int8[]","name": "","type": "int8[]"},

                {"internalType": "uint64","name": "","type": "uint64"}

            ],

            "stateMutability": "payable",

            "type": "function"

        }

    ]

    

    # FTSO Feed IDs for supported tokens

    FTSO_FEED_IDS: dict[str, str] = {

        "FLR": "0x01464c522f55534400000000000000000000000000",  # FLR/USD

        "BTC": "0x014254432f55534400000000000000000000000000",  # BTC/USD

        "ETH": "0x014554482f55534400000000000000000000000000",  # ETH/USD

        "XRP": "0x015852502f55534400000000000000000000000000",  # XRP/USD

        "DOGE": "0x01444f47452f555344000000000000000000000000", # DOGE/USD

        "ADA": "0x014144412f55534400000000000000000000000000",  # ADA/USD

        "ALGO": "0x01414c474f2f555344000000000000000000000000", # ALGO/USD

        "SOL": "0x01534f4c2f55534400000000000000000000000000"   # SOL/USD

    }

    

    # List of tokens actually supported by FTSO

    FTSO_SUPPORTED_TOKENS: list[str] = list(FTSO_FEED_IDS.keys())

    

    # FTSO Symbol Mapping - maps various token representations to their FTSO symbol

    FTSO_SYMBOLS: dict[str, str] = {

        # Native token variations

        "FLR": "FLR",

        "FLARE": "FLR",

        "FLARE NETWORK": "FLR",

        

        # Bitcoin variations

        "BTC": "BTC",

        "BITCOIN": "BTC",

        "WBTC": "BTC",

        "WRAPPED BITCOIN": "BTC",

        "XBT": "BTC",

        

        # Ethereum variations

        "ETH": "ETH",

        "ETHEREUM": "ETH",

        "WETH": "ETH",

        "WRAPPED ETHEREUM": "ETH",

        

        # XRP variations

        "XRP": "XRP",

        "RIPPLE": "XRP",

        

        # Dogecoin variations

        "DOGE": "DOGE",

        "DOGECOIN": "DOGE",

        

        # Cardano variations

        "ADA": "ADA",

        "CARDANO": "ADA",

        

        # Algorand variations

        "ALGO": "ALGO",

        "ALGORAND": "ALGO",

        

        # Solana variations

        "SOL": "SOL",

        "SOLANA": "SOL"

    }

    model_config = SettingsConfigDict(
        # This enables .env file support
        env_file=".env",
        # If .env file is not found, don't raise an error
        env_file_encoding="utf-8",
        # Optional: you can also specify multiple .env files
        extra="ignore",
    )


# Create a global settings instance
settings = Settings()
logger.debug("settings", settings=settings.model_dump())
