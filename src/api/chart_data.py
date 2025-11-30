"""
Chart Data API
==============
Provides historical price data for charts.
Primary: Decibel.trade API
Fallback: CoinGecko API
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx

from src.api.decibel import (
    get_chart_data_from_decibel,
    get_available_symbols,
    normalize_symbol
)

# CoinGecko ID mapping for fallback
COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "APT": "aptos",
    "SOL": "solana",
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
}


async def get_coingecko_chart_data(symbol: str, days: int = 7) -> Optional[Dict[str, Any]]:
    """Fallback to CoinGecko for chart data."""
    coin_id = COINGECKO_IDS.get(symbol.upper())
    if not coin_id:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                params={"vs_currency": "usd", "days": days}
            )
            
            if response.status_code != 200:
                print(f"CoinGecko API error: {response.status_code}")
                return None
            
            data = response.json()
            prices_raw = data.get("prices", [])
            
            if not prices_raw:
                return None
            
            # Format prices
            prices = [{"time": int(p[0]), "value": p[1]} for p in prices_raw]
            
            # Calculate stats
            price_values = [p["value"] for p in prices]
            current_price = price_values[-1] if price_values else 0
            start_price = price_values[0] if price_values else 0
            high_price = max(price_values) if price_values else 0
            low_price = min(price_values) if price_values else 0
            price_change = current_price - start_price
            price_change_percent = (price_change / start_price * 100) if start_price else 0
            
            return {
                "symbol": symbol.upper(),
                "prices": prices,
                "stats": {
                    "current": current_price,
                    "open": start_price,
                    "high": high_price,
                    "low": low_price,
                    "change": price_change,
                    "change_percent": round(price_change_percent, 2),
                    "period": f"{days}d"
                },
                "days": days,
                "data_points": len(prices),
                "source": "coingecko",
                "last_updated": datetime.utcnow().isoformat()
            }
    except Exception as e:
        print(f"CoinGecko fallback error for {symbol}: {e}")
        return None


async def get_chart_data(
    symbol: str,
    days: int = 7,
    interval: str = "hourly"
) -> Optional[Dict[str, Any]]:
    """
    Get historical price data for charting.
    
    Primary: Decibel API
    Fallback: CoinGecko API
    
    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        days: Number of days of history (1, 7, 30, 90, 365)
        interval: Data interval
    
    Returns:
        Dictionary with prices, stats, and metadata for charting
    """
    normalized = normalize_symbol(symbol)
    
    # Try Decibel first
    result = await get_chart_data_from_decibel(normalized, days)
    if result:
        return result
    
    # Fallback to CoinGecko
    print(f"Falling back to CoinGecko for {symbol}")
    return await get_coingecko_chart_data(normalized, days)


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
