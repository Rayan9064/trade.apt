"""
AI Parser Module
================
This module uses OpenAI's GPT model to parse natural language trading instructions
and provide conversational responses with real-time price data.

Supports:
- Trade parsing: "buy $20 APT if price drops to $7"
- Price queries: "what's the price of bitcoin?"
- General chat: "hello", "help me trade"
"""

import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = None
if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") not in ["", "your_openai_api_key_here"]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_conversational_prompt(prices: dict) -> str:
    """Build system prompt with current prices."""
    price_info = "\n".join([f"- {k}: ${v:,.2f}" for k, v in prices.items() if v])
    
    return f"""You are a friendly DeFi trading assistant for Trade.apt. You help users trade cryptocurrencies with natural, conversational responses.

CURRENT REAL-TIME PRICES:
{price_info}

Your personality:
- Friendly, helpful, and knowledgeable about crypto
- Always mention the CURRENT REAL price when discussing any token
- Use emojis occasionally to be engaging 🚀📈💰
- Be concise but informative

RESPONSE RULES:

1. For PRICE QUERIES (e.g., "price of BTC", "how much is ethereum"):
   - Give the current price from the data above
   - Mention if it seems like a good time to buy/sell
   - Keep it conversational

2. For TRADE REQUESTS (buy/sell/swap):
   - Acknowledge the request naturally
   - Mention the current price
   - Include a JSON block at the END with trade details:
   
   ```json
   {{"intent": "trade", "action": "buy|sell|swap", "tokenFrom": "SYMBOL", "tokenTo": "SYMBOL", "amountUsd": NUMBER, "conditions": {{"type": "immediate|price_trigger", "operator": "<|>|null", "value": NUMBER|null}}}}
   ```

3. For GREETINGS/GENERAL CHAT:
   - Be friendly and helpful
   - Suggest what you can do (check prices, execute trades, set alerts)

4. For UNCLEAR REQUESTS:
   - Ask for clarification
   - Give examples of what you can do

EXAMPLES:

User: "what's bitcoin at?"
You: "Bitcoin (BTC) is currently at $97,234! 📈 It's been showing strong momentum. Are you thinking of buying or selling?"

User: "sell my bitcoin"
You: "Got it! � BTC is at $97,234 right now. I'll set up a market sell order for you. How much would you like to sell (in USD)?

If you want to proceed with selling all, just confirm!
```json
{{"intent": "trade", "action": "sell", "tokenFrom": "BTC", "tokenTo": "USDC", "amountUsd": 0, "conditions": {{"type": "immediate", "operator": null, "value": null}}}}
```"

User: "buy $100 ETH if it drops to $3000"
You: "Smart move! 🎯 ETH is currently at $3,456. I'll set up a conditional buy order for $100 worth of ETH when it drops to $3,000.
```json
{{"intent": "trade", "action": "buy", "tokenFrom": "USDC", "tokenTo": "ETH", "amountUsd": 100, "conditions": {{"type": "price_trigger", "operator": "<", "value": 3000}}}}
```"

Always use the REAL prices provided above in your responses!"""


async def chat_with_ai(text: str, prices: dict) -> dict:
    """
    Have a conversational interaction with the AI, including real price data.
    
    Args:
        text: User's message
        prices: Dict of current token prices
    
    Returns:
        dict with 'message' (conversational response) and optionally 'trade' (parsed trade)
    """
    if not client:
        # Use mock response if no API key
        return await chat_mock(text, prices)
    
    try:
        system_prompt = build_conversational_prompt(prices)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON if present
        trade = None
        message = content
        
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                trade = json.loads(json_match.group(1))
                # Remove JSON block from message
                message = re.sub(r'```json\s*\{.*?\}\s*```', '', content, flags=re.DOTALL).strip()
            except json.JSONDecodeError:
                pass
        
        return {
            "message": message,
            "trade": trade
        }
        
    except Exception as e:
        return {
            "message": f"Sorry, I'm having trouble right now. Error: {str(e)}",
            "trade": None
        }


