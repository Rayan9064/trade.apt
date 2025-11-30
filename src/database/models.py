"""
Database Models for Trade.apt
=============================
Uses SQLite for development, easily switchable to PostgreSQL for production.

This stores:
- User wallets (addresses connected to the app)
- User sessions (login state)
- Trade history (for audit logs)
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets
import json

# Database path
DB_PATH = os.environ.get("DATABASE_PATH", "data/tradeapt.db")


class WalletType(Enum):
    """Supported wallet types."""
    PETRA = "petra"
    PONTEM = "pontem"
    MARTIAN = "martian"
    FEWCHA = "fewcha"
    OTHER = "other"


class NetworkType(Enum):
    """Aptos network types."""
    MAINNET = "mainnet"
    TESTNET = "testnet"
    DEVNET = "devnet"


@dataclass
class User:
    """User model - linked to wallet address."""
    id: int
    wallet_address: str
    wallet_type: str
    display_name: Optional[str]
    network: str
    created_at: datetime
    last_login: datetime
    is_active: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "wallet_address": self.wallet_address,
            "wallet_type": self.wallet_type,
            "display_name": self.display_name or self.short_address,
            "network": self.network,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat(),
            "is_active": self.is_active,
        }
    
    @property
    def short_address(self) -> str:
        """Return shortened wallet address for display."""
        if len(self.wallet_address) > 10:
            return f"{self.wallet_address[:6]}...{self.wallet_address[-4:]}"
        return self.wallet_address


@dataclass
class Session:
    """User session for authentication."""
    id: int
    user_id: int
    session_token: str
    expires_at: datetime
    created_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    @property
    def is_valid(self) -> bool:
        return datetime.utcnow() < self.expires_at


@dataclass
class TradeRecord:
    """Record of trades for history/audit."""
    id: int
    user_id: int
    action: str  # buy, sell, swap
    token_from: str
    token_to: str
    amount_usd: float
    price_at_trade: float
    tx_hash: Optional[str]
    status: str  # pending, completed, failed, cancelled
    created_at: datetime
    completed_at: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "token_from": self.token_from,
            "token_to": self.token_to,
            "amount_usd": self.amount_usd,
            "price_at_trade": self.price_at_trade,
            "tx_hash": self.tx_hash,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


def init_database():
    """Initialize the database with required tables."""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else "data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table - wallet-based authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address TEXT UNIQUE NOT NULL,
            wallet_type TEXT DEFAULT 'petra',
            display_name TEXT,
            network TEXT DEFAULT 'testnet',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Sessions table - for maintaining login state
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Trade history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            token_from TEXT NOT NULL,
            token_to TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            price_at_trade REAL,
            tx_hash TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_wallet ON users(wallet_address)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id)")
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {DB_PATH}")


def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)


# =============================================================================
# User Operations
# =============================================================================

def create_user(
    wallet_address: str,
    wallet_type: str = "petra",
    network: str = "testnet",
    display_name: Optional[str] = None
) -> Optional[User]:
    """Create a new user or return existing one."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute(
            "SELECT * FROM users WHERE wallet_address = ?",
            (wallet_address.lower(),)
        )
        row = cursor.fetchone()
        
        if row:
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE wallet_address = ?",
                (datetime.utcnow(), wallet_address.lower())
            )
            conn.commit()
            
            return User(
                id=row[0],
                wallet_address=row[1],
                wallet_type=row[2],
                display_name=row[3],
                network=row[4],
                created_at=row[5] if isinstance(row[5], datetime) else datetime.fromisoformat(row[5]),
                last_login=datetime.utcnow(),
                is_active=bool(row[7])
            )
        
        # Create new user
        cursor.execute(
            """INSERT INTO users (wallet_address, wallet_type, display_name, network)
               VALUES (?, ?, ?, ?)""",
            (wallet_address.lower(), wallet_type, display_name, network)
        )
        conn.commit()
        
        return User(
            id=cursor.lastrowid,
            wallet_address=wallet_address.lower(),
            wallet_type=wallet_type,
            display_name=display_name,
            network=network,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            is_active=True
        )
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return None
    finally:
        conn.close()


