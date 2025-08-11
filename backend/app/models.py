from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class MarketType(enum.Enum):
    CRYPTO = "crypto"
    STOCK = "stock"

class SignalType(enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class SignalStrength(enum.Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"

class TradeStatus(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class Ticker(Base):
    __tablename__ = "tickers"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    market_type = Column(Enum(MarketType), nullable=False)
    exchange = Column(String(50), nullable=False)
    name = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    signals = relationship("Signal", back_populates="ticker")
    watchlist_items = relationship("WatchlistItem", back_populates="ticker")
    trades = relationship("Trade", back_populates="ticker")

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    signal_type = Column(Enum(SignalType), nullable=False)
    signal_strength = Column(Enum(SignalStrength), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    signal_data = Column(Text)  # JSON data for signal details
    confidence_score = Column(Float)
    signal_date = Column(Date, nullable=True, index=True)  # Date of last candle used in calculation
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)  # Add index for performance
    is_processed = Column(Boolean, default=False, index=True)  # Add index for filtering
    
    ticker = relationship("Ticker", back_populates="signals")

class WatchlistItem(Base):
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"))
    target_price = Column(Float, nullable=True)  # Keep for backward compatibility
    support_price = Column(Float, nullable=True)  # Support level
    resistance_price = Column(Float, nullable=True)  # Resistance level
    target_min = Column(Float, nullable=True)  # Target range minimum (for retracement)
    target_max = Column(Float, nullable=True)  # Target range maximum (for retracement)
    signal_price = Column(Float, nullable=True)  # Original signal price for reference
    signal_type = Column(String(10), nullable=True)  # Signal type for reference
    signal_date = Column(Date, nullable=True)  # Signal date for reference
    added_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    ticker = relationship("Ticker", back_populates="watchlist_items")
    signal = relationship("Signal")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"))
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    quantity = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    pnl = Column(Float, default=0.0)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    notes = Column(Text)
    
    ticker = relationship("Ticker", back_populates="trades")
    signal = relationship("Signal")

class PriceData(Base):
    __tablename__ = "price_data"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    ticker = relationship("Ticker")

class WatchlistSignalCondition(enum.Enum):
    SUPPORT_TRIGGERED = "support_triggered"
    RESISTANCE_TRIGGERED = "resistance_triggered"
    TARGET_RANGE_REACHED = "target_range_reached"
    TARGET_MIN_REACHED = "target_min_reached"
    TARGET_MAX_REACHED = "target_max_reached"

class WatchlistSignalCheck(Base):
    __tablename__ = "watchlist_signal_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    run_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_checked = Column(Integer, nullable=False)
    total_triggered = Column(Integer, nullable=False)
    filters_applied = Column(Text)  # JSON string of applied filters
    created_at = Column(DateTime, default=datetime.utcnow)

class WatchlistSignalResult(Base):
    __tablename__ = "watchlist_signal_results"
    
    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(Integer, ForeignKey("watchlist_signal_checks.id"), nullable=False)
    watchlist_item_id = Column(Integer, ForeignKey("watchlist.id"), nullable=False)
    condition_triggered = Column(Enum(WatchlistSignalCondition), nullable=False)
    trigger_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    market_data_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Mark if action was taken on this result
    action_taken = Column(String(20))  # 'trade', 'watchlist_updated', 'ignored'
    action_timestamp = Column(DateTime)
    action_notes = Column(Text)
    
    check = relationship("WatchlistSignalCheck")
    watchlist_item = relationship("WatchlistItem")