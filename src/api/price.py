"""
Price API Module
================
This module fetches real-time cryptocurrency prices from Decibel.trade API.

Usage:
    price = await get_token_price("APT")
    prices = await get_multiple_prices(["APT", "BTC", "ETH"])
"""

from typing import Optional, Dict
from src.api.decibel import (
    get_prices,
    get_price_by_symbol,
    get_markets,
    normalize_symbol
)


async def get_token_price(token: str) -> Optional[float]:
    """
    Fetch real-time price for a single token in USD from Decibel.
    
    Args:
        token: Token symbol (e.g., "APT", "BTC", "ETH")
    
    Returns:
        Current price in USD or None if fetch fails
    """
    # Stablecoins - return 1.0 directly
    if token.upper() in ["USDC", "USDT"]:
        return 1.0
    
    normalized = normalize_symbol(token)
    price_data = await get_price_by_symbol(normalized)
    
    if price_data:
        # Use oracle price as it's most accurate
        return price_data.oracle_px if price_data.oracle_px else price_data.mark_px
    
    return None


async def get_multiple_prices(tokens: list[str]) -> Dict[str, Optional[float]]:
    """
    Fetch real-time prices for multiple tokens in USD from Decibel.
    
    Args:
        tokens: List of token symbols (e.g., ["APT", "BTC", "ETH"])
    
    Returns:
        Dictionary mapping token symbols to prices
    """
    result = {}
    
    # Handle stablecoins separately
    stablecoins = {"USDC", "USDT"}
    for token in tokens:
        if token.upper() in stablecoins:
            result[token.upper()] = 1.0
    
    # Get all prices from Decibel
    all_prices = await get_prices()
    markets = await get_markets()
    
    # Create a map from market address to symbol
    addr_to_symbol = {m.market_addr: m.symbol for m in markets.values()}
    
    # Create a map from symbol to price
    symbol_prices = {}
    for price in all_prices:
        symbol = addr_to_symbol.get(price.market)
        if symbol:
            symbol_prices[symbol] = price.oracle_px if price.oracle_px else price.mark_px
    
    # Map requested tokens to prices
    for token in tokens:
        token_upper = token.upper()
        if token_upper in stablecoins:
            continue
        
        normalized = normalize_symbol(token_upper)
        result[token_upper] = symbol_prices.get(normalized)
    
    return result


async def get_token_info(token: str) -> Optional[dict]:
    """
    Fetch detailed token information including price and funding rate.
    
    Args:
        token: Token symbol (e.g., "APT", "BTC")
    
    Returns:
        Dictionary with token info or None if fetch fails
    """
    normalized = normalize_symbol(token)
    price_data = await get_price_by_symbol(normalized)
    
    if not price_data:
        return None
    
    markets = await get_markets()
    market = markets.get(normalized)
    
    return {
        "symbol": token.upper(),
        "name": f"{normalized}-PERP",
        "price_usd": price_data.oracle_px if price_data.oracle_px else price_data.mark_px,
        "mark_price": price_data.mark_px,
        "mid_price": price_data.mid_px,
        "oracle_price": price_data.oracle_px,
        "funding_rate_bps": price_data.funding_rate_bps,
        "is_funding_positive": price_data.is_funding_positive,
        "open_interest": price_data.open_interest,
        "max_leverage": market.max_leverage if market else None,
        "timestamp_ms": price_data.timestamp_ms
    }


async def get_supported_tokens() -> list[str]:
    """
    Get list of all supported token symbols from Decibel.
    
    Returns:
        List of token symbols that can be used with price APIs
    """
    markets = await get_markets()
    return list(markets.keys())
