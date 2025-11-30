"""
Trade.apt - DeFi Trading Assistant Server
==========================================
FastAPI server providing endpoints for:
- AI-powered natural language trade parsing
- Real-time crypto price streaming via WebSocket/SSE
- Simulated trade execution
- Price alerts management
- User authentication via wallet
- Aptos blockchain integration

Endpoints:
    POST /ai/parse         - Parse natural language trading instructions
    GET  /ai/stream        - SSE stream for live AI updates
    POST /trade/execute    - Execute a parsed trade (simulated)
    GET  /price/{token}    - Get real-time token price
    GET  /prices/stream    - SSE stream for live price updates
    POST /alerts           - Create a price alert
    GET  /alerts           - List all alerts
    DELETE /alerts/{id}    - Cancel/delete an alert
    POST /auth/login       - Login with wallet
    POST /auth/logout      - Logout and invalidate session
    GET  /auth/session     - Validate session
    GET  /wallet/balance   - Get wallet balance
    POST /wallet/faucet    - Request testnet tokens
"""

import os
import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, AsyncGenerator, List

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from src.ai.parser import parse_user_request, parse_user_request_mock, chat_with_ai
from src.ai.agent import process_message as ai_agent_process
from src.api.price import get_token_price, get_token_info, get_supported_tokens, get_multiple_prices
from src.api.websocket_price import (
    get_price_service,
    start_price_service,
    stop_price_service,
    RealTimePriceService,
    PriceData,
)
from src.api.chart_data import get_chart_data
from src.engine.trade_engine import (
    TradeRequest,
    TradeCondition,
    execute_trade,
    get_pending_trades,
    cancel_pending_trade,
)
from src.engine.alert_engine import (
    AlertRequest,
    Alert,
    create_alert,
    get_all_alerts,
    get_active_alerts,
    get_alert,
    cancel_alert,
    delete_alert,
    start_background_worker,
    stop_background_worker,
)

# Database and Blockchain imports
from src.database.models import (
    create_user,
    get_user_by_address,
    get_all_users,
    create_session,
    validate_session,
    delete_session,
    delete_all_user_sessions,
    record_trade,
    get_user_trades,
    User,
)
from src.blockchain.aptos import (
    AptosNetwork,
    verify_wallet_address,
    get_wallet_balance,
    fund_from_faucet,
    get_account_transactions,
    get_explorer_url,
    get_onboarding_info,
)


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class ParseRequest(BaseModel):
    """Request body for /ai/parse endpoint."""
    text: str


class ParseResponse(BaseModel):
    """Response from /ai/parse endpoint."""
    success: bool
    message: Optional[str] = None  # Conversational response
    parsed: Optional[dict] = None  # Trade data if detected
    error: Optional[str] = None
    original_text: str


class PriceResponse(BaseModel):
    """Response from /price/{token} endpoint."""
    token: str
    price_usd: Optional[float]
    timestamp: datetime
    error: Optional[str] = None


class TokenInfoResponse(BaseModel):
    """Detailed token info response."""
    symbol: str
    name: Optional[str]
    price_usd: Optional[float]
    market_cap_usd: Optional[float]
    volume_24h_usd: Optional[float]
    price_change_24h_percent: Optional[float]
    high_24h: Optional[float]
    low_24h: Optional[float]


