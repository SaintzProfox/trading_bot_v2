# 🥇 AuraTrade — XAUUSD Algorithmic Trading Bot

Production-grade trading bot system for XAUUSD on HFM (HotForex) broker with full-stack dashboard.

---

## 🏗️ Architecture

```
trading-bot/
├── backend/              # Python FastAPI trading engine
│   ├── app/
│   │   ├── core/         # Trading bot, strategy, risk manager, ML model, backtester
│   │   ├── api/routes/   # REST API & WebSocket endpoints
│   │   ├── services/     # Database service (PostgreSQL/asyncpg)
│   │   └── utils/        # Metrics calculator
│   ├── models/           # Saved ML models (auto-generated)
│   └── requirements.txt
├── frontend/             # Next.js dashboard
│   └── src/
│       ├── app/          # Pages: login, dashboard, trades, performance, settings
│       ├── components/   # Bot controls, charts, MetricCard, LiveTradesFeed
│       └── lib/          # API client
├── docker/
│   ├── docker-compose.yml
│   └── nginx.conf
└── .env.example
```

---

## ⚡ Quick Start (Docker)

### 1. Prerequisites
- Docker & Docker Compose
- MetaTrader5 installed (Windows or Wine on Linux/VPS)
- HFM broker account

### 2. Clone & Configure
```bash
git clone https://github.com/yourrepo/auratrade.git
cd auratrade
cp .env.example .env
```

Edit `.env` with your actual credentials:
```env
POSTGRES_PASSWORD=your_strong_password
JWT_SECRET_KEY=$(openssl rand -hex 32)
MT5_LOGIN=12345678
MT5_PASSWORD=your_mt5_password
MT5_SERVER=HFM-Demo
```

### 3. Start all services
```bash
cd docker
docker compose up -d
```

### 4. Access the dashboard
- Dashboard: http://localhost (via Nginx)
- API Docs:  http://localhost:8000/api/docs
- Direct frontend: http://localhost:3000

### 5. Create first user
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","email":"admin@example.com"}'
```

---

## 🖥️ VPS Deployment (Ubuntu 22.04)

### 1. Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 2. Install MetaTrader5 via Wine (for Linux VPS)
```bash
sudo apt install wine wine64 -y
wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe
wine mt5setup.exe
# Log into HFM account from MT5 terminal
```

### 3. Deploy
```bash
git clone https://github.com/yourrepo/auratrade.git
cd auratrade
cp .env.example .env && nano .env  # Fill your credentials
cd docker && docker compose up -d
```

### 4. Configure Nginx + SSL (optional)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

Then update `docker/nginx.conf` to enable HTTPS block and update `.env`:
```env
NEXT_PUBLIC_API_URL=https://yourdomain.com
NEXT_PUBLIC_WS_URL=wss://yourdomain.com
```

---

## 🔧 Local Development

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local  # Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### Database (Docker only)
```bash
docker run -e POSTGRES_DB=trading_bot -e POSTGRES_USER=trader \
           -e POSTGRES_PASSWORD=dev -p 5432:5432 postgres:16-alpine
```

---

## 📊 Trading Strategy

### Signal Generation
The bot uses a confluence of three indicators:
1. **RSI** — Identifies overbought/oversold conditions
2. **MA Crossover** — Fast EMA vs Slow EMA for trend direction
3. **ATR** — Dynamic stop loss and take profit levels

### Signal Logic
```
BUY signal:  Fast MA crosses above Slow MA AND (RSI < 30 OR RSI in 40-60 with bullish trend)
SELL signal: Fast MA crosses below Slow MA AND (RSI > 70 OR RSI in 40-60 with bearish trend)

Stop Loss  = entry ± ATR × atr_multiplier_sl (default 1.5)
Take Profit = entry ± ATR × atr_multiplier_tp (default 2.5)
```

### ML Enhancement
A GradientBoosting classifier is optionally applied to filter signals. It's trained on:
- Price momentum features
- RSI, Bollinger Band position
- Volume ratios
- Candlestick patterns

Train via API: `POST /api/bot/train-ml` (to be implemented)

---

## 🛡️ Risk Management

| Parameter | Default | Description |
|---|---|---|
| Risk per trade | 1% | % of balance risked per trade |
| Daily loss limit | 5% | Bot auto-stops when hit |
| Max open trades | 3 | Concurrent position cap |
| Max lot size | 1.0 | Hard cap on position size |
| Min signal strength | 50 | Quality filter 0-100 |

---

## 🔌 API Reference

### Authentication
```
POST /api/auth/login      # Get JWT token
POST /api/auth/register   # Create user
GET  /api/auth/me         # Get current user
```

### Bot Control
```
POST /api/bot/start           # Start trading bot
POST /api/bot/stop            # Stop bot gracefully
POST /api/bot/emergency-stop  # Stop + close all positions
GET  /api/bot/status          # Get bot status + account
```

### Trades
```
GET  /api/trades/             # Paginated trade history
GET  /api/trades/open         # Active open trades
GET  /api/trades/{id}         # Single trade details
```

### Metrics
```
GET /api/metrics/summary      # Overall performance stats
GET /api/metrics/daily        # Daily PnL by date
GET /api/metrics/equity-curve # Equity curve data
GET /api/metrics/drawdown     # Drawdown analysis
```

### Settings
```
GET /api/settings/  # Get current strategy settings
PUT /api/settings/  # Update strategy settings
```

### WebSocket
```
WS /ws/trading?token=<jwt>
# Receives: trade_opened, trade_closed, bot_status, account_update
# Send:     {"type": "ping"} → receives {"type": "pong"}
```

---

## 🔒 Security Checklist

- [x] JWT authentication on all endpoints
- [x] Rate limiting (30 req/min API, 5/min auth)
- [x] All secrets via environment variables
- [x] CORS configured for specific origins
- [x] PostgreSQL with parameterized queries (no SQL injection)
- [x] Nginx reverse proxy
- [ ] SSL/TLS certificate (configure certbot)
- [ ] Firewall: only ports 80/443 public, 22 for SSH

---

## 🐛 Troubleshooting

**MT5 connection fails**: Ensure MT5 is running and logged into HFM account. On Linux, use Wine.

**Bot won't start**: Check `docker logs trading_backend`. Common issue: MT5 server name mismatch — log into your HFM account and check exact server name in Tools > Options.

**Database errors**: Run `docker logs trading_postgres` and verify `DATABASE_URL` is correct.

---

## 📜 Disclaimer

> **RISK WARNING**: Trading XAUUSD and other forex/CFD instruments involves substantial risk of loss and is not suitable for all investors. This software is for educational purposes. Past performance is not indicative of future results. Always test on a demo account first.
