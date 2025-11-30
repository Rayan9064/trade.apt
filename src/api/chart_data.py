"""
Chart Data API
==============
Provides historical price data for charts.
Uses CoinGecko for historical data (free tier).
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# CoinGecko API
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Symbol to CoinGecko ID mapping
SYMBOL_TO_COINGECKO = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "SOL": "solana",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "LTC": "litecoin",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "ETC": "ethereum-classic",
    "XLM": "stellar",
    "ALGO": "algorand",
    "VET": "vechain",
    "FIL": "filecoin",
    "AAVE": "aave",
    "EOS": "eos",
    "XTZ": "tezos",
    "THETA": "theta-token",
    "FTM": "fantom",
    "HBAR": "hedera-hashgraph",
    "EGLD": "elrond-erd-2",
    "FLOW": "flow",
    "AXS": "axie-infinity",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "GRT": "the-graph",
    "CHZ": "chiliz",
    "ENJ": "enjincoin",
    "BAT": "basic-attention-token",
    "ZEC": "zcash",
    "DASH": "dash",
    "NEO": "neo",
    "WAVES": "waves",
    "KSM": "kusama",
    "CAKE": "pancakeswap-token",
    "CRV": "curve-dao-token",
    "SNX": "havven",
    "COMP": "compound-governance-token",
    "MKR": "maker",
    "YFI": "yearn-finance",
    "SUSHI": "sushi",
    "1INCH": "1inch",
    "ENS": "ethereum-name-service",
    "LDO": "lido-dao",
    "APE": "apecoin",
    "GMX": "gmx",
    "RNDR": "render-token",
    "IMX": "immutable-x",
    "FET": "fetch-ai",
    "AGIX": "singularitynet",
    "OCEAN": "ocean-protocol",
    "WLD": "worldcoin-wld",
    "APT": "aptos",
    "SUI": "sui",
    "SEI": "sei-network",
    "ARB": "arbitrum",
    "OP": "optimism",
    "NEAR": "near",
    "INJ": "injective-protocol",
    "TIA": "celestia",
    "STX": "blockstack",
    "MINA": "mina-protocol",
    "KAVA": "kava",
    "ROSE": "oasis-network",
    "PEPE": "pepe",
    "SHIB": "shiba-inu",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
    "FLOKI": "floki",
}


async def get_chart_data(
    symbol: str,
    days: int = 7,
    interval: str = "hourly"
) -> Optional[Dict[str, Any]]:
    """
    Get historical price data for charting.
    
    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        days: Number of days of history (1, 7, 30, 90, 365)
        interval: Data interval - "minutely" (1 day max), "hourly" (90 days max), "daily"
    
    Returns:
        Dictionary with prices, volumes, market_caps arrays
    """
    coingecko_id = SYMBOL_TO_COINGECKO.get(symbol.upper())
    
    if not coingecko_id:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": str(days),
            }
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                print(f"CoinGecko error for {symbol}: {response.status_code}")
                return None
            
            data = response.json()
            
            # Format the data for frontend charts
            prices = data.get("prices", [])
            volumes = data.get("total_volumes", [])
            market_caps = data.get("market_caps", [])
            
            # Convert to chart-friendly format
            formatted_prices = [
                {"time": p[0], "value": p[1]} for p in prices
            ]
            formatted_volumes = [
                {"time": v[0], "value": v[1]} for v in volumes
            ]
            
            # Calculate price statistics
            if prices:
                price_values = [p[1] for p in prices]
                current_price = price_values[-1]
                start_price = price_values[0]
                high_price = max(price_values)
                low_price = min(price_values)
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
            
            return {
                "symbol": symbol.upper(),
                "prices": formatted_prices,
                "volumes": formatted_volumes,
                "stats": stats,
                "days": days,
                "data_points": len(formatted_prices),
                "last_updated": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        print(f"Error fetching chart data for {symbol}: {e}")
        return None


async def get_multi_chart_data(
    symbols: List[str],
    days: int = 7
) -> Dict[str, Any]:
    """
    Get chart data for multiple symbols at once.
    
    Args:
        symbols: List of token symbols
        days: Number of days of history
    
    Returns:
        Dictionary mapping symbols to their chart data
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


