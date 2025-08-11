"""
Market Hours Validation Module
Determines if markets are open/closed and validates candle data accordingly.
"""

from datetime import datetime, date, time
import pytz
from typing import Dict, Optional, Tuple
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class MarketHours:
    """Market hours and timezone management for different exchanges"""
    
    # Market trading hours (local time)
    MARKET_HOURS = {
        'NYSE': {
            'timezone': 'US/Eastern',
            'open': time(9, 30),    # 9:30 AM ET
            'close': time(16, 0),   # 4:00 PM ET
        },
        'NASDAQ': {
            'timezone': 'US/Eastern', 
            'open': time(9, 30),    # 9:30 AM ET
            'close': time(16, 0),   # 4:00 PM ET
        },
        'ASX': {
            'timezone': 'Australia/Sydney',
            'open': time(10, 0),    # 10:00 AM AEST/AEDT
            'close': time(16, 0),   # 4:00 PM AEST/AEDT
        }
    }
    
    @classmethod
    def is_market_open(cls, exchange: str, check_time: datetime = None) -> bool:
        """
        Check if market is currently open
        
        Args:
            exchange: Exchange name (NYSE, NASDAQ, ASX)
            check_time: Time to check (UTC), defaults to now
            
        Returns:
            True if market is open, False if closed
        """
        if check_time is None:
            check_time = datetime.utcnow()
        
        if exchange.upper() not in cls.MARKET_HOURS:
            logger.warning(f"Unknown exchange {exchange}, assuming closed")
            return False
        
        market_info = cls.MARKET_HOURS[exchange.upper()]
        market_tz = pytz.timezone(market_info['timezone'])
        
        # Convert UTC time to market timezone
        market_time = check_time.replace(tzinfo=pytz.UTC).astimezone(market_tz)
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if market_time.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        
        # Check if within trading hours
        current_time = market_time.time()
        return market_info['open'] <= current_time <= market_info['close']
    
    @classmethod
    def get_market_close_time_today(cls, exchange: str, reference_date: date = None) -> Optional[datetime]:
        """
        Get today's market close time in UTC
        
        Args:
            exchange: Exchange name
            reference_date: Date to check, defaults to today
            
        Returns:
            Market close time in UTC, or None if unknown exchange
        """
        if reference_date is None:
            reference_date = date.today()
        
        if exchange.upper() not in cls.MARKET_HOURS:
            return None
        
        market_info = cls.MARKET_HOURS[exchange.upper()]
        market_tz = pytz.timezone(market_info['timezone'])
        
        # Create market close time for the given date
        market_close_local = datetime.combine(reference_date, market_info['close'])
        market_close_localized = market_tz.localize(market_close_local)
        
        # Convert to UTC
        return market_close_localized.astimezone(pytz.UTC)
    
    @classmethod
    def validate_candle_data(cls, data: pd.DataFrame, exchange: str) -> Tuple[pd.DataFrame, str]:
        """
        Validate candle data and remove forming candles if market is open
        
        Args:
            data: DataFrame with OHLCV data
            exchange: Exchange name
            
        Returns:
            Tuple of (validated_data, reason_string)
        """
        if data.empty:
            return data, "No data provided"
        
        # Get the last candle date and current time
        last_candle_date = data.index[-1].date() if hasattr(data.index[-1], 'date') else data.index[-1]
        today = date.today()
        current_utc = datetime.utcnow()
        
        # Check if last candle is from today
        if last_candle_date != today:
            # Last candle is from a previous day - safe to use all data
            return data, f"Using all data - last candle from {last_candle_date}"
        
        # Last candle is from today - need to check if market is still open
        is_open = cls.is_market_open(exchange, current_utc)
        
        if is_open:
            # Market is open - today's candle is still forming, remove it
            if len(data) > 1:
                validated_data = data.iloc[:-1]  # Remove last (forming) candle
                reason = f"Market open - removed today's forming candle, using {validated_data.index[-1].date()}"
            else:
                validated_data = data  # Keep single candle if that's all we have
                reason = f"Market open but only one candle available - using {last_candle_date} with caution"
        else:
            # Market is closed - today's candle should be complete
            market_close_utc = cls.get_market_close_time_today(exchange, today)
            
            # Ensure both times are timezone-aware for comparison
            if current_utc.tzinfo is None:
                current_utc = pytz.UTC.localize(current_utc)
            
            if market_close_utc and current_utc >= market_close_utc:
                # We're past market close - today's candle should be closed
                validated_data = data
                reason = f"Market closed - using today's closed candle {last_candle_date}"
            else:
                # We're before market close but market shows as closed (weekend/holiday?)
                validated_data = data
                reason = f"Market closed (weekend/holiday?) - using {last_candle_date}"
        
        return validated_data, reason
    
    @classmethod
    def get_safe_signal_date(cls, data: pd.DataFrame, exchange: str) -> Tuple[date, str]:
        """
        Get the safe date to use for signal generation based on market hours
        
        Args:
            data: DataFrame with OHLCV data  
            exchange: Exchange name
            
        Returns:
            Tuple of (signal_date, reason_string)
        """
        validated_data, validation_reason = cls.validate_candle_data(data, exchange)
        
        if validated_data.empty:
            return date.today(), f"No data available - using today's date"
        
        # Get the date of the last candle we'll actually use for signals
        last_usable_candle_date = validated_data.index[-1].date() if hasattr(validated_data.index[-1], 'date') else validated_data.index[-1]
        
        # Always use today's date for signal generation (when we generate the signal)
        # But log which candle data we're basing it on
        signal_date = date.today()
        reason = f"Signal date: {signal_date} (based on {last_usable_candle_date} candle)"
        
        return signal_date, reason


# Convenience function for backward compatibility
def validate_candle_for_signals(data: pd.DataFrame, exchange: str) -> Tuple[pd.DataFrame, date, str]:
    """
    Validate candle data and get appropriate signal date
    
    Args:
        data: DataFrame with OHLCV data
        exchange: Exchange name  
        
    Returns:
        Tuple of (validated_data, signal_date, explanation)
    """
    validated_data, validation_reason = MarketHours.validate_candle_data(data, exchange)
    signal_date, date_reason = MarketHours.get_safe_signal_date(data, exchange)
    
    combined_reason = f"{validation_reason}; {date_reason}"
    
    return validated_data, signal_date, combined_reason