async def chat_mock(text: str, prices: dict) -> dict:
    """
    Mock conversational AI for when no API key is available.
    Uses pattern matching to provide helpful responses with real prices.
    """
    text_lower = text.lower()
    
    # Token name mappings
    token_names = {
        "APT": "Aptos", "BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana",
        "USDC": "USD Coin", "USDT": "Tether", "BNB": "BNB", "XRP": "Ripple",
        "ADA": "Cardano", "DOGE": "Dogecoin", "AVAX": "Avalanche", "DOT": "Polkadot",
        "MATIC": "Polygon", "LINK": "Chainlink", "UNI": "Uniswap", "ATOM": "Cosmos",
        "LTC": "Litecoin", "NEAR": "NEAR", "ARB": "Arbitrum", "OP": "Optimism",
        "SUI": "Sui", "SEI": "Sei", "INJ": "Injective", "TIA": "Celestia"
    }
    
    # Detect which token is being discussed
    detected_token = None
    for symbol, name in token_names.items():
        if symbol.lower() in text_lower or name.lower() in text_lower:
            detected_token = symbol
            break
    
    # Handle greetings
    if any(word in text_lower for word in ["hello", "hi", "hey", "help", "what can you do"]):
        btc_price = prices.get("BTC", 0)
        eth_price = prices.get("ETH", 0)
        apt_price = prices.get("APT", 0)
        
        return {
            "message": f"""Hey there! 👋 I'm your AI trading assistant for Trade.apt!

Here's what I can help you with:
• **Check prices** - "What's the price of Bitcoin?"
• **Buy crypto** - "Buy $100 of ETH"
• **Sell crypto** - "Sell $50 worth of APT"
• **Set conditional orders** - "Buy BTC if it drops below $95k"

📊 **Current Market:**
• BTC: ${btc_price:,.2f}
• ETH: ${eth_price:,.2f}
• APT: ${apt_price:,.2f}

What would you like to do?""",
            "trade": None
        }
    
    # Handle price queries
    if any(word in text_lower for word in ["price", "how much", "what's", "whats", "cost", "worth"]):
        if detected_token and detected_token in prices and prices[detected_token]:
            price = prices[detected_token]
            name = token_names.get(detected_token, detected_token)
            return {
                "message": f"📈 **{name} ({detected_token})** is currently trading at **${price:,.2f}**!\n\nWould you like to buy or sell some?",
                "trade": None
            }
        else:
            # Show multiple prices - filter out None values
            top_prices = {k: v for k, v in list(prices.items())[:5] if v is not None}
            if top_prices:
                price_list = "\n".join([f"• **{k}**: ${v:,.2f}" for k, v in top_prices.items()])
                return {
                    "message": f"📊 **Current Crypto Prices:**\n{price_list}\n\nWhich token are you interested in?",
                    "trade": None
                }
            else:
                return {
                    "message": "Sorry, I couldn't fetch prices right now. Please try again in a moment!",
                    "trade": None
                }
    
    # Handle sell requests
    if "sell" in text_lower:
        token = detected_token or "BTC"
        price = prices.get(token) or 0
        name = token_names.get(token, token)
        
        # Extract amount
        amount = 0
        amount_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)', text)
        if amount_match:
            amount = float(amount_match.group(1).replace(",", ""))
        
        trade = {
            "intent": "trade",
            "action": "sell",
            "tokenFrom": token,
            "tokenTo": "USDC",
            "amountUsd": amount,
            "conditions": {"type": "immediate", "operator": None, "value": None}
        }
        
        # Check for price conditions
        condition_match = re.search(r'(?:above|over|hits?|reaches?)\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text_lower)
        if condition_match:
            target = float(condition_match.group(1).replace(",", ""))
            trade["conditions"] = {"type": "price_trigger", "operator": ">", "value": target}
            return {
                "message": f"🎯 Setting up a conditional sell order!\n\n**{name} ({token})** is currently at **${price:,.2f}**.\n\nI'll sell when it rises above **${target:,.2f}**.",
                "trade": trade
            }
        
        return {
            "message": f"💰 Got it! **{name} ({token})** is currently at **${price:,.2f}**.\n\n{'Selling $' + f'{amount:,.2f}' if amount > 0 else 'Ready to sell'} {token} for USDC at market price!",
            "trade": trade
        }
    
    # Handle buy requests
    if "buy" in text_lower:
        token = detected_token or "APT"
        price = prices.get(token) or 0
        name = token_names.get(token, token)
        
        # Extract amount
        amount = 0
        amount_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)', text)
        if amount_match:
            amount = float(amount_match.group(1).replace(",", ""))
        
        trade = {
            "intent": "trade",
            "action": "buy",
            "tokenFrom": "USDC",
            "tokenTo": token,
            "amountUsd": amount,
            "conditions": {"type": "immediate", "operator": None, "value": None}
        }
        
        # Check for price conditions
        condition_match = re.search(r'(?:below|under|drops?\s*to|falls?\s*to)\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)', text_lower)
        if condition_match:
            target = float(condition_match.group(1).replace(",", ""))
            trade["conditions"] = {"type": "price_trigger", "operator": "<", "value": target}
            
            tokens_if_hit = amount / target if target > 0 and amount > 0 else 0
            
            return {
                "message": f"🎯 Smart move! Setting up a conditional buy order.\n\n**{name} ({token})** is currently at **${price:,.2f}**.\n\nI'll buy {'$' + f'{amount:,.2f} worth' if amount > 0 else ''} when it drops to **${target:,.2f}**." + (f"\n\nYou'll get approximately **{tokens_if_hit:.4f} {token}** if triggered!" if tokens_if_hit > 0 else ""),
                "trade": trade
            }
        
        tokens_received = amount / price if price > 0 and amount > 0 else 0
        
        return {
            "message": f"🚀 Great choice! **{name} ({token})** is at **${price:,.2f}**.\n\n{'Buying $' + f'{amount:,.2f} worth of {token}' if amount > 0 else f'Ready to buy {token}'} at market price!" + (f"\n\nYou'll receive approximately **{tokens_received:.4f} {token}**!" if tokens_received > 0 else ""),
            "trade": trade
        }
    
    # Handle swap requests
    if "swap" in text_lower:
        return {
            "message": "🔄 I can help you swap tokens! Try something like:\n• \"Swap $100 from BTC to ETH\"\n• \"Swap my SOL for APT\"",
            "trade": None
        }
    
    # Default response
    return {
        "message": f"I'm not sure I understood that. 🤔\n\nTry asking me:\n• \"What's the price of Bitcoin?\"\n• \"Buy $50 of ETH\"\n• \"Sell APT when it hits $20\"\n\nHow can I help you trade today?",
        "trade": None
    }


