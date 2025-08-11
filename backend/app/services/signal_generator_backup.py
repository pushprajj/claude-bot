import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import logging
from sqlalchemy.orm import Session

from app.models import Ticker, Signal, SignalType, SignalStrength, MarketType
from app.services.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self):
        self.data_fetcher = DataFetcher()
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for numpy types"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period).mean()
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def detect_ema_crossover_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect EMA crossover signals (12 EMA crosses 26 EMA)"""
        if len(data) < 26:
            return None
        
        try:
            ema_12 = self.calculate_ema(data['close'], 12)
            ema_26 = self.calculate_ema(data['close'], 26)
            rsi = self.calculate_rsi(data['close'])
            
            # Get last few values
            current_ema_12 = ema_12.iloc[-1]
            current_ema_26 = ema_26.iloc[-1]
            prev_ema_12 = ema_12.iloc[-2]
            prev_ema_26 = ema_26.iloc[-2]
            current_rsi = rsi.iloc[-1]
            
            # Check for crossover
            bullish_crossover = (prev_ema_12 <= prev_ema_26) and (current_ema_12 > current_ema_26)
            bearish_crossover = (prev_ema_12 >= prev_ema_26) and (current_ema_12 < current_ema_26)
            
            if bullish_crossover and current_rsi < 70:  # Not overbought
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.MODERATE,
                    'confidence_score': 0.7,
                    'details': {
                        'type': 'ema_crossover',
                        'ema_12': current_ema_12,
                        'ema_26': current_ema_26,
                        'rsi': current_rsi,
                        'reason': 'Bullish EMA crossover with RSI confirmation'
                    }
                }
            
            elif bearish_crossover and current_rsi > 30:  # Not oversold
                return {
                    'signal_type': SignalType.SELL,
                    'signal_strength': SignalStrength.MODERATE,
                    'confidence_score': 0.7,
                    'details': {
                        'type': 'ema_crossover',
                        'ema_12': current_ema_12,
                        'ema_26': current_ema_26,
                        'rsi': current_rsi,
                        'reason': 'Bearish EMA crossover with RSI confirmation'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in EMA crossover detection: {str(e)}")
            return None
    
    def detect_golden_cross_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect Golden Cross signal (50 SMA crosses above 200 SMA)"""
        if len(data) < 200:
            return None
        
        try:
            sma_50 = self.calculate_sma(data['close'], 50)
            sma_200 = self.calculate_sma(data['close'], 200)
            
            current_sma_50 = sma_50.iloc[-1]
            current_sma_200 = sma_200.iloc[-1]
            prev_sma_50 = sma_50.iloc[-2]
            prev_sma_200 = sma_200.iloc[-2]
            
            # Golden Cross: 50 SMA crosses above 200 SMA
            golden_cross = (prev_sma_50 <= prev_sma_200) and (current_sma_50 > current_sma_200)
            
            # Death Cross: 50 SMA crosses below 200 SMA
            death_cross = (prev_sma_50 >= prev_sma_200) and (current_sma_50 < current_sma_200)
            
            if golden_cross:
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.85,
                    'details': {
                        'type': 'golden_cross',
                        'sma_50': current_sma_50,
                        'sma_200': current_sma_200,
                        'reason': 'Golden Cross - 50 SMA crossed above 200 SMA'
                    }
                }
            
            elif death_cross:
                return {
                    'signal_type': SignalType.SELL,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.85,
                    'details': {
                        'type': 'death_cross',
                        'sma_50': current_sma_50,
                        'sma_200': current_sma_200,
                        'reason': 'Death Cross - 50 SMA crossed below 200 SMA'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Golden Cross detection: {str(e)}")
            return None
    
    def detect_sma_volume_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect 200 SMA cross with higher volume"""
        if len(data) < 200:
            return None
        
        try:
            sma_200 = self.calculate_sma(data['close'], 200)
            volume_avg = self.calculate_sma(data['volume'], 20)
            
            current_price = data['close'].iloc[-1]
            current_sma_200 = sma_200.iloc[-1]
            prev_price = data['close'].iloc[-2]
            prev_sma_200 = sma_200.iloc[-2]
            current_volume = data['volume'].iloc[-1]
            avg_volume = volume_avg.iloc[-1]
            
            # Price crosses above 200 SMA with higher volume
            bullish_cross = (prev_price <= prev_sma_200) and (current_price > current_sma_200)
            bearish_cross = (prev_price >= prev_sma_200) and (current_price < current_sma_200)
            high_volume = current_volume > (avg_volume * 1.2)  # 20% above average
            
            if bullish_cross and high_volume:
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.8,
                    'details': {
                        'type': 'sma_volume_breakout',
                        'price': current_price,
                        'sma_200': current_sma_200,
                        'volume': current_volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': current_volume / avg_volume,
                        'reason': 'Price crossed above 200 SMA with high volume'
                    }
                }
            
            elif bearish_cross and high_volume:
                return {
                    'signal_type': SignalType.SELL,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.8,
                    'details': {
                        'type': 'sma_volume_breakdown',
                        'price': current_price,
                        'sma_200': current_sma_200,
                        'volume': current_volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': current_volume / avg_volume,
                        'reason': 'Price crossed below 200 SMA with high volume'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in SMA volume detection: {str(e)}")
            return None
    
    def detect_sma_above_50_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Simple test signal: SMA 50 above current price"""
        if len(data) < 50:
            return None
        
        try:
            sma_50 = self.calculate_sma(data['close'], 50)
            current_price = data['close'].iloc[-1]
            current_sma_50 = sma_50.iloc[-1]
            prev_price = data['close'].iloc[-2]
            prev_sma_50 = sma_50.iloc[-2]
            
            # Check if price crossed above SMA 50
            crossed_above = (prev_price <= prev_sma_50) and (current_price > current_sma_50)
            
            # Or if price is above SMA 50 and trending up
            above_sma = current_price > current_sma_50
            trending_up = current_price > prev_price
            
            if crossed_above or (above_sma and trending_up):
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.WEAK if above_sma else SignalStrength.MODERATE,
                    'confidence_score': 0.6 if above_sma else 0.75,
                    'details': {
                        'type': 'sma_50_test',
                        'price': float(current_price),
                        'sma_50': float(current_sma_50),
                        'crossed_above': bool(crossed_above),
                        'above_sma': bool(above_sma),
                        'trending_up': bool(trending_up),
                        'reason': 'Price crossed above SMA 50' if crossed_above else 'Price above SMA 50 and trending up'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in SMA 50 detection: {str(e)}")
            return None

    def detect_confirmed_buy_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """
        Detect confirmed buy signal with specific conditions:
        1. 5 EMA crossed 20 EMA in the last 5 days, excluding latest closed candle
        2. Last closed candle (both open and close prices) above both 5 EMA and 20 EMA
        3. Closed price of last candle above 50 SMA
        4. Average Volume for latest 5 candles > average of last 50 candles
        5. RSI above 50
        6. MACD positive on the last candle
        """
        if len(data) < 50:  # Need at least 50 candles for all calculations
            return None
        
        try:
            # Calculate indicators
            ema_5 = self.calculate_ema(data['close'], 5)
            ema_20 = self.calculate_ema(data['close'], 20)
            sma_50 = self.calculate_sma(data['close'], 50)
            rsi = self.calculate_rsi(data['close'])
            macd_data = self.calculate_macd(data['close'])
            macd_line = macd_data['macd']
            signal_line = macd_data['signal']
            
            # Current values (last closed candle) - convert to native Python types
            current_open = float(data['open'].iloc[-1])
            current_close = float(data['close'].iloc[-1])
            current_ema_5 = float(ema_5.iloc[-1])
            current_ema_20 = float(ema_20.iloc[-1])
            current_sma_50 = float(sma_50.iloc[-1])
            current_rsi = float(rsi.iloc[-1])
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            
            # Get the signal date (date of last closed candle used in calculation)
            signal_date = data.index[-1].date() if hasattr(data.index[-1], 'date') else data.index[-1]
            
            # Calculate volume ratios like the reference implementation
            if 'volume' in data.columns:
                volume_5_day_avg = data['volume'].rolling(window=5, min_periods=1).mean()
                volume_50_day_avg = data['volume'].rolling(window=50, min_periods=1).mean()
                volume_ratio = volume_5_day_avg / volume_50_day_avg
                current_volume_ratio = float(volume_ratio.iloc[-1])
            else:
                current_volume_ratio = 0.0
            
            # Condition 1: 5 EMA crossed 20 EMA in last 5 candles (days -6 to -2, excluding latest)
            ema_crossover_detected = False
            current_above = current_ema_5 > current_ema_20
            
            # Find cross points in window [-6, -2] (excluding current candle at -1)
            cross_points = []
            for j in range(-6, -1):  # Check indices -6, -5, -4, -3, -2
                if len(data) > abs(j):  # Ensure we have enough data
                    curr_ema_5 = float(ema_5.iloc[j])
                    curr_ema_20 = float(ema_20.iloc[j])
                    prev_ema_5 = float(ema_5.iloc[j-1]) if len(data) > abs(j-1) else curr_ema_5
                    prev_ema_20 = float(ema_20.iloc[j-1]) if len(data) > abs(j-1) else curr_ema_20
                    
                    # Bullish crossover: 5 EMA crosses above 20 EMA
                    if curr_ema_5 > curr_ema_20 and prev_ema_5 <= prev_ema_20:
                        cross_points.append(j)
            
            # Only consider if there is a cross and we're currently above
            if cross_points and current_above:
                most_recent_cross = max(cross_points)
                # Only trigger if most recent cross is at -2, -3, -4, -5, or -6
                if most_recent_cross in [-2, -3, -4, -5, -6]:
                    ema_crossover_detected = True
            
            # Condition 2: Last closed candle (open and close) above both EMAs
            price_above_emas = (current_open > current_ema_5 and current_open > current_ema_20 and
                               current_close > current_ema_5 and current_close > current_ema_20)
            
            # Condition 3: Close price above 50 SMA
            price_above_sma50 = current_close > current_sma_50
            
            # Condition 4: Volume ratio > 1.0 (like reference implementation)
            volume_confirmation = current_volume_ratio > 1.0
            
            # Condition 5: RSI above 50
            rsi_bullish = current_rsi > 50
            
            # Condition 6: MACD above Signal Line (correct condition!)
            macd_cross = current_macd > current_signal
            
            # Define all core conditions
            core_conditions = [
                ema_crossover_detected,
                price_above_emas,
                price_above_sma50,
                rsi_bullish,
                macd_cross
            ]
            
            conditions_met = sum(core_conditions) + (1 if volume_confirmation else 0)
            
            # Generate signals with different strictness levels (like reference implementation)
            # Priority: volume confirmed > no volume confirmed
            
            if all(core_conditions + [volume_confirmation]):  # All 6 conditions including volume
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.95,
                    'signal_date': signal_date,
                    'details': {
                        'type': 'confirmed_buy_volume',
                        'reason': 'All buy conditions met (volume confirmed)',
                        'price': float(current_close),
                        'open_price': float(current_open),
                        'ema_5': float(current_ema_5),
                        'ema_20': float(current_ema_20),
                        'sma_50': float(current_sma_50),
                        'rsi': float(current_rsi),
                        'macd': float(current_macd),
                        'volume_ratio': float(current_volume_ratio),
                        'conditions_met': 6,
                        'ema_crossover': ema_crossover_detected,
                        'price_above_emas': price_above_emas,
                        'price_above_sma50': price_above_sma50,
                        'volume_confirmation': volume_confirmation,
                        'rsi_bullish': rsi_bullish,
                        'macd_cross': macd_cross,
                        'reason': 'Confirmed buy signal - all 6 conditions met: 5EMA/20EMA crossover in last 5 days, price above EMAs, price above 50 SMA, volume spike, RSI > 50, MACD > Signal Line'
                    }
                }
            # Skip signals without volume confirmation when focus_confirmed_buy is True
            # elif all(core_conditions):  # 5 core conditions without volume - DISABLED for volume-only mode
            #     return {
            #         'signal_type': SignalType.BUY,
            #         'signal_strength': SignalStrength.MODERATE,
            #         'confidence_score': 0.85,
            #         'details': {
            #             'type': 'confirmed_buy_no_volume',
            #             'reason': 'All buy conditions met (no volume confirmation)',
            #             'price': float(current_close),
            #             'open_price': float(current_open),
            #             'ema_5': float(current_ema_5),
            #             'ema_20': float(current_ema_20),
            #             'sma_50': float(current_sma_50),
            #             'rsi': float(current_rsi),
            #             'macd': float(current_macd),
            #             'volume_ratio': float(current_volume_ratio),
            #             'conditions_met': 5,
            #             'ema_crossover': ema_crossover_detected,
            #             'price_above_emas': price_above_emas,
            #             'price_above_sma50': price_above_sma50,
            #             'volume_confirmation': volume_confirmation,
            #             'rsi_bullish': rsi_bullish,
            #             'macd_cross': macd_cross,
            #             'reason': 'Confirmed buy signal - 5 conditions met (no volume confirmation)'
            #         }
            #     }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in confirmed buy detection: {str(e)}")
            return None
    
    def generate_signals_for_ticker(self, ticker: Ticker, data: pd.DataFrame, focus_confirmed_buy: bool = False) -> List[Dict]:
        """Generate signals for a single ticker"""
        signals = []
        
        if focus_confirmed_buy:
            # Only generate confirmed buy signals
            signal_methods = [self.detect_confirmed_buy_signal]
        else:
            # Apply all signal detection methods
            signal_methods = [
                self.detect_sma_above_50_signal,  # Simple test signal first
                self.detect_ema_crossover_signal,
                self.detect_golden_cross_signal,
                self.detect_sma_volume_signal,
                self.detect_confirmed_buy_signal
            ]
        
        for method in signal_methods:
            try:
                signal = method(data)
                if signal:
                    signal['ticker_id'] = ticker.id
                    signal['price'] = float(data['close'].iloc[-1])
                    signal['volume'] = int(data['volume'].iloc[-1]) if 'volume' in data.columns else None
                    # Ensure signal_date is present (fallback for other signal methods)
                    if 'signal_date' not in signal:
                        signal['signal_date'] = data.index[-1].date() if hasattr(data.index[-1], 'date') else data.index[-1]
                    # Convert numpy types to Python types for JSON serialization
                    signal['signal_data'] = json.dumps(signal['details'], default=self._json_serializer)
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error applying {method.__name__} to {ticker.symbol}: {str(e)}")
        
        return signals
    
    async def generate_signals_for_tickers(self, tickers: List[Ticker], db: Session, focus_confirmed_buy: bool = False, batch_size: int = 20):
        """Generate signals using direct yfinance calls (no complex data fetcher)"""
        try:
            import yfinance as yf
            
            logger.info(f"Starting direct signal generation for {len(tickers)} tickers")
            
            # Filter stock tickers only
            stock_tickers = [t for t in tickers if t.market_type.value == 'stock']
            if not stock_tickers:
                logger.warning("No stock tickers found")
                return
            
            # Format symbols for ASX
            formatted_symbols = []
            ticker_map = {}
            
            for ticker in stock_tickers:
                symbol = ticker.symbol
                if ticker.exchange == 'ASX' and not symbol.endswith('.AX'):
                    symbol = f"{symbol}.AX"
                formatted_symbols.append(symbol)
                ticker_map[symbol] = ticker
            
            logger.info(f"Formatted symbols: {formatted_symbols[:10]}...")
            
            # Use subprocess to call yfinance in separate process (avoids web server context issues)
            logger.info("Using subprocess to call yfinance...")
            try:
                import subprocess
                import tempfile
                import pickle
                import os
                
                # Create a temporary script to run yfinance
                script_content = f'''
import yfinance as yf
import pickle
import sys

symbols = {formatted_symbols}
print(f"Fetching {{len(symbols)}} symbols: {{symbols[:5]}}...")

try:
    data = yf.download(
        symbols,
        period="60d",
        group_by='ticker',
        auto_adjust=False,
        threads=True,
        progress=False
    )
    
    print(f"Downloaded data shape: {{data.shape}}")
    print(f"Data empty: {{data.empty}}")
    
    # Save to pickle file
    with open(sys.argv[1], 'wb') as f:
        pickle.dump(data, f)
    print("Data saved successfully")
    
except Exception as e:
    print(f"Error: {{e}}")
    sys.exit(1)
'''
                
                # Write script to temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
                    script_file.write(script_content)
                    script_path = script_file.name
                
                # Create temporary file for data
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as data_file:
                    data_path = data_file.name
                
                try:
                    # Run the script in subprocess
                    result = subprocess.run([
                        r"C:\Users\pushp\AppData\Local\Programs\Python\Python310\python.exe",
                        script_path,
                        data_path
                    ], capture_output=True, text=True, timeout=120)
                    
                    logger.info(f"Subprocess stdout: {result.stdout}")
                    if result.stderr:
                        logger.warning(f"Subprocess stderr: {result.stderr}")
                    
                    if result.returncode != 0:
                        logger.error(f"Subprocess failed with return code: {result.returncode}")
                        return
                    
                    # Load the data
                    with open(data_path, 'rb') as f:
                        batch_data = pickle.load(f)
                    
                    logger.info(f"Loaded data from subprocess: {type(batch_data)}, shape: {batch_data.shape}")
                    
                finally:
                    # Clean up temporary files
                    if os.path.exists(script_path):
                        os.unlink(script_path)
                    if os.path.exists(data_path):
                        os.unlink(data_path)
                
                if batch_data.empty:
                    logger.error("Subprocess returned empty data")
                    return
                    
            except Exception as e:
                logger.error(f"Subprocess yfinance call failed: {e}")
                return
            
            # Process results
            ticker_data = {}
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            for symbol in formatted_symbols:
                ticker = ticker_map[symbol]
                
                try:
                    if len(formatted_symbols) == 1:
                        hist = batch_data
                        # Fix single symbol column structure - yfinance returns MultiIndex even for single symbols
                        if hasattr(hist.columns, 'levels') and len(hist.columns.levels) == 2:
                            # Flatten MultiIndex columns for single symbol - use level 1 (price names)
                            hist.columns = hist.columns.get_level_values(1)
                    else:
                        if symbol not in batch_data.columns.levels[0]:
                            logger.warning(f"No data for {symbol}")
                            continue
                        hist = batch_data[symbol]
                    
                    if hist.empty or len(hist) < 50:
                        logger.warning(f"Insufficient data for {symbol}")
                        continue
                    
                    # Check required columns
                    missing = [col for col in required_columns if col not in hist.columns]
                    if missing:
                        logger.warning(f"Missing columns {missing} for {symbol}")
                        continue
                    
                    # Forward fill and rename columns
                    hist = hist.ffill()
                    hist = hist.rename(columns={
                        'Open': 'open', 'High': 'high', 'Low': 'low',
                        'Close': 'close', 'Volume': 'volume'
                    })
                    
                    ticker_data[ticker.id] = hist
                    logger.info(f"Successfully processed {ticker.symbol}: {len(hist)} rows")
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            logger.info(f"Successfully fetched data for {len(ticker_data)} tickers")
            
            if not ticker_data:
                logger.warning("No ticker data fetched")
                return
            
            logger.info(f"Successfully fetched data for {len(ticker_data)} tickers, generating signals...")
            
            # Generate signals concurrently using thread pool for CPU-bound work
            import concurrent.futures
            from functools import partial
            
            def process_ticker_signals(ticker_id_and_data):
                ticker_id, (ticker, data) = ticker_id_and_data
                try:
                    return self.generate_signals_for_ticker(ticker, data, focus_confirmed_buy)
                except Exception as e:
                    logger.error(f"Error generating signals for {ticker.symbol}: {str(e)}")
                    return []
            
            # Prepare ticker data with ticker objects
            ticker_lookup = {t.id: t for t in tickers}
            ticker_data_pairs = [(tid, (ticker_lookup[tid], data)) for tid, data in ticker_data.items() if tid in ticker_lookup]
            
            # Process signals in parallel using thread pool
            all_signals = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                signal_results = list(executor.map(process_ticker_signals, ticker_data_pairs))
                
                # Flatten results
                for signals in signal_results:
                    all_signals.extend(signals)
            
            logger.info(f"Generated {len(all_signals)} total signals")
            
            # Debug: Log some signal details
            if all_signals:
                logger.info(f"Sample signals generated:")
                for i, signal in enumerate(all_signals[:5]):  # Log first 5 signals
                    logger.info(f"  Signal {i+1}: {signal.get('ticker_id')} - {signal.get('signal_type')} - {signal.get('signal_strength')}")
            
            # Cleanup and save signals to database
            if all_signals:
                try:
                    from datetime import datetime, timedelta, date
                    
                    # 1. Cleanup: Delete signals older than 10 days
                    cleanup_date = (datetime.utcnow() - timedelta(days=10)).date()
                    deleted_count = db.query(Signal).filter(Signal.signal_date < cleanup_date).delete(synchronize_session=False)
                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} signals older than {cleanup_date}")
                    
                    # 2. Duplicate prevention: Remove existing signals for same ticker_id + signal_date combinations
                    ticker_signal_dates = set()
                    for signal_data in all_signals:
                        if signal_data.get('signal_date'):
                            ticker_signal_dates.add((signal_data['ticker_id'], signal_data['signal_date']))
                    
                    if ticker_signal_dates:
                        # Build OR conditions for bulk deletion of duplicates
                        from sqlalchemy import and_, or_
                        duplicate_conditions = []
                        for ticker_id, sig_date in ticker_signal_dates:
                            duplicate_conditions.append(
                                and_(Signal.ticker_id == ticker_id, Signal.signal_date == sig_date)
                            )
                        
                        if duplicate_conditions:
                            duplicate_deleted = db.query(Signal).filter(or_(*duplicate_conditions)).delete(synchronize_session=False)
                            if duplicate_deleted > 0:
                                logger.info(f"Removed {duplicate_deleted} duplicate signals for same ticker+date combinations")
                    
                    # 3. Create new signal objects
                    db_signals = []
                    for signal_data in all_signals:
                        db_signal = Signal(
                            ticker_id=signal_data['ticker_id'],
                            signal_type=signal_data['signal_type'],
                            signal_strength=signal_data['signal_strength'],
                            price=signal_data['price'],
                            volume=signal_data['volume'],
                            signal_data=signal_data['signal_data'],
                            confidence_score=signal_data['confidence_score'],
                            signal_date=signal_data.get('signal_date')
                        )
                        db_signals.append(db_signal)
                    
                    # 4. Batch insert with proper error handling
                    db.add_all(db_signals)
                    db.flush()  # Flush to detect any SQL errors before commit
                    db.commit()
                    logger.info(f"Successfully saved {len(db_signals)} new signals to database")
                    
                except Exception as db_error:
                    logger.error(f"Database error during signal save: {str(db_error)}")
                    db.rollback()
                    raise
            else:
                logger.info("No signals generated")
            
        except Exception as e:
            logger.error(f"Error in signal generation: {str(e)}")
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {str(rollback_error)}")
            raise