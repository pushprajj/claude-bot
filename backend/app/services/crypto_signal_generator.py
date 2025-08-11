"""
Crypto Signal Generator
Handles signal generation for cryptocurrency trading pairs using Binance data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, date
import json
import logging

from app.services.binance_service import binance_service
from app.services.signal_detectors_extended import ExtendedSignalDetectors
from app.models import SignalType, SignalStrength

logger = logging.getLogger(__name__)


class CryptoSignalGenerator:
    """Generate trading signals for cryptocurrency pairs"""
    
    def __init__(self):
        self.binance = binance_service
        self.detectors = ExtendedSignalDetectors()
    
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
    
    def generate_signals_for_crypto_pair(self, symbol: str, data: pd.DataFrame, base_asset: str = 'ETH', focus_confirmed_buy: bool = True) -> List[Dict]:
        """
        Generate signals for a single crypto trading pair
        
        Args:
            symbol: Trading pair symbol (e.g., 'ADA' for ADA/ETH or ADA/BTC)
            data: OHLCV DataFrame
            base_asset: Base asset ('ETH', 'BTC', etc.)
            focus_confirmed_buy: Whether to focus on confirmed buy signals only
        
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        try:
            logger.debug(f"Generating signals for {symbol}/{base_asset} with {len(data)} candles")
            
            # Validate data length
            if len(data) < 50:
                logger.warning(f"Insufficient data for {symbol}: {len(data)} candles (need at least 50)")
                return signals
            
            # Generate confirmed buy signals (similar to stocks)
            if focus_confirmed_buy:
                confirmed_signal = self.detectors.detect_confirmed_buy_signal(data)
                
                if confirmed_signal:
                    # Create signal data structure similar to stocks
                    current_price = float(data['close'].iloc[-1])
                    signal_date = date.today()
                    
                    signal_data = {
                        'symbol': symbol,
                        'exchange': 'Binance',
                        'market_type': 'crypto',
                        'base_asset': base_asset,
                        'signal_type': confirmed_signal['signal_type'].value,
                        'signal_strength': confirmed_signal['signal_strength'].value,
                        'confidence_score': confirmed_signal['confidence_score'],
                        'price': current_price,
                        'signal_date': signal_date.isoformat(),
                        'generated_at': datetime.utcnow().isoformat(),
                        'signal_data': json.dumps(confirmed_signal['details'], default=self._json_serializer),
                        'volume': float(data['volume'].iloc[-1]) if 'volume' in data.columns else 0
                    }
                    
                    signals.append(signal_data)
                    logger.info(f"Generated confirmed buy signal for {symbol}/{base_asset} at price {current_price:.8f}")
            
        except Exception as e:
            logger.error(f"Error generating signals for {symbol}: {str(e)}")
        
        return signals
    
    async def generate_crypto_pair_signals(self, 
                                           base_asset: str = 'ETH',
                                           min_volume_usdt: float = 1000000,
                                           days_check: int = 3,
                                           focus_confirmed_buy: bool = True,
                                           limit_pairs: Optional[int] = None) -> List[Dict]:
        """
        Generate signals for all active crypto trading pairs for a specific base asset
        
        Args:
            base_asset: Base asset ('ETH', 'BTC', etc.)
            min_volume_usdt: Minimum 24h volume in USDT equivalent
            days_check: Number of days to check for recent data
            focus_confirmed_buy: Whether to focus on confirmed buy signals only
            limit_pairs: Optional limit on number of pairs to process
        
        Returns:
            List of signal dictionaries
        """
        all_signals = []
        
        try:
            print(f"[DEBUG] Starting {base_asset} pair signal generation...")
            logger.info(f"Starting {base_asset} pair signal generation...")
            
            # Get active pairs with recent data for the specified base asset
            active_pairs = await self.binance.get_active_pairs_with_data(base_asset, min_volume_usdt, days_check)
            
            print(f"[DEBUG] Found {len(active_pairs)} active {base_asset} pairs")
            
            if not active_pairs:
                print(f"[DEBUG] No active {base_asset} pairs found - returning empty")
                logger.warning(f"No active {base_asset} pairs found")
                return all_signals
            
            # Apply pair limit if specified
            if limit_pairs:
                active_pairs = active_pairs[:limit_pairs]
                print(f"[DEBUG] Limited to first {limit_pairs} pairs for testing")
                logger.info(f"Limited to first {limit_pairs} pairs for testing")
            
            print(f"[DEBUG] Processing {len(active_pairs)} pairs: {active_pairs[:5]}...")  # Show first 5
            
            # Fetch data for all pairs
            pairs_data = await self.binance.fetch_multiple_pairs_data(
                active_pairs, 
                base_asset,
                timeframe='1d', 
                limit=100
            )
            
            print(f"[DEBUG] Fetched data for {len(pairs_data)} out of {len(active_pairs)} pairs")
            
            if not pairs_data:
                print(f"[DEBUG] No data fetched for any pairs - returning empty")
                logger.warning("No data fetched for any pairs")
                return all_signals
            
            print(f"[DEBUG] Pairs with data: {list(pairs_data.keys())[:5]}...")  # Show first 5
            logger.info(f"Generating signals for {len(pairs_data)} pairs with data...")
            
            # Generate signals for each pair
            for symbol, data in pairs_data.items():
                try:
                    signals = self.generate_signals_for_crypto_pair(
                        symbol, 
                        data, 
                        base_asset,
                        focus_confirmed_buy=focus_confirmed_buy
                    )
                    all_signals.extend(signals)
                    
                except Exception as e:
                    logger.error(f"Error processing signals for {symbol}: {str(e)}")
                    continue
            
            print(f"[DEBUG] Generated {len(all_signals)} total signals for {len(pairs_data)} {base_asset} pairs")
            logger.info(f"Generated {len(all_signals)} total signals for {len(pairs_data)} {base_asset} pairs")
            
        except Exception as e:
            logger.error(f"Error in {base_asset} pair signal generation: {str(e)}")
        
        return all_signals
    
    async def generate_eth_pair_signals(self, 
                                       min_volume_usdt: float = 1000000,
                                       days_check: int = 3,
                                       focus_confirmed_buy: bool = True,
                                       limit_pairs: Optional[int] = None) -> List[Dict]:
        """
        Generate signals for all active ETH trading pairs (legacy method for backward compatibility)
        
        Args:
            min_volume_usdt: Minimum 24h volume in USDT equivalent
            days_check: Number of days to check for recent data
            focus_confirmed_buy: Whether to focus on confirmed buy signals only
            limit_pairs: Optional limit on number of pairs to process
        
        Returns:
            List of signal dictionaries
        """
        return await self.generate_crypto_pair_signals('ETH', min_volume_usdt, days_check, focus_confirmed_buy, limit_pairs)
    
    async def generate_btc_pair_signals(self, 
                                       min_volume_usdt: float = 1000000,
                                       days_check: int = 3,
                                       focus_confirmed_buy: bool = True,
                                       limit_pairs: Optional[int] = None) -> List[Dict]:
        """
        Generate signals for all active BTC trading pairs
        
        Args:
            min_volume_usdt: Minimum 24h volume in USDT equivalent
            days_check: Number of days to check for recent data
            focus_confirmed_buy: Whether to focus on confirmed buy signals only
            limit_pairs: Optional limit on number of pairs to process
        
        Returns:
            List of signal dictionaries
        """
        return await self.generate_crypto_pair_signals('BTC', min_volume_usdt, days_check, focus_confirmed_buy, limit_pairs)
    
    async def test_crypto_signal_workflow(self, base_asset: str = 'ETH', test_symbols: List[str] = None) -> Dict:
        """
        Test the crypto signal workflow with a limited set of pairs
        
        Args:
            base_asset: Base asset to test ('ETH', 'BTC', etc.)
            test_symbols: Optional list of symbols to test with
        
        Returns:
            Test results dictionary
        """
        try:
            logger.info(f"Testing crypto signal workflow for {base_asset} pairs...")
            
            if test_symbols is None:
                # Use different symbols based on base asset
                if base_asset == 'ETH':
                    test_symbols = ['ADA', 'BNB', 'MATIC', 'LINK', 'UNI']
                elif base_asset == 'BTC':
                    test_symbols = ['ADA', 'ETH', 'MATIC', 'LINK', 'UNI']
                else:
                    test_symbols = ['ADA', 'ETH', 'MATIC']  # Default fallback
            
            results = {
                'success': False,
                'pairs_tested': 0,
                'signals_generated': 0,
                'errors': [],
                'base_asset': base_asset
            }
            
            # Fetch data for test symbols
            pairs_data = await self.binance.fetch_multiple_pairs_data(
                test_symbols, 
                base_asset,
                timeframe='1d', 
                limit=100
            )
            
            results['pairs_tested'] = len(pairs_data)
            
            if not pairs_data:
                results['errors'].append("No data fetched for test symbols")
                return results
            
            # Generate signals
            all_signals = []
            for symbol, data in pairs_data.items():
                try:
                    signals = self.generate_signals_for_crypto_pair(symbol, data, base_asset)
                    all_signals.extend(signals)
                except Exception as e:
                    results['errors'].append(f"Error processing {symbol}: {str(e)}")
            
            results['signals_generated'] = len(all_signals)
            results['success'] = True
            
            if all_signals:
                logger.info(f"Test successful: Generated {len(all_signals)} signals from {len(pairs_data)} {base_asset} pairs")
                # Log sample signal for debugging
                sample_signal = all_signals[0]
                logger.info(f"Sample signal: {sample_signal['symbol']}/{base_asset} at {sample_signal['price']:.8f}")
            else:
                logger.info(f"Test completed: No signals generated for {base_asset} pairs (normal if no buy conditions met)")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in crypto signal workflow test: {str(e)}")
            return {
                'success': False,
                'pairs_tested': 0,
                'signals_generated': 0,
                'errors': [str(e)],
                'base_asset': base_asset
            }


# Global instance
crypto_signal_generator = CryptoSignalGenerator()