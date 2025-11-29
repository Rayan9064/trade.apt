"""
Price API Module
================
This module fetches real-time cryptocurrency prices from free APIs.
Primary source: CoinGecko API (free tier, no API key required)
Fallback: DexScreener API

Usage:
    price = await get_token_price("APT")
    prices = await get_multiple_prices(["APT", "BTC", "ETH"])
"""

import httpx
from typing import Optional, Dict

# CoinGecko API base URL (free tier)
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Token symbol to CoinGecko ID mapping
# CoinGecko uses specific IDs for each cryptocurrency
TOKEN_TO_COINGECKO_ID = {
    "APT": "aptos",
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "USDC": "usd-coin",
    "USDT": "tether",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "NEAR": "near",
    "ARB": "arbitrum",
    "OP": "optimism",
    "SUI": "sui",
    "SEI": "sei-network",
    "INJ": "injective-protocol",
    "TIA": "celestia",
    "PEPE": "pepe",
    "SHIB": "shiba-inu",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
}

# Reverse mapping for lookups
COINGECKO_ID_TO_TOKEN = {v: k for k, v in TOKEN_TO_COINGECKO_ID.items()}


def get_coingecko_id(token: str) -> Optional[str]:
    """
    Convert token symbol to CoinGecko ID.
    
    Args:
        token: Token symbol (e.g., "APT", "BTC", "ETH")
    
    Returns:
        CoinGecko ID or None if not found
    """
    # Normalize to uppercase
    token_upper = token.upper()
    
    # Direct lookup
    if token_upper in TOKEN_TO_COINGECKO_ID:
        return TOKEN_TO_COINGECKO_ID[token_upper]
    
    # Try lowercase as fallback (might be a CoinGecko ID already)
    token_lower = token.lower()
    if token_lower in COINGECKO_ID_TO_TOKEN:
        return token_lower
    
    return None


async def get_token_price(token: str) -> Optional[float]:
    """
    Fetch real-time price for a single token in USD.
    
    Args:
        token: Token symbol (e.g., "APT", "BTC", "ETH")
    
    Returns:
        Current price in USD or None if fetch fails
    
    Example:
        price = await get_token_price("APT")
        # Returns: 8.45
    """
    coingecko_id = get_coingecko_id(token)
    
    if not coingecko_id:
        print(f"Warning: Unknown token '{token}', cannot fetch price")
        return None
    
    # Stablecoins - return 1.0 directly
    if token.upper() in ["USDC", "USDT"]:
        return 1.0
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{COINGECKO_BASE_URL}/simple/price"
            params = {
                "ids": coingecko_id,
                "vs_currencies": "usd"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if coingecko_id in data and "usd" in data[coingecko_id]:
                return float(data[coingecko_id]["usd"])
            
            return None
            
    except httpx.HTTPError as e:
        print(f"HTTP error fetching price for {token}: {e}")
        return None
    except Exception as e:
        print(f"Error fetching price for {token}: {e}")
        return None


async def get_multiple_prices(tokens: list[str]) -> Dict[str, Optional[float]]:
    """
    Fetch real-time prices for multiple tokens in USD.
    More efficient than calling get_token_price multiple times.
    
    Args:
        tokens: List of token symbols (e.g., ["APT", "BTC", "ETH"])
    
    Returns:
        Dictionary mapping token symbols to prices
    
    Example:
        prices = await get_multiple_prices(["APT", "BTC", "ETH"])
        # Returns: {"APT": 8.45, "BTC": 43250.00, "ETH": 2280.50}
    """
    result = {}
    
    # Handle stablecoins separately
    stablecoins = {"USDC", "USDT"}
    for token in tokens:
        if token.upper() in stablecoins:
            result[token.upper()] = 1.0
    
    # Filter out stablecoins and unknown tokens
    tokens_to_fetch = []
    coingecko_ids = []
    
    for token in tokens:
        token_upper = token.upper()
        if token_upper in stablecoins:
            continue
        
        cg_id = get_coingecko_id(token)
        if cg_id:
            tokens_to_fetch.append(token_upper)
            coingecko_ids.append(cg_id)
        else:
            result[token_upper] = None
    
    if not coingecko_ids:
        return result
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{COINGECKO_BASE_URL}/simple/price"
            params = {
                "ids": ",".join(coingecko_ids),
                "vs_currencies": "usd"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Map prices back to token symbols
            for token, cg_id in zip(tokens_to_fetch, coingecko_ids):
                if cg_id in data and "usd" in data[cg_id]:
                    result[token] = float(data[cg_id]["usd"])
                else:
                    result[token] = None
            
            return result
            
    except httpx.HTTPError as e:
        print(f"HTTP error fetching multiple prices: {e}")
        # Return None for all tokens on error
        for token in tokens_to_fetch:
            result[token] = None
        return result
    except Exception as e:
        print(f"Error fetching multiple prices: {e}")
        for token in tokens_to_fetch:
            result[token] = None
        return result


async def get_token_info(token: str) -> Optional[dict]:
    """
    Fetch detailed token information including price, market cap, volume.
    
    Args:
        token: Token symbol (e.g., "APT", "BTC")
    
    Returns:
        Dictionary with token info or None if fetch fails
    """
    coingecko_id = get_coingecko_id(token)
    
    if not coingecko_id:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            market_data = data.get("market_data", {})
            
            return {
                "symbol": token.upper(),
                "name": data.get("name"),
                "price_usd": market_data.get("current_price", {}).get("usd"),
                "market_cap_usd": market_data.get("market_cap", {}).get("usd"),
                "volume_24h_usd": market_data.get("total_volume", {}).get("usd"),
                "price_change_24h_percent": market_data.get("price_change_percentage_24h"),
                "high_24h": market_data.get("high_24h", {}).get("usd"),
                "low_24h": market_data.get("low_24h", {}).get("usd"),
            }
            
    except Exception as e:
        print(f"Error fetching token info for {token}: {e}")
        return None


def get_supported_tokens() -> list[str]:
    """
    Get list of all supported token symbols.
    
    Returns:
        List of token symbols that can be used with price APIs
    """
    return list(TOKEN_TO_COINGECKO_ID.keys())
