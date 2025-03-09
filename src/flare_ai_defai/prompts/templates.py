from typing import Final

SEMANTIC_ROUTER: Final = """
Classify the following user input into EXACTLY ONE category. Analyze carefully and choose the most specific matching category.

Categories (in order of precedence):
1. GENERATE_ACCOUNT
   • Keywords: create wallet, new account, generate address, make wallet
   • Must express intent to create/generate new account/wallet
   • Ignore if just asking about existing accounts

2. SEND_TOKEN
   • Keywords: send, transfer, pay, give tokens
   • Must include intent to transfer tokens to another address
   • Should involve one-way token movement

3. SWAP_TOKEN
   • Keywords: swap, exchange, trade, convert tokens
   • Must involve exchanging one token type for another
   • Should mention both source and target tokens

4. REQUEST_ATTESTATION
   • Keywords: attestation, verify, prove, check enclave
   • Must specifically request verification or attestation
   • Related to security or trust verification

5. MARKET_WATCH
   • Keywords: market trends, price changes, market overview, performance
   • Must be asking about general market performance or trends
   • Should NOT mention specific coins (use COIN_INFO instead)
   • Examples: "How's the market doing?", "Show me top performers"

6. COIN_INFO
   • Use when input asks for current market information on a specific coin
   • Keywords: data, trends, coin, information, price
   • Must have a specific coin ticker (Such as FLR, cFLR, ETH, BTC, and so on.)

7. CONVERSATIONAL (default)
   • Use when input doesn't clearly match above categories
   • General questions, greetings, or unclear requests
   • Any ambiguous or multi-category inputs

Input: ${user_input}

Instructions:
- Choose ONE category only
- Select most specific matching category
- Default to CONVERSATIONAL if unclear
- Ignore politeness phrases or extra context
- Focus on core intent of request
"""

GENERATE_ACCOUNT: Final = """
Generate a welcoming message that includes ALL of these elements in order:

1. Welcome message that conveys enthusiasm for the user joining
2. Security explanation:
   - Account is secured in a Trusted Execution Environment (TEE)
   - Private keys never leave the secure enclave
   - Hardware-level protection against tampering
3. Account address display:
   - EXACTLY as provided, make no changes: ${address}
   - Format with clear visual separation
4. Funding account instructions:
   - Tell the user to fund the new account: [Add funds to account](https://faucet.flare.network/coston2)

Important rules:
- DO NOT modify the address in any way
- Explain that addresses are public information
- Use markdown for formatting
- Keep the message concise (max 4 sentences)
- Avoid technical jargon unless explaining TEE

Example tone:
"Welcome to Flare! 🎉 Your new account is secured by secure hardware (TEE),
keeping your private keys safe and secure, you freely share your
public address: 0x123...
[Add funds to account](https://faucet.flare.network/coston2)
Ready to start exploring the Flare network?"
"""

TOKEN_SEND: Final = """
You are a tool to extract wallet address and a numerical amount from text 

Extract EXACTLY two pieces of information from the input text for a token send operation:

1. DESTINATION ADDRESS
   Required format:
   • Must start with "0x"
   • Exactly 42 characters long
   • Hexadecimal characters only (0-9, a-f, A-F)
   • Extract COMPLETE address only
   • DO NOT modify or truncate
   • FAIL if no valid address found

2. TOKEN AMOUNT
   Number extraction rules:
   • Convert written numbers to digits (e.g., "five" → 5)
   • Handle decimals and integers
   • Convert ALL integers to float (e.g., 100 → 100.0)
   • Recognize common amount formats:
     - Decimal: "1.5", "0.5"
     - Integer: "1", "100"
     - With words: "5 tokens", "10 FLR"
   • Extract first valid number only
   • FAIL if no valid amount found


Input: ${user_input}

Examples:
✓ "Send 100 C2FLR to 0x8F63Aa5704d732678aC8a3A22E8F679894357408" → {"to_address": "0x8F63Aa5704d732678aC8a3A22E8F679894357408", "amount": 100.0}
✓ "Send 100 BTC to 0x8F63Aa5704d732678aC8a3A22E8F679894357408" → {"to_address": "0x8F63Aa5704d732678aC8a3A22E8F679894357408", "amount": 100.0}
Explanaton: The response must be a valid JSON object with the correct format and CORRECT QUOTES.

Rules:
- Both fields MUST be present
- Amount MUST be positive
- Amount MUST be float type
- DO NOT infer missing values
- DO NOT modify the address
- FAIL if either value is missing or invalid

Return the TWO PIECES of information in this format:

Response format:
{
  "to_address": <address>,
  "amount": <float_value>
}
"""