# Legacy function for backward compatibility
async def parse_user_request(text: str) -> dict:
    """Legacy parser - use chat_with_ai instead for conversational responses."""
    if not client:
        return await parse_user_request_mock(text)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": TRADE_PARSE_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        return json.loads(content)
        
    except Exception as e:
        raise Exception(f"OpenAI API error: {e}")


# Simple system prompt for trade parsing only
TRADE_PARSE_PROMPT = """You are a trading instruction parser. Convert natural language trading instructions into structured JSON.

Respond ONLY with valid JSON:
{
    "action": "buy" | "sell" | "swap",
    "tokenFrom": "TOKEN_SYMBOL",
    "tokenTo": "TOKEN_SYMBOL", 
    "amountUsd": NUMBER,
    "conditions": {
        "type": "price_trigger" | "immediate",
        "operator": "<" | ">" | null,
        "value": NUMBER | null
    }
}

Rules:
- For "buy": tokenFrom=USDC, tokenTo=target token
- For "sell": tokenFrom=sold token, tokenTo=USDC  
- "if price drops to $X" → operator: "<", value: X
- "if price rises above $X" → operator: ">", value: X
- No condition specified → type: "immediate"

ONLY respond with JSON, no other text."""


async def parse_user_request_mock(text: str) -> dict:
    """Mock parser for testing without OpenAI API."""
    text_lower = text.lower()
    
    result = {
        "action": "buy",
        "tokenFrom": "USDC",
        "tokenTo": "APT",
        "amountUsd": 0,
        "conditions": {"type": "immediate", "operator": None, "value": None}
    }
    
    if "sell" in text_lower:
        result["action"] = "sell"
        result["tokenFrom"] = "APT"
        result["tokenTo"] = "USDC"
    elif "swap" in text_lower:
        result["action"] = "swap"
    
    amount_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
    if amount_match:
        result["amountUsd"] = float(amount_match.group(1))
    
    tokens = ["APT", "BTC", "ETH", "SOL", "USDC", "USDT", "BNB", "XRP", "ADA", "DOGE"]
    for token in tokens:
        if token.lower() in text_lower or token in text:
            if result["action"] == "buy":
                result["tokenTo"] = token
            elif result["action"] == "sell":
                result["tokenFrom"] = token
            break
    
    price_match = re.search(r'(?:drops?\s*to|below|under)\s*\$?(\d+(?:\.\d+)?)', text_lower)
    if price_match:
        result["conditions"] = {"type": "price_trigger", "operator": "<", "value": float(price_match.group(1))}
    else:
        price_match = re.search(r'(?:rises?\s*(?:to|above)|above|over|hits?)\s*\$?(\d+(?:\.\d+)?)', text_lower)
        if price_match:
            result["conditions"] = {"type": "price_trigger", "operator": ">", "value": float(price_match.group(1))}
    
    return result
