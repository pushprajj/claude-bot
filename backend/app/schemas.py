from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models import MarketType, SignalType, SignalStrength, TradeStatus

class TickerBase(BaseModel):
    symbol: str
    market_type: MarketType
    exchange: str
    name: Optional[str] = None
    is_active: bool = True

class TickerCreate(TickerBase):
    pass

class TickerUpdate(BaseModel):
    symbol: Optional[str] = None
    market_type: Optional[MarketType] = None
    exchange: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None

class Ticker(TickerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SignalBase(BaseModel):
    signal_type: SignalType
    signal_strength: SignalStrength
    price: float
    volume: Optional[float] = None
    signal_data: Optional[str] = None
    confidence_score: Optional[float] = None

class SignalCreate(SignalBase):
    ticker_id: int

class Signal(SignalBase):
    id: int
    ticker_id: int
    generated_at: datetime
    is_processed: bool
    ticker: Ticker
    
    class Config:
        from_attributes = True

class WatchlistItemBase(BaseModel):
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None

class WatchlistItemCreate(WatchlistItemBase):
    ticker_id: int
    signal_id: Optional[int] = None

class WatchlistItem(WatchlistItemBase):
    id: int
    ticker_id: int
    signal_id: Optional[int]
    added_at: datetime
    is_active: bool
    ticker: Ticker
    
    class Config:
        from_attributes = True

class TradeBase(BaseModel):
    entry_price: float
    quantity: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None

class TradeCreate(TradeBase):
    ticker_id: int
    signal_id: Optional[int] = None

class Trade(TradeBase):
    id: int
    ticker_id: int
    signal_id: Optional[int]
    current_price: Optional[float]
    status: TradeStatus
    pnl: float
    opened_at: datetime
    closed_at: Optional[datetime]
    ticker: Ticker
    
    class Config:
        from_attributes = True

class SignalGenerationRequest(BaseModel):
    market_type: Optional[MarketType] = None
    exchange: Optional[str] = None
    ticker_symbols: Optional[List[str]] = None
    signal_types: Optional[List[str]] = None