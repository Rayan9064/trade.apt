# TradeAPT Frontend 🎨

Next.js frontend application for TradeAPT - an AI-powered trading platform on Aptos.

**🌐 Live:** [https://trade-apt.vercel.app/](https://trade-apt.vercel.app/)

### Deployed Contract Address
**0xf522b301773ca60d8e70f1e258708cbf0735eb6e38f22158563ad92c19c349ea**

---

## 📋 Overview

Modern React frontend built with:
- **Next.js 14** - App Router & Server Components
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Beautiful UI components
- **Aptos Wallet Adapter** - Multi-wallet support

---

## ✨ Features

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

---

## 🛠 Available Commands

The tool utilizes [aptos-cli npm package](https://github.com/aptos-labs/aptos-cli) that lets us run Aptos CLI in a Node environment.

| Script | Description |
|--------|-------------|
| `pnpm dev` | Start development server |
| `pnpm build` | Build for production |
| `pnpm start` | Start production server |
| `pnpm lint` | Run ESLint |
| `pnpm move:publish` | Publish Move contract |
| `pnpm move:test` | Run Move unit tests |
| `pnpm move:compile` | Compile Move contract |
| `pnpm move:upgrade` | Upgrade Move contract |
| `pnpm deploy` | Deploy dapp to Vercel |

For all other available CLI commands, run `npx aptos` to see the full list.

---

## 🔐 Environment Variables

Create `.env.local`:

```env
# Network Configuration
NEXT_PUBLIC_APP_NETWORK=testnet

# Contract Address
NEXT_PUBLIC_MODULE_ADDRESS=0xf522b301773ca60d8e70f1e258708cbf0735eb6e38f22158563ad92c19c349ea

# API Backend
NEXT_PUBLIC_API_URL=https://trade-apt.onrender.com
```

---

## 🚀 Deployment (Vercel)

1. Import project to Vercel
2. Set framework preset to Next.js
3. Configure environment variables
4. Deploy

Automatic deployments on push to `main`.

**Live:** [https://trade-apt.vercel.app/](https://trade-apt.vercel.app/)

---

## License

MIT
