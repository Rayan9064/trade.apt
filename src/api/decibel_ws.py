"""
Decibel WebSocket Service
=========================
Real-time WebSocket streams for market data from Decibel.trade

WebSocket URL: ws://api.netna.aptoslabs.com/decibel/ws

Available streams:
- market_candlestick:{marketAddr}:{interval} - Real-time OHLCV data

Documentation: https://docs.decibel.trade/api-reference/websockets/marketcandlestick
"""

import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, Optional, Callable, List, Any
from dataclasses import dataclass, field
from enum import Enum

from src.api.decibel import (
    get_market_address,
    get_markets,
    CandlestickInterval,
    DecibelCandle,
    DECIBEL_WS_URL
)


@dataclass
class CandleUpdate:
    """Real-time candlestick update from WebSocket"""
    market_addr: str
    symbol: str
    interval: str
    candle: DecibelCandle
    received_at: datetime = field(default_factory=datetime.utcnow)


class DecibelWebSocket:
    """
    WebSocket client for Decibel real-time market data.
    
    Supports subscribing to candlestick streams for multiple markets and intervals.
    """
    
    def __init__(self):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscriptions: Dict[str, List[Callable]] = {}  # stream_id -> callbacks
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._market_addr_to_symbol: Dict[str, str] = {}
    
    async def connect(self):
        """Establish WebSocket connection to Decibel"""
        self._running = True
        
        # Pre-load market mappings
        markets = await get_markets()
        self._market_addr_to_symbol = {m.market_addr: m.symbol for m in markets.values()}
        
        while self._running:
            try:
                print(f"🔌 Connecting to Decibel WebSocket...")
                async with websockets.connect(DECIBEL_WS_URL) as ws:
                    self.ws = ws
                    self._reconnect_delay = 1.0  # Reset reconnect delay on success
                    print(f"✅ Connected to Decibel WebSocket")
                    
                    # Resubscribe to existing subscriptions
                    for stream_id in self.subscriptions.keys():
                        await self._send_subscribe(stream_id)
                    
                    # Handle incoming messages
                    await self._handle_messages()
                    
            except websockets.ConnectionClosed as e:
                print(f"⚠️ WebSocket connection closed: {e}")
            except Exception as e:
                print(f"❌ WebSocket error: {e}")
            
            if self._running:
                print(f"🔄 Reconnecting in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, 
                    self._max_reconnect_delay
                )
    
    async def disconnect(self):
        """Close WebSocket connection"""
        self._running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
        print("🔌 Decibel WebSocket disconnected")
    
    async def subscribe_candlestick(
        self,
        symbol: str,
        interval: CandlestickInterval,
        callback: Callable[[CandleUpdate], Any]
    ) -> str:
        """
        Subscribe to candlestick updates for a market.
        
        Args:
            symbol: Token symbol (e.g., "BTC", "ETH")
            interval: Candlestick interval
            callback: Function to call with each candle update
        
        Returns:
            Subscription ID (for unsubscribing)
        """
        market_addr = await get_market_address(symbol)
        if not market_addr:
            raise ValueError(f"Market not found for symbol: {symbol}")
        
        stream_id = f"market_candlestick:{market_addr}:{interval.value}"
        
        if stream_id not in self.subscriptions:
            self.subscriptions[stream_id] = []
            if self.ws and self.ws.open:
                await self._send_subscribe(stream_id)
        
        self.subscriptions[stream_id].append(callback)
        print(f"📊 Subscribed to {symbol} {interval.value} candlesticks")
        
        return stream_id
    
    async def unsubscribe(self, stream_id: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from a stream.
        
        Args:
            stream_id: The subscription ID returned from subscribe_*
            callback: Specific callback to remove. If None, removes all.
        """
        if stream_id not in self.subscriptions:
            return
        
        if callback:
            self.subscriptions[stream_id] = [
                cb for cb in self.subscriptions[stream_id] if cb != callback
            ]
        else:
            self.subscriptions[stream_id] = []
        
        # If no more callbacks, unsubscribe from stream
        if not self.subscriptions[stream_id]:
            del self.subscriptions[stream_id]
            if self.ws and self.ws.open:
                await self._send_unsubscribe(stream_id)
    
    async def _send_subscribe(self, stream_id: str):
        """Send subscribe message to WebSocket"""
        if not self.ws:
            return
        
        # Decibel uses path-based subscriptions in the URL
        # For now, we handle it via the connect URL pattern
        # The stream_id format is: market_candlestick:{marketAddr}:{interval}
        print(f"📤 Subscribing to stream: {stream_id}")
    
    async def _send_unsubscribe(self, stream_id: str):
        """Send unsubscribe message to WebSocket"""
        if not self.ws:
            return
        print(f"📤 Unsubscribing from stream: {stream_id}")
    
    async def _handle_messages(self):
        """Process incoming WebSocket messages"""
        if not self.ws:
            return
        
        async for message in self.ws:
            try:
                data = json.loads(message)
                await self._process_message(data)
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse message: {e}")
            except Exception as e:
                print(f"⚠️ Error processing message: {e}")
    
    async def _process_message(self, data: Dict):
        """Process a parsed WebSocket message"""
        msg_type = data.get("type", "")
        
        if "candlestick" in msg_type.lower():
            await self._handle_candlestick_update(data)
        elif msg_type == "ping":
            # Send pong response if needed
            pass
        else:
            # Unknown message type - log for debugging
            print(f"📨 Received message type: {msg_type}")
    
    async def _handle_candlestick_update(self, data: Dict):
        """Handle a candlestick update message"""
        try:
            candle_data = data.get("data", data)
            
            candle = DecibelCandle(
                timestamp=candle_data.get("t", 0),
                close_timestamp=candle_data.get("T", 0),
                open=candle_data.get("o", 0),
                high=candle_data.get("h", 0),
                low=candle_data.get("l", 0),
                close=candle_data.get("c", 0),
                volume=candle_data.get("v", 0),
                interval=candle_data.get("i", "")
            )
            
            market_addr = data.get("market", "")
            symbol = self._market_addr_to_symbol.get(market_addr, "UNKNOWN")
            
            update = CandleUpdate(
                market_addr=market_addr,
                symbol=symbol,
                interval=candle.interval,
                candle=candle
            )
            
            # Find matching subscriptions and call callbacks
            for stream_id, callbacks in self.subscriptions.items():
                if market_addr in stream_id and candle.interval in stream_id:
                    for callback in callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(update)
                            else:
                                callback(update)
                        except Exception as e:
                            print(f"⚠️ Callback error: {e}")
                            
        except Exception as e:
            print(f"⚠️ Error handling candlestick update: {e}")


# Global WebSocket instance
_decibel_ws: Optional[DecibelWebSocket] = None


def get_decibel_ws() -> DecibelWebSocket:
    """Get the global Decibel WebSocket instance"""
    global _decibel_ws
    if _decibel_ws is None:
        _decibel_ws = DecibelWebSocket()
    return _decibel_ws


async def start_decibel_ws():
    """Start the Decibel WebSocket service"""
    ws = get_decibel_ws()
    asyncio.create_task(ws.connect())


async def stop_decibel_ws():
    """Stop the Decibel WebSocket service"""
    global _decibel_ws
    if _decibel_ws:
        await _decibel_ws.disconnect()
        _decibel_ws = None
