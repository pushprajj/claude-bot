# Claude Trading Bot 🤖📈

A sophisticated trading bot built with FastAPI and Next.js that generates high-quality confirmed buy signals for ASX stocks using advanced technical analysis.

## ✨ Features

### 🎯 **Confirmed Buy Signal Generation**
- **6-Condition Confirmed Buy Signals** with volume confirmation
- **5-day EMA crossover detection** (5 EMA crosses above 20 EMA)
- **Volume spike confirmation** (5-day average > 50-day average)
- **Multiple technical indicators**: RSI > 50, MACD > Signal Line, Price above 50 SMA
- **Only volume-confirmed signals** displayed (highest quality)

### 🚀 **Smart Real-Time Updates**
- **Intelligent frontend refresh** - only updates when backend completes
- **Status-based polling** every 10 seconds (lightweight)
- **Automatic completion detection** with success notifications
- **No premature refreshing** or wasteful API calls

### 🏗️ **Architecture**
- **Backend**: FastAPI with SQLite database
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Data Source**: yfinance via subprocess (avoids rate limiting)
- **Signal Processing**: 122/123 ASX tickers successfully processed

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
- SQLite database (auto-created)

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

4. **Setup environment variables (optional):**
   ```bash
   # Create .env file if you need custom settings
   # The app works without .env file using SQLite defaults
   ```

5. **Run the backend:**
   ```bash
   uvicorn app.main_with_db:app --reload --host 127.0.0.1 --port 8002
   ```
   
   The SQLite database will be created automatically on first run.

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
   echo "NEXT_PUBLIC_API_URL=http://localhost:8002" > .env.local
   ```

4. **Run the frontend:**
   ```bash
   npm run dev
   ```

5. **Access the application:**
   Open [http://localhost:3000](http://localhost:3000) in your browser

## 📊 Current Signal Implementation

### **Confirmed Buy Signal (Primary Focus)**
The system currently focuses exclusively on high-quality **volume-confirmed buy signals** that meet all 6 strict conditions:

#### **Required Conditions (All 6 Must Be Met):**
1. **5 EMA Crossover**: 5 EMA crossed above 20 EMA within last 5 days (excluding current candle)
2. **Price Above EMAs**: Both open and close prices above 5 EMA and 20 EMA
3. **Price Above SMA50**: Closing price above 50-day Simple Moving Average
4. **Volume Confirmation**: 5-day volume average > 50-day volume average
5. **RSI Bullish**: RSI above 50 (momentum confirmation)
6. **MACD Positive**: MACD line above Signal line

#### **Technical Details:**
- **Lookback Period**: 5 days excluding current candle (indices -6 to -2)
- **Volume Ratio**: Must be > 1.0 for confirmation
- **Data Requirements**: Minimum 60 days of historical data
- **Processing**: 122/123 ASX tickers successfully processed

### **Other Signal Types (Available but Disabled)**
The codebase includes additional signal types that can be enabled:
- EMA Crossover (12/26 EMA with RSI)
- Golden Cross (50/200 SMA)
- SMA Volume Breakout (200 SMA with volume spike)
- Simple SMA50 signals

## 🔄 Key API Endpoints

### **Primary Endpoints (Currently Active)**

#### Signals
- `GET /api/signals` - List signals with market/exchange filters
- `POST /api/signals/generate-confirmed-buy` - **Main endpoint** for ASX signal generation
- `GET /api/signals/generation-status` - Check signal generation progress
- `GET /api/signals/statistics/summary` - Signal statistics

#### Tickers
- `GET /api/tickers` - List all tickers (123 ASX stocks loaded)
- `POST /api/tickers/bulk` - Bulk import tickers

### **Additional Endpoints (Available)**

#### Watchlist & Trades
- `GET /api/watchlist` - List watchlist items
- `POST /api/watchlist` - Add signal to watchlist
- `GET /api/trades` - List trades
- `POST /api/trades` - Create trade entry

#### System Endpoints
- `GET /` - API status and database connection
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### **Signal Generation Process**
1. **POST** `/api/signals/generate-confirmed-buy` - Starts background processing
2. **GET** `/api/signals/generation-status` - Polls for completion (frontend auto-refresh)
3. **GET** `/api/signals?market_type=stock&exchange=ASX` - Retrieves generated signals

## 🚀 Current Status & Next Steps

### **✅ Completed (Phase 1)**
- ✅ **Core Infrastructure**: FastAPI + Next.js + SQLite
- ✅ **ASX Stock Data**: 123 tickers successfully loaded
- ✅ **Confirmed Buy Signals**: 6-condition volume-confirmed algorithm
- ✅ **Subprocess Data Fetching**: Bypasses yfinance web server rate limiting
- ✅ **Intelligent Frontend**: Status-based polling with completion detection
- ✅ **Clean Project Structure**: Archived unused files, proper .gitignore
- ✅ **GitHub Repository**: https://github.com/pushprajj/claude-bot

### **🎯 Ready for Phase 2 Enhancements**

1. **Signal Algorithm Improvements**
   - Backtesting framework for signal performance validation
   - Additional technical indicators (Bollinger Bands, Stochastic)
   - Multi-timeframe analysis (daily, weekly confluence)

2. **User Interface Enhancements**
   - Interactive price charts with signal markers
   - Signal filtering and sorting options
   - Watchlist management with alerts
   - Trade tracking and performance metrics

3. **Automation & Scheduling**
   - Automated daily signal generation
   - Email/SMS notification system
   - Scheduled reports and summaries

4. **Data & Performance**
   - Real-time price updates
   - Additional exchanges (NYSE, NASDAQ)
   - Historical signal performance tracking
   - Mobile-responsive design

## 🚨 Important Notes

### **Technical Considerations**
- **Data Fetching**: Uses subprocess approach to avoid yfinance rate limiting
- **Processing Time**: ~10 seconds per ticker (122 tickers ≈ 20 minutes)
- **Database**: SQLite auto-created, no setup required
- **Rate Limiting**: Built-in delays prevent API blocking

### **Trading Disclaimers**
- **Educational Purpose**: This is a technical analysis tool, not financial advice
- **Risk Management**: Always use proper position sizing and stop losses
- **Testing**: Backtest signals before live implementation
- **Market Conditions**: Signals work best in trending markets

### **Security & Maintenance**
- **No API Keys Required**: Uses public yfinance data
- **Local Database**: All data stored locally in SQLite
- **Regular Updates**: Monitor for new ASX listings
- **Backup**: Database file is `trading_bot.db` in backend directory

## 📞 Support

For issues and questions:
- Check the API documentation at `http://localhost:8000/docs`
- Review logs for debugging information
- Ensure all environment variables are properly set

---

**Status**: Production Ready ✅  
**Last Updated**: August 2025  
**Version**: 1.0.0  
**Repository**: https://github.com/pushprajj/claude-bot  
**Focus**: ASX Volume-Confirmed Buy Signals