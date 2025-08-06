from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.WatchlistItem])
def get_watchlist(
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.WatchlistItem).join(models.Ticker)
    
    if is_active is not None:
        query = query.filter(models.WatchlistItem.is_active == is_active)
    
    watchlist_items = query.order_by(models.WatchlistItem.added_at.desc()).offset(skip).limit(limit).all()
    return watchlist_items

@router.get("/{item_id}", response_model=schemas.WatchlistItem)
def get_watchlist_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.WatchlistItem).filter(models.WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return item

@router.post("/", response_model=schemas.WatchlistItem)
def add_to_watchlist(item: schemas.WatchlistItemCreate, db: Session = Depends(get_db)):
    # Check if ticker exists
    ticker = db.query(models.Ticker).filter(models.Ticker.id == item.ticker_id).first()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    
    # Check if item already exists in active watchlist
    existing_item = db.query(models.WatchlistItem).filter(
        models.WatchlistItem.ticker_id == item.ticker_id,
        models.WatchlistItem.is_active == True
    ).first()
    
    if existing_item:
        raise HTTPException(status_code=400, detail="Ticker already in watchlist")
    
    db_item = models.WatchlistItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{item_id}")
def update_watchlist_item(
    item_id: int,
    notes: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    item = db.query(models.WatchlistItem).filter(models.WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    if notes is not None:
        item.notes = notes
    if expires_at is not None:
        item.expires_at = expires_at
    if is_active is not None:
        item.is_active = is_active
    
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.WatchlistItem).filter(models.WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Item removed from watchlist"}

@router.post("/{item_id}/promote-to-trade")
def promote_to_trade(
    item_id: int,
    entry_price: float,
    quantity: float,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Promote watchlist item to an active trade"""
    item = db.query(models.WatchlistItem).filter(models.WatchlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    # Create trade
    trade = models.Trade(
        ticker_id=item.ticker_id,
        signal_id=item.signal_id,
        entry_price=entry_price,
        current_price=entry_price,
        quantity=quantity,
        stop_loss=stop_loss,
        take_profit=take_profit
    )
    
    db.add(trade)
    
    # Deactivate watchlist item
    item.is_active = False
    
    db.commit()
    db.refresh(trade)
    
    return {"message": "Promoted to trade", "trade_id": trade.id}