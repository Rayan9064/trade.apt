# Trade.apt - Project Documentation
## DeFi Trading Assistant for Aptos Hackathon

---

# 📧 EMAIL CONTENT

**Subject:** Trade.apt - Project Flow, Use Cases & Hackathon Analysis

---

## 🔄 SYSTEM FLOW

### High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────▶│   AI Parser     │────▶│  Trade Engine   │
│ (Natural Lang)  │     │  (GPT-4o-mini)  │     │  (Simulator)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Price Alerts   │◀────│ Background      │◀────│  CoinGecko API  │
│  (In-Memory)    │     │ Worker (10s)    │     │  (Real Prices)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Request Flow

#### 1. AI Parsing Flow (`POST /ai/parse`)
```
User Input: "buy $20 APT if price drops to $7"
     │
     ▼
┌─────────────────────────────────────────┐
│  OpenAI GPT-4o-mini processes input     │
│  with custom system prompt              │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Structured JSON Output:                │
│  {                                      │
│    "action": "buy",                     │
│    "tokenFrom": "USDC",                 │
│    "tokenTo": "APT",                    │
│    "amountUsd": 20,                     │
│    "conditions": {                      │
│      "type": "price_trigger",           │
│      "operator": "<",                   │
│      "value": 7                         │
│    }                                    │
│  }                                      │
└─────────────────────────────────────────┘
```

#### 2. Trade Execution Flow (`POST /trade/execute`)
```
Parsed Trade JSON
     │
     ▼
┌─────────────────────────────────────────┐
│  Fetch current price from CoinGecko    │
│  APT = $12.50 (example)                 │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Evaluate condition: $12.50 < $7?       │
│  Result: FALSE                          │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Condition NOT met:                     │
│  → Store in pending_trades              │
│  → Return status: "pending"             │
│  → Background worker monitors           │
└─────────────────────────────────────────┘
```

#### 3. Background Worker Flow (Every 10 seconds)
```
┌─────────────────────────────────────────┐
│  Check all active price alerts          │
│  Check all pending conditional trades   │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Fetch prices for monitored tokens      │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  If condition met:                      │
│  → Execute trade (simulated)            │
│  → Trigger alert (console log)          │
│  → Remove from pending                  │
└─────────────────────────────────────────┘
```

---

## 💼 USE CASES

### Use Case 1: Conditional Buy Order
**Scenario:** User wants to buy APT when price drops
```
User: "Buy $100 worth of APT when it drops below $8"

→ AI parses to: buy APT, condition: price < $8
→ System checks: current APT = $12
→ Trade stored as PENDING
→ Background worker monitors every 10s
→ When APT < $8: Trade EXECUTED (simulated)
```

### Use Case 2: Immediate Market Order
**Scenario:** User wants to buy immediately at market price
```
User: "Buy $50 of ETH right now"

→ AI parses to: buy ETH, condition: immediate
→ System fetches current ETH price
→ Trade EXECUTED immediately (simulated)
→ Returns: tokens received, execution price
```

### Use Case 3: Price Alert
**Scenario:** User wants notification when BTC hits $100k
```
User creates alert: BTC > $100,000

→ Alert stored in memory (status: active)
→ Background worker checks BTC price every 10s
→ When BTC > $100k: Alert TRIGGERED
→ Console notification printed
```

### Use Case 4: Token Swap
**Scenario:** User wants to swap tokens with condition
```
User: "Swap $200 from ETH to SOL when SOL is under $100"

→ AI parses to: swap ETH→SOL, condition: SOL < $100
→ System monitors SOL price
→ When condition met: Swap EXECUTED (simulated)
```

### Use Case 5: Portfolio Monitoring
**Scenario:** User checks multiple token prices
```
GET /price/APT → Returns live APT price
GET /price/BTC → Returns live BTC price
GET /price/ETH/info → Returns detailed market data
GET /tokens → Returns all 28 supported tokens
```

