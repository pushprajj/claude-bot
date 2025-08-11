"""
Refactored Signal Generator Module
Main orchestrator for signal generation using modular components.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging
from sqlalchemy.orm import Session

from app.models import Ticker, Signal, SignalType, SignalStrength, MarketType
from app.services.data_fetcher import DataFetcher
from app.services.technical_indicators import TechnicalIndicators
from app.services.signal_detectors import SignalDetectors
from app.services.signal_detectors_extended import ExtendedSignalDetectors
from app.services.market_hours import validate_candle_for_signals

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Main signal generation orchestrator using modular components"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.indicators = TechnicalIndicators()
        self.detectors = SignalDetectors()
        self.extended_detectors = ExtendedSignalDetectors()
    
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
    
    def generate_signals_for_ticker(self, ticker: Ticker, data: pd.DataFrame, focus_confirmed_buy: bool = False) -> List[Dict]:
        """Generate signals for a single ticker using modular detection methods"""
        signals = []
        
        # Validate candle data based on market hours
        validated_data, signal_date, validation_reason = validate_candle_for_signals(data, ticker.exchange)
        logger.info(f"{ticker.symbol} ({ticker.exchange}): {validation_reason}")
        
        if validated_data.empty:
            logger.warning(f"No valid candle data for {ticker.symbol} after market hours validation")
            return signals
        
        if focus_confirmed_buy:
            # Only generate confirmed buy signals
            signal_methods = [
                ('confirmed_buy', self.extended_detectors.detect_confirmed_buy_signal)
            ]
        else:
            # Apply all signal detection methods
            signal_methods = [
                ('sma_above_50', self.extended_detectors.detect_sma_above_50_signal),
                ('ema_crossover', self.detectors.detect_ema_crossover_signal),
                ('golden_cross', self.detectors.detect_golden_cross_signal),
                ('sma_volume', self.extended_detectors.detect_sma_volume_signal),
                ('confirmed_buy', self.extended_detectors.detect_confirmed_buy_signal)
            ]
        
        for method_name, method in signal_methods:
            try:
                signal = method(validated_data)
                if signal:
                    signal['ticker_id'] = ticker.id
                    signal['price'] = float(validated_data['close'].iloc[-1])
                    signal['volume'] = int(validated_data['volume'].iloc[-1]) if 'volume' in validated_data.columns else None
                    
                    # Use the validated signal date from market hours validation
                    if 'signal_date' not in signal:
                        signal['signal_date'] = signal_date
                    
                    # Convert numpy types to Python types for JSON serialization
                    signal['signal_data'] = json.dumps(signal['details'], default=self._json_serializer)
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error applying {method_name} to {ticker.symbol}: {str(e)}")
        
        return signals
    
    async def generate_signals_for_tickers(self, tickers: List[Ticker], db: Session, focus_confirmed_buy: bool = False, batch_size: int = 20):
        """Generate signals using direct yfinance calls"""
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
            
            # Use subprocess approach for yfinance data fetching
            all_signals = []
            
            try:
                import subprocess
                import tempfile
                import pickle
                import os
                
                # Create temporary script to run yfinance
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
    
    with open(sys.argv[1], 'wb') as f:
        pickle.dump(data, f)
    print("Data saved successfully")
    
except Exception as e:
    print(f"Error in yfinance: {{e}}")
    sys.exit(1)
'''
                
                # Write and execute script
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(script_content)
                    script_path = f.name
                
                with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                    data_path = f.name
                
                try:
                    result = subprocess.run([
                        'python', script_path, data_path
                    ], capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        with open(data_path, 'rb') as f:
                            data = pickle.load(f)
                        logger.info("Successfully loaded data from subprocess")
                    else:
                        logger.error(f"Subprocess failed: {result.stderr}")
                        return
                        
                finally:
                    # Cleanup temp files
                    for path in [script_path, data_path]:
                        if os.path.exists(path):
                            os.unlink(path)
                
            except Exception as e:
                logger.error(f"Subprocess approach failed: {e}")
                return
            
            # Process the downloaded data
            all_signals = self._process_ticker_data(data, ticker_map, formatted_symbols, focus_confirmed_buy)
            
            # Save signals to database
            if all_signals:
                # Extract ticker IDs from the processed tickers for targeted signal cleanup
                processed_ticker_ids = [ticker.id for ticker in stock_tickers]
                self._save_signals_to_database(all_signals, db, processed_ticker_ids)
                logger.info(f"Successfully generated and saved {len(all_signals)} signals")
            else:
                logger.info("No signals generated")
                
        except Exception as e:
            logger.error(f"Error in generate_signals_for_tickers: {str(e)}")
            raise
    
    def _process_ticker_data(self, data, ticker_map: Dict, formatted_symbols: List[str], focus_confirmed_buy: bool = False) -> List[Dict]:
        """Process downloaded ticker data and generate signals"""
        all_signals = []
        
        for symbol in formatted_symbols:
            try:
                ticker = ticker_map[symbol]
                
                # Get data for this ticker
                if len(formatted_symbols) == 1:
                    ticker_data = data
                else:
                    ticker_data = data[symbol] if symbol in data.columns.get_level_values(0) else None
                
                if ticker_data is None or ticker_data.empty:
                    logger.warning(f"No data available for {symbol}")
                    continue
                
                # Ensure we have the required columns
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                if not all(col in ticker_data.columns for col in required_columns):
                    logger.warning(f"Missing required columns for {symbol}")
                    continue
                
                # Rename columns to lowercase for consistency
                ticker_data = ticker_data.rename(columns={
                    'Open': 'open',
                    'High': 'high', 
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                
                # Remove any NaN rows and ensure we have enough data
                ticker_data = ticker_data.dropna()
                if len(ticker_data) < 51:  # Need extra candle since we'll use [-2]
                    logger.warning(f"Insufficient data for {symbol}: {len(ticker_data)} candles")
                    continue
                
                # Generate signals - market hours validation is now handled inside generate_signals_for_ticker
                signals = self.generate_signals_for_ticker(ticker, ticker_data, focus_confirmed_buy)
                all_signals.extend(signals)
                
                if signals:
                    logger.info(f"Generated {len(signals)} signals for {ticker.symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        return all_signals
    
    def _save_signals_to_database(self, signals: List[Dict], db: Session, ticker_ids: List[int] = None):
        """Save generated signals to database with proper error handling"""
        try:
            from datetime import timedelta, date
            from app.models import WatchlistItem
            
            # 1. CLEANUP: Delete signals older than 10 days (rolling basis)
            cleanup_date = (datetime.utcnow() - timedelta(days=10)).date()
            old_signals_query = db.query(Signal).filter(Signal.signal_date < cleanup_date)
            old_count = old_signals_query.count()
            if old_count > 0:
                try:
                    # First clear watchlist references for old signals
                    db.query(WatchlistItem).filter(
                        WatchlistItem.signal_id.in_(
                            db.query(Signal.id).filter(Signal.signal_date < cleanup_date)
                        )
                    ).update({"signal_id": None}, synchronize_session=False)
                    
                    # Then delete old signals
                    old_signals_query.delete(synchronize_session=False)
                    logger.info(f"Cleaned up {old_count} signals older than 10 days ({cleanup_date})")
                except Exception as e:
                    db.rollback()
                    logger.warning(f"Could not cleanup old signals (foreign key constraints): {str(e)}")
                    logger.info("Continuing with signal generation - old signals will be preserved")
            
            # 2. CURRENT RUN: Handle signals for current ticker batch
            if ticker_ids:
                # Handle foreign key constraints: First update watchlist items to remove signal references for specific tickers
                db.query(WatchlistItem).filter(
                    WatchlistItem.signal_id.in_(
                        db.query(Signal.id).filter(Signal.ticker_id.in_(ticker_ids))
                    )
                ).update({"signal_id": None}, synchronize_session=False)
                
                # Now safely remove old signals for specific tickers only
                try:
                    deleted_count = db.query(Signal).filter(Signal.ticker_id.in_(ticker_ids)).delete(synchronize_session=False)
                    db.commit()
                    logger.info(f"Cleared {deleted_count} old signals for {len(ticker_ids)} specific tickers (after clearing watchlist references)")
                except Exception as e:
                    db.rollback()
                    logger.warning(f"Could not delete existing signals (foreign key constraints): {str(e)}")
                    logger.info("Continuing with signal generation - existing signals will be preserved")
            else:
                logger.warning("No ticker_ids provided - skipping signal cleanup to preserve existing signals from other markets/exchanges")
            
            # Prepare database signals
            db_signals = []
            for signal_data in signals:
                db_signal = Signal(
                    ticker_id=signal_data['ticker_id'],
                    signal_type=signal_data['signal_type'],
                    signal_strength=signal_data['signal_strength'],
                    price=signal_data['price'],
                    volume=signal_data.get('volume'),
                    generated_at=datetime.utcnow(),
                    is_processed=False,
                    signal_data=signal_data['signal_data'],
                    confidence_score=signal_data['confidence_score'],
                    signal_date=signal_data.get('signal_date')
                )
                db_signals.append(db_signal)
            
            # Batch insert with proper error handling
            db.add_all(db_signals)
            db.flush()  # Flush to detect any SQL errors before commit
            db.commit()
            logger.info(f"Successfully saved {len(db_signals)} new signals to database")
            
        except Exception as db_error:
            logger.error(f"Database error during signal save: {str(db_error)}")
            db.rollback()
            raise