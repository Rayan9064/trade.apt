"""
Trade.apt - DeFi Trading Assistant Server
==========================================
FastAPI server providing endpoints for:
- AI-powered natural language trade parsing
- Real-time crypto price fetching
- Simulated trade execution
- Price alerts management

This is a SIMULATION/DEMO backend - no actual blockchain transactions occur.

Endpoints:
    POST /ai/parse         - Parse natural language trading instructions
    POST /trade/execute    - Execute a parsed trade (simulated)
    GET  /price/{token}    - Get real-time token price
    POST /alerts           - Create a price alert
    GET  /alerts           - List all alerts
    DELETE /alerts/{id}    - Cancel/delete an alert
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from src.ai.parser import parse_user_request, parse_user_request_mock
from src.api.price import get_token_price, get_token_info, get_supported_tokens
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


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class ParseRequest(BaseModel):
    """Request body for /ai/parse endpoint."""
    text: str


class ParseResponse(BaseModel):
    """Response from /ai/parse endpoint."""
    success: bool
    parsed: Optional[dict] = None
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
    Starts background worker on startup, stops on shutdown.
    """
    # Startup
    print("🚀 Trade.apt server starting...")
    start_background_worker()
    print("✅ Background worker started")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
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

@app.post("/ai/parse", response_model=ParseResponse)
async def parse_trading_instruction(request: ParseRequest):
    """
    Parse natural language trading instruction into structured JSON.
    
    Example input:
        {"text": "buy $20 APT if price drops to $7"}
    
    Example output:
        {
            "success": true,
            "parsed": {
                "action": "buy",
                "tokenFrom": "USDC",
                "tokenTo": "APT",
                "amountUsd": 20,
                "conditions": {
                    "type": "price_trigger",
                    "operator": "<",
                    "value": 7
                }
            },
            "original_text": "buy $20 APT if price drops to $7"
        }
    """
    try:
        # Check if OpenAI API key is configured
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
            # Use real OpenAI parsing
            parsed = await parse_user_request(request.text)
        else:
            # Use mock parser for testing without API key
            print("⚠️  No OpenAI API key configured, using mock parser")
            parsed = await parse_user_request_mock(request.text)
        
        return ParseResponse(
            success=True,
            parsed=parsed,
            original_text=request.text
        )
        
    except ValueError as e:
        return ParseResponse(
            success=False,
            error=str(e),
            original_text=request.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI parsing error: {str(e)}")


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
    Get real-time price for a token.
    
    Example: GET /price/APT
    Response: {"token": "APT", "price_usd": 8.45, "timestamp": "..."}
    """
    price = await get_token_price(token)
    
    return PriceResponse(
        token=token.upper(),
        price_usd=price,
        timestamp=datetime.utcnow(),
        error=None if price else f"Could not fetch price for {token}"
    )


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
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"🚀 Starting Trade.apt server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
