"""
Trade.apt Autonomous AI Trading Agent (Production)
===================================================
A comprehensive AI agent that handles trading operations professionally.
No emojis, detailed responses, enterprise-ready.

Capabilities:
- Natural language understanding for trading requests
- Real-time market analysis with price data
- Risk assessment and warnings
- Portfolio analysis
- Multi-step trade planning
- Error recovery and graceful degradation
"""

import os
import json
import re
from datetime import datetime
from typing import Optional, Dict, List, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client
client = None
API_KEY = os.getenv("GROQ_API_KEY")
if API_KEY and API_KEY not in ["", "your_groq_api_key_here"]:
    client = Groq(api_key=API_KEY)

# AI Model Configuration
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "2000"))


def build_system_prompt(context: Dict[str, Any]) -> str:
    """Build a comprehensive system prompt with full context."""
    prices = context.get("prices", {})
    wallet = context.get("wallet", {})
    pending_orders = context.get("pending_orders", [])
    
    # Format price data
    price_lines = []
    for token, data in prices.items():
        if isinstance(data, dict):
            price = data.get("price", 0)
            change = data.get("change_24h", 0)
            direction = "up" if change >= 0 else "down"
            price_lines.append(f"  {token}: ${price:,.2f} ({direction} {abs(change):.2f}% 24h)")
        elif data:
            price_lines.append(f"  {token}: ${data:,.2f}")
    
    price_info = "\n".join(price_lines) if price_lines else "  (Loading prices...)"
    
    # Format wallet info
    wallet_info = "Not connected"
    if wallet.get("connected"):
        wallet_info = f"""Connected: {wallet.get('address', 'Unknown')[:8]}...
  Balance: ${wallet.get('balance_usd', 0):,.2f}"""
    
    return f"""You are Trade.apt's AI Trading Agent - a professional, precise, and comprehensive trading assistant built on Aptos blockchain.

CRITICAL REQUIREMENTS FOR ALL RESPONSES:
1. NEVER use emojis - this is a professional trading platform
2. Be detailed and informative with specific numbers
3. Explain risks clearly and professionally
4. Use proper financial terminology

═══════════════════════════════════════════════════════════════
                    REAL-TIME MARKET DATA
═══════════════════════════════════════════════════════════════
{price_info}

═══════════════════════════════════════════════════════════════
                      WALLET STATUS
═══════════════════════════════════════════════════════════════
{wallet_info}

═══════════════════════════════════════════════════════════════
                    RESPONSE PROTOCOL
═══════════════════════════════════════════════════════════════

ALWAYS structure your response as JSON:
{{
  "message": "Your detailed, professional response (markdown supported, ABSOLUTELY NO EMOJIS)",
  "intent": "chat|trade|price_check|portfolio|alert|analysis|help|error",
  "action": {{
    "type": "none|buy|sell|swap|limit_order|stop_loss|alert|cancel",
    "token_from": "SYMBOL or null",
    "token_to": "SYMBOL or null", 
    "amount_usd": number or null,
    "amount_tokens": number or null,
    "condition": {{
      "type": "immediate|price_above|price_below|time_based",
      "trigger_price": number or null,
      "expiry": "ISO datetime or null"
    }},
    "risk_level": "low|medium|high|critical",
    "requires_confirmation": true/false
  }},
  "warnings": ["List of risk warnings - NO EMOJIS"],
  "suggestions": ["Follow-up suggestions"],
  "market_context": "Market analysis if relevant"
}}

═══════════════════════════════════════════════════════════════
                    SAFETY PROTOCOLS
═══════════════════════════════════════════════════════════════

1. NEVER execute trades without confirmation
2. ALWAYS warn about trades exceeding 20% of portfolio
3. Flag high-volatility tokens (memecoins: PEPE, SHIB, DOGE, BONK, etc.)
4. For HIGH-RISK actions, set requires_confirmation: true
5. If unclear, ask clarifying questions - do not assume

Current timestamp: {datetime.utcnow().isoformat()}Z
"""


