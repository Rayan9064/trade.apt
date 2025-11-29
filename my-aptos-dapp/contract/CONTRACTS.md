# Trade.apt Smart Contracts - MVP

This directory contains the Move smart contracts for the Trade.apt DeFi trading assistant system.

## Overview

Three core contracts have been created for the MVP:

### 1. **TradeRegistry** (`trade_registry.move`)
Manages and records all executed trades on the blockchain.

**Key Features:**
- Records buy, sell, and swap trades
- Tracks trade history per user
- Stores detailed trade metadata (price, tokens, timestamp)
- Immutable trade records

**Entry Functions:**
- `record_buy_trade()` - Record a buy trade
- `record_sell_trade()` - Record a sell trade
- `record_swap_trade()` - Record a swap trade

**View Functions:**
- `get_trade_count()` - Get total number of trades
- `get_user_trades(user)` - Get all trades by a user
- `get_trade(trade_id)` - Get specific trade details

**Trade Structure:**
```move
struct Trade has store, copy, drop {
    trade_id: u64,
    user: address,
    action: u8,              // 0=buy, 1=sell, 2=swap
    token_from: String,
    token_to: String,
    amount_usd: u64,
    executed_price: u64,
    tokens_received: u64,
    timestamp: u64,
}
```

---

### 2. **PriceAlert** (`price_alert.move`)
Manages user price alerts for tokens.

**Key Features:**
- Create alerts for specific price conditions
- Support for <, >, and = operators
- Track alert status (active/inactive)
- Query alerts by user or ID

**Entry Functions:**
- `create_alert_lt(token, price, message)` - Alert when price < target
- `create_alert_gt(token, price, message)` - Alert when price > target
- `create_alert_eq(token, price, message)` - Alert when price = target
- `deactivate_alert(alert_id)` - Deactivate an alert

**View Functions:**
- `get_alert_count()` - Get total number of alerts
- `get_user_active_alerts(user)` - Get user's active alerts
- `get_alert(alert_id)` - Get alert details
- `should_alert_trigger(alert_id, price)` - Check if alert should trigger

**Alert Structure:**
```move
struct Alert has store, copy, drop {
    alert_id: u64,
    user: address,
    token: String,
    operator: u8,            // 0=<, 1=>, 2==
    target_price: u64,
    message: String,
    is_active: bool,
    created_at: u64,
}
```

---

### 3. **UserPortfolio** (`user_portfolio.move`)
Tracks user token positions and portfolio value.

**Key Features:**
- Initialize user portfolios
- Track token holdings and entry prices
- Calculate average entry prices
- Query portfolio composition and value

**Entry Functions:**
- `initialize_portfolio()` - Create a new portfolio for user
- `update_position(token, amount, price)` - Add/update token position
- `remove_position(token)` - Remove a token position

**View Functions:**
- `get_portfolio(user)` - Get entire portfolio
- `get_position(user, token)` - Get specific token position
- `get_portfolio_value(user)` - Get total portfolio USD value

**TokenPosition Structure:**
```move
struct TokenPosition has store, copy, drop {
    token: String,
    amount: u64,
    average_entry_price: u64,
    total_value_usd: u64,
}
```

---

## Module Addresses

In `Move.toml`, the following module addresses are defined:

```toml
[addresses]
message_board_addr = "_"
trade_registry_addr = "_"
price_alert_addr = "_"
user_portfolio_addr = "_"
```

These will be assigned actual addresses when the contracts are published to the network.

---

## Building and Testing

### Compile the contracts:
```bash
cd contract
aptos move compile
```

### Run tests:
```bash
aptos move test
```

### Publish to network:
```bash
aptos move publish --profile <network>
```

---

## Integration with Backend

These contracts are designed to work with the FastAPI backend (`../src/`):

1. **TradeRegistry** - Backend logs trades here after execution
2. **PriceAlert** - Backend queries alerts and triggers notifications
3. **UserPortfolio** - Backend updates portfolio after trades

The JavaScript files in `../scripts/move/` can be used to interact with these contracts from the frontend.

---

## MVP Limitations

- No token transfers (simulation mode)
- Simplified price handling (no decimals)
- Centralized alert management (no distributed oracle)
- Basic portfolio tracking

## Future Enhancements

- Token swap integration with DEX
- Automated trigger execution via Oracle
- Advanced portfolio analytics
- Historical performance tracking
- Multi-asset portfolio rebalancing

---

## Error Codes

### TradeRegistry
- `ERR_REGISTRY_NOT_INITIALIZED (1)` - Registry not found
- `ERR_INVALID_ACTION (2)` - Invalid trade action

### PriceAlert
- `ERR_ALERT_NOT_FOUND (1)` - Alert ID doesn't exist
- `ERR_INVALID_OPERATOR (2)` - Invalid price operator
- `ERR_ALERT_INACTIVE (3)` - Alert is not active

### UserPortfolio
- `ERR_PORTFOLIO_NOT_FOUND (1)` - User portfolio doesn't exist
- `ERR_POSITION_NOT_FOUND (2)` - Token position not found
- `ERR_INVALID_AMOUNT (3)` - Invalid amount provided
