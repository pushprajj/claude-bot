from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas
import yfinance as yf
import asyncio
import json
from sqlalchemy import func

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

@router.get("/check-history")
def get_watchlist_signal_check_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get history of watchlist signal checks"""
    
    checks = db.query(models.WatchlistSignalCheck)\
        .order_by(models.WatchlistSignalCheck.run_timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return {"checks": checks}

@router.get("/check-history/{check_id}/results")
def get_watchlist_signal_check_results(
    check_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed results for a specific signal check run"""
    
    check = db.query(models.WatchlistSignalCheck)\
        .filter(models.WatchlistSignalCheck.id == check_id)\
        .first()
    
    if not check:
        raise HTTPException(status_code=404, detail="Signal check not found")
    
    results = db.query(models.WatchlistSignalResult)\
        .join(models.WatchlistItem)\
        .join(models.Ticker)\
        .filter(models.WatchlistSignalResult.check_id == check_id)\
        .all()
    
    return {
        "check": check,
        "results": results
    }

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

@router.post("/check-signals")
async def check_watchlist_signals(
    request: schemas.WatchlistSignalCheckRequest,
    db: Session = Depends(get_db)
):
    """Check watchlist items for triggered conditions"""
    
    # Create a record for this check run
    filters_applied = json.dumps({
        "market_type": request.market_type.value if request.market_type else None,
        "exchange": request.exchange,
        "base_asset": request.base_asset
    })
    
    # Get watchlist items based on filters
    query = db.query(models.WatchlistItem).join(models.Ticker).filter(
        models.WatchlistItem.is_active == True
    )
    
    if request.market_type:
        query = query.filter(models.Ticker.market_type == request.market_type)
    if request.exchange:
        query = query.filter(func.lower(models.Ticker.exchange) == request.exchange.lower())
    
    watchlist_items = query.all()
    
    if not watchlist_items:
        # Create empty check record
        check_record = models.WatchlistSignalCheck(
            total_checked=0,
            total_triggered=0,
            filters_applied=filters_applied
        )
        db.add(check_record)
        db.commit()
        db.refresh(check_record)
        
        return {
            "message": "No active watchlist items found for the selected criteria",
            "total_checked": 0,
            "total_triggered": 0,
            "check_id": check_record.id,
            "results": []
        }
    
    results = []
    db_results = []
    
    for item in watchlist_items:
        try:
            # Get current price data using yfinance
            ticker_symbol = item.ticker.symbol
            
            # Adjust symbol for different exchanges
            if item.ticker.exchange.upper() == 'ASX':
                ticker_symbol = f"{ticker_symbol}.AX"
            elif item.ticker.exchange.upper() in ['NYSE', 'NASDAQ']:
                # Keep symbol as is for US markets
                pass
                
            # Fetch recent price data (last 2 days to ensure we have latest close)
            ticker_data = yf.Ticker(ticker_symbol)
            hist_data = ticker_data.history(period="2d", interval="1d")
            
            if hist_data.empty:
                continue
                
            # Get the most recent candle
            latest_candle = hist_data.iloc[-1]
            open_price = latest_candle['Open']
            close_price = latest_candle['Close']
            current_price = close_price  # Use close as current price
            
            # Check conditions
            triggered_conditions = []
            
            # Check support level (both open and close should be below)
            if item.support_price and open_price < item.support_price and close_price < item.support_price:
                triggered_conditions.append({
                    "condition": "Closed below support",
                    "condition_type": models.WatchlistSignalCondition.SUPPORT_TRIGGERED,
                    "trigger_price": item.support_price,
                    "current_price": current_price,
                    "description": f"Both open (${open_price:.2f}) and close (${close_price:.2f}) below support level"
                })
            
            # Check resistance level (both open and close should be above)
            if item.resistance_price and open_price > item.resistance_price and close_price > item.resistance_price:
                triggered_conditions.append({
                    "condition": "Closed above resistance", 
                    "condition_type": models.WatchlistSignalCondition.RESISTANCE_TRIGGERED,
                    "trigger_price": item.resistance_price,
                    "current_price": current_price,
                    "description": f"Both open (${open_price:.2f}) and close (${close_price:.2f}) above resistance level"
                })
            
            # Check target range (current price within min-max range)
            if item.target_min and item.target_max and item.target_min <= current_price <= item.target_max:
                triggered_conditions.append({
                    "condition": "Reached target range",
                    "condition_type": models.WatchlistSignalCondition.TARGET_RANGE_REACHED,
                    "trigger_price": f"{item.target_min} - {item.target_max}",
                    "current_price": current_price,
                    "description": f"Price ${current_price:.2f} within target range ${item.target_min:.2f} - ${item.target_max:.2f}"
                })
            elif item.target_min and not item.target_max and current_price >= item.target_min:
                triggered_conditions.append({
                    "condition": "Reached target minimum",
                    "condition_type": models.WatchlistSignalCondition.TARGET_MIN_REACHED,
                    "trigger_price": item.target_min,
                    "current_price": current_price,
                    "description": f"Price ${current_price:.2f} reached target minimum ${item.target_min:.2f}"
                })
            elif item.target_max and not item.target_min and current_price <= item.target_max:
                triggered_conditions.append({
                    "condition": "Reached target maximum", 
                    "condition_type": models.WatchlistSignalCondition.TARGET_MAX_REACHED,
                    "trigger_price": item.target_max,
                    "current_price": current_price,
                    "description": f"Price ${current_price:.2f} reached target maximum ${item.target_max:.2f}"
                })
            
            # Add results for each triggered condition and save to database
            for condition in triggered_conditions:
                # Create database record for this result
                db_result = models.WatchlistSignalResult(
                    watchlist_item_id=item.id,
                    condition_triggered=condition["condition_type"],
                    trigger_price=float(condition["trigger_price"]) if isinstance(condition["trigger_price"], (int, float)) else 0,
                    current_price=condition["current_price"],
                    open_price=open_price,
                    close_price=close_price,
                    description=condition["description"],
                    market_data_timestamp=datetime.utcnow()
                )
                db_results.append(db_result)
                
                # Update watchlist item with trigger information
                trigger_note = f"TRIGGERED: {condition['description']} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                if item.notes:
                    item.notes = f"{item.notes}\n{trigger_note}"
                else:
                    item.notes = trigger_note
                
                # For support/resistance triggers, consider deactivating the item
                # as the condition has been met
                if condition["condition_type"] in [
                    models.WatchlistSignalCondition.SUPPORT_TRIGGERED,
                    models.WatchlistSignalCondition.RESISTANCE_TRIGGERED
                ]:
                    # Mark as inactive since the breakout/breakdown has occurred
                    item.is_active = False
                
                # Add to response results
                results.append({
                    "watchlist_item_id": item.id,
                    "ticker_symbol": item.ticker.symbol,
                    "ticker_name": item.ticker.name or item.ticker.symbol,
                    "exchange": item.ticker.exchange,
                    "condition": condition["condition"],
                    "trigger_price": condition["trigger_price"],
                    "current_price": condition["current_price"],
                    "description": condition["description"],
                    "signal_price": item.signal_price,
                    "signal_date": item.signal_date,
                    "watchlist_item": item
                })
                
        except Exception as e:
            print(f"Error checking {item.ticker.symbol}: {e}")
            continue
    
    # Create the main check record
    check_record = models.WatchlistSignalCheck(
        total_checked=len(watchlist_items),
        total_triggered=len(results),
        filters_applied=filters_applied
    )
    db.add(check_record)
    db.flush()  # Get the ID without committing
    
    # Associate results with this check
    for db_result in db_results:
        db_result.check_id = check_record.id
        db.add(db_result)
    
    # Commit all changes
    db.commit()
    db.refresh(check_record)
    
    return {
        "message": f"Checked {len(watchlist_items)} watchlist items, found {len(results)} triggered conditions",
        "total_checked": len(watchlist_items),
        "total_triggered": len(results),
        "check_id": check_record.id,
        "results": results
    }