### Use Case 6: Sell Order with Target
**Scenario:** User wants to sell when price rises
```
User: "Sell $500 of APT when it goes above $15"

→ AI parses to: sell APT, condition: price > $15
→ Trade stored as PENDING
→ Executes when APT > $15
```

---

## ⚠️ EDGE CASES & POTENTIAL PROBLEMS FOR APTOS HACKATHON

### 🔴 CRITICAL ISSUES

#### 1. **No Actual Blockchain Integration**
```
PROBLEM: This is purely a simulation - no real Aptos transactions
IMPACT: Judges may expect actual on-chain execution
RISK LEVEL: HIGH

MITIGATION OPTIONS:
- Clearly label as "Backend Simulation / MVP Phase 1"
- Show roadmap for Aptos SDK integration
- Emphasize AI/NLP innovation over blockchain
- Add mock Aptos transaction IDs to responses
```

#### 2. **No Wallet Connection**
```
PROBLEM: No Petra/Martian wallet integration
IMPACT: Users can't actually trade with their tokens
RISK LEVEL: HIGH

MITIGATION OPTIONS:
- Present as "Intent Layer" that feeds into DEX aggregators
- Show architecture diagram with wallet integration planned
- Focus demo on AI parsing + price monitoring capabilities
```

#### 3. **In-Memory Storage (Data Loss on Restart)**
```
PROBLEM: All alerts/pending trades lost when server restarts
IMPACT: Unreliable for production use

MITIGATION OPTIONS:
- Add Redis/PostgreSQL before demo
- Mention as known limitation with solution planned
- For demo, keep server running continuously
```

### 🟡 MODERATE ISSUES

#### 4. **CoinGecko Rate Limiting**
```
PROBLEM: Free tier limited to ~10-30 calls/minute
IMPACT: Background worker checking every 10s may hit limits

SYMPTOMS:
- Price fetches return None
- Alerts/trades fail to execute
- HTTP 429 errors in logs

MITIGATION:
- Implement request caching (cache prices for 30s)
- Add exponential backoff on rate limit
- Use CoinGecko Pro API key ($129/mo)
- Switch to DexScreener as fallback
```

#### 5. **OpenAI API Dependency**
```
PROBLEM: Requires OpenAI API key for full AI functionality
IMPACT: Demo may fail if API key missing/expired

SYMPTOMS:
- Falls back to mock parser (limited capability)
- Complex queries misinterpreted
- Error messages exposed to user

MITIGATION:
- Test with valid API key before demo
- Have backup API key ready
- Mock parser handles basic cases as fallback
```

#### 6. **AI Parsing Ambiguity**
```
PROBLEM: Natural language can be ambiguous

EDGE CASES:
- "Buy APT" → No amount specified (what do we do?)
- "Trade some crypto" → No token specified
- "Buy low sell high" → Philosophical, not actionable
- "Buy $20 APT and $30 ETH" → Multiple orders in one

CURRENT BEHAVIOR:
- Missing amount → amountUsd: 0
- Missing token → defaults to APT
- Complex queries → may misparse

MITIGATION:
- Add validation layer before trade execution
- Return "clarification needed" for ambiguous requests
- Add examples in UI showing valid commands
```

#### 7. **Price Slippage Not Simulated**
```
PROBLEM: Real DEX trades have slippage, ours don't
IMPACT: Simulated "tokens received" is unrealistic

MITIGATION:
- Add configurable slippage (0.5%, 1%, etc.)
- Show "estimated" vs "minimum received"
- Document as simplification for demo
```

### 🟢 MINOR ISSUES

#### 8. **Limited Token Support**
```
PROBLEM: Only 28 tokens mapped to CoinGecko IDs
IMPACT: User asks for obscure token → fails

MITIGATION:
- Return clear error: "Token XYZ not supported"
- Add endpoint to check if token is supported
- Allow adding custom CoinGecko ID mappings
```

