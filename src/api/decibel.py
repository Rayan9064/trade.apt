"""
Decibel API Integration
=======================
Provides real-time market data from Decibel.trade API.
API Base URL: https://api.netna.aptoslabs.com/decibel

Endpoints used:
- GET /api/v1/markets - Get all available markets
- GET /api/v1/prices - Get current prices
- GET /api/v1/candlesticks - Get OHLC chart data
- WSS ws://api.netna.aptoslabs.com/decibel/ws - Real-time WebSocket

Documentation: https://docs.decibel.trade/
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Decibel API Configuration
DECIBEL_BASE_URL = "https://api.netna.aptoslabs.com/decibel"
DECIBEL_WS_URL = "ws://api.netna.aptoslabs.com/decibel/ws"

# Cache for market addresses
_markets_cache: Optional[Dict[str, Dict]] = None
_markets_cache_time: Optional[datetime] = None
MARKETS_CACHE_DURATION = timedelta(minutes=30)


class CandlestickInterval(str, Enum):
    """Supported candlestick intervals"""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    TWO_HOURS = "2h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"


@dataclass
class DecibelMarket:
    """Decibel market information"""
    market_addr: str
    market_name: str
    symbol: str  # Extracted from market_name (e.g., "BTC" from "BTC-PERP")
    lot_size: int
    min_size: int
    tick_size: int
    px_decimals: int
    sz_decimals: int
    max_leverage: int
    max_open_interest: float


@dataclass
class DecibelPrice:
    """Decibel price data"""
    market: str
    mark_px: float
    mid_px: float
    oracle_px: float
    funding_rate_bps: int
    is_funding_positive: bool
    open_interest: float
    timestamp_ms: int


@dataclass
class DecibelCandle:
    """Decibel candlestick data"""
    timestamp: int  # Open time in ms (t)
    close_timestamp: int  # Close time in ms (T)
    open: float  # o
    high: float  # h
    low: float  # l
    close: float  # c
    volume: float  # v
    interval: str  # i


async def get_markets(force_refresh: bool = False) -> Dict[str, DecibelMarket]:
    """
    Get all available Decibel markets.
    Results are cached for 30 minutes.
    
    Returns:
        Dictionary mapping symbol (e.g., "BTC") to DecibelMarket
    """
    global _markets_cache, _markets_cache_time
    
    # Check cache
    if not force_refresh and _markets_cache and _markets_cache_time:
        if datetime.utcnow() - _markets_cache_time < MARKETS_CACHE_DURATION:
            return _markets_cache
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{DECIBEL_BASE_URL}/api/v1/markets")
            
            if response.status_code != 200:
                print(f"Decibel markets API error: {response.status_code}")
                return _markets_cache or {}
            
            data = response.json()
            markets = {}
            
            for market_data in data:
                market_name = market_data.get("market_name", "")
                # Extract symbol from market name (e.g., "BTC-PERP" -> "BTC")
                symbol = market_name.split("-")[0] if "-" in market_name else market_name
                
                market = DecibelMarket(
                    market_addr=market_data.get("market_addr", ""),
                    market_name=market_name,
                    symbol=symbol,
                    lot_size=market_data.get("lot_size", 0),
                    min_size=market_data.get("min_size", 0),
                    tick_size=market_data.get("tick_size", 0),
                    px_decimals=market_data.get("px_decimals", 0),
                    sz_decimals=market_data.get("sz_decimals", 0),
                    max_leverage=market_data.get("max_leverage", 0),
                    max_open_interest=market_data.get("max_open_interest", 0)
                )
                markets[symbol] = market
            
            # Update cache
            _markets_cache = markets
            _markets_cache_time = datetime.utcnow()
            
            return markets
            
    except Exception as e:
        print(f"Error fetching Decibel markets: {e}")
        return _markets_cache or {}


async def get_market_address(symbol: str) -> Optional[str]:
    """
    Get market address for a symbol.
    
    Args:
        symbol: Token symbol (e.g., "BTC", "ETH", "APT")
    
    Returns:
        Market address or None if not found
    """
    markets = await get_markets()
    market = markets.get(symbol.upper())
    return market.market_addr if market else None


async def get_prices(market_addr: Optional[str] = None) -> List[DecibelPrice]:
    """
    Get current prices for markets.
    
    Args:
        market_addr: Optional market address filter. Use "all" or omit for all markets.
    
    Returns:
        List of DecibelPrice objects
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            params = {}
            if market_addr and market_addr != "all":
                params["market"] = market_addr
            
            response = await client.get(
                f"{DECIBEL_BASE_URL}/api/v1/prices",
                params=params
            )
            
            if response.status_code != 200:
                print(f"Decibel prices API error: {response.status_code}")
                return []
            
            data = response.json()
            prices = []
            
            for price_data in data:
                price = DecibelPrice(
                    market=price_data.get("market", ""),
                    mark_px=price_data.get("mark_px", 0),
                    mid_px=price_data.get("mid_px", 0),
                    oracle_px=price_data.get("oracle_px", 0),
                    funding_rate_bps=price_data.get("funding_rate_bps", 0),
                    is_funding_positive=price_data.get("is_funding_positive", True),
                    open_interest=price_data.get("open_interest", 0),
                    timestamp_ms=price_data.get("transaction_unix_ms", 0)
                )
                prices.append(price)
            
            return prices
            
    except Exception as e:
        print(f"Error fetching Decibel prices: {e}")
        return []