def get_user_by_address(wallet_address: str) -> Optional[User]:
    """Get user by wallet address."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM users WHERE wallet_address = ?",
            (wallet_address.lower(),)
        )
        row = cursor.fetchone()
        
        if row:
            return User(
                id=row[0],
                wallet_address=row[1],
                wallet_type=row[2],
                display_name=row[3],
                network=row[4],
                created_at=row[5] if isinstance(row[5], datetime) else datetime.fromisoformat(str(row[5])),
                last_login=row[6] if isinstance(row[6], datetime) else datetime.fromisoformat(str(row[6])),
                is_active=bool(row[7])
            )
        return None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            return User(
                id=row[0],
                wallet_address=row[1],
                wallet_type=row[2],
                display_name=row[3],
                network=row[4],
                created_at=row[5] if isinstance(row[5], datetime) else datetime.fromisoformat(str(row[5])),
                last_login=row[6] if isinstance(row[6], datetime) else datetime.fromisoformat(str(row[6])),
                is_active=bool(row[7])
            )
        return None
    finally:
        conn.close()


def get_all_users() -> List[User]:
    """Get all users (for admin purposes)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        return [
            User(
                id=row[0],
                wallet_address=row[1],
                wallet_type=row[2],
                display_name=row[3],
                network=row[4],
                created_at=row[5] if isinstance(row[5], datetime) else datetime.fromisoformat(str(row[5])),
                last_login=row[6] if isinstance(row[6], datetime) else datetime.fromisoformat(str(row[6])),
                is_active=bool(row[7])
            )
            for row in rows
        ]
    finally:
        conn.close()


def update_user_display_name(wallet_address: str, display_name: str) -> bool:
    """Update user's display name."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE users SET display_name = ? WHERE wallet_address = ?",
            (display_name, wallet_address.lower())
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def deactivate_user(wallet_address: str) -> bool:
    """Deactivate a user account."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE users SET is_active = 0 WHERE wallet_address = ?",
            (wallet_address.lower(),)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =============================================================================
# Session Operations
# =============================================================================

def create_session(
    user_id: int,
    expires_hours: int = 24,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[str]:
    """Create a new session and return the token."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        cursor.execute(
            """INSERT INTO sessions (user_id, session_token, expires_at, ip_address, user_agent)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, token, expires_at, ip_address, user_agent)
        )
        conn.commit()
        
        return token
    except Exception as e:
        print(f"Error creating session: {e}")
        return None
    finally:
        conn.close()


def validate_session(token: str) -> Optional[User]:
    """Validate a session token and return the user if valid."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT s.*, u.* FROM sessions s
               JOIN users u ON s.user_id = u.id
               WHERE s.session_token = ? AND s.expires_at > ?""",
            (token, datetime.utcnow())
        )
        row = cursor.fetchone()
        
        if row:
            # Session fields: 0-6, User fields: 7-14
            return User(
                id=row[7],
                wallet_address=row[8],
                wallet_type=row[9],
                display_name=row[10],
                network=row[11],
                created_at=row[12] if isinstance(row[12], datetime) else datetime.fromisoformat(str(row[12])),
                last_login=row[13] if isinstance(row[13], datetime) else datetime.fromisoformat(str(row[13])),
                is_active=bool(row[14])
            )
        return None
    finally:
        conn.close()


def delete_session(token: str) -> bool:
    """Delete a session (logout)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_all_user_sessions(user_id: int) -> int:
    """Delete all sessions for a user (logout everywhere)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def cleanup_expired_sessions():
    """Remove expired sessions."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM sessions WHERE expires_at < ?", (datetime.utcnow(),))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


# =============================================================================
# Trade Record Operations
# =============================================================================

def record_trade(
    user_id: int,
    action: str,
    token_from: str,
    token_to: str,
    amount_usd: float,
    price_at_trade: Optional[float] = None,
    tx_hash: Optional[str] = None,
    status: str = "pending"
) -> Optional[int]:
    """Record a trade."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO trades 
               (user_id, action, token_from, token_to, amount_usd, price_at_trade, tx_hash, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, action, token_from, token_to, amount_usd, price_at_trade, tx_hash, status)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error recording trade: {e}")
        return None
    finally:
        conn.close()


def update_trade_status(trade_id: int, status: str, tx_hash: Optional[str] = None) -> bool:
    """Update trade status."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if tx_hash:
            cursor.execute(
                """UPDATE trades SET status = ?, tx_hash = ?, completed_at = ?
                   WHERE id = ?""",
                (status, tx_hash, datetime.utcnow() if status == "completed" else None, trade_id)
            )
        else:
            cursor.execute(
                """UPDATE trades SET status = ?, completed_at = ?
                   WHERE id = ?""",
                (status, datetime.utcnow() if status == "completed" else None, trade_id)
            )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_user_trades(user_id: int, limit: int = 50) -> List[TradeRecord]:
    """Get trade history for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM trades WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        
        return [
            TradeRecord(
                id=row[0],
                user_id=row[1],
                action=row[2],
                token_from=row[3],
                token_to=row[4],
                amount_usd=row[5],
                price_at_trade=row[6],
                tx_hash=row[7],
                status=row[8],
                created_at=row[9] if isinstance(row[9], datetime) else datetime.fromisoformat(str(row[9])),
                completed_at=row[10] if row[10] and isinstance(row[10], datetime) else (datetime.fromisoformat(str(row[10])) if row[10] else None)
            )
            for row in rows
        ]
    finally:
        conn.close()


# Initialize database on import
init_database()
