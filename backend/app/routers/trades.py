from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Trade])
def get_trades(
    status: Optional[str] = None,
    ticker_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Trade).join(models.Ticker)
    
    if status:
        query = query.filter(models.Trade.status == status)
    if ticker_id:
        query = query.filter(models.Trade.ticker_id == ticker_id)
    
    trades = query.order_by(models.Trade.opened_at.desc()).offset(skip).limit(limit).all()
    return trades

@router.get("/{trade_id}", response_model=schemas.Trade)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(models.Trade).filter(models.Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

@router.post("/", response_model=schemas.Trade)
def create_trade(trade: schemas.TradeCreate, db: Session = Depends(get_db)):
    # Check if ticker exists
    ticker = db.query(models.Ticker).filter(models.Ticker.id == trade.ticker_id).first()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    
    db_trade = models.Trade(
        **trade.dict(),
        current_price=trade.entry_price
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

@router.put("/{trade_id}/update-price")
def update_trade_price(
    trade_id: int,
    current_price: float,
    db: Session = Depends(get_db)
):
    """Update current price and calculate P&L"""
    trade = db.query(models.Trade).filter(models.Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    trade.current_price = current_price
    
    # Calculate P&L
    price_change = current_price - trade.entry_price
    trade.pnl = price_change * trade.quantity
    
    db.commit()
    db.refresh(trade)
    return trade

@router.put("/{trade_id}/close")
def close_trade(
    trade_id: int,
    closing_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Close a trade"""
    trade = db.query(models.Trade).filter(models.Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status != models.TradeStatus.OPEN:
        raise HTTPException(status_code=400, detail="Trade is not open")
    
    if closing_price:
        trade.current_price = closing_price
        price_change = closing_price - trade.entry_price
        trade.pnl = price_change * trade.quantity
    
    trade.status = models.TradeStatus.CLOSED
    trade.closed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(trade)
    return trade

@router.put("/{trade_id}")
def update_trade(
    trade_id: int,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update trade parameters"""
    trade = db.query(models.Trade).filter(models.Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if stop_loss is not None:
        trade.stop_loss = stop_loss
    if take_profit is not None:
        trade.take_profit = take_profit
    if notes is not None:
        trade.notes = notes
    
    db.commit()
    db.refresh(trade)
    return trade

@router.get("/statistics/summary")
def get_trade_statistics(db: Session = Depends(get_db)):
    """Get trade statistics"""
    total_trades = db.query(models.Trade).count()
    open_trades = db.query(models.Trade).filter(models.Trade.status == models.TradeStatus.OPEN).count()
    closed_trades = db.query(models.Trade).filter(models.Trade.status == models.TradeStatus.CLOSED).count()
    
    # Calculate total P&L for closed trades
    closed_trades_pnl = db.query(models.Trade).filter(
        models.Trade.status == models.TradeStatus.CLOSED
    ).with_entities(models.Trade.pnl).all()
    
    total_pnl = sum([trade.pnl for trade in closed_trades_pnl if trade.pnl])
    
    return {
        "total_trades": total_trades,
        "open_trades": open_trades,
        "closed_trades": closed_trades,
        "total_pnl": total_pnl
    }