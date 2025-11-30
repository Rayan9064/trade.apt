"""
Chart Data API
==============
Provides historical price data for charts using Decibel.trade API only.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from src.api.decibel import (
    get_chart_data_from_decibel,
    get_available_symbols,
    normalize_symbol
)


async def get_chart_data(
    symbol: str,
    days: int = 7,
    interval: str = "hourly"
) -> Optional[Dict[str, Any]]:
    """
    Get historical price data for charting using Decibel API.
    
    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        days: Number of days of history (1, 7, 30, 90, 365)
        interval: Data interval
    
    Returns:
        Dictionary with prices, stats, and metadata for charting
    """
    normalized = normalize_symbol(symbol)
    return await get_chart_data_from_decibel(normalized, days)


async def get_multi_chart_data(
    symbols: List[str],
    days: int = 7
) -> Dict[str, Any]:
    """
    Get chart data for multiple symbols at once.
    """
    import asyncio
    
    tasks = [get_chart_data(s, days) for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    chart_data = {}
    for symbol, result in zip(symbols, results):
        if isinstance(result, Exception):
            print(f"Error getting chart for {symbol}: {result}")
            chart_data[symbol.upper()] = None
        else:
            chart_data[symbol.upper()] = result
    
    return chart_data
