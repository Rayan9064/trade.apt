# Trade.apt Smart Contracts

This directory contains the Move smart contracts for the Trade.apt DeFi trading assistant system running on the Aptos blockchain.

## 📋 Table of Contents

- [Overview](#overview)
- [Contract Architecture](#contract-architecture)
- [Contracts](#contracts)
- [Getting Started](#getting-started)
- [Building & Testing](#building--testing)
- [Deployment](#deployment)
- [Usage Examples](#usage-examples)
- [Integration Guide](#integration-guide)

## Overview

Trade.apt uses three core smart contracts to handle:
- **Trade Recording**: Immutable ledger of all trades
- **Price Alerts**: User-defined price monitoring
- **Portfolio Tracking**: Real-time portfolio management

These contracts work together with the FastAPI backend to provide a complete DeFi trading experience on Aptos.

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
│  - Trade Simulation                      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Aptos Blockchain Contracts            │
│  ├─ TradeRegistry                        │
│  ├─ PriceAlert                           │
│  └─ UserPortfolio                        │
└──────────────────────────────────────────┘
```

## Contracts

### 1. TradeRegistry

**Purpose**: Immutable record of all executed trades

**Location**: `sources/trade_registry.move`

**Key Structs**:
```move
struct Trade {
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

**Entry Functions**:
- `record_buy_trade()` - Log a buy transaction
- `record_sell_trade()` - Log a sell transaction
- `record_swap_trade()` - Log a token swap

**View Functions**:
- `get_trade_count()` - Total trades recorded
- `get_user_trades(user)` - All trades by user
- `get_trade(trade_id)` - Specific trade details

**Use Cases**:
- Audit trail for all trades
- User trade history
- Performance analytics
- Tax reporting

---

### 2. PriceAlert

**Purpose**: Manage user price monitoring and alerts

**Location**: `sources/price_alert.move`

**Key Structs**:
```move
struct Alert {
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

**Entry Functions**:
- `create_alert_lt(token, price, message)` - Alert when price falls below
- `create_alert_gt(token, price, message)` - Alert when price rises above
- `create_alert_eq(token, price, message)` - Alert at exact price
- `deactivate_alert(alert_id)` - Turn off alert

**View Functions**:
- `get_alert_count()` - Total alerts in system
- `get_user_active_alerts(user)` - User's active alerts
- `get_alert(alert_id)` - Alert details
- `should_alert_trigger(alert_id, price)` - Check trigger condition

**Use Cases**:
- Price monitoring
- Automated notifications
- Trade trigger conditions
- Portfolio watch lists

---

### 3. UserPortfolio

**Purpose**: Track user token positions and portfolio composition

**Location**: `sources/user_portfolio.move`

**Key Structs**:
```move
struct TokenPosition {
    token: String,
    amount: u64,
    average_entry_price: u64,
    total_value_usd: u64,
}

struct Portfolio {
    user: address,
    total_value_usd: u64,
    positions: vector<TokenPosition>,
}
```

**Entry Functions**:
- `initialize_portfolio()` - Create portfolio for user
- `update_position(token, amount, price)` - Add or modify holding
- `remove_position(token)` - Remove token from portfolio

**View Functions**:
- `get_portfolio(user)` - Full portfolio snapshot
- `get_position(user, token)` - Single token position
- `get_portfolio_value(user)` - Total USD value

**Use Cases**:
- Portfolio composition tracking
- Average cost basis tracking
- Position management
- Portfolio valuation

---

## Getting Started

### Prerequisites

- **Move SDK**: Install from https://aptos.dev/en/build/setup-cli
- **Node.js**: v16+ (for scripts)
- **Aptos CLI**: Latest version

### Installation

```bash
# Navigate to contract directory
cd my-aptos-dapp/contract

# Install dependencies (if needed)
# Aptos framework is automatically fetched from Move.toml
```

### Project Structure

```
contract/
├── Move.toml              # Package manifest
├── README.md              # This file
├── CONTRACTS.md           # Detailed contract documentation
├── sources/
│   ├── message_board.move
│   ├── trade_registry.move
│   ├── price_alert.move
│   └── user_portfolio.move
└── tests/
    └── test_end_to_end.move
```

## Building & Testing

### Compile Contracts

```bash
# Compile all contracts
aptos move compile

# Compile with verbose output
aptos move compile --verbose

# Compile specific contract
aptos move compile --package trade_registry_addr
```

### Run Tests

```bash
# Run all tests
aptos move test

# Run specific test
aptos move test --filter test_trade_registry

# Run with verbose output
aptos move test --verbose

# Generate coverage report
aptos move test --coverage
```

### Linting

```bash
# Check for style issues
aptos move lint
```

## Deployment

### Testnet Deployment

```bash
# Set up test profile
aptos init --profile testnet --network testnet

# Publish contracts to testnet
aptos move publish --profile testnet

# View transaction result
# Copy the transaction hash and check on Explorer
```

### Mainnet Deployment

```bash
# ⚠️ Requires mainnet credentials
aptos init --profile mainnet --network mainnet

# Publish contracts (requires APT for gas)
aptos move publish --profile mainnet
```

### Upgrade Existing Contracts

```bash
# Use upgrade capability (if enabled)
aptos move publish --profile testnet --assume-yes
```

## Usage Examples

### Example 1: Record a Trade

```bash
aptos move run \
  --function-id 'trade_registry_addr::trade_registry::record_buy_trade' \
  --args 'string:"USDC"' 'string:"APT"' '100' '8' '12' \
  --profile testnet
```

### Example 2: Create a Price Alert

```bash
aptos move run \
  --function-id 'price_alert_addr::price_alert::create_alert_lt' \
  --args 'string:"APT"' '7' 'string:"APT dropped below $7!"' \
  --profile testnet
```

### Example 3: Initialize Portfolio

```bash
aptos move run \
  --function-id 'user_portfolio_addr::user_portfolio::initialize_portfolio' \
  --profile testnet
```

### Example 4: Query Trade History

```bash
aptos move view \
  --function-id 'trade_registry_addr::trade_registry::get_user_trades' \
  --args '<user_address>' \
  --profile testnet
```

## Integration Guide

### With Backend (FastAPI)

The contracts integrate with the FastAPI backend as follows:

**Trade Recording Flow:**
```
User Input → Backend Parsing → Trade Execution → Record to TradeRegistry
```

**Alert Management Flow:**
```
User Creates Alert → Store in PriceAlert → Backend Monitors → Execute when Triggered
```

**Portfolio Tracking Flow:**
```
Trade Executed → Update UserPortfolio → Query Portfolio Value
```

### JavaScript Integration

Use these scripts in `../../scripts/move/` to interact with contracts:

```javascript
// Example: Get user trades
import { getAptosClient } from '../utils/aptosClient';

const client = getAptosClient();
const trades = await client.getResource(
  userAddress,
  '0x..::trade_registry::Trade'
);
```

### TypeScript Types

Reference types in `../../src/utils/` for contract structures:
- `trade_registry_abi.ts` - Trade types
- `message_board_abi.ts` - Message types (adapt for alerts/portfolio)

## Configuration

### Module Addresses

Edit `Move.toml` to set actual addresses after deployment:

```toml
[addresses]
message_board_addr = "0x..."
trade_registry_addr = "0x..."
price_alert_addr = "0x..."
user_portfolio_addr = "0x..."
```

### Gas Settings

Adjust in `.aptos/config.yaml`:

```yaml
gas_unit_price: 100
max_gas: 100000
```

## Error Handling

Each contract defines specific error codes:

**TradeRegistry:**
- `1` - Registry not initialized
- `2` - Invalid action type

**PriceAlert:**
- `1` - Alert not found
- `2` - Invalid operator
- `3` - Alert inactive

**UserPortfolio:**
- `1` - Portfolio not found
- `2` - Position not found
- `3` - Invalid amount

### Handling Errors in Code

```move
assert!(amount > 0, ERR_INVALID_AMOUNT);
// Aborts with error code 3
```

## Monitoring & Debugging

### View Transactions

```bash
aptos account list-transactions --account <address> --profile testnet
```

### Get Transaction Details

```bash
aptos transaction get-tx --txn-hash <hash> --profile testnet
```

### View Contract Resources

```bash
aptos account resource --account <address> --resource-type '<contract>::<module>::<struct>'
```

## Performance Considerations

- **Trade Recording**: O(1) append operation
- **Portfolio Updates**: O(n) where n = number of positions
- **Alert Queries**: O(m) where m = number of alerts

For production use with many users, consider:
- Sharding trades by date
- Batch alert processing
- Off-chain indexing

## Security Notes

### Current Limitations

- ✅ Immutable trade records
- ⚠️ Centralized alert management (no Oracle)
- ⚠️ Manual portfolio updates (no auto-execution)
- ⚠️ No token transfers (simulation mode)

### Future Security Enhancements

- Oracle-based price feeds for automated triggers
- Multi-sig authorization for critical functions
- Rate limiting for portfolio updates
- Emergency pause mechanism

## FAQ

**Q: Do these contracts execute real trades?**
A: No, this is a simulation system. Trade execution happens in the backend. Contracts only record and track simulated trades.

**Q: Can I modify contract state after deployment?**
A: No, Move contracts are immutable. Update requires publishing a new version.

**Q: What fees do I need?**
A: Gas fees for transactions (typically <$0.01 on Aptos testnet).

**Q: How do I reset my portfolio?**
A: Remove all positions and reinitialize. No built-in reset function by design.

**Q: Can I use these contracts on different networks?**
A: Yes, after redeployment to each network with new addresses.

## Resources

- [Aptos Documentation](https://aptos.dev/)
- [Move Book](https://move-language.github.io/move/)
- [Aptos Explorer](https://explorer.aptoslabs.com/)
- [Move by Example](https://move-by-example.com/)

## Support

For issues or questions:
1. Check `CONTRACTS.md` for detailed contract documentation
2. Review error codes section above
3. Check Aptos documentation
4. Open an issue on GitHub

## License

MIT - See LICENSE file in project root

---

**Last Updated**: November 2024
**Contract Version**: 1.0.0 (MVP)
