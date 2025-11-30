## Trade.apt - DeFi Trading Assistant for Aptos

A full-stack DeFi trading application built on the Aptos blockchain with AI-powered trading capabilities.

### Deployed Contract Address
**0xf522b301773ca60d8e70f1e258708cbf0735eb6e38f22158563ad92c19c349ea**

## Features

- 🤖 **AI-Powered Parsing**: Convert natural language trading instructions to structured JSON
- 💰 **Real-Time Prices**: Fetch live crypto prices from price oracles
- 📊 **Conditional Orders**: Create limit orders with price-based conditions
- 🔔 **Price Alerts**: Set alerts that trigger when tokens reach target prices
- 🔄 **DEX Integration**: Swap router for token exchanges
- 📈 **Portfolio Tracking**: Track user trades and volume

## Smart Contracts

The project includes four Move modules:

- **trade_apt.move** - Main trading module with conditional orders, swaps, and alerts
- **price_oracle.move** - Price oracle integration with Pyth Network support
- **swap_router.move** - DEX router for token swaps (Liquidswap/PancakeSwap integration)
- **events.move** - Centralized event definitions for cross-module use

## Project Structure

```
contract/
├── sources/
│   ├── trade_apt.move      # Main trading logic
│   ├── price_oracle.move   # Price feed integration
│   ├── swap_router.move    # DEX swap router
│   └── events.move         # Event definitions
└── tests/
    └── trade_apt_tests.move  # Unit tests
```

## What tools the template uses?

- React framework
- shadcn/ui + tailwind for styling
- Aptos TS SDK
- Aptos Wallet Adapter
- Node based Move commands
- [Next-pwa](https://ducanh-next-pwa.vercel.app/)

## What Move commands are available?

The tool utilizes [aptos-cli npm package](https://github.com/aptos-labs/aptos-cli) that lets us run Aptos CLI in a Node environment.

Some commands are built-in the template and can be ran as a npm script, for example:

- `npm run move:publish` - a command to publish the Move contract
- `npm run move:test` - a command to run Move unit tests
- `npm run move:compile` - a command to compile the Move contract
- `npm run move:upgrade` - a command to upgrade the Move contract
- `npm run dev` - a command to run the frontend locally
- `npm run deploy` - a command to deploy the dapp to Vercel

For all other available CLI commands, can run `npx aptos` and see a list of all available commands.

## License

MIT
