# TradeAPT 🚀

An AI-powered trading assistant for the Aptos blockchain with natural language commands, real-time price tracking, and automated trading strategies.

**🌐 Live Demo:** [https://trade-apt.vercel.app/](https://trade-apt.vercel.app/)

**🤖 AI Backend:** [https://trade-apt.onrender.com](https://trade-apt.onrender.com)

**📜 Contract Address:** `0xf522b301773ca60d8e70f1e258708cbf0735eb6e38f22158563ad92c19c349ea`

---

## ✨ Features

### Backend (Python/FastAPI)
- 🤖 **AI Trading Agent**: Natural language trading powered by Groq (llama-3.3-70b) or OpenAI GPT-4o-mini
- 💰 **Real-Time Prices**: WebSocket streaming from Binance + REST from CoinGecko
- 📊 **Trade Simulation**: Simulate buy/sell/swap trades with conditional execution
- 🔔 **Price Alerts**: Set alerts that trigger when tokens reach target prices
- ⏰ **Background Worker**: Continuously monitors prices for alerts and pending trades
- 🔐 **Wallet Auth**: Aptos wallet-based authentication
- 🗄️ **Database**: SQLite for users, sessions, trades, and audit logs

### Frontend (Next.js/React)
- 📈 **Interactive Charts**: Real-time price charts with Chart.js
- 💬 **AI Chatbot**: Natural language trading assistant
- 📱 **Responsive Dashboard**: Modern UI with Sidebar, Header, Ticker
- 🎨 **Dark Theme**: Sleek dark mode design
- 🔗 **Wallet Integration**: Aptos wallet connection via Petra/Pontem/etc.
- ⚡ **Live Price Ticker**: SSE-powered real-time price updates

### Smart Contracts (Move)
- 🔄 **Swap Router**: Token swap functionality
- 📊 **Price Oracle**: On-chain price feeds
- 📢 **Events**: On-chain event emission

## Project Structure

```
trade.apt/
├── src/                           # Python Backend
│   ├── ai/
│   │   ├── agent.py              # AI trading agent (Groq/OpenAI)
│   │   └── parser.py             # Trade instruction parser
│   ├── api/
│   │   ├── price.py              # CoinGecko price fetching
│   │   ├── chart_data.py         # OHLC chart data
│   │   └── websocket_price.py    # Binance WebSocket streaming
│   ├── engine/
│   │   ├── trade_engine.py       # Trade simulation logic
│   │   └── alert_engine.py       # Alert system & background worker
│   ├── database/
│   │   └── models.py             # SQLite models (users, sessions, trades)
│   ├── blockchain/
│   │   └── aptos.py              # Aptos wallet verification & faucet
│   └── server.py                 # FastAPI application (924 lines)
├── my-aptos-dapp/                 # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Main dashboard
│   │   │   ├── layout.tsx        # Root layout
│   │   │   ├── login/page.tsx    # Login page
│   │   │   └── wallet/page.tsx   # Wallet management
│   │   ├── components/
│   │   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   │   ├── Header.tsx        # Top header
│   │   │   ├── Ticker.tsx        # Price ticker bar
│   │   │   ├── Chatbot.tsx       # AI chatbot interface
│   │   │   ├── ChartPanel.tsx    # Main chart panel
│   │   │   ├── CoinChart.tsx     # Individual coin chart
│   │   │   ├── WalletPanel.tsx   # Wallet info panel
│   │   │   ├── LivePriceTicker.tsx # Live price component
│   │   │   └── views/            # View components
│   │   └── context/
│   │       ├── PriceContext.tsx  # SSE price streaming
│   │       └── AuthContext.tsx   # Wallet authentication
│   └── contract/                  # Move Smart Contracts
│       └── sources/
│           ├── trade_apt.move
│           ├── swap_router.move
│           ├── price_oracle.move
│           └── events.move
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### 1. Install Backend Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd my-aptos-dapp
npm install
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys:
# GROQ_API_KEY=your-groq-key (recommended - free tier available)
# OPENAI_API_KEY=sk-your-key (alternative)
# COINGECKO_API_KEY=your-key (optional, for higher rate limits)
```

> **Note**: The server works without API keys using mock responses. For full AI capabilities, add your Groq or OpenAI key.

### 4. Run the Backend Server

```bash
# Run with uvicorn
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000

# Or run with Python
python -m src.server
```

The backend will start at `http://localhost:8000`

### 5. Run the Frontend

```bash
cd my-aptos-dapp
npm run dev
```

The frontend will start at `http://localhost:3000`

### 6. View API Documentation

Open your browser to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check

```bash
GET /
GET /health
```

### AI Agent

```bash
# Parse and respond to natural language trading requests
POST /ai/parse
Content-Type: application/json

{
    "text": "buy $20 APT if price drops to $7",
    "wallet_address": "0x1234...",  # optional
    "context": {}                    # optional market context
}
```

**Response:**
```json
{
    "success": true,
    "response": "I'll set up a limit order to buy $20 worth of APT when the price drops to $7...",
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
    }
}
```

### Trade Execution

```bash
POST /trade/execute
Content-Type: application/json

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
```

**Response (Executed):**
```json
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
```

**Response (Pending - condition not met):**
```json
{
    "trade_id": "def456",
    "status": "pending",
    "action": "buy",
    "tokenFrom": "USDC",
    "tokenTo": "APT",
    "amountUsd": 20,
    "executedPrice": 8.50,
    "reason": "Condition not met: APT price is $8.50, waiting for < $7"
}
```

### Price Fetching

```bash
# Get current price
GET /price/APT

# Get detailed token info
GET /price/APT/info

# List supported tokens
GET /tokens
```

### Alerts

```bash
# Create alert
POST /alerts
Content-Type: application/json

{
    "token": "APT",
    "operator": "<",
    "target_price": 7.0,
    "message": "APT dropped below $7!"
}

# List all alerts
GET /alerts

# List active alerts only
GET /alerts?active_only=true

# Get specific alert
GET /alerts/{alert_id}

# Delete alert
DELETE /alerts/{alert_id}

# Cancel alert (mark as cancelled but keep record)
DELETE /alerts/{alert_id}?cancel_only=true
```

### Pending Trades

```bash
# List pending trades
GET /trade/pending

# Cancel pending trade
DELETE /trade/pending/{trade_id}
```

## Supported Tokens

The following tokens are supported for price fetching:

| Symbol | Name |
|--------|------|
| APT | Aptos |
| BTC | Bitcoin |
| ETH | Ethereum |
| SOL | Solana |
| USDC | USD Coin |
| USDT | Tether |
| BNB | Binance Coin |
| XRP | Ripple |
| ADA | Cardano |
| DOGE | Dogecoin |
| AVAX | Avalanche |
| DOT | Polkadot |
| MATIC | Polygon |
| LINK | Chainlink |
| UNI | Uniswap |
| ATOM | Cosmos |
| LTC | Litecoin |
| NEAR | NEAR Protocol |
| ARB | Arbitrum |
| OP | Optimism |
| SUI | Sui |
| SEI | Sei |
| INJ | Injective |
| TIA | Celestia |
| PEPE | Pepe |
| SHIB | Shiba Inu |
| WIF | dogwifhat |
| BONK | Bonk |

## Example Usage with cURL

```bash
# Parse a trading instruction
curl -X POST http://localhost:8000/ai/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "sell $50 ETH when price goes above $2500"}'

# Get APT price
curl http://localhost:8000/price/APT

# Create a price alert
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{"token": "BTC", "operator": ">", "target_price": 50000, "message": "BTC hit 50k!"}'

# Execute a trade
curl -X POST http://localhost:8000/trade/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "buy",
    "tokenFrom": "USDC",
    "tokenTo": "APT",
    "amountUsd": 100,
    "conditions": {"type": "immediate", "operator": null, "value": null}
  }'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key for AI agent (recommended) | None |
| `OPENAI_API_KEY` | OpenAI API key for AI (fallback) | None (uses mock) |
| `COINGECKO_API_KEY` | CoinGecko API key for prices | None (uses free tier) |
| `DATABASE_PATH` | SQLite database path | `./trade_apt.db` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `ALERT_CHECK_INTERVAL` | Background check interval (seconds) | `10` |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend | `http://localhost:8000` |
| `NEXT_PUBLIC_APTOS_NETWORK` | Aptos network (mainnet/testnet) | `testnet` |

## Background Worker

The server starts a background worker that:
- Checks all active alerts every 10 seconds (configurable)
- Monitors pending conditional trades
- Prints to console when alerts trigger or trades execute
- Automatically executes pending trades when conditions are met

## Tech Stack

### Backend
- **Framework**: FastAPI with Uvicorn
- **AI**: Groq (llama-3.3-70b-versatile) / OpenAI (GPT-4o-mini)
- **Database**: SQLite with custom ORM
- **WebSocket**: Binance real-time price streaming
- **REST**: CoinGecko for price data

### Frontend
- **Framework**: Next.js 14.2 with App Router
- **UI**: TailwindCSS 3.4, FontAwesome icons
- **Charts**: Chart.js 4.4 with react-chartjs-2
- **Wallet**: Aptos Wallet Adapter
- **State**: React Context + SSE for real-time prices

### Smart Contracts
- **Language**: Move
- **Network**: Aptos (testnet/mainnet)

---

## 🌐 Deployment

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Set environment variables
3. Deploy automatically on push

**Live:** [https://trade-apt.vercel.app/](https://trade-apt.vercel.app/)

### Backend (Render)

1. Create new Web Service on Render
2. Connect to repository, set root to `src/`
3. Set environment variables
4. Deploy

**Live:** [https://trade-apt.onrender.com](https://trade-apt.onrender.com)

---

## Important Notes

⚠️ **Trade simulation mode:**
- Trades are simulated unless connected to Aptos mainnet
- Always test on testnet first
- No actual funds are at risk in simulation mode

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 🙏 Acknowledgments

- [Aptos Labs](https://aptoslabs.com/) - Blockchain infrastructure
- [Groq](https://groq.com/) - AI inference
- [Vercel](https://vercel.com/) - Frontend hosting
- [Render](https://render.com/) - Backend hosting

---

## License

MIT

---

**Built with ❤️ for the Aptos ecosystem**
