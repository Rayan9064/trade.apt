"""
Trade Engine Module
===================
This module handles trade simulation and execution logic.
It evaluates trade conditions against current prices and returns
simulated execution results.

Note: This is a SIMULATION only - no actual blockchain transactions occur.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum
import uuid

from src.api.price import get_token_price


class TradeStatus(str, Enum):
    """Possible statuses for a trade."""
    EXECUTED = "executed"
    PENDING = "pending"
    FAILED = "failed"


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


class TradeResult(BaseModel):
    """Result of trade execution attempt."""
    trade_id: str
    status: TradeStatus
    action: str
    tokenFrom: str
    tokenTo: str
    amountUsd: float
    executedPrice: Optional[float] = None
    tokensReceived: Optional[float] = None
    timestamp: datetime
    reason: Optional[str] = None


# In-memory storage for pending trades
pending_trades: dict[str, TradeRequest] = {}


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
    
    This is a SIMULATION - no actual blockchain transaction occurs.
    The function checks if trade conditions are met and returns
    a simulated execution result.
    
    Args:
        trade: Trade request with action, tokens, amount, and conditions
    
    Returns:
        TradeResult with execution status and details
    """
    trade_id = str(uuid.uuid4())[:8]
    timestamp = datetime.utcnow()
    
    # Determine which token price to check for condition
    # For buy: check the token we're buying (tokenTo)
    # For sell: check the token we're selling (tokenFrom)
    # For swap: check the tokenTo price
    if trade.action == "buy":
        price_check_token = trade.tokenTo
    elif trade.action == "sell":
        price_check_token = trade.tokenFrom
    else:  # swap
        price_check_token = trade.tokenTo
    
    # Fetch current price
    current_price = await get_token_price(price_check_token)
    
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
        
        return TradeResult(
            trade_id=trade_id,
            status=TradeStatus.EXECUTED,
            action=trade.action,
            tokenFrom=trade.tokenFrom,
            tokenTo=trade.tokenTo,
            amountUsd=trade.amountUsd,
            executedPrice=current_price,
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
