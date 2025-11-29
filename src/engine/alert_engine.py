"""
Alert Engine Module
===================
This module handles price alerts - users can register alerts that trigger
when a token reaches a specific price. A background worker checks prices
periodically and fires alerts when conditions are met.

Features:
- In-memory alert storage
- Background price checking loop
- Console notifications when alerts trigger
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable
from pydantic import BaseModel
from enum import Enum
import uuid
import os
from dotenv import load_dotenv

from src.api.price import get_token_price
from src.engine.trade_engine import check_pending_trades

load_dotenv()

# Get check interval from environment or default to 10 seconds
ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "10"))


class AlertOperator(str, Enum):
    """Operators for price comparison."""
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="


class AlertStatus(str, Enum):
    """Status of an alert."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"


class Alert(BaseModel):
    """Price alert model."""
    id: str
    token: str
    operator: AlertOperator
    target_price: float
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime
    triggered_at: Optional[datetime] = None
    triggered_price: Optional[float] = None
    message: Optional[str] = None


class AlertRequest(BaseModel):
    """Request to create a new alert."""
    token: str
    operator: str  # "<", ">", "<=", ">="
    target_price: float
    message: Optional[str] = None


# In-memory storage for alerts
alerts: dict[str, Alert] = {}

# Background task reference
background_task: Optional[asyncio.Task] = None

# Callback for alert notifications (can be set by server)
alert_callback: Optional[Callable[[Alert, float], None]] = None


def create_alert(request: AlertRequest) -> Alert:
    """
    Create a new price alert.
    
    Args:
        request: Alert request with token, operator, target_price
    
    Returns:
        Created Alert object
    """
    alert_id = str(uuid.uuid4())[:8]
    
    # Map string operator to enum
    operator_map = {
        "<": AlertOperator.LESS_THAN,
        ">": AlertOperator.GREATER_THAN,
        "<=": AlertOperator.LESS_EQUAL,
        ">=": AlertOperator.GREATER_EQUAL,
    }
    
    operator = operator_map.get(request.operator)
    if operator is None:
        raise ValueError(f"Invalid operator: {request.operator}. Use <, >, <=, or >=")
    
    alert = Alert(
        id=alert_id,
        token=request.token.upper(),
        operator=operator,
        target_price=request.target_price,
        status=AlertStatus.ACTIVE,
        created_at=datetime.utcnow(),
        message=request.message
    )
    
    alerts[alert_id] = alert
    print(f"🔔 Alert created: {alert.token} {alert.operator.value} ${alert.target_price}")
    
    return alert


def get_all_alerts() -> list[Alert]:
    """Get all alerts (active, triggered, and cancelled)."""
    return list(alerts.values())


def get_active_alerts() -> list[Alert]:
    """Get only active (not yet triggered) alerts."""
    return [a for a in alerts.values() if a.status == AlertStatus.ACTIVE]


def get_alert(alert_id: str) -> Optional[Alert]:
    """Get a specific alert by ID."""
    return alerts.get(alert_id)


def cancel_alert(alert_id: str) -> bool:
    """
    Cancel an active alert.
    
    Args:
        alert_id: ID of the alert to cancel
    
    Returns:
        True if alert was cancelled, False if not found or already triggered
    """
    if alert_id in alerts:
        alert = alerts[alert_id]
        if alert.status == AlertStatus.ACTIVE:
            alert.status = AlertStatus.CANCELLED
            print(f"🔕 Alert {alert_id} cancelled")
            return True
    return False


def delete_alert(alert_id: str) -> bool:
    """
    Delete an alert completely.
    
    Args:
        alert_id: ID of the alert to delete
    
    Returns:
        True if alert was deleted, False if not found
    """
    if alert_id in alerts:
        del alerts[alert_id]
        return True
    return False


def check_alert_condition(alert: Alert, current_price: float) -> bool:
    """
    Check if an alert condition is met.
    
    Args:
        alert: Alert to check
        current_price: Current token price
    
    Returns:
        True if condition is met
    """
    if alert.operator == AlertOperator.LESS_THAN:
        return current_price < alert.target_price
    elif alert.operator == AlertOperator.GREATER_THAN:
        return current_price > alert.target_price
    elif alert.operator == AlertOperator.LESS_EQUAL:
        return current_price <= alert.target_price
    elif alert.operator == AlertOperator.GREATER_EQUAL:
        return current_price >= alert.target_price
    return False


async def check_alerts():
    """
    Check all active alerts against current prices.
    Triggers alerts whose conditions are met.
    
    Returns:
        List of triggered alerts
    """
    triggered = []
    active = get_active_alerts()
    
    if not active:
        return triggered
    
    # Get unique tokens to check
    tokens = list(set(a.token for a in active))
    
    # Fetch prices for all tokens
    for token in tokens:
        current_price = await get_token_price(token)
        
        if current_price is None:
            continue
        
        # Check alerts for this token
        for alert in active:
            if alert.token != token:
                continue
            
            if check_alert_condition(alert, current_price):
                # Trigger the alert
                alert.status = AlertStatus.TRIGGERED
                alert.triggered_at = datetime.utcnow()
                alert.triggered_price = current_price
                
                triggered.append(alert)
                
                # Console notification
                print(f"\n🚨 ALERT TRIGGERED! 🚨")
                print(f"   Token: {alert.token}")
                print(f"   Condition: {alert.operator.value} ${alert.target_price}")
                print(f"   Current Price: ${current_price:.4f}")
                if alert.message:
                    print(f"   Message: {alert.message}")
                print()
                
                # Call callback if set
                if alert_callback:
                    alert_callback(alert, current_price)
    
    return triggered


async def background_worker():
    """
    Background worker that periodically checks prices for alerts and pending trades.
    Runs every ALERT_CHECK_INTERVAL seconds.
    """
    print(f"🔄 Background worker started (checking every {ALERT_CHECK_INTERVAL}s)")
    
    while True:
        try:
            # Check alerts
            triggered_alerts = await check_alerts()
            if triggered_alerts:
                print(f"   {len(triggered_alerts)} alert(s) triggered")
            
            # Check pending trades
            executed_trades = await check_pending_trades()
            if executed_trades:
                print(f"   {len(executed_trades)} pending trade(s) executed")
            
            # Wait for next check
            await asyncio.sleep(ALERT_CHECK_INTERVAL)
            
        except asyncio.CancelledError:
            print("🛑 Background worker stopped")
            break
        except Exception as e:
            print(f"❌ Background worker error: {e}")
            await asyncio.sleep(ALERT_CHECK_INTERVAL)


def start_background_worker():
    """Start the background worker task."""
    global background_task
    
    if background_task is None or background_task.done():
        background_task = asyncio.create_task(background_worker())
        return True
    return False


def stop_background_worker():
    """Stop the background worker task."""
    global background_task
    
    if background_task and not background_task.done():
        background_task.cancel()
        background_task = None
        return True
    return False


def set_alert_callback(callback: Callable[[Alert, float], None]):
    """
    Set a callback function to be called when an alert triggers.
    
    Args:
        callback: Function that takes (Alert, current_price) as arguments
    """
    global alert_callback
    alert_callback = callback