async def process_message(
    user_message: str,
    prices: Dict[str, Any],
    wallet: Optional[Dict] = None,
    pending_orders: Optional[List] = None,
    alerts: Optional[List] = None,
    conversation_history: Optional[List] = None
) -> Dict[str, Any]:
    """Process a user message and return AI response."""
    
    context = {
        "prices": prices,
        "wallet": wallet or {"connected": False},
        "pending_orders": pending_orders or [],
        "alerts": alerts or []
    }
    
    system_prompt = build_system_prompt(context)
    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_history:
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    messages.append({"role": "user", "content": user_message})
    
    if not client:
        return await fallback_response(user_message, prices)
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Remove any emojis that might have slipped through
        result = remove_emojis_from_response(result)
        
        return validate_response(result, prices)
        
    except json.JSONDecodeError:
        return {
            "message": "I understood your request but encountered a formatting issue. Please rephrase your request.",
            "intent": "error",
            "action": {"type": "none", "requires_confirmation": False},
            "warnings": ["Response parsing error"],
            "suggestions": ["Try rephrasing your request"]
        }
    except Exception as e:
        print(f"AI Agent error: {e}")
        return await fallback_response(user_message, prices)


def remove_emojis_from_response(response: Dict) -> Dict:
    """Remove all emojis from response fields."""
    
    # Comprehensive emoji pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+",
        flags=re.UNICODE
    )
    
    def clean_text(text):
        if isinstance(text, str):
            return emoji_pattern.sub('', text).strip()
        return text
    
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [clean_dict(item) for item in d]
        elif isinstance(d, str):
            return clean_text(d)
        return d
    
    return clean_dict(response)


def validate_response(response: Dict, prices: Dict) -> Dict:
    """Validate and enhance AI response with safety checks."""
    if "message" not in response:
        response["message"] = "Request processed."
    
    if "intent" not in response:
        response["intent"] = "chat"
    
    if "action" not in response:
        response["action"] = {"type": "none", "requires_confirmation": False}
    
    action = response.get("action", {})
    amount = action.get("amount_usd", 0) or 0
    
    if amount > 1000:
        if "warnings" not in response:
            response["warnings"] = []
        response["warnings"].append(f"Large trade amount: ${amount:,.2f}")
        action["requires_confirmation"] = True
        action["risk_level"] = "high" if amount > 5000 else "medium"
    
    token = action.get("token_to") or action.get("token_from") or ""
    memecoins = ["PEPE", "SHIB", "DOGE", "BONK", "WIF", "FLOKI"]
    if token.upper() in memecoins:
        if "warnings" not in response:
            response["warnings"] = []
        response["warnings"].append(f"{token} is a high-volatility memecoin")
        action["risk_level"] = "high"
    
    return response


