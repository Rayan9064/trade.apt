"""
Trade Engine Module
===================
This module handles trade simulation and execution logic.
It evaluates trade conditions against current prices and returns
simulated execution results.

Features:
- Price staleness protection (rejects if price moved too much)
- Real-time price from WebSocket cache
- Conditional order support

Note: This is a SIMULATION only - no actual blockchain transactions occur.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator
from enum import Enum
import uuid

from src.api.price import get_token_price

# Try to use real-time prices if available
try:
    from src.api.websocket_price import get_price_service
    USE_REALTIME_PRICES = True
except ImportError:
    USE_REALTIME_PRICES = False


class TradeStatus(str, Enum):
    """Possible statuses for a trade."""
    EXECUTED = "executed"
    PENDING = "pending"
    FAILED = "failed"
    REJECTED_STALE_PRICE = "rejected_stale_price"


class TradeCondition(BaseModel):
    """Trade condition model."""
    type: str  # "price_trigger" or "immediate"
    operator: Optional[str] = None  # "<", ">", "<=", ">=", "=="
    value: Optional[float] = None


class TradeRequest(BaseModel):
    """Incoming trade request from parsed AI response."""
    action: str  # "buy", "sell", "swap"
    tokenFrom: str
    tokenTo: str
    amountUsd: float
    conditions: TradeCondition
    expectedPrice: Optional[float] = None  # Price user saw when making request
    maxSlippagePercent: Optional[float] = 2.0  # Max allowed price deviation
    
    @validator('amountUsd')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class TradeResult(BaseModel):
    """Result of trade execution attempt."""
    trade_id: str
    status: TradeStatus
    action: str
    tokenFrom: str
    tokenTo: str
    amountUsd: float
    executedPrice: Optional[float] = None
    expectedPrice: Optional[float] = None
    priceDeviation: Optional[float] = None  # Percentage price moved
    tokensReceived: Optional[float] = None
    timestamp: datetime
    reason: Optional[str] = None


# In-memory storage for pending trades
pending_trades: dict[str, TradeRequest] = {}


async def get_current_price(token: str) -> Optional[float]:
    """Get current price, preferring real-time WebSocket cache."""
    if USE_REALTIME_PRICES:
        service = get_price_service()
        price = service.get_price(token)
        if price is not None:
            return price
    # Fallback to REST API
    return await get_token_price(token)


def check_price_staleness(
    expected_price: Optional[float], 
    current_price: float, 
    max_slippage: float = 2.0
) -> tuple[bool, float]:
    """
    Check if price has moved too much since user made the request.
    
    Args:
        expected_price: Price user saw when making request
        current_price: Current market price
        max_slippage: Maximum allowed deviation in percent (default 2%)
    
    Returns:
        (is_valid, deviation_percent)
    """
    if expected_price is None:
        return True, 0.0
    
    deviation = ((current_price - expected_price) / expected_price) * 100
    is_valid = abs(deviation) <= max_slippage
    
    return is_valid, deviation


def evaluate_condition(condition: TradeCondition, current_price: float) -> bool:
    """
    Evaluate if a trade condition is met based on current price.
    
    Args:
        condition: Trade condition with type, operator, and value
        current_price: Current token price in USD
    
    Returns:
        True if condition is met, False otherwise
    """
    # Immediate execution - always true
    if condition.type == "immediate":
        return True
    
    # Price trigger condition
    if condition.type == "price_trigger":
        if condition.operator is None or condition.value is None:
            return False
        
        target_value = condition.value
        
        if condition.operator == "<":
            return current_price < target_value
        elif condition.operator == ">":
            return current_price > target_value
        elif condition.operator == "<=":
            return current_price <= target_value
        elif condition.operator == ">=":
            return current_price >= target_value
        elif condition.operator == "==":
            # Allow small tolerance for equality
            return abs(current_price - target_value) < 0.01
        else:
            return False
    
    return False


async def execute_trade(trade: TradeRequest) -> TradeResult:
    """
    Attempt to execute a trade based on current market conditions.
    
    Features:
    - Price staleness protection: rejects if price moved more than maxSlippagePercent
    - Uses real-time WebSocket prices when available
    - Supports conditional orders (price triggers)
    
    This is a SIMULATION - no actual blockchain transaction occurs.
    
    Args:
        trade: Trade request with action, tokens, amount, and conditions
    
    Returns:
        TradeResult with execution status and details
    """
    trade_id = str(uuid.uuid4())[:8]
    timestamp = datetime.utcnow()
    
    # Determine which token price to check for condition
    if trade.action == "buy":
        price_check_token = trade.tokenTo
    elif trade.action == "sell":
        price_check_token = trade.tokenFrom
    else:  # swap
        price_check_token = trade.tokenTo
    
    # Fetch current price (prefer real-time WebSocket)
    current_price = await get_current_price(price_check_token)
    
    if current_price is None:
        return TradeResult(
            trade_id=trade_id,
            status=TradeStatus.FAILED,
            action=trade.action,
            tokenFrom=trade.tokenFrom,
            tokenTo=trade.tokenTo,
            amountUsd=trade.amountUsd,
            timestamp=timestamp,
            reason=f"Failed to fetch price for {price_check_token}"
        )
    
    # ==========================================
    # PRICE STALENESS PROTECTION
    # ==========================================
    # If user provided expected price, check if it's still valid
    if trade.expectedPrice is not None:
        max_slippage = trade.maxSlippagePercent or 2.0
        is_valid, deviation = check_price_staleness(
            trade.expectedPrice, 
            current_price, 
            max_slippage
        )
        
        if not is_valid:
            direction = "increased" if deviation > 0 else "decreased"
            return TradeResult(
                trade_id=trade_id,
                status=TradeStatus.REJECTED_STALE_PRICE,
                action=trade.action,
                tokenFrom=trade.tokenFrom,
                tokenTo=trade.tokenTo,
                amountUsd=trade.amountUsd,
                executedPrice=current_price,
                expectedPrice=trade.expectedPrice,
                priceDeviation=round(deviation, 2),
                timestamp=timestamp,
                reason=f"⚠️ Price {direction} by {abs(deviation):.2f}% since your request. "
                       f"Expected ${trade.expectedPrice:.2f}, now ${current_price:.2f}. "
                       f"Please review and try again."
            )
    
    # Evaluate trade condition
    condition_met = evaluate_condition(trade.conditions, current_price)
    
    if condition_met:
        # Simulate execution
        # Calculate tokens received (simplified: amount / price)
        if trade.action == "buy":
            tokens_received = trade.amountUsd / current_price
        elif trade.action == "sell":
            tokens_received = trade.amountUsd  # Receiving USD equivalent
        else:  # swap
            tokens_received = trade.amountUsd / current_price
        
        # Calculate actual deviation if expected price was provided
        deviation = None
        if trade.expectedPrice:
            _, deviation = check_price_staleness(trade.expectedPrice, current_price, 100)
        
        return TradeResult(
            trade_id=trade_id,
            status=TradeStatus.EXECUTED,
            action=trade.action,
            tokenFrom=trade.tokenFrom,
            tokenTo=trade.tokenTo,
            amountUsd=trade.amountUsd,
            executedPrice=current_price,
            expectedPrice=trade.expectedPrice,
            priceDeviation=round(deviation, 2) if deviation else None,
            tokensReceived=round(tokens_received, 8),
            timestamp=timestamp,
            reason=None
        )
    else:
        # Condition not met - store as pending
        pending_trades[trade_id] = trade
        
        condition_desc = f"{trade.conditions.operator} ${trade.conditions.value}"
        
        return TradeResult(
            trade_id=trade_id,
            status=TradeStatus.PENDING,
            action=trade.action,
            tokenFrom=trade.tokenFrom,
            tokenTo=trade.tokenTo,
            amountUsd=trade.amountUsd,
            executedPrice=current_price,
            timestamp=timestamp,
            reason=f"Condition not met: {price_check_token} price is ${current_price:.4f}, waiting for {condition_desc}"
        )


async def check_pending_trades() -> list[TradeResult]:
    """
    Check all pending trades and execute any whose conditions are now met.
    Called periodically by the background worker.
    
    Returns:
        List of TradeResults for trades that were executed
    """
    executed_trades = []
    trades_to_remove = []
    
    for trade_id, trade in pending_trades.items():
        # Determine price check token
        if trade.action == "buy":
            price_check_token = trade.tokenTo
        elif trade.action == "sell":
            price_check_token = trade.tokenFrom
        else:
            price_check_token = trade.tokenTo
        
        # Fetch current price
        current_price = await get_token_price(price_check_token)
        
        if current_price is None:
            continue
        
        # Check if condition is now met
        if evaluate_condition(trade.conditions, current_price):
            # Execute the trade
            if trade.action == "buy":
                tokens_received = trade.amountUsd / current_price
            elif trade.action == "sell":
                tokens_received = trade.amountUsd
            else:
                tokens_received = trade.amountUsd / current_price
            
            result = TradeResult(
                trade_id=trade_id,
                status=TradeStatus.EXECUTED,
                action=trade.action,
                tokenFrom=trade.tokenFrom,
                tokenTo=trade.tokenTo,
                amountUsd=trade.amountUsd,
                executedPrice=current_price,
                tokensReceived=round(tokens_received, 8),
                timestamp=datetime.utcnow(),
                reason="Pending trade condition met"
            )
            
            executed_trades.append(result)
            trades_to_remove.append(trade_id)
            
            print(f"🎯 Pending trade {trade_id} EXECUTED at ${current_price:.4f}")
    
    # Remove executed trades from pending
    for trade_id in trades_to_remove:
        del pending_trades[trade_id]
    
    return executed_trades


def get_pending_trades() -> dict[str, TradeRequest]:
    """Get all pending trades."""
    return pending_trades.copy()


def cancel_pending_trade(trade_id: str) -> bool:
    """
    Cancel a pending trade.
    
    Args:
        trade_id: ID of the trade to cancel
    
    Returns:
        True if trade was cancelled, False if not found
    """
    if trade_id in pending_trades:
        del pending_trades[trade_id]
        return True
    return False
