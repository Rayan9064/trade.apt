"""
AI Parser Module
================
This module uses OpenAI's GPT model to parse natural language trading instructions
into structured JSON format that can be processed by the trade engine.

Example input: "buy $20 APT if price drops to $7"
Example output: {
    "action": "buy",
    "tokenFrom": "USDC",
    "tokenTo": "APT",
    "amountUsd": 20,
    "conditions": {
        "type": "price_trigger",
        "operator": "<",
        "value": 7
    }
}
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompt for the AI to understand trading instructions
SYSTEM_PROMPT = """You are a trading instruction parser. Your job is to convert natural language trading instructions into structured JSON.

You must ALWAYS respond with valid JSON in this exact format:
{
    "action": "buy" | "sell" | "swap",
    "tokenFrom": "TOKEN_SYMBOL",
    "tokenTo": "TOKEN_SYMBOL", 
    "amountUsd": NUMBER,
    "conditions": {
        "type": "price_trigger" | "immediate",
        "operator": "<" | ">" | "<=" | ">=" | "==" | null,
        "value": NUMBER | null
    }
}

Rules:
1. For "buy" actions: tokenFrom is typically USDC/USDT (stablecoin), tokenTo is the target token
2. For "sell" actions: tokenFrom is the token being sold, tokenTo is typically USDC/USDT
3. For "swap" actions: tokenFrom and tokenTo are the tokens being exchanged
4. If no condition is specified, use "type": "immediate" with operator and value as null
5. Parse price conditions like "if price drops to $7" as operator: "<", value: 7
6. Parse conditions like "if price rises above $10" as operator: ">", value: 10
7. Common token mappings: APT=Aptos, BTC=Bitcoin, ETH=Ethereum, SOL=Solana
8. Always extract the USD amount from phrases like "$20", "20 dollars", "20 USD"
9. If tokenFrom is not specified for a buy, default to "USDC"
10. If tokenTo is not specified for a sell, default to "USDC"

Examples:
- "buy $20 APT if price drops to $7" → action: buy, tokenFrom: USDC, tokenTo: APT, amountUsd: 20, conditions: {type: price_trigger, operator: <, value: 7}
- "sell 50 dollars of ETH" → action: sell, tokenFrom: ETH, tokenTo: USDC, amountUsd: 50, conditions: {type: immediate, operator: null, value: null}
- "swap $100 from BTC to SOL when SOL is below $150" → action: swap, tokenFrom: BTC, tokenTo: SOL, amountUsd: 100, conditions: {type: price_trigger, operator: <, value: 150}

IMPORTANT: Only respond with the JSON object, no additional text or markdown formatting."""


async def parse_user_request(text: str) -> dict:
    """
    Parse natural language trading instruction into structured JSON.
    
    Args:
        text: Natural language trading instruction (e.g., "buy $20 APT if price drops to $7")
    
    Returns:
        dict: Structured trading instruction with action, tokens, amount, and conditions
    
    Raises:
        ValueError: If the AI response cannot be parsed as valid JSON
        Exception: If OpenAI API call fails
    """
    try:
        # Call OpenAI API with GPT-4o-mini (cost-effective and fast)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.1,  # Low temperature for consistent parsing
            max_tokens=500
        )
        
        # Extract the response content
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON response
        parsed = json.loads(content)
        
        # Validate required fields
        required_fields = ["action", "tokenFrom", "tokenTo", "amountUsd", "conditions"]
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate action type
        if parsed["action"] not in ["buy", "sell", "swap"]:
            raise ValueError(f"Invalid action: {parsed['action']}")
        
        # Validate conditions structure
        conditions = parsed["conditions"]
        if "type" not in conditions:
            raise ValueError("Missing conditions.type")
        
        if conditions["type"] not in ["price_trigger", "immediate"]:
            raise ValueError(f"Invalid condition type: {conditions['type']}")
        
        return parsed
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        raise Exception(f"OpenAI API error: {e}")


# For testing without OpenAI API key
async def parse_user_request_mock(text: str) -> dict:
    """
    Mock parser for testing without OpenAI API.
    Provides basic parsing for common patterns.
    """
    text_lower = text.lower()
    
    # Default structure
    result = {
        "action": "buy",
        "tokenFrom": "USDC",
        "tokenTo": "APT",
        "amountUsd": 0,
        "conditions": {
            "type": "immediate",
            "operator": None,
            "value": None
        }
    }
    
    # Detect action
    if "sell" in text_lower:
        result["action"] = "sell"
        result["tokenFrom"] = "APT"
        result["tokenTo"] = "USDC"
    elif "swap" in text_lower:
        result["action"] = "swap"
    
    # Extract amount (simple regex-like parsing)
    import re
    amount_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
    if amount_match:
        result["amountUsd"] = float(amount_match.group(1))
    
    # Extract token (look for common tokens)
    tokens = ["APT", "BTC", "ETH", "SOL", "USDC", "USDT"]
    for token in tokens:
        if token.lower() in text_lower or token in text:
            if result["action"] == "buy":
                result["tokenTo"] = token
            elif result["action"] == "sell":
                result["tokenFrom"] = token
            break
    
    # Extract price condition
    price_match = re.search(r'(?:drops?\s*to|below|under|less\s*than)\s*\$?(\d+(?:\.\d+)?)', text_lower)
    if price_match:
        result["conditions"] = {
            "type": "price_trigger",
            "operator": "<",
            "value": float(price_match.group(1))
        }
    else:
        price_match = re.search(r'(?:rises?\s*(?:to|above)|above|over|greater\s*than)\s*\$?(\d+(?:\.\d+)?)', text_lower)
        if price_match:
            result["conditions"] = {
                "type": "price_trigger",
                "operator": ">",
                "value": float(price_match.group(1))
            }
    
    return result
