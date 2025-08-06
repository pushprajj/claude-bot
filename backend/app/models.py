from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
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
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)  # Add index for performance
    is_processed = Column(Boolean, default=False, index=True)  # Add index for filtering
    
    ticker = relationship("Ticker", back_populates="signals")

class WatchlistItem(Base):
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"))
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