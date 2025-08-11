"""
Binance API Service
Handles fetching cryptocurrency data and pairs from Binance exchange.
"""

import ccxt
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


class BinanceService:
    """Service for interacting with Binance API"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'sandbox': False,  # Set to True for testnet
            'rateLimit': 1200,  # milliseconds
            'enableRateLimit': True,
        })
    
    def get_pairs_by_base_asset(self, base_asset: str = 'ETH', min_volume_usdt: float = 1000000) -> List[str]:
        """
        Get all trading pairs for a specific base asset from Binance
        
        Args:
            base_asset: Base asset to get pairs for ('ETH' or 'BTC')
            min_volume_usdt: Minimum 24h volume in USDT equivalent
        
        Returns:
            List of trading pair symbols (e.g., ['ADA', 'BNB', ...])
        """
        try:
            logger.info(f"Fetching {base_asset} pairs from Binance...")
            
            # Discover ALL available pairs for the base asset (like reference script)
            logger.info(f"Discovering all {base_asset} pairs from Binance markets...")
            
            # Load all markets from Binance
            markets = self.exchange.load_markets()
            
            # Find all spot pairs with the specified base asset as quote
            pairs = []
            for symbol, market_info in markets.items():
                # Only active spot pairs
                if not (market_info.get('spot') and market_info.get('active')):
                    continue
                
                # Check if this pair uses our base asset as quote (e.g., */BTC pairs)
                quote_asset = market_info.get('quote', '')
                if quote_asset.upper() == base_asset.upper():
                    # Get volume for filtering
                    volume = float(market_info.get('info', {}).get('quoteVolume', 0) or 0)
                    base_symbol = market_info.get('base', '')
                    
                    if base_symbol:
                        pairs.append((base_symbol, volume))
            
            # Sort by volume descending and take top 80% (like reference)
            pairs = sorted(pairs, key=lambda x: x[1], reverse=True)
            n = int(len(pairs) * 0.8) if len(pairs) > 0 else 0
            top_pairs = [p[0] for p in pairs[:n]]
            
            logger.info(f"Discovered {len(pairs)} total {base_asset} pairs, using top {len(top_pairs)} (80%)")
            return top_pairs
            
        except Exception as e:
            logger.error(f"Error fetching {base_asset} pairs from Binance: {str(e)}")
            return []
    
    def get_eth_pairs(self, min_volume_usdt: float = 1000000) -> List[str]:
        """
        Get all ETH trading pairs from Binance (legacy method for backward compatibility)
        
        Args:
            min_volume_usdt: Minimum 24h volume in USDT equivalent
        
        Returns:
            List of trading pair symbols (e.g., ['ADA', 'BNB', ...])
        """
        return self.get_pairs_by_base_asset('ETH', min_volume_usdt)
    
    def get_btc_pairs(self, min_volume_usdt: float = 1000000) -> List[str]:
        """
        Get all BTC trading pairs from Binance
        
        Args:
            min_volume_usdt: Minimum 24h volume in USDT equivalent
        
        Returns:
            List of trading pair symbols (e.g., ['ADA', 'ETH', ...])
        """
        return self.get_pairs_by_base_asset('BTC', min_volume_usdt)
    
    def fetch_kline_data(self, symbol: str, base_asset: str = 'ETH', timeframe: str = '1d', limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch kline/candlestick data for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'ADA')
            base_asset: Base asset ('ETH', 'BTC', etc.)
            timeframe: Timeframe ('1m', '5m', '1h', '1d', etc.)
            limit: Number of candles to fetch
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Format symbol for Binance (e.g., 'ADA' -> 'ADA/ETH' or 'ADA/BTC')
            formatted_symbol = f"{symbol}/{base_asset}"
            
            logger.debug(f"Fetching {limit} {timeframe} candles for {formatted_symbol}")
            
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=limit)
            
            if not ohlcv:
                logger.warning(f"No data returned for {formatted_symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Ensure numeric types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            logger.debug(f"Successfully fetched {len(df)} candles for {formatted_symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def check_recent_data_availability(self, symbol: str, base_asset: str = 'ETH', days: int = 3) -> bool:
        """
        Check if symbol has data within the last N days
        
        Args:
            symbol: Trading pair symbol
            base_asset: Base asset ('ETH', 'BTC', etc.)
            days: Number of days to check
        
        Returns:
            True if data is available, False otherwise
        """
        try:
            # Fetch recent data (small limit for speed)
            df = self.fetch_kline_data(symbol, base_asset, timeframe='1d', limit=5)
            
            if df is None or df.empty:
                return False
            
            # Check if most recent data is within the specified days
            latest_timestamp = df.index.max()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            return latest_timestamp.to_pydatetime() >= cutoff_date
            
        except Exception as e:
            logger.error(f"Error checking data availability for {symbol}: {str(e)}")
            return False
    
    def check_data_exists(self, symbol: str, base_asset: str = 'ETH') -> bool:
        """
        Check if symbol has sufficient historical data (relaxed check)
        
        Args:
            symbol: Trading pair symbol
            base_asset: Base asset ('ETH', 'BTC', etc.)
        
        Returns:
            True if data exists with at least 200 candles, False otherwise
        """
        try:
            # Fetch data to check availability (similar to reference script requirements)
            df = self.fetch_kline_data(symbol, base_asset, timeframe='1d', limit=200)
            
            # Just check if we have enough data for analysis (200 candles)
            return df is not None and not df.empty and len(df) >= 200
            
        except Exception as e:
            # If we can't fetch data, assume it doesn't exist
            return False
    
    async def get_active_pairs_with_data(self, base_asset: str = 'ETH', min_volume_usdt: float = 1000000, days_check: int = 3) -> List[str]:
        """
        Get pairs that have data available for a specific base asset
        
        Args:
            base_asset: Base asset ('ETH', 'BTC', etc.)
            min_volume_usdt: Minimum 24h volume in USDT equivalent (currently ignored to match reference)
            days_check: Number of days to check for recent data (relaxed to match reference)
        
        Returns:
            List of trading pair symbols with available data
        """
        try:
            # Get all discovered pairs for the base asset (now includes many more pairs)
            all_pairs = self.get_pairs_by_base_asset(base_asset, min_volume_usdt)
            
            logger.info(f"Checking data availability for {len(all_pairs)} {base_asset} pairs...")
            
            active_pairs = []
            
            # Check data availability with relaxed constraints (like reference script)
            batch_size = 30  # Increased for faster processing
            for i in range(0, len(all_pairs), batch_size):
                batch = all_pairs[i:i + batch_size]
                
                for symbol in batch:
                    # Relax the data availability check - just require that data exists (not necessarily recent)
                    if self.check_data_exists(symbol, base_asset):
                        active_pairs.append(symbol)
                
                # Very small delay between batches
                if i + batch_size < len(all_pairs):
                    await asyncio.sleep(0.05)  # Reduced delay
            
            logger.info(f"Found {len(active_pairs)} {base_asset} pairs with available data")
            return active_pairs
            
        except Exception as e:
            logger.error(f"Error getting active {base_asset} pairs: {str(e)}")
            return []
    
    async def get_active_eth_pairs_with_data(self, min_volume_usdt: float = 1000000, days_check: int = 3) -> List[str]:
        """
        Get ETH pairs that have recent data and sufficient volume (legacy method for backward compatibility)
        
        Args:
            min_volume_usdt: Minimum 24h volume in USDT equivalent
            days_check: Number of days to check for recent data
        
        Returns:
            List of active trading pair symbols with recent data
        """
        return await self.get_active_pairs_with_data('ETH', min_volume_usdt, days_check)
    
    async def get_active_btc_pairs_with_data(self, min_volume_usdt: float = 1000000, days_check: int = 3) -> List[str]:
        """
        Get BTC pairs that have recent data and sufficient volume
        
        Args:
            min_volume_usdt: Minimum 24h volume in USDT equivalent
            days_check: Number of days to check for recent data
        
        Returns:
            List of active trading pair symbols with recent data
        """
        return await self.get_active_pairs_with_data('BTC', min_volume_usdt, days_check)
    
    async def fetch_multiple_pairs_data(self, symbols: List[str], base_asset: str = 'ETH', timeframe: str = '1d', limit: int = 100) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple pairs efficiently
        
        Args:
            symbols: List of trading pair symbols
            base_asset: Base asset ('ETH', 'BTC', etc.)
            timeframe: Timeframe for data
            limit: Number of candles per symbol
        
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}
        
        logger.info(f"Fetching data for {len(symbols)} {base_asset} pairs...")
        
        # Process in larger batches with shorter delays for better performance
        batch_size = 20  # Increased batch size
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            logger.debug(f"Processing batch {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size}")
            
            for symbol in batch:
                df = self.fetch_kline_data(symbol, base_asset, timeframe, limit)
                if df is not None and not df.empty:
                    results[symbol] = df
                else:
                    logger.debug(f"No data available for {symbol}")  # Reduced to debug to avoid spam
            
            # Shorter delay between batches
            if i + batch_size < len(symbols):
                await asyncio.sleep(0.1)  # Reduced delay
        
        logger.info(f"Successfully fetched data for {len(results)}/{len(symbols)} {base_asset} pairs")
        return results


# Global instance
binance_service = BinanceService()