async def get_coin_analysis(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive coin analysis for AI trading suggestions.
    
    Includes:
    - Current price and 24h change
    - 7d, 30d, 90d price trends
    - Volume analysis
    - Simple technical indicators
    """
    coingecko_id = SYMBOL_TO_COINGECKO.get(symbol.upper())
    
    if not coingecko_id:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get detailed coin data
            url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "true"  # 7-day sparkline
            }
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            market_data = data.get("market_data", {})
            
            # Extract key metrics
            current_price = market_data.get("current_price", {}).get("usd", 0)
            
            # Price changes
            price_changes = {
                "1h": market_data.get("price_change_percentage_1h_in_currency", {}).get("usd"),
                "24h": market_data.get("price_change_percentage_24h"),
                "7d": market_data.get("price_change_percentage_7d"),
                "30d": market_data.get("price_change_percentage_30d"),
                "1y": market_data.get("price_change_percentage_1y"),
            }
            
            # ATH/ATL analysis
            ath = market_data.get("ath", {}).get("usd", 0)
            atl = market_data.get("atl", {}).get("usd", 0)
            ath_change = market_data.get("ath_change_percentage", {}).get("usd", 0)
            
            # Volume analysis
            volume_24h = market_data.get("total_volume", {}).get("usd", 0)
            market_cap = market_data.get("market_cap", {}).get("usd", 0)
            volume_to_mcap = (volume_24h / market_cap * 100) if market_cap else 0
            
            # Simple trend analysis
            sparkline = market_data.get("sparkline_7d", {}).get("price", [])
            trend = "neutral"
            if sparkline and len(sparkline) > 1:
                recent = sparkline[-24:]  # Last 24 hours
                if recent[-1] > recent[0] * 1.02:
                    trend = "bullish"
                elif recent[-1] < recent[0] * 0.98:
                    trend = "bearish"
            
            # Trading suggestion based on simple analysis
            suggestion = generate_trading_suggestion(
                price_changes, volume_to_mcap, ath_change, trend
            )
            
            return {
                "symbol": symbol.upper(),
                "name": data.get("name"),
                "current_price": current_price,
                "price_changes": price_changes,
                "market_cap": market_cap,
                "volume_24h": volume_24h,
                "volume_to_mcap_ratio": round(volume_to_mcap, 2),
                "ath": ath,
                "ath_change_percent": round(ath_change, 2),
                "atl": atl,
                "trend_7d": trend,
                "sparkline_7d": sparkline[-48:] if sparkline else [],  # Last 2 days
                "suggestion": suggestion,
                "last_updated": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None


def generate_trading_suggestion(
    price_changes: Dict,
    volume_ratio: float,
    ath_change: float,
    trend: str
) -> Dict[str, Any]:
    """
    Generate a simple trading suggestion based on metrics.
    
    This is NOT financial advice - just pattern-based suggestions.
    """
    signals = []
    score = 50  # Neutral starting point
    
    # Short-term momentum
    change_24h = price_changes.get("24h", 0) or 0
    change_7d = price_changes.get("7d", 0) or 0
    
    if change_24h > 5:
        signals.append("📈 Strong 24h momentum (+{:.1f}%)".format(change_24h))
        score += 10
    elif change_24h < -5:
        signals.append("📉 24h pullback ({:.1f}%)".format(change_24h))
        score -= 10
    
    if change_7d > 10:
        signals.append("🚀 Strong weekly trend (+{:.1f}%)".format(change_7d))
        score += 15
    elif change_7d < -10:
        signals.append("⚠️ Weak weekly performance ({:.1f}%)".format(change_7d))
        score -= 15
    
    # Volume analysis
    if volume_ratio > 10:
        signals.append("🔥 High trading volume")
        score += 5
    elif volume_ratio < 2:
        signals.append("😴 Low trading activity")
        score -= 5
    
    # ATH analysis
    if ath_change > -20:
        signals.append("💎 Near all-time high")
    elif ath_change < -80:
        signals.append("💰 Far from ATH - potential value")
        score += 5
    
    # Trend
    if trend == "bullish":
        signals.append("📊 Bullish short-term trend")
        score += 10
    elif trend == "bearish":
        signals.append("📊 Bearish short-term trend")
        score -= 10
    
    # Generate action
    if score >= 70:
        action = "consider_buy"
        action_text = "🟢 Conditions favor buying"
    elif score <= 30:
        action = "consider_sell"
        action_text = "🔴 Conditions suggest caution"
    else:
        action = "hold"
        action_text = "🟡 Neutral - consider holding"
    
    return {
        "action": action,
        "action_text": action_text,
        "score": score,
        "signals": signals,
        "disclaimer": "⚠️ This is not financial advice. Always do your own research."
    }
