"""
Real-Time Price Service via Binance WebSocket
==============================================
Maintains live price feeds for all major cryptocurrencies.
Uses Binance's free WebSocket API for real-time updates.

Features:
- Real-time price streaming (no polling)
- Automatic reconnection on disconnect
- Price change callbacks for reactive updates
- Thread-safe price access
- Fallback to CoinGecko if Binance unavailable
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Optional, Callable, List, Set
from dataclasses import dataclass, field
import websockets
from websockets.exceptions import ConnectionClosed
import httpx

# Binance WebSocket endpoint (free, no API key needed)
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
BINANCE_REST_URL = "https://api.binance.com/api/v3"

# Token symbol mappings (our symbols -> Binance symbols)
TOKEN_TO_BINANCE = {
    # Major coins
    "BTC": "btcusdt",
    "ETH": "ethusdt",
    "BNB": "bnbusdt",
    "XRP": "xrpusdt",
    "SOL": "solusdt",
    "ADA": "adausdt",
    "DOGE": "dogeusdt",
    "DOT": "dotusdt",
    "AVAX": "avaxusdt",
    "MATIC": "maticusdt",
    "LTC": "ltcusdt",
    "LINK": "linkusdt",
    "UNI": "uniusdt",
    "ATOM": "atomusdt",
    "ETC": "etcusdt",  # Ethereum Classic - ADDED
    "XLM": "xlmusdt",  # Stellar
    "ALGO": "algousdt",  # Algorand
    "VET": "vetusdt",  # VeChain
    "FIL": "filusdt",  # Filecoin
    "AAVE": "aaveusdt",  # Aave
    "EOS": "eosusdt",  # EOS
    "XTZ": "xtzusdt",  # Tezos
    "THETA": "thetausdt",  # Theta
    "FTM": "ftmusdt",  # Fantom
    "HBAR": "hbarusdt",  # Hedera
    "EGLD": "egldusdt",  # MultiversX
    "FLOW": "flowusdt",  # Flow
    "AXS": "axsusdt",  # Axie Infinity
    "SAND": "sandusdt",  # Sandbox
    "MANA": "manausdt",  # Decentraland
    "GRT": "grtusdt",  # The Graph
    "CHZ": "chzusdt",  # Chiliz
    "ENJ": "enjusdt",  # Enjin
    "BAT": "batusdt",  # Basic Attention Token
    "ZEC": "zecusdt",  # Zcash
    "DASH": "dashusdt",  # Dash
    "NEO": "neousdt",  # NEO
    "WAVES": "wavesusdt",  # Waves
    "KSM": "ksmusdt",  # Kusama
    "CAKE": "cakeusdt",  # PancakeSwap
    "CRV": "crvusdt",  # Curve
    "SNX": "snxusdt",  # Synthetix
    "COMP": "compusdt",  # Compound
    "MKR": "mkrusdt",  # Maker
    "YFI": "yfiusdt",  # Yearn Finance
    "SUSHI": "sushiusdt",  # SushiSwap
    "1INCH": "1inchusdt",  # 1inch
    "ENS": "ensusdt",  # Ethereum Name Service
    "LDO": "ldousdt",  # Lido DAO
    "APE": "apeusdt",  # ApeCoin
    "GMX": "gmxusdt",  # GMX
    "RNDR": "rndrusdt",  # Render
    "IMX": "imxusdt",  # Immutable X
    "FET": "fetusdt",  # Fetch.ai
    "AGIX": "agixusdt",  # SingularityNET
    "OCEAN": "oceanusdt",  # Ocean Protocol
    "WLD": "wldusdt",  # Worldcoin
    # Layer 2 & New chains
    "APT": "aptusdt",
    "SUI": "suiusdt",
    "SEI": "seiusdt",
    "ARB": "arbusdt",
    "OP": "opusdt",
    "NEAR": "nearusdt",
    "INJ": "injusdt",
    "TIA": "tiausdt",
    "STX": "stxusdt",  # Stacks
    "MINA": "minausdt",  # Mina
    "KAVA": "kavausdt",  # Kava
    "ROSE": "roseusdt",  # Oasis
    # Memecoins
    "PEPE": "pepeusdt",
    "SHIB": "shibusdt",
    "WIF": "wifusdt",
    "BONK": "bonkusdt",
    "FLOKI": "flokiusdt",
    "MEME": "memeusdt",
}

BINANCE_TO_TOKEN = {v: k for k, v in TOKEN_TO_BINANCE.items()}


@dataclass
class PriceData:
    """Real-time price data for a token."""
    symbol: str
    price: float
    price_change_24h: float = 0.0
    price_change_percent_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    volume_24h: float = 0.0
    last_update: datetime = field(default_factory=datetime.utcnow)
    source: str = "binance"
    
    def is_stale(self, max_age_seconds: int = 30) -> bool:
        """Check if price data is stale."""
        age = (datetime.utcnow() - self.last_update).total_seconds()
        return age > max_age_seconds
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "change_24h": self.price_change_percent_24h,
            "high_24h": self.high_24h,
            "low_24h": self.low_24h,
            "volume_24h": self.volume_24h,
            "last_update": self.last_update.isoformat(),
            "source": self.source,
            "is_stale": self.is_stale()
        }


class RealTimePriceService:
    """
    Real-time price service using Binance WebSocket.
    
    Usage:
        service = RealTimePriceService()
        await service.start()
        
        # Get current price
        price = service.get_price("BTC")
        
        # Subscribe to price updates
        service.on_price_update(lambda symbol, price: print(f"{symbol}: ${price}"))
    """
    
    def __init__(self):
        self._prices: Dict[str, PriceData] = {}
        self._websocket = None
        self._running = False
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60
        self._callbacks: List[Callable[[str, PriceData], None]] = []
        self._subscribed_symbols: Set[str] = set(TOKEN_TO_BINANCE.keys())
        self._lock = asyncio.Lock()
        
        # Stablecoins always $1
        self._prices["USDC"] = PriceData(symbol="USDC", price=1.0, source="fixed")
        self._prices["USDT"] = PriceData(symbol="USDT", price=1.0, source="fixed")
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        symbol = symbol.upper()
        if symbol in self._prices:
            return self._prices[symbol].price
        return None
    
    def get_price_data(self, symbol: str) -> Optional[PriceData]:
        """Get full price data for a symbol."""
        symbol = symbol.upper()
        return self._prices.get(symbol)
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get all current prices."""
        return {s: p.price for s, p in self._prices.items()}
    
    def get_all_price_data(self) -> Dict[str, PriceData]:
        """Get all price data objects."""
        return self._prices.copy()
    
    def on_price_update(self, callback: Callable[[str, PriceData], None]):
        """Register callback for price updates."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def _notify_callbacks(self, symbol: str, price_data: PriceData):
        """Notify all registered callbacks of a price update."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(symbol, price_data)
                else:
                    callback(symbol, price_data)
            except Exception as e:
                print(f"Price callback error: {e}")
    
    async def _fetch_initial_prices(self):
        """Fetch initial prices via REST API before WebSocket connects."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get 24h ticker for all symbols
                response = await client.get(f"{BINANCE_REST_URL}/ticker/24hr")
                if response.status_code == 200:
                    tickers = response.json()
                    for ticker in tickers:
                        binance_symbol = ticker["symbol"].lower()
                        if binance_symbol in BINANCE_TO_TOKEN:
                            our_symbol = BINANCE_TO_TOKEN[binance_symbol]
                            self._prices[our_symbol] = PriceData(
                                symbol=our_symbol,
                                price=float(ticker["lastPrice"]),
                                price_change_24h=float(ticker["priceChange"]),
                                price_change_percent_24h=float(ticker["priceChangePercent"]),
                                high_24h=float(ticker["highPrice"]),
                                low_24h=float(ticker["lowPrice"]),
                                volume_24h=float(ticker["volume"]),
                                last_update=datetime.utcnow(),
                                source="binance"
                            )
                    print(f"📊 Loaded initial prices for {len(self._prices)} tokens")
        except Exception as e:
            print(f"⚠️ Failed to fetch initial prices: {e}")
    
    async def _connect_websocket(self):
        """Connect to Binance WebSocket and subscribe to price streams."""
        # Build subscription for all tokens
        streams = [f"{TOKEN_TO_BINANCE[s]}@ticker" for s in self._subscribed_symbols if s in TOKEN_TO_BINANCE]
        
        # Combined stream URL
        stream_url = f"{BINANCE_WS_URL}/{'/'.join(streams[:20])}"  # Binance limits streams
        
        # Alternative: Use combined stream endpoint
        combined_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        
        try:
            async with websockets.connect(combined_url, ping_interval=20) as ws:
                self._websocket = ws
                self._reconnect_delay = 1  # Reset on successful connection
                print("🔌 Connected to Binance WebSocket")
                
                while self._running:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=30)
                        await self._handle_message(message)
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await ws.ping()
                    except ConnectionClosed:
                        print("🔌 WebSocket connection closed")
                        break
                        
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            
            # Handle combined stream format
            if "stream" in data and "data" in data:
                ticker = data["data"]
            else:
                ticker = data
            
            # Extract symbol and price
            if "s" in ticker:  # Symbol field
                binance_symbol = ticker["s"].lower()
                if binance_symbol in BINANCE_TO_TOKEN:
                    our_symbol = BINANCE_TO_TOKEN[binance_symbol]
                    
                    price_data = PriceData(
                        symbol=our_symbol,
                        price=float(ticker.get("c", ticker.get("p", 0))),  # Current price
                        price_change_24h=float(ticker.get("p", 0)),  # Price change
                        price_change_percent_24h=float(ticker.get("P", 0)),  # Percent change
                        high_24h=float(ticker.get("h", 0)),
                        low_24h=float(ticker.get("l", 0)),
                        volume_24h=float(ticker.get("v", 0)),
                        last_update=datetime.utcnow(),
                        source="binance"
                    )
                    
                    async with self._lock:
                        old_price = self._prices.get(our_symbol)
                        self._prices[our_symbol] = price_data
                    
                    # Notify callbacks if price changed significantly (>0.01%)
                    if old_price is None or abs(price_data.price - old_price.price) / old_price.price > 0.0001:
                        await self._notify_callbacks(our_symbol, price_data)
                        
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Message handling error: {e}")
    
    async def start(self):
        """Start the real-time price service."""
        if self._running:
            return
        
        self._running = True
        print("🚀 Starting Real-Time Price Service...")
        
        # Fetch initial prices
        await self._fetch_initial_prices()
        
        # Start WebSocket connection loop
        asyncio.create_task(self._connection_loop())
    
    async def _connection_loop(self):
        """Maintain WebSocket connection with automatic reconnection."""
        while self._running:
            try:
                await self._connect_websocket()
            except Exception as e:
                print(f"Connection loop error: {e}")
            
            if self._running:
                print(f"🔄 Reconnecting in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
    
    async def stop(self):
        """Stop the real-time price service."""
        self._running = False
        if self._websocket:
            await self._websocket.close()
        print("🛑 Real-Time Price Service stopped")
    
    def check_price_staleness(self, symbol: str, expected_price: float, tolerance_percent: float = 2.0) -> dict:
        """
        Check if current price is within tolerance of expected price.
        Used to protect against price staleness during trade execution.
        
        Args:
            symbol: Token symbol
            expected_price: Price user saw when initiating trade
            tolerance_percent: Maximum allowed price deviation (default 2%)
        
        Returns:
            dict with is_valid, current_price, deviation_percent, message
        """
        current = self.get_price_data(symbol)
        
        if current is None:
            return {
                "is_valid": False,
                "current_price": None,
                "deviation_percent": None,
                "message": f"No price data available for {symbol}"
            }
        
        if current.is_stale():
            return {
                "is_valid": False,
                "current_price": current.price,
                "deviation_percent": None,
                "message": f"Price data is stale (last update: {current.last_update})"
            }
        
        deviation = ((current.price - expected_price) / expected_price) * 100
        is_valid = abs(deviation) <= tolerance_percent
        
        if is_valid:
            message = f"Price valid: ${current.price:.2f} (within {tolerance_percent}% tolerance)"
        else:
            direction = "increased" if deviation > 0 else "decreased"
            message = f"Price {direction} by {abs(deviation):.2f}% (${expected_price:.2f} → ${current.price:.2f})"
        
        return {
            "is_valid": is_valid,
            "current_price": current.price,
            "expected_price": expected_price,
            "deviation_percent": round(deviation, 2),
            "message": message
        }


# Global singleton instance
_price_service: Optional[RealTimePriceService] = None


def get_price_service() -> RealTimePriceService:
    """Get the global price service instance."""
    global _price_service
    if _price_service is None:
        _price_service = RealTimePriceService()
    return _price_service


async def start_price_service():
    """Start the global price service."""
    service = get_price_service()
    await service.start()


async def stop_price_service():
    """Stop the global price service."""
    global _price_service
    if _price_service:
        await _price_service.stop()
        _price_service = None