async def fallback_response(user_message: str, prices: Dict) -> Dict:
    """Fallback response when AI service is unavailable."""
    message_lower = user_message.lower()
    
    tokens = {
        "bitcoin": "BTC", "btc": "BTC",
        "ethereum": "ETH", "eth": "ETH",
        "aptos": "APT", "apt": "APT",
        "solana": "SOL", "sol": "SOL",
        "doge": "DOGE", "dogecoin": "DOGE",
        "usdc": "USDC", "usdt": "USDT",
        "bnb": "BNB", "xrp": "XRP",
        "cardano": "ADA", "ada": "ADA",
        "polygon": "MATIC", "matic": "MATIC",
        "avalanche": "AVAX", "avax": "AVAX",
    }
    
    def get_price(symbol: str) -> float:
        price = prices.get(symbol, 0)
        if isinstance(price, dict):
            return price.get("price", 0)
        return price or 0
    
    detected_tokens = []
    for name, symbol in tokens.items():
        if name in message_lower and symbol not in detected_tokens:
            detected_tokens.append(symbol)
    
    detected_token = detected_tokens[0] if detected_tokens else None
    
    amounts = re.findall(r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)', user_message)
    amounts = [float(a.replace(",", "")) for a in amounts]
    
    # PRICE CHECK
    if any(word in message_lower for word in ["price", "how much", "what's", "cost", "worth"]):
        if detected_token:
            price = get_price(detected_token)
            return {
                "message": f"**{detected_token} Market Data**\n\nCurrent Price: **${price:,.2f}**\n\nThis price is updated in real-time from major exchanges. Would you like to execute a trade or set a price alert?",
                "intent": "price_check",
                "action": {"type": "none", "requires_confirmation": False},
                "suggestions": [f"Buy $100 of {detected_token}", f"Set price alert"]
            }
        else:
            price_list = "\n".join([f"- **{k}**: ${get_price(k):,.2f}" for k in ["BTC", "ETH", "APT", "SOL"] if get_price(k)])
            return {
                "message": f"**Current Market Prices**\n\n{price_list}\n\nSelect a token for more details or to execute a trade.",
                "intent": "price_check",
                "action": {"type": "none", "requires_confirmation": False}
            }
    
    # BUY
    if "buy" in message_lower:
        token = detected_token or "APT"
        price = get_price(token)
        amount = amounts[0] if amounts else None
        
        if any(word in message_lower for word in ["all", "everything", "max"]):
            return {
                "message": f"**Buy Order: {token} (Maximum Amount)**\n\nCurrent Price: ${price:,.2f}\n\nThis order will utilize your entire available balance. This is classified as a high-risk transaction.\n\n**Execution:** Your wallet will prompt for transaction approval.",
                "intent": "trade",
                "action": {
                    "type": "buy",
                    "token_from": "USDC",
                    "token_to": token,
                    "use_max": True,
                    "condition": {"type": "immediate"},
                    "risk_level": "high",
                    "requires_confirmation": True
                },
                "warnings": ["Maximum balance transaction - high risk"]
            }
        
        msg = f"**Buy Order: {token}**\n\nCurrent Price: ${price:,.2f}\n"
        if amount:
            token_amount = amount / price if price > 0 else 0
            msg += f"\n**Order Details:**\n- USD Amount: ${amount:,.2f}\n- Estimated {token}: {token_amount:.6f}\n"
        else:
            msg += "\nPlease specify the purchase amount.\n"
        msg += "\n**Execution:** Wallet approval required."
        
        return {
            "message": msg,
            "intent": "trade",
            "action": {
                "type": "buy",
                "token_from": "USDC",
                "token_to": token,
                "amount_usd": amount,
                "condition": {"type": "immediate"},
                "risk_level": "medium" if (amount or 0) > 500 else "low",
                "requires_confirmation": True
            }
        }
    
    # SELL
    if "sell" in message_lower:
        token = detected_token or "BTC"
        price = get_price(token)
        
        if any(word in message_lower for word in ["all", "everything"]):
            return {
                "message": f"**Sell Order: {token} (Full Position)**\n\nCurrent Price: ${price:,.2f}\n\nThis will liquidate your entire {token} position.\n\n**Warning:** This action is irreversible once confirmed.",
                "intent": "trade",
                "action": {
                    "type": "sell",
                    "token_from": token,
                    "token_to": "USDC",
                    "sell_all": True,
                    "condition": {"type": "immediate"},
                    "risk_level": "high",
                    "requires_confirmation": True
                },
                "warnings": [f"Full {token} position liquidation"]
            }
        
        return {
            "message": f"**Sell Order: {token}**\n\nCurrent Price: ${price:,.2f}\n\nPlease specify the amount to sell.",
            "intent": "trade",
            "action": {
                "type": "sell",
                "token_from": token,
                "token_to": "USDC",
                "condition": {"type": "immediate"},
                "requires_confirmation": True
            }
        }
    
    # SWAP
    if any(word in message_lower for word in ["swap", "exchange", "convert"]) and len(detected_tokens) >= 2:
        from_token = detected_tokens[0]
        to_token = detected_tokens[1]
        from_price = get_price(from_token)
        to_price = get_price(to_token)
        rate = from_price / to_price if to_price > 0 else 0
        
        return {
            "message": f"**Token Swap: {from_token} to {to_token}**\n\n**Exchange Rates:**\n- {from_token}: ${from_price:,.2f}\n- {to_token}: ${to_price:,.2f}\n- Rate: 1 {from_token} = {rate:.6f} {to_token}\n\nSpecify amount or confirm to proceed.",
            "intent": "trade",
            "action": {
                "type": "swap",
                "token_from": from_token,
                "token_to": to_token,
                "condition": {"type": "immediate"},
                "risk_level": "medium",
                "requires_confirmation": True
            }
        }
    
    # REBALANCE
    if any(word in message_lower for word in ["liquidate", "rebalance", "split"]):
        split_pattern = re.search(r'(\d+)\s*[/\-]\s*(\d+)', message_lower)
        split1 = int(split_pattern.group(1)) if split_pattern else 50
        split2 = int(split_pattern.group(2)) if split_pattern else 50
        
        targets = detected_tokens[:2] if len(detected_tokens) >= 2 else ["BTC", "ETH"]
        
        return {
            "message": f"**Portfolio Rebalance**\n\n**Target Allocation:**\n- {targets[0]}: {split1}% (${get_price(targets[0]):,.2f})\n- {targets[1]}: {split2}% (${get_price(targets[1]):,.2f})\n\n**Process:**\n1. Liquidate current holdings\n2. Reallocate per target percentages\n\n**Risk Level:** High - Multiple transactions required.",
            "intent": "trade",
            "action": {
                "type": "multi_trade",
                "risk_level": "high",
                "requires_confirmation": True
            },
            "warnings": ["Full portfolio restructuring", "Multiple transactions", "Price volatility risk"]
        }
    
    # ALERT
    if any(word in message_lower for word in ["alert", "notify"]):
        token = detected_token or "BTC"
        price = get_price(token)
        
        price_match = re.search(r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?k?)', message_lower)
        target = None
        if price_match:
            p = price_match.group(1).replace(",", "")
            target = float(p.replace('k', '')) * 1000 if 'k' in p.lower() else float(p)
        
        return {
            "message": f"**Price Alert: {token}**\n\nCurrent: ${price:,.2f}\n" + (f"Target: ${target:,.2f}" if target else "Please specify target price."),
            "intent": "alert",
            "action": {"type": "alert", "token": token, "target_price": target, "requires_confirmation": True}
        }
    
    # HELP
    if any(word in message_lower for word in ["hello", "hi", "help", "hey", "start"]):
        return {
            "message": f"""**Trade.apt - AI Trading Assistant**

**Available Commands:**

**Market Data**
- "What is the price of Bitcoin?"
- "Show current prices"

**Trading**
- "Buy $100 of ETH"
- "Sell my APT"
- "Swap BTC for ETH"

**Portfolio**
- "Rebalance to 50/50 BTC/ETH"
- "Show my holdings"

**Alerts**
- "Alert when BTC hits $100,000"

**Current Prices:**
- BTC: ${get_price('BTC'):,.2f}
- ETH: ${get_price('ETH'):,.2f}
- APT: ${get_price('APT'):,.2f}

How may I assist you?""",
            "intent": "help",
            "action": {"type": "none", "requires_confirmation": False}
        }
    
    # DEFAULT
    return {
        "message": f"""**Trade.apt Assistant**

I can assist with:
- Trading (buy, sell, swap)
- Price information
- Portfolio management
- Price alerts

**Market Overview:**
- BTC: ${get_price('BTC'):,.2f}
- ETH: ${get_price('ETH'):,.2f}
- APT: ${get_price('APT'):,.2f}

What would you like to do?""",
        "intent": "chat",
        "action": {"type": "none", "requires_confirmation": False}
    }


async def chat(message: str, prices: Dict) -> Dict:
    """Simple chat interface."""
    return await process_message(message, prices)
