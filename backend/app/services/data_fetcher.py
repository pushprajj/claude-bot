import yfinance as yf
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import aiohttp
from app.models import MarketType, Ticker
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.binance = ccxt.binance()
        self.bybit = ccxt.bybit()
    
    def _format_crypto_symbol(self, symbol: str, exchange: str) -> str:
        """Convert database symbol format to exchange-specific format"""
        if exchange == "binance":
            # Most Binance pairs are against USDT
            if "/" not in symbol:
                return f"{symbol}/USDT"
            return symbol
        elif exchange == "bybit":
            # Bybit also uses USDT pairs primarily
            if "/" not in symbol:
                return f"{symbol}/USDT"
            return symbol
        else:
            return symbol
        
    def fetch_stock_data_batch_sync(self, symbols: List[str], period: str = "60d", start_date: str = None, end_date: str = None) -> Dict[str, pd.DataFrame]:
        """Fetch multiple stock symbols using exact approach from working script"""
        logger.info(f"Fetching {len(symbols)} stock symbols using working script approach...")
        
        # Format symbols for ASX market exactly like working script
        formatted_symbols = []
        symbol_map = {}
        
        for symbol in symbols:
            formatted = symbol
            # Add .AX suffix for ASX symbols if not present (like working script)
            if not symbol.endswith('.AX') and '.' not in symbol:
                formatted = f"{symbol}.AX"
            formatted_symbols.append(formatted)
            symbol_map[formatted] = symbol
        
        logger.info(f"Formatted symbols: {formatted_symbols}")
        
        try:
            # Exact yf.download call from working script
            if start_date and end_date:
                batch_data = yf.download(
                    formatted_symbols,
                    start=start_date,
                    end=end_date,
                    group_by='ticker',
                    auto_adjust=False,
                    threads=True,
                    progress=False
                )
            else:
                batch_data = yf.download(
                    formatted_symbols,
                    period=period,
                    group_by='ticker',
                    auto_adjust=False,
                    threads=True,
                    progress=False
                )
            
            # Process results exactly like working script
            results = {}
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            min_data_days = 50
            
            for formatted_symbol in formatted_symbols:
                original_symbol = symbol_map[formatted_symbol]
                
                try:
                    if len(formatted_symbols) == 1:
                        hist = batch_data
                    else:
                        if formatted_symbol not in batch_data:
                            logger.warning(f"No data for {original_symbol} (formatted: {formatted_symbol})")
                            continue
                        hist = batch_data[formatted_symbol]
                    
                    if hist.empty:
                        logger.warning(f"No data for {original_symbol} (formatted: {formatted_symbol})")
                        continue
                    
                    # Check required columns (exactly like working script)
                    missing = [col for col in required_columns if col not in hist.columns]
                    if missing:
                        logger.warning(f"Missing columns {missing} for {original_symbol}")
                        continue
                    
                    # Check minimum data requirement (exactly like working script)
                    if len(hist) < min_data_days:
                        logger.warning(f"Insufficient data for {original_symbol}: {len(hist)} rows")
                        continue
                    
                    # Forward fill exactly like working script
                    hist = hist.ffill()
                    
                    # Convert to lowercase columns for our system
                    hist = hist.rename(columns={
                        'Open': 'open',
                        'High': 'high', 
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })
                    
                    results[original_symbol] = hist
                    logger.info(f"Successfully fetched {len(hist)} rows for {original_symbol}")
                    
                except Exception as e:
                    logger.error(f"Error processing {original_symbol}: {str(e)}")
                    continue
            
            logger.info(f"Batch download completed: {len(results)}/{len(symbols)} symbols successful")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch stock download: {str(e)}")
            return {}

    async def fetch_stock_data_batch(self, symbols: List[str], period: str = "60d", interval: str = "1d", start_date: str = None, end_date: str = None) -> Dict[str, pd.DataFrame]:
        """Async wrapper for sync batch fetch"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_stock_data_batch_sync, symbols, period, start_date, end_date)

    async def fetch_stock_data(self, symbol: str, period: str = "60d", interval: str = "1d") -> Optional[pd.DataFrame]:
        """Fetch stock data using simple yfinance download (like working script)"""
        try:
            # Simple direct download like working script
            data = yf.download(
                symbol,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False
            )
            
            if data.empty or len(data) < 10:
                logger.warning(f"Insufficient data for {symbol}: {len(data) if not data.empty else 0} rows")
                return None
            
            # Convert column names to lowercase
            if 'Open' in data.columns:
                data = data.rename(columns={
                    'Open': 'open',
                    'High': 'high', 
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
            
            logger.debug(f"Successfully fetched {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.debug(f"Error fetching stock data for {symbol}: {str(e)}")
            return None
    
    async def fetch_crypto_data(self, symbol: str, exchange: str = "binance", timeframe: str = "1d", limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch cryptocurrency data using ccxt"""
        try:
            if exchange.lower() == "binance":
                exchange_obj = self.binance
            elif exchange.lower() == "bybit":
                exchange_obj = self.bybit
            else:
                logger.error(f"Unsupported exchange: {exchange}")
                return None
            
            # Convert symbol to exchange format (e.g., BTC -> BTC/USDT for Binance)
            formatted_symbol = self._format_crypto_symbol(symbol, exchange.lower())
            logger.info(f"Fetching data for {symbol} -> {formatted_symbol} on {exchange}")
            
            # Fetch OHLCV data
            ohlcv = exchange_obj.fetch_ohlcv(formatted_symbol, timeframe, limit=limit)
            
            if not ohlcv:
                logger.warning(f"No data found for crypto symbol: {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching crypto data for {symbol} on {exchange}: {str(e)}")
            return None
    
    async def fetch_current_price(self, ticker: Ticker) -> Optional[float]:
        """Fetch current price for a ticker"""
        try:
            if ticker.market_type == MarketType.STOCK:
                data = await self.fetch_stock_data(ticker.symbol, period="1d", interval="5m")
                if data is not None and not data.empty:
                    return float(data['close'].iloc[-1])
            
            elif ticker.market_type == MarketType.CRYPTO:
                data = await self.fetch_crypto_data(ticker.symbol, ticker.exchange, timeframe="1m", limit=1)
                if data is not None and not data.empty:
                    return float(data['close'].iloc[-1])
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching current price for {ticker.symbol}: {str(e)}")
            return None
    
    async def fetch_multiple_tickers_data(self, tickers: List[Ticker], period: str = "60d", timeframe: str = "1d", batch_size: int = 50) -> Dict[int, pd.DataFrame]:
        """Fetch data for multiple tickers with optimized batch processing"""
        results = {}
        
        # Separate stocks and crypto for different processing strategies
        stock_tickers = [t for t in tickers if t.market_type == MarketType.STOCK]
        crypto_tickers = [t for t in tickers if t.market_type == MarketType.CRYPTO]
        
        logger.info(f"Processing {len(stock_tickers)} stock tickers and {len(crypto_tickers)} crypto tickers")
        
        # Process stocks using exact working script approach
        if stock_tickers:
            logger.info(f"Processing {len(stock_tickers)} stock tickers using working script approach...")
            
            # Get symbols for batch processing (working script approach)
            symbols = [ticker.symbol for ticker in stock_tickers]
            
            try:
                # Use synchronous batch fetch (exactly like working script)
                batch_stock_data = self.fetch_stock_data_batch_sync(symbols, period)
                logger.info(f"Batch download completed: {len(batch_stock_data)}/{len(symbols)} symbols successful")
                
                # Map results back to ticker IDs
                for ticker in stock_tickers:
                    if ticker.symbol in batch_stock_data:
                        results[ticker.id] = batch_stock_data[ticker.symbol]
                        logger.debug(f"Mapped stock data for {ticker.symbol}")
                        
            except Exception as e:
                logger.error(f"Batch download failed: {str(e)}")
        
        # Process crypto tickers in smaller batches (as they use different exchanges)
        if crypto_tickers:
            logger.info(f"Processing {len(crypto_tickers)} crypto tickers in batches...")
            crypto_batches = [crypto_tickers[i:i + 10] for i in range(0, len(crypto_tickers), 10)]
            
            for batch_num, batch in enumerate(crypto_batches, 1):
                logger.info(f"Processing crypto batch {batch_num}/{len(crypto_batches)} ({len(batch)} tickers)")
                
                # Create tasks for concurrent execution within batch
                tasks = []
                for ticker in batch:
                    task = self.fetch_crypto_data(ticker.symbol, ticker.exchange, timeframe)
                    tasks.append((ticker.id, ticker.symbol, task))
                
                # Execute batch tasks concurrently
                try:
                    batch_results = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)
                    
                    # Process results
                    for (ticker_id, symbol, _), result in zip(tasks, batch_results):
                        if isinstance(result, Exception):
                            logger.error(f"Error fetching crypto data for {symbol} (ID {ticker_id}): {str(result)}")
                        elif result is not None:
                            results[ticker_id] = result
                            logger.debug(f"Successfully fetched crypto data for {symbol}")
                        else:
                            logger.warning(f"No crypto data returned for {symbol}")
                            
                except Exception as e:
                    logger.error(f"Error in crypto batch {batch_num}: {str(e)}")
                    continue
                
                # Small delay between crypto batches
                if batch_num < len(crypto_batches):
                    await asyncio.sleep(0.3)
        
        logger.info(f"Successfully fetched data for {len(results)}/{len(tickers)} tickers ({len([t for t in stock_tickers if t.id in results])} stocks, {len([t for t in crypto_tickers if t.id in results])} crypto)")
        return results
    
    def get_supported_stock_symbols(self) -> List[str]:
        """Get list of popular stock symbols for different exchanges"""
        return {
            "NYSE": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "JNJ", "V"],
            "NASDAQ": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "ADBE", "CRM"],
            "ASX": ["CBA.AX", "BHP.AX", "CSL.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "WES.AX", "MQG.AX", "TLS.AX", "RIO.AX"]
        }
    
    def get_supported_crypto_symbols(self) -> List[str]:
        """Get list of popular crypto symbols"""
        return [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT",
            "SOL/USDT", "DOGE/USDT", "DOT/USDT", "MATIC/USDT", "LTC/USDT",
            "AVAX/USDT", "LINK/USDT", "UNI/USDT", "ATOM/USDT", "XLM/USDT"
        ]
    
    async def validate_ticker_symbol(self, symbol: str, market_type: MarketType, exchange: str = None) -> bool:
        """Validate if a ticker symbol is valid and tradeable"""
        try:
            if market_type == MarketType.STOCK:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return bool(info and 'symbol' in info)
            
            elif market_type == MarketType.CRYPTO:
                if exchange.lower() == "binance":
                    markets = self.binance.load_markets()
                elif exchange.lower() == "bybit":
                    markets = self.bybit.load_markets()
                else:
                    return False
                
                return symbol in markets
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating ticker {symbol}: {str(e)}")
            return False