# TradeAPT Python Backend 🐍

AI-powered trading backend service for TradeAPT, providing natural language processing, price feeds, and trade execution.

**Live API:** [https://trade-apt.onrender.com](https://trade-apt.onrender.com)

---

## 📋 Overview

This backend service provides:
- **AI Agent**: Natural language command processing using Groq LLM
- **Price API**: Real-time cryptocurrency price data
- **WebSocket Server**: Live price streaming
- **Trade Engine**: Automated trade execution
- **Alert Engine**: Price alert monitoring and notifications

---

## 🏗 Architecture

```
src/
├── server.py           # FastAPI main server
├── ai/
│   ├── agent.py        # Groq LLM agent implementation
│   └── parser.py       # Intent parsing & command extraction
├── api/
│   ├── price.py        # Price REST endpoints
│   ├── chart_data.py   # Chart data endpoints
│   └── websocket_price.py  # WebSocket price streaming
├── blockchain/
│   └── aptos.py        # Aptos SDK integration
├── database/
│   └── models.py       # SQLAlchemy data models
└── engine/
    ├── trade_engine.py # Trade execution logic
    └── alert_engine.py # Price alert monitoring
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip or pipenv

### Installation

```bash
cd src
pip install -r requirements.txt
```

### Configuration

Create `.env` file in project root:

```env
GROQ_API_KEY=your_groq_api_key_here
APTOS_NODE_URL=https://fullnode.testnet.aptoslabs.com/v1
APTOS_PRIVATE_KEY=<your_private_key>
```

### Run Server

```bash
python server.py
```

Server runs on `http://localhost:8000`

---

## 📡 API Reference

### Health Check

```http
GET /health
```

### Chat with AI Agent

```http
POST /api/chat
Content-Type: application/json

{
  "message": "What is the current price of APT?",
  "user_id": "user123",
  "wallet_address": "0x..."
}
```

### Get Price

```http
GET /api/price/{symbol}
```

Response:
```json
{
  "symbol": "APT",
  "price": 8.45,
  "change_24h": 2.5,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Chart Data

```http
GET /api/chart/{symbol}?interval=1h&limit=100
```

### WebSocket Price Stream

```javascript
const ws = new WebSocket('wss://trade-apt.onrender.com/ws/price');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Price update:', data);
};

// Subscribe to symbols
ws.send(JSON.stringify({ action: 'subscribe', symbols: ['APT', 'USDC'] }));
```

### Create Alert

```http
POST /api/alerts
Content-Type: application/json

{
  "symbol": "APT",
  "target_price": 10.00,
  "condition": "above",
  "user_id": "user123"
}
```

### Execute Trade

```http
POST /api/trade
Content-Type: application/json

{
  "action": "swap",
  "from_token": "APT",
  "to_token": "USDC",
  "amount": 10,
  "wallet_address": "0x...",
  "slippage": 0.5
}
```

---

## 🤖 AI Agent

The AI agent uses Groq's LLM to parse natural language commands and execute trading operations.

### Supported Commands

| Command Type | Examples |
|--------------|----------|
| Price Check | "What's the price of APT?" |
| Swap | "Swap 10 APT for USDC" |
| Transfer | "Send 5 APT to 0x..." |
| Alert | "Alert me when APT hits $10" |
| Portfolio | "Show my portfolio" |
| Analysis | "Should I buy APT now?" |

### Agent Flow

```
User Message → Parser → Intent Classification → Action Execution → Response
```

---

## 🗄 Database Models

### Alert Model

```python
class Alert:
    id: int
    user_id: str
    symbol: str
    target_price: float
    condition: str  # 'above' | 'below'
    active: bool
    created_at: datetime
```

### Trade Model

```python
class Trade:
    id: int
    user_id: str
    action: str
    from_token: str
    to_token: str
    amount: float
    status: str
    tx_hash: str
    created_at: datetime
```

---

## 🔧 Development

### Run with Hot Reload

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
pytest tests/
```

### Linting

```bash
flake8 .
black .
```

---

## 🐳 Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "server.py"]
```

Build and run:

```bash
docker build -t tradeapt-backend .
docker run -p 8000:8000 --env-file .env tradeapt-backend
```

---

## 📦 Dependencies

Key dependencies from `requirements.txt`:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `groq` - LLM API client
- `aptos-sdk` - Aptos blockchain SDK
- `sqlalchemy` - Database ORM
- `websockets` - WebSocket support
- `httpx` - HTTP client
- `python-dotenv` - Environment management

---

## 🚀 Deployment (Render)

1. Create new Web Service
2. Connect GitHub repository
3. Set root directory to `src/`
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python server.py`
6. Add environment variables

---

## 📄 License

MIT License