async def get_price_by_symbol(symbol: str) -> Optional[DecibelPrice]:
    """
    Get current price for a specific symbol.
    
    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
    
    Returns:
        DecibelPrice object or None
    """
    market_addr = await get_market_address(symbol)
    if not market_addr:
        return None
    
    prices = await get_prices(market_addr)
    return prices[0] if prices else None


async def get_candlesticks(
    symbol: str,
    interval: CandlestickInterval,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    days: int = 7
) -> List[DecibelCandle]:
    """
    Get candlestick (OHLC) data for a market.
    
    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        interval: Candlestick interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w)
        start_time: Start time in milliseconds (optional)
        end_time: End time in milliseconds (optional)
        days: Number of days of data if start/end not provided
    
    Returns:
        List of DecibelCandle objects
    """
    market_addr = await get_market_address(symbol)
    if not market_addr:
        print(f"Market not found for symbol: {symbol}")
        return []
    
    # Calculate time range if not provided
    if not end_time:
        end_time = int(datetime.utcnow().timestamp() * 1000)
    if not start_time:
        start_time = end_time - (days * 24 * 60 * 60 * 1000)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "market": market_addr,
                "interval": interval.value,
                "startTime": start_time,
                "endTime": end_time
            }
            
            response = await client.get(
                f"{DECIBEL_BASE_URL}/api/v1/candlesticks",
                params=params
            )
            
            if response.status_code != 200:
                print(f"Decibel candlesticks API error: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            candles = []
            
            for candle_data in data:
                candle = DecibelCandle(
                    timestamp=candle_data.get("t", 0),
                    close_timestamp=candle_data.get("T", 0),
                    open=candle_data.get("o", 0),
                    high=candle_data.get("h", 0),
                    low=candle_data.get("l", 0),
                    close=candle_data.get("c", 0),
                    volume=candle_data.get("v", 0),
                    interval=candle_data.get("i", interval.value)
                )
                candles.append(candle)
            
            return candles
            
    except Exception as e:
        print(f"Error fetching Decibel candlesticks for {symbol}: {e}")
        return []


async def get_chart_data_from_decibel(
    symbol: str,
    days: int = 7
) -> Optional[Dict[str, Any]]:
    """
    Get chart data formatted for the frontend CoinChart component.
    
    Args:
        symbol: Token symbol (e.g., "BTC", "ETH", "APT")
        days: Number of days of history
    
    Returns:
        Dictionary with prices, stats, and metadata for charting
    """
    # Determine appropriate interval based on days
    if days <= 1:
        interval = CandlestickInterval.FIFTEEN_MINUTES
    elif days <= 7:
        interval = CandlestickInterval.ONE_HOUR
    elif days <= 30:
        interval = CandlestickInterval.FOUR_HOURS
    elif days <= 90:
        interval = CandlestickInterval.ONE_DAY
    else:
        interval = CandlestickInterval.ONE_DAY
    
    candles = await get_candlesticks(symbol, interval, days=days)
    
    if not candles:
        return None
    
    # Sort by timestamp
    candles.sort(key=lambda c: c.timestamp)
    
    # Format for frontend
    formatted_prices = [
        {"time": c.timestamp, "value": c.close}
        for c in candles
    ]
    
    # Calculate statistics
    if candles:
        price_values = [c.close for c in candles]
        current_price = price_values[-1]
        start_price = price_values[0]
        high_price = max(c.high for c in candles)
        low_price = min(c.low for c in candles)
        price_change = current_price - start_price
        price_change_percent = (price_change / start_price) * 100 if start_price else 0
        
        stats = {
            "current": current_price,
            "open": start_price,
            "high": high_price,
            "low": low_price,
            "change": price_change,
            "change_percent": round(price_change_percent, 2),
            "period": f"{days}d"
        }
    else:
        stats = None
    
    # Also format OHLCV data for candlestick charts
    ohlcv = [
        {
            "time": c.timestamp,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume
        }
        for c in candles
    ]
    
    return {
        "symbol": symbol.upper(),
        "prices": formatted_prices,
        "ohlcv": ohlcv,
        "stats": stats,
        "days": days,
        "interval": interval.value,
        "data_points": len(formatted_prices),
        "source": "decibel",
        "last_updated": datetime.utcnow().isoformat()
    }


async def get_available_symbols() -> List[str]:
    """
    Get list of available trading symbols on Decibel.
    
    Returns:
        List of symbols (e.g., ["BTC", "ETH", "SOL", ...])
    """
    markets = await get_markets()
    return list(markets.keys())


# Mapping of common symbols that might need special handling
SYMBOL_ALIASES = {
    "BITCOIN": "BTC",
    "ETHEREUM": "ETH",
    "SOLANA": "SOL",
    "APTOS": "APT",
    "BINANCECOIN": "BNB",
    "RIPPLE": "XRP",
    "CARDANO": "ADA",
    "DOGECOIN": "DOGE",
    "AVALANCHE": "AVAX",
    "POLKADOT": "DOT"
}


def normalize_symbol(symbol: str) -> str:
    """Normalize symbol to Decibel format."""
    upper = symbol.upper()
    return SYMBOL_ALIASES.get(upper, upper)
