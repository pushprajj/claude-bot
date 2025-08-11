from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from app.models import MarketType, SignalType, SignalStrength, TradeStatus, WatchlistSignalCondition

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
    signal_date: Optional[date] = None

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
    target_price: Optional[float] = None  # Keep for backward compatibility
    support_price: Optional[float] = None
    resistance_price: Optional[float] = None
    target_min: Optional[float] = None  # Target range minimum (for retracement)
    target_max: Optional[float] = None  # Target range maximum (for retracement)
    signal_price: Optional[float] = None
    signal_type: Optional[str] = None
    signal_date: Optional[date] = None
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

class WatchlistSignalCheckRequest(BaseModel):
    market_type: Optional[MarketType] = None
    exchange: Optional[str] = None
    base_asset: Optional[str] = None  # For future crypto implementation

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

class HistoricalSignalRequest(BaseModel):
    market_type: Optional[MarketType] = None
    exchange: Optional[str] = None
    ticker_symbol: Optional[str] = None
    signal_type: Optional[SignalType] = None
    signal_strength: Optional[SignalStrength] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_asset: Optional[str] = None  # For future crypto relative performance
    is_processed: Optional[bool] = None
    skip: int = 0
    limit: int = 25

class PaginatedHistoricalSignalsResponse(BaseModel):
    signals: List[Signal]
    total: int
    page: int
    per_page: int
    total_pages: int

class WatchlistSignalCheckBase(BaseModel):
    total_checked: int
    total_triggered: int
    filters_applied: Optional[str] = None

class WatchlistSignalCheck(WatchlistSignalCheckBase):
    id: int
    run_timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class WatchlistSignalResultBase(BaseModel):
    condition_triggered: WatchlistSignalCondition
    trigger_price: float
    current_price: float
    open_price: float
    close_price: float
    description: str
    market_data_timestamp: datetime
    action_taken: Optional[str] = None
    action_timestamp: Optional[datetime] = None
    action_notes: Optional[str] = None

class WatchlistSignalResultCreate(WatchlistSignalResultBase):
    check_id: int
    watchlist_item_id: int

class WatchlistSignalResult(WatchlistSignalResultBase):
    id: int
    check_id: int
    watchlist_item_id: int
    created_at: datetime
    watchlist_item: WatchlistItem
    
    class Config:
        from_attributes = True

class WatchlistSignalCheckResponse(BaseModel):
    message: str
    total_checked: int
    total_triggered: int
    check_id: int  # ID of the database record for this check

class CryptoSignalGenerationRequest(BaseModel):
    market: str = "crypto"
    exchange: str = "binance"
    base_asset: str = "ETH"
    signal_type: str = "confirmed_buy"
    limit_pairs: Optional[int] = None