class AlertResponse(BaseModel):
    """Response for alert operations."""
    success: bool
    alert: Optional[Alert] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Starts background worker and real-time price service on startup.
    """
    # Startup
    print("🚀 Trade.apt server starting...")
    
    # Start real-time price service (Binance WebSocket)
    await start_price_service()
    print("✅ Real-time price service started (Binance WebSocket)")
    
    # Start background worker for alerts
    start_background_worker()
    print("✅ Background worker started")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await stop_price_service()
    print("✅ Real-time price service stopped")
    stop_background_worker()
    print("✅ Background worker stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Trade.apt - DeFi Trading Assistant",
    description="AI-powered trading assistant backend (simulation mode)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


# ----------------------------------------------------------------------------
# AI Parsing Endpoints
# ----------------------------------------------------------------------------

@app.post("/ai/parse")
async def parse_trading_instruction(request: ParseRequest):
    """
    Autonomous AI Agent endpoint.
    
    Handles all trading requests with full context awareness,
    risk assessment, and comprehensive response formatting.
    
    The AI agent:
    - Understands natural language trading instructions
    - Provides real-time price data
    - Assesses risk and provides warnings
    - Handles edge cases and errors gracefully
    - Never executes without user confirmation
    """
    try:
        # Fetch real-time prices for context
        top_tokens = ["BTC", "ETH", "APT", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT"]
        prices = await get_multiple_prices(top_tokens)
        
        # Filter out None values and format prices
        clean_prices = {k: v for k, v in prices.items() if v is not None}
        
        # Use the new AI agent
        result = await ai_agent_process(
            user_message=request.text,
            prices=clean_prices,
            wallet=None,  # Will be passed from frontend when available
            pending_orders=None,
            alerts=None
        )
        
        # Format response for frontend compatibility
        return {
            "success": True,
            "message": result.get("message", ""),
            "parsed": result.get("action") if result.get("action", {}).get("type") != "none" else None,
            "intent": result.get("intent", "chat"),
            "warnings": result.get("warnings", []),
            "suggestions": result.get("suggestions", []),
            "market_context": result.get("market_context"),
            "original_text": request.text
        }
        
    except Exception as e:
        print(f"AI Agent error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "I'm having trouble processing your request. Please try again.",
            "original_text": request.text
        }


# ----------------------------------------------------------------------------
# Trade Execution Endpoints
# ----------------------------------------------------------------------------

@app.post("/trade/execute")
async def execute_trade_endpoint(trade: TradeRequest):
    """
    Execute a parsed trade (simulated).
    
    Checks current price against trade conditions and returns
    either an execution receipt or pending status.
    
    Example input:
        {
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
    
    Example output (executed):
        {
            "trade_id": "abc123",
            "status": "executed",
            "action": "buy",
            "tokenFrom": "USDC",
            "tokenTo": "APT",
            "amountUsd": 20,
            "executedPrice": 6.85,
            "tokensReceived": 2.91970803,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    Example output (pending):
        {
            "trade_id": "def456",
            "status": "pending",
            "reason": "Condition not met: APT price is $8.50, waiting for < $7"
        }
    """
    try:
        result = await execute_trade(trade)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade execution error: {str(e)}")


@app.get("/trade/pending")
async def get_pending_trades_endpoint():
    """Get all pending (conditional) trades."""
    trades = get_pending_trades()
    return {
        "count": len(trades),
        "trades": [
            {
                "trade_id": tid,
                "action": t.action,
                "tokenFrom": t.tokenFrom,
                "tokenTo": t.tokenTo,
                "amountUsd": t.amountUsd,
                "conditions": t.conditions.model_dump()
            }
            for tid, t in trades.items()
        ]
    }


@app.delete("/trade/pending/{trade_id}")
async def cancel_pending_trade_endpoint(trade_id: str):
    """Cancel a pending trade."""
    if cancel_pending_trade(trade_id):
        return {"success": True, "message": f"Trade {trade_id} cancelled"}
    raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")


# ----------------------------------------------------------------------------
# Price Endpoints
# ----------------------------------------------------------------------------

@app.get("/price/{token}", response_model=PriceResponse)
async def get_price_endpoint(token: str):
    """
    Get real-time price for a token (from WebSocket cache, falls back to REST).
    
    Example: GET /price/APT
    Response: {"token": "APT", "price_usd": 8.45, "timestamp": "..."}
    """
    # Try WebSocket cache first (real-time)
    service = get_price_service()
    price_data = service.get_price_data(token.upper())
    
    if price_data:
        return PriceResponse(
            token=token.upper(),
            price_usd=price_data.price,
            timestamp=price_data.last_update,
            error=None
        )
    
    # Fallback to REST API
    price = await get_token_price(token)
    
    return PriceResponse(
        token=token.upper(),
        price_usd=price,
        timestamp=datetime.utcnow(),
        error=None if price else f"Could not fetch price for {token}"
    )


@app.get("/prices/live")
async def get_all_live_prices():
    """
    Get all live prices from WebSocket cache.
    Returns real-time prices with metadata.
    """
    service = get_price_service()
    prices = service.get_all_price_data()
    
    return {
        "prices": {s: p.to_dict() for s, p in prices.items()},
        "count": len(prices),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/prices/stream")
async def stream_prices(request: Request):
    """
    Server-Sent Events (SSE) endpoint for real-time price streaming.
    
    Frontend can subscribe to this endpoint to receive live price updates.
    
    Example (JavaScript):
        const eventSource = new EventSource('/prices/stream');
        eventSource.onmessage = (event) => {
            const prices = JSON.parse(event.data);
            console.log('Price update:', prices);
        };
    """
    async def price_generator() -> AsyncGenerator[str, None]:
        service = get_price_service()
        queue: asyncio.Queue = asyncio.Queue()
        
        # Callback to add price updates to queue
        async def on_price_update(symbol: str, price_data: PriceData):
            await queue.put((symbol, price_data))
        
        # Register callback
        service.on_price_update(on_price_update)
        
        try:
            # Send initial prices
            all_prices = service.get_all_price_data()
            initial_data = {s: p.to_dict() for s, p in all_prices.items()}
            yield f"data: {json.dumps({'type': 'initial', 'prices': initial_data})}\n\n"
            
            # Stream updates
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for price update with timeout
                    symbol, price_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    update = {
                        "type": "update",
                        "symbol": symbol,
                        "price": price_data.to_dict()
                    }
                    yield f"data: {json.dumps(update)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    
        finally:
            # Cleanup callback
            service.remove_callback(on_price_update)
    
    return StreamingResponse(
        price_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.post("/prices/check-staleness")
async def check_price_staleness(
    symbol: str,
    expected_price: float,
    tolerance_percent: float = 2.0
):
    """
    Check if current price is within tolerance of expected price.
    Use this before executing trades to protect against price staleness.
    
    Returns:
        is_valid: True if price is within tolerance
        current_price: Current live price
        deviation_percent: How much price has moved
        message: Human-readable explanation
    """
    service = get_price_service()
    result = service.check_price_staleness(symbol, expected_price, tolerance_percent)
    return result


@app.get("/price/{token}/info", response_model=TokenInfoResponse)
async def get_token_info_endpoint(token: str):
    """Get detailed token information including market data."""
    info = await get_token_info(token)
    
    if not info:
        raise HTTPException(status_code=404, detail=f"Token {token} not found")
    
    return TokenInfoResponse(**info)


@app.get("/tokens")
async def get_supported_tokens_endpoint():
    """Get list of supported tokens."""
    tokens = get_supported_tokens()
    return {
        "count": len(tokens),
        "tokens": tokens
    }


# ----------------------------------------------------------------------------
# Chart Data Endpoints
# ----------------------------------------------------------------------------

@app.get("/chart/{token}")
async def get_chart_data_endpoint(token: str, days: int = 7):
    """
    Get historical OHLC chart data for a token.
    
    Args:
        token: Token symbol (e.g., BTC, ETH, APT)
        days: Number of days of history (1, 7, 30, 90, 365)
    
    Returns:
        OHLC data with timestamps for charting
    """
    if days not in [1, 7, 30, 90, 365]:
        days = 7  # Default to 7 days if invalid
    
    chart_data = await get_chart_data(token, days)
    
    if not chart_data or "error" in chart_data:
        raise HTTPException(
            status_code=404, 
            detail=f"Chart data not found for {token}"
        )
    
    return chart_data


@app.get("/chart/{token}/simple")
async def get_simple_chart_data_endpoint(token: str, days: int = 7):
    """
    Get simplified price history for sparkline charts.
    Returns just prices without OHLC detail.
    """
    chart_data = await get_chart_data(token, days)
    
    if not chart_data or "error" in chart_data:
        raise HTTPException(
            status_code=404, 
            detail=f"Chart data not found for {token}"
        )
    
    # Extract just closing prices for simple charts
    return {
        "token": chart_data["token"],
        "days": days,
        "prices": chart_data["close"],
        "timestamps": chart_data["timestamps"],
        "current_price": chart_data["close"][-1] if chart_data["close"] else None,
        "price_change_percent": (
            ((chart_data["close"][-1] - chart_data["close"][0]) / chart_data["close"][0] * 100)
            if chart_data["close"] and len(chart_data["close"]) > 1
            else 0
        )
    }


# ----------------------------------------------------------------------------
# Alert Endpoints
# ----------------------------------------------------------------------------

@app.post("/alerts", response_model=AlertResponse)
async def create_alert_endpoint(request: AlertRequest):
    """
    Create a new price alert.
    
    Example input:
        {
            "token": "APT",
            "operator": "<",
            "target_price": 7.0,
            "message": "APT dropped below $7!"
        }
    """
    try:
        alert = create_alert(request)
        return AlertResponse(
            success=True,
            alert=alert,
            message=f"Alert created: {alert.token} {alert.operator.value} ${alert.target_price}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/alerts")
async def list_alerts_endpoint(active_only: bool = False):
    """
    List all alerts.
    
    Query params:
        active_only: If true, only return active (not triggered) alerts
    """
    if active_only:
        alerts_list = get_active_alerts()
    else:
        alerts_list = get_all_alerts()
    
    return {
        "count": len(alerts_list),
        "alerts": alerts_list
    }


@app.get("/alerts/{alert_id}")
async def get_alert_endpoint(alert_id: str):
    """Get a specific alert by ID."""
    alert = get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert


@app.delete("/alerts/{alert_id}")
async def delete_alert_endpoint(alert_id: str, cancel_only: bool = False):
    """
    Delete or cancel an alert.
    
    Query params:
        cancel_only: If true, just mark as cancelled instead of deleting
    """
    if cancel_only:
        if cancel_alert(alert_id):
            return {"success": True, "message": f"Alert {alert_id} cancelled"}
    else:
        if delete_alert(alert_id):
            return {"success": True, "message": f"Alert {alert_id} deleted"}
    
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


# ============================================================================
# Authentication Endpoints
# ============================================================================

class LoginRequest(BaseModel):
    """Request for wallet login."""
    wallet_address: str
    wallet_type: str = "petra"
    network: str = "testnet"
    signature: Optional[str] = None  # For signature verification


class LoginResponse(BaseModel):
    """Response from login."""
    success: bool
    session_token: Optional[str] = None
    user: Optional[dict] = None
    message: str


@app.post("/auth/login", response_model=LoginResponse)
async def login_with_wallet(request: LoginRequest, req: Request):
    """
    Login with a wallet address.
    
    In production, this should verify a signed message from the wallet.
    For hackathon demo, we trust the wallet address from the frontend.
    """
    # Validate wallet address format
    if not await verify_wallet_address(request.wallet_address):
        raise HTTPException(
            status_code=400, 
            detail="Invalid Aptos wallet address format"
        )
    
    # Create or get user
    user = create_user(
        wallet_address=request.wallet_address,
        wallet_type=request.wallet_type,
        network=request.network
    )
    
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    # Create session
    ip_address = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")
    
    session_token = create_session(
        user_id=user.id,
        expires_hours=24,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not session_token:
        raise HTTPException(status_code=500, detail="Failed to create session")
    
    return LoginResponse(
        success=True,
        session_token=session_token,
        user=user.to_dict(),
        message="Login successful"
    )


@app.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout and invalidate session."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No session token provided")
    
    token = authorization.replace("Bearer ", "")
    
    if delete_session(token):
        return {"success": True, "message": "Logged out successfully"}
    else:
        return {"success": False, "message": "Session not found or already expired"}


@app.get("/auth/session")
async def validate_session_endpoint(authorization: Optional[str] = Header(None)):
    """Validate current session and return user info."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No session token provided")
    
    token = authorization.replace("Bearer ", "")
    user = validate_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "valid": True,
        "user": user.to_dict()
    }