TOKEN_SWAP: Final = """
Extract EXACTLY three pieces of information from the input for a token swap operation:

1. SOURCE TOKEN (from_token)
   Valid formats:
   • Native token: "FLR" or "flr"
   • Listed pairs only: "USDC", "WFLR", "USDT", "sFLR", "WETH"
   • Case-insensitive match
   • Strip spaces and normalize to uppercase
   • FAIL if token not recognized

2. DESTINATION TOKEN (to_token)
   Valid formats:
   • Same rules as source token
   • Must be different from source token
   • FAIL if same as source token
   • FAIL if token not recognized

3. SWAP AMOUNT
   Number extraction rules:
   • Convert written numbers to digits (e.g., "five" → 5.0)
   • Handle decimal and integer inputs
   • Convert ALL integers to float (e.g., 100 → 100.0)
   • Valid formats:
     - Decimal: "1.5", "0.5"
     - Integer: "1", "100"
     - With tokens: "5 FLR", "10 USDC"
   • Extract first valid number only
   • Amount MUST be positive
   • FAIL if no valid amount found

Input: ${user_input}

Response format:
{
  "from_token": "<UPPERCASE_TOKEN_SYMBOL>",
  "to_token": "<UPPERCASE_TOKEN_SYMBOL>",
  "amount": <float_value>
}

Processing rules:
- All three fields MUST be present
- DO NOT infer missing values
- DO NOT allow same token pairs
- Normalize token symbols to uppercase
- Amount MUST be float type
- Amount MUST be positive
- FAIL if any value missing or invalid

Examples:
✓ "swap 100 FLR to USDC" → {"from_token": "FLR", "to_token": "USDC", "amount": 100.0}
✓ "exchange 50.5 flr for usdc" → {"from_token": "FLR", "to_token": "USDC", "amount": 50.5}
✗ "swap flr to flr" → FAIL (same token)
✗ "swap tokens" → FAIL (missing amount)
"""

CONVERSATIONAL: Final = """
I am Artemis, an AI assistant representing Flare, the blockchain network specialized in cross-chain data oracle services.

Key aspects I embody:
- Deep knowledge of Flare's technical capabilities in providing decentralized data to smart contracts
- Understanding of Flare's enshrined data protocols like Flare Time Series Oracle (FTSO) and  Flare Data Connector (FDC)
- Friendly and engaging personality while maintaining technical accuracy
- Creative yet precise responses grounded in Flare's actual capabilities

When responding to queries, I will:
1. Address the specific question or topic raised
2. Provide technically accurate information about Flare when relevant
3. Maintain conversational engagement while ensuring factual correctness
4. Acknowledge any limitations in my knowledge when appropriate

<input>
${user_input}
</input>
"""

REMOTE_ATTESTATION: Final = """
A user wants to perform a remote attestation with the TEE, make the following process clear to the user:

1. Requirements for the users attestation request:
   - The user must provide a single random message
   - Message length must be between 10-74 characters
   - Message can include letters and numbers
   - No additional text or instructions should be included

2. Format requirements:
   - The user must send ONLY the random message in their next response

3. Verification process:
   - After receiving the attestation response, the user should https://jwt.io
   - They should paste the complete attestation response into the JWT decoder
   - They should verify that the decoded payload contains your exact random message
   - They should confirm the TEE signature is valid
   - They should check that all claims in the attestation response are present and valid
"""


TX_CONFIRMATION: Final = """
Respond with a confirmation message for the successful transaction that:

1. Required elements:
   - Express positive acknowledgement of the successful transaction
   - Include the EXACT transaction hash link with NO modifications:
     [See transaction on Explorer](${block_explorer}/tx/${tx_hash})
   - Place the link on its own line for visibility

2. Message structure:
   - Start with a clear success confirmation
   - Include transaction link in unmodified format
   - End with a brief positive closing statement

3. Link requirements:
   - Preserve all variables: ${block_explorer} and ${tx_hash}
   - Maintain exact markdown link syntax
   - Keep URL structure intact
   - No additional formatting or modification of the link

Sample format:
Great news! Your transaction has been successfully confirmed. 🎉

[See transaction on Explorer](${block_explorer}/tx/${tx_hash})

Your transaction is now securely recorded on the blockchain.
"""


COIN_INFO: Final = """
Extract token information from the input text.

1. SOURCE TOKEN (token)
   Valid formats:
   • Native token: "FLR" or "flr"
   • Listed pairs only: "USDC", "WFLR", "USDT", "sFLR", "WETH"
   • Case-insensitive match
   • Strip spaces and normalize to uppercase
   • FAIL if token not recognized

DO NOT accept more than one token. If more than one token is recognized in the prompt, tell the user that they must query token information one at a time.

Input: ${user_input}

Response Format: 
{ 
   "token": "<UPPERCASE_TOKEN_SYMBOL>"
}

Processing rules:
- TOKEN ID MUST be present
- DO NOT infer missing values
- DO NOT allow same token pairs
- Normalize token symbols to uppercase
- FAIL if any more than one token, no token, missing or invalid

Examples:
✓ "Give me data on FLR" → {"token": "FLR"}
✓ "I need info on usdt" → {"token": "USDT"}
✓ "What is WFLR's price?" → {"token": "WFLR"}
✓ "Show me sflr" → {"token": "SFLR"}

✗ "Tell me about FLR and USDC" → FAIL (Only one token can be queried at a time)
✗ "What is the latest price of BTC?" → FAIL (Token not recognized)
✗ "Can you check the data?" → FAIL (Token ID must be present)
✗ "I need data on WFLR and wflr" → FAIL (Duplicate token detected)
"""

MARKET_WATCH: Final = """
Analyze the user's request for market trend information.

The response should be empty JSON as the actual market analysis will be performed by the system.

Input: ${user_input}

Response Format:
{}

Processing rules:
- Always return empty JSON object
- All market analysis will be done by the system
- This prompt is just for routing validation

Examples:
✓ "How's the market doing?" → {}
✓ "Show me the top performers" → {}
✓ "What are the market trends?" → {}
✓ "Which coins are performing best?" → {}
"""