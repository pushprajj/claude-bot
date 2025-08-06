# Trading Bot - Signal Generation & Portfolio Management

A comprehensive trading bot system for cryptocurrency and stock markets that provides automated signal detection, portfolio management, and trading capabilities.

## 🚀 Features Implemented (Phase 1)

### Backend (Python FastAPI)
- ✅ **Ticker Management**: Add, edit, delete tickers for both crypto and stocks
- ✅ **Signal Generation**: EMA crossover, Golden Cross, SMA+Volume, Confirmed Buy signals
- ✅ **Data Fetching**: Real-time data from Binance, Bybit (crypto) and yfinance (stocks)
- ✅ **Watchlist Management**: Monitor specific tickers with expiration dates
- ✅ **Trade Management**: Track open positions, P&L, stop loss, take profit
- ✅ **Email Reports**: Daily signals summary, portfolio reports, instant alerts
- ✅ **PostgreSQL Database**: Comprehensive schema for all trading data

### Frontend (Next.js + TypeScript)
- ✅ **Responsive Dashboard**: Overview of signals, trades, watchlist
- ✅ **Ticker Management UI**: Interactive forms and tables
- ✅ **Navigation System**: Clean sidebar navigation
- ✅ **Real-time Updates**: API integration with loading states
- ✅ **Modern UI**: Tailwind CSS with professional design

## 🏗️ Project Structure

```
trading-bot/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── models.py       # Database models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── database.py     # Database connection
│   │   ├── main.py         # FastAPI app
│   │   ├── routers/        # API endpoints
│   │   │   ├── tickers.py
│   │   │   ├── signals.py
│   │   │   ├── watchlist.py
│   │   │   ├── trades.py
│   │   │   └── reports.py
│   │   └── services/       # Business logic
│   │       ├── data_fetcher.py
│   │       ├── signal_generator.py
│   │       └── email_service.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   └── lib/          # API client and utilities
│   └── package.json
└── PROJECT_REQUIREMENTS.md
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL database
- Redis (for background tasks)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/trading_bot
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_SECRET_KEY=your_binance_secret_key
   BYBIT_API_KEY=your_bybit_api_key
   BYBIT_SECRET_KEY=your_bybit_secret_key
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_email_password
   ```

5. **Setup database:**
   ```bash
   # Create PostgreSQL database named 'trading_bot'
   # Tables will be created automatically on first run
   ```

6. **Run the backend:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create environment file:**
   ```bash
   # Create .env.local
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

4. **Run the frontend:**
   ```bash
   npm run dev
   ```

5. **Access the application:**
   Open [http://localhost:3000](http://localhost:3000) in your browser

## 📊 Signal Types Implemented

### 1. EMA Crossover Signal
- **Logic**: 12 EMA crosses 26 EMA with RSI confirmation
- **Buy**: Bullish crossover + RSI < 70 (not overbought)
- **Sell**: Bearish crossover + RSI > 30 (not oversold)

### 2. Golden Cross Signal
- **Logic**: 50 SMA crosses 200 SMA
- **Buy**: Golden Cross (50 SMA > 200 SMA)
- **Sell**: Death Cross (50 SMA < 200 SMA)

### 3. SMA + Volume Signal
- **Logic**: Price crosses 200 SMA with high volume
- **Buy**: Price breaks above 200 SMA + volume > 1.2x average
- **Sell**: Price breaks below 200 SMA + volume > 1.2x average

### 4. Confirmed Buy Signal
- **Logic**: Multiple indicators alignment
- **Conditions**: EMA bullish + RSI recovery + MACD bullish
- **Strength**: Strong if 3/3 conditions, Moderate if 2/3

## 🔄 API Endpoints

### Tickers
- `GET /api/tickers` - List all tickers
- `POST /api/tickers` - Create new ticker
- `PUT /api/tickers/{id}` - Update ticker
- `DELETE /api/tickers/{id}` - Delete ticker
- `POST /api/tickers/bulk` - Bulk create tickers

### Signals
- `GET /api/signals` - List signals with filters
- `POST /api/signals/generate` - Generate signals on-demand
- `POST /api/signals/{id}/process` - Process signal (watchlist/trade/skip)
- `GET /api/signals/statistics/summary` - Signal statistics

### Watchlist
- `GET /api/watchlist` - List watchlist items
- `POST /api/watchlist` - Add to watchlist
- `POST /api/watchlist/{id}/promote-to-trade` - Promote to trade

### Trades
- `GET /api/trades` - List trades
- `POST /api/trades` - Create trade
- `PUT /api/trades/{id}/close` - Close trade
- `GET /api/trades/statistics/summary` - Trade statistics

### Reports
- `POST /api/reports/send-daily-report` - Email daily signals
- `POST /api/reports/send-portfolio-summary` - Email portfolio summary
- `GET /api/reports/preview-daily-report` - Preview report HTML

## 📈 Next Steps (Phase 2)

1. **Enhanced Signal Algorithms**
   - Custom signal parameters
   - Backtesting capabilities
   - Signal performance tracking

2. **Advanced Frontend Features**
   - Signal generation interface
   - Watchlist management page
   - Trade management dashboard
   - Charts and visualizations

3. **Automation Features**
   - Scheduled signal generation
   - Automated email reports
   - Background task processing

4. **Integration Enhancements**
   - More exchanges support
   - Additional technical indicators
   - Real-time price updates
   - Mobile responsiveness

## 🚨 Important Notes

- **Security**: Never commit API keys or credentials
- **Testing**: Test with small amounts before live trading
- **Backup**: Regularly backup your database
- **Monitoring**: Monitor API rate limits for exchanges

## 📞 Support

For issues and questions:
- Check the API documentation at `http://localhost:8000/docs`
- Review logs for debugging information
- Ensure all environment variables are properly set

---

**Status**: Phase 1 Complete ✅  
**Last Updated**: August 2025  
**Version**: 1.0.0