@app.get("/auth/users")
async def list_all_users():
    """Get all registered users (admin endpoint)."""
    users = get_all_users()
    return {
        "count": len(users),
        "users": [u.to_dict() for u in users]
    }


# ============================================================================
# Wallet & Blockchain Endpoints
# ============================================================================

@app.get("/wallet/balance/{address}")
async def get_wallet_balance_endpoint(
    address: str, 
    network: str = "testnet"
):
    """Get wallet balance from Aptos blockchain."""
    # Validate address
    if not await verify_wallet_address(address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    # Get network enum
    try:
        net = AptosNetwork(network)
    except ValueError:
        net = AptosNetwork.TESTNET
    
    # Get APT price for USD conversion
    apt_price = None
    service = get_price_service()
    if service:
        price_data = service.get_price("APT")
        if price_data:
            apt_price = price_data.price
    
    balance = await get_wallet_balance(address, net, apt_price)
    
    if not balance:
        raise HTTPException(status_code=404, detail="Could not fetch wallet balance")
    
    return {
        "address": address,
        "network": network,
        "apt_balance": balance.apt_balance,
        "apt_balance_octas": balance.apt_balance_octas,
        "usd_value": balance.usd_value,
        "apt_price": apt_price
    }


class FaucetRequest(BaseModel):
    """Request tokens from faucet."""
    address: str
    amount_apt: float = 1.0
    network: str = "testnet"


@app.post("/wallet/faucet")
async def request_faucet_tokens(request: FaucetRequest):
    """
    Request free testnet/devnet tokens from the Aptos faucet.
    
    This only works on testnet and devnet, not mainnet.
    """
    # Validate address
    if not await verify_wallet_address(request.address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    # Get network
    try:
        net = AptosNetwork(request.network)
    except ValueError:
        net = AptosNetwork.TESTNET
    
    if net == AptosNetwork.MAINNET:
        raise HTTPException(
            status_code=400, 
            detail="Faucet not available on mainnet. Please acquire APT through an exchange."
        )
    
    # Request from faucet
    result = await fund_from_faucet(
        address=request.address,
        amount_apt=request.amount_apt,
        network=net
    )
    
    # Return the result (includes helpful info even if API fails)
    return result


@app.get("/wallet/transactions/{address}")
async def get_wallet_transactions(
    address: str,
    network: str = "testnet",
    limit: int = 25
):
    """Get recent transactions for a wallet."""
    if not await verify_wallet_address(address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    try:
        net = AptosNetwork(network)
    except ValueError:
        net = AptosNetwork.TESTNET
    
    transactions = await get_account_transactions(address, net, limit)
    
    return {
        "address": address,
        "network": network,
        "count": len(transactions),
        "transactions": transactions,
        "explorer_url": get_explorer_url(address=address, network=net)
    }


@app.get("/onboarding")
async def get_onboarding():
    """
    Get onboarding information for new users.
    Includes wallet setup guide, faucet links, etc.
    """
    return get_onboarding_info()


# ============================================================================
# Trade History Endpoints
# ============================================================================

@app.get("/trades/history")
async def get_trade_history(
    authorization: Optional[str] = Header(None),
    limit: int = 50
):
    """Get trade history for authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    user = validate_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    trades = get_user_trades(user.id, limit)
    
    return {
        "count": len(trades),
        "trades": [t.to_dict() for t in trades]
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting Trade.apt server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