#### 9. **No User Authentication**
```
PROBLEM: Anyone can create alerts, execute trades
IMPACT: No user isolation, potential abuse

MITIGATION:
- Add basic API key authentication
- Implement user sessions
- For demo: acceptable as single-user system
```

#### 10. **Timezone Issues**
```
PROBLEM: All timestamps in UTC
IMPACT: May confuse users in different timezones

MITIGATION:
- Document that times are UTC
- Add timezone parameter to responses
```

---

## 🎯 HACKATHON DEMO STRATEGY

### What to Emphasize ✅
1. **AI Innovation**: Natural language → structured trading intent
2. **Real-Time Data**: Live prices from CoinGecko
3. **Conditional Logic**: Price triggers, pending orders
4. **Clean Architecture**: Modular, well-documented code
5. **Developer Experience**: Docker, Swagger UI, clear APIs

### What to Downplay ⚠️
1. Lack of actual blockchain transactions
2. In-memory storage limitations
3. No wallet integration

### Demo Script (5 minutes)
```
1. Show Swagger UI (30s)
   "Here's our REST API with interactive docs"

2. AI Parsing Demo (60s)
   - "buy $20 APT if price drops to $7" → show JSON output
   - "sell $100 ETH when it hits $3000" → show JSON output
   - Emphasize GPT-4o-mini intelligence

3. Live Price Fetching (30s)
   - GET /price/APT → show real-time price
   - GET /tokens → show 28 supported tokens

4. Trade Execution Flow (60s)
   - Execute immediate trade → show receipt
   - Execute conditional trade → show pending status
   - Explain background worker monitors prices

5. Price Alerts (60s)
   - Create alert for BTC > $100k
   - Show alert stored
   - Explain trigger mechanism

6. Architecture Overview (60s)
   - Show Docker containerization
   - Explain modular design
   - Mention Aptos integration roadmap
```

### Killer Phrases for Judges
- "We're building the **intent layer** for DeFi on Aptos"
- "Natural language is the **new UI** for crypto trading"
- "Our AI understands **trading intent**, not just keywords"
- "This is **Phase 1** - backend simulation proving the concept"

---

## 🛠️ QUICK FIXES BEFORE HACKATHON

### Priority 1 (Must Do)
- [ ] Test with valid OpenAI API key
- [ ] Ensure Docker runs smoothly
- [ ] Prepare 3-5 demo commands that work perfectly
- [ ] Have backup if CoinGecko rate-limits

### Priority 2 (Nice to Have)
- [ ] Add price caching (Redis or in-memory TTL)
- [ ] Add fake "Aptos Transaction ID" to responses
- [ ] Create simple frontend demo page
- [ ] Add WebSocket for real-time updates

### Priority 3 (Future Roadmap)
- [ ] Aptos SDK integration
- [ ] Petra wallet connection
- [ ] Actual DEX integration (Liquidswap, PancakeSwap)
- [ ] Persistent database storage

---

## 📊 TECHNICAL SPECIFICATIONS

### API Endpoints Summary
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ai/parse` | POST | Parse natural language |
| `/trade/execute` | POST | Execute/queue trade |
| `/trade/pending` | GET | List pending trades |
| `/price/{token}` | GET | Get token price |
| `/alerts` | POST/GET | Manage alerts |

### Supported Tokens (28 total)
APT, BTC, ETH, SOL, USDC, USDT, BNB, XRP, ADA, DOGE, 
AVAX, DOT, MATIC, LINK, UNI, ATOM, LTC, NEAR, ARB, OP,
SUI, SEI, INJ, TIA, PEPE, SHIB, WIF, BONK

### Technology Stack
- **Backend**: Python 3.11, FastAPI, Pydantic
- **AI**: OpenAI GPT-4o-mini
- **Prices**: CoinGecko Free API
- **Container**: Docker, docker-compose
- **Async**: asyncio, httpx

---

## 📞 CONTACT & RESOURCES

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **GitHub**: [Repository Link]

---

*Document generated for Aptos Hackathon preparation*
*Last updated: November 29, 2025*
