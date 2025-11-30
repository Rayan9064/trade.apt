# TradeAPT Smart Contracts 📜

Move smart contracts powering TradeAPT's on-chain trading functionality on Aptos.

**🌐 Live App:** [https://trade-apt.vercel.app/](https://trade-apt.vercel.app/)

**🤖 AI Backend:** [https://trade-apt.onrender.com](https://trade-apt.onrender.com)

---

This directory contains the Move smart contracts for the Trade.apt DeFi trading assistant system running on the Aptos blockchain.

## 📋 Table of Contents

- [Overview](#overview)
- [Deployed Contract](#deployed-contract)
- [Contract Architecture](#contract-architecture)
- [Contracts](#contracts)
- [Getting Started](#getting-started)
- [Building & Testing](#building--testing)
- [Deployment](#deployment)
- [Usage Examples](#usage-examples)
- [Integration Guide](#integration-guide)

## Overview

Trade.apt provides a complete DeFi trading experience with:
- **Conditional Orders**: Limit orders with price-based conditions
- **Price Alerts**: User-defined price monitoring and notifications
- **DEX Integration**: Swap router for token exchanges
- **Portfolio Tracking**: Real-time trade and volume tracking

## Deployed Contract

**Mainnet Address**: `0xf522b301773ca60d8e70f1e258708cbf0735eb6e38f22158563ad92c19c349ea`

## Contract Architecture

```
┌─────────────────────────────────────────┐
│       Frontend (Next.js + React)         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Backend (FastAPI)                     │
│  - AI Parsing                            │
│  - Price Fetching                        │
│  - Trade Execution                       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Aptos Blockchain Contracts            │
│  ├─ trade_apt (Main Trading Logic)       │
│  ├─ price_oracle (Price Feeds)           │
│  ├─ swap_router (DEX Integration)        │
│  └─ events (Event Definitions)           │
└──────────────────────────────────────────┘
```

## Contracts

### 1. Trade.apt (Main Module)

**Purpose**: Core trading logic with conditional orders, swaps, and alerts

**Location**: `sources/trade_apt.move`

**Key Structs**:
```move
struct ConditionalOrder {
    order_id: u64,
    owner: address,
    token_in: String,
    token_out: String,
    amount_in: u64,
    min_amount_out: u64,
    condition_type: u8,      // 1=above, 2=below, 3=immediate
    target_price: u64,
    status: u8,              // 1=pending, 2=executed, 3=cancelled, 4=expired
    created_at: u64,
    expires_at: u64,
}

struct PriceAlert {
    alert_id: u64,
    owner: address,
    token: String,
    condition_type: u8,
    target_price: u64,
    is_active: bool,
}
```

**Entry Functions**:
- `initialize()` - Initialize the protocol (admin only)
- `init_user_account()` - Create user trading account
- `execute_swap<TokenIn, TokenOut>()` - Execute immediate swap
- `create_conditional_order()` - Create limit/conditional order
- `cancel_order()` - Cancel a pending order
- `execute_conditional_order()` - Execute order when conditions met
- `create_alert()` - Create price alert
- `trigger_alert()` - Trigger alert when conditions met
- `cancel_alert()` - Cancel an alert

**View Functions**:
- `get_user_stats(address)` - User's trade count, volume, creation time
- `get_protocol_stats()` - Total trades, volume, orders created
- `get_pending_orders_count()` - Number of pending orders

---

### 2. Price Oracle

**Purpose**: Price feed integration with Pyth Network support

**Location**: `sources/price_oracle.move`

**Key Features**:
- Cached price data with staleness checks
- Keeper-based price updates
- Batch price updates support

**Entry Functions**:
- `initialize()` - Initialize oracle configuration
- `add_keeper()` - Add authorized price updater
- `update_price()` - Update single token price
- `batch_update_prices()` - Update multiple prices

**View Functions**:
- `get_price(oracle_addr, token)` - Get current price
- `is_price_fresh(oracle_addr, token)` - Check price staleness
- `get_price_safe(oracle_addr, token)` - Get price with freshness flag

---

### 3. Swap Router

**Purpose**: DEX integration for token swaps

**Location**: `sources/swap_router.move`

**Key Features**:
- Exact input swaps
- Exact output swaps
- Multi-hop swaps
- Price impact calculation

**Entry Functions**:
- `swap_exact_input<CoinIn, CoinOut>()` - Swap exact amount in
- `swap_exact_output<CoinIn, CoinOut>()` - Swap for exact amount out
- `swap_multi_hop<CoinIn, CoinMid, CoinOut>()` - Multi-hop swap

**View Functions**:
- `get_amount_out(amount_in)` - Expected output amount
- `get_amount_in(amount_out)` - Required input amount
- `get_price_impact(amount_in)` - Price impact in basis points

---

### 4. Events

**Purpose**: Centralized event definitions for cross-module use

**Location**: `sources/events.move`

**Event Types**:
- Protocol events (initialized, paused, unpaused)
- User events (registered, settings updated)
- Trading events (market orders, limit orders, stop loss, take profit)
- Alert events (created, triggered, deleted)
- Portfolio events (deposit, withdraw, rebalance)

---

## Getting Started

### Prerequisites

- **Aptos CLI**: Install from https://aptos.dev/en/build/setup-cli
- **Node.js**: v16+ (for scripts)

### Project Structure

```
contract/
├── Move.toml              # Package manifest
├── README.md              # This file
├── sources/
│   ├── trade_apt.move     # Main trading logic
│   ├── price_oracle.move  # Price feed integration
│   ├── swap_router.move   # DEX swap router
│   └── events.move        # Event definitions
└── tests/
    └── trade_apt_tests.move  # Unit tests
```

## Building & Testing

### Compile Contracts

```bash
# Compile all contracts
aptos move compile

# Or use npm script
npm run move:compile
```

### Run Tests

```bash
# Run all tests
aptos move test

# Or use npm script
npm run move:test

# Run with verbose output
aptos move test --verbose
```

## Deployment

### Testnet Deployment

```bash
# Set up test profile
aptos init --profile testnet --network testnet

# Publish contracts to testnet
aptos move publish --profile testnet

# Or use npm script
npm run move:publish
```

### Mainnet Deployment

```bash
# ⚠️ Requires mainnet credentials
aptos init --profile mainnet --network mainnet

# Publish contracts (requires APT for gas)
aptos move publish --profile mainnet
```

## Usage Examples

### Example 1: Create a Conditional Order

```bash
aptos move run \
  --function-id 'trade_apt::trade_apt::create_conditional_order' \
  --args 'string:"USDC"' 'string:"APT"' '20000000' '2000000' '2' '700000000' '86400' \
  --profile testnet
```

### Example 2: Create a Price Alert

```bash
aptos move run \
  --function-id 'trade_apt::trade_apt::create_alert' \
  --args 'string:"APT"' '2' '700000000' \
  --profile testnet
```

### Example 3: Query User Stats

```bash
aptos move view \
  --function-id 'trade_apt::trade_apt::get_user_stats' \
  --args '<user_address>' \
  --profile testnet
```

### Example 4: Get Protocol Stats

```bash
aptos move view \
  --function-id 'trade_apt::trade_apt::get_protocol_stats' \
  --profile testnet
```

## Integration Guide

### With Backend (FastAPI)

**Trade Flow:**
```
User Input → AI Parsing → Validate Conditions → Create Order → Execute when Met
```

**Alert Flow:**
```
User Creates Alert → Store On-chain → Backend Monitors → Trigger when Conditions Met
```

### Error Codes

**trade_apt:**
- `1` - Not initialized
- `2` - Already initialized
- `3` - Insufficient balance
- `4` - Invalid amount
- `5` - Order not found
- `6` - Unauthorized
- `7` - Invalid condition
- `8` - Order expired
- `9` - Slippage exceeded

**price_oracle:**
- `1` - Price stale
- `2` - Invalid price
- `3` - Unauthorized
- `4` - Feed not found

**swap_router:**
- `1` - Insufficient output
- `2` - Invalid path
- `3` - Deadline exceeded
- `4` - Zero amount

## Resources

- [Aptos Documentation](https://aptos.dev/)
- [Move Book](https://move-language.github.io/move/)
- [Aptos Explorer](https://explorer.aptoslabs.com/)

## License

MIT

---

**Last Updated**: November 2025
**Contract Version**: 2.0.0
