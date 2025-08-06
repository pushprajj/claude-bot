from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app import models, schemas
from app.models import MarketType

router = APIRouter()
# Force reload

@router.get("/", response_model=List[schemas.Ticker])
def get_tickers(
    market_type: Optional[str] = None,
    exchange: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    query = db.query(models.Ticker)
    
    if market_type:
        # Convert string to enum safely
        if market_type.lower() in ['crypto', 'stock']:
            market_type_enum = MarketType(market_type.lower())
            query = query.filter(models.Ticker.market_type == market_type_enum)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid market_type: {market_type}. Must be 'crypto' or 'stock'")
    if exchange:
        # Case-insensitive exchange filtering
        query = query.filter(func.lower(models.Ticker.exchange) == exchange.lower())
    if is_active is not None:
        query = query.filter(models.Ticker.is_active == is_active)
    
    tickers = query.order_by(func.lower(models.Ticker.symbol)).offset(skip).limit(limit).all()
    return tickers

@router.get("/{ticker_id}", response_model=schemas.Ticker)
def get_ticker(ticker_id: int, db: Session = Depends(get_db)):
    ticker = db.query(models.Ticker).filter(models.Ticker.id == ticker_id).first()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return ticker

@router.post("/", response_model=schemas.Ticker)
def create_ticker(ticker: schemas.TickerCreate, db: Session = Depends(get_db)):
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received ticker creation request: {ticker}")
    logger.info(f"Ticker dict: {ticker.dict()}")
    
    try:
        # Check if ticker already exists
        existing_ticker = db.query(models.Ticker).filter(
            models.Ticker.symbol == ticker.symbol,
            models.Ticker.market_type == ticker.market_type,
            models.Ticker.exchange == ticker.exchange
        ).first()
        
        if existing_ticker:
            raise HTTPException(
                status_code=400,
                detail="Ticker already exists for this market and exchange"
            )
        
        # Validate ticker data before creating
        ticker_data = ticker.dict()
        logger.info(f"Creating ticker with data: {ticker_data}")
        
        db_ticker = models.Ticker(**ticker_data)
        db.add(db_ticker)
        db.commit()
        db.refresh(db_ticker)
        
        logger.info(f"Successfully created ticker: {db_ticker.id}")
        return db_ticker
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error creating ticker: {str(e)}")
        logger.error(f"Ticker data: {ticker.dict()}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker data: {str(e)}"
        )

@router.put("/{ticker_id}", response_model=schemas.Ticker)
def update_ticker(
    ticker_id: int,
    ticker_update: schemas.TickerUpdate,
    db: Session = Depends(get_db)
):
    ticker = db.query(models.Ticker).filter(models.Ticker.id == ticker_id).first()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    
    update_data = ticker_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticker, field, value)
    
    db.commit()
    db.refresh(ticker)
    return ticker

@router.delete("/{ticker_id}")
def delete_ticker(ticker_id: int, db: Session = Depends(get_db)):
    ticker = db.query(models.Ticker).filter(models.Ticker.id == ticker_id).first()
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    
    db.delete(ticker)
    db.commit()
    return {"message": "Ticker deleted successfully"}

@router.post("/bulk", response_model=List[schemas.Ticker])
def create_bulk_tickers(tickers: List[schemas.TickerCreate], db: Session = Depends(get_db)):
    created_tickers = []
    for ticker_data in tickers:
        # Check if ticker already exists
        existing_ticker = db.query(models.Ticker).filter(
            models.Ticker.symbol == ticker_data.symbol,
            models.Ticker.market_type == ticker_data.market_type,
            models.Ticker.exchange == ticker_data.exchange
        ).first()
        
        if not existing_ticker:
            db_ticker = models.Ticker(**ticker_data.dict())
            db.add(db_ticker)
            created_tickers.append(db_ticker)
    
    db.commit()
    for ticker in created_tickers:
        db.refresh(ticker)
    
    return created_tickers

@router.post("/normalize-exchanges")
def normalize_exchange_names(db: Session = Depends(get_db)):
    """Normalize exchange names to title case for consistency"""
    
    # Update lowercase exchange names to title case
    exchange_mappings = {
        'binance': 'Binance',
        'bybit': 'Bybit', 
        'kraken': 'Kraken',
        'kucoin': 'KuCoin'
    }
    
    updated_count = 0
    for old_name, new_name in exchange_mappings.items():
        result = db.query(models.Ticker).filter(
            models.Ticker.exchange == old_name
        ).update(
            {models.Ticker.exchange: new_name}, 
            synchronize_session=False
        )
        updated_count += result
    
    db.commit()
    
    return {
        "message": f"Successfully normalized {updated_count} ticker exchange names",
        "mappings": exchange_mappings
    }