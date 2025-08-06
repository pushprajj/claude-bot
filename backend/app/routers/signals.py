from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import threading
from app.database import get_db
from app import models, schemas
from app.services.signal_generator import SignalGenerator
import json
import logging

router = APIRouter()
signal_generator = SignalGenerator()
logger = logging.getLogger(__name__)

# Global status tracking for signal generation
generation_status = {
    "is_running": False,
    "started_at": None,
    "completed_at": None,
    "ticker_count": 0,
    "signals_generated": 0,
    "status": "idle"  # idle, running, completed, error
}

@router.get("/", response_model=List[schemas.Signal])
def get_signals(
    ticker_id: Optional[int] = None,
    signal_type: Optional[str] = None,
    signal_strength: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_processed: Optional[bool] = None,
    market_type: Optional[str] = None,
    exchange: Optional[str] = None,
    skip: int = 0,
    limit: int = 25,  # Reduced default limit for better performance
    db: Session = Depends(get_db)
):
    # If filtering by market_type or exchange, we need to join with ticker table
    if market_type or exchange:
        from sqlalchemy import func
        query = db.query(models.Signal).join(models.Ticker, models.Signal.ticker_id == models.Ticker.id)
        
        if market_type:
            from app.models import MarketType
            if market_type.lower() in ['crypto', 'stock']:
                market_type_enum = MarketType(market_type.lower())
                query = query.filter(models.Ticker.market_type == market_type_enum)
        
        if exchange:
            query = query.filter(func.lower(models.Ticker.exchange) == exchange.lower())
    else:
        query = db.query(models.Signal)
    
    # Apply other filters
    if ticker_id:
        query = query.filter(models.Signal.ticker_id == ticker_id)
    if signal_type:
        query = query.filter(models.Signal.signal_type == signal_type)
    if signal_strength:
        query = query.filter(models.Signal.signal_strength == signal_strength)
    if start_date:
        query = query.filter(models.Signal.generated_at >= start_date)
    if end_date:
        query = query.filter(models.Signal.generated_at <= end_date)
    if is_processed is not None:
        query = query.filter(models.Signal.is_processed == is_processed)
    
    signals = query.order_by(models.Signal.generated_at.desc()).offset(skip).limit(limit).all()
    
    # Manually load ticker data for the signals to avoid JOIN performance issues
    ticker_ids = list(set(signal.ticker_id for signal in signals))
    tickers = db.query(models.Ticker).filter(models.Ticker.id.in_(ticker_ids)).all()
    ticker_map = {ticker.id: ticker for ticker in tickers}
    
    # Attach ticker data to signals
    for signal in signals:
        signal.ticker = ticker_map.get(signal.ticker_id)
    
    return signals

@router.get("/generation-status")
def get_generation_status():
    """Get the current status of signal generation"""
    try:
        # Return a safe copy with explicit JSON-serializable types
        return {
            "is_running": bool(generation_status.get("is_running", False)),
            "started_at": generation_status.get("started_at"),
            "completed_at": generation_status.get("completed_at"),
            "ticker_count": int(generation_status.get("ticker_count", 0)),
            "signals_generated": int(generation_status.get("signals_generated", 0)),
            "status": str(generation_status.get("status", "idle"))
        }
    except Exception as e:
        logger.error(f"Error getting generation status: {e}")
        # Return safe default status on error
        return {
            "is_running": False,
            "started_at": None,
            "completed_at": None,
            "ticker_count": 0,
            "signals_generated": 0,
            "status": "idle"
        }

@router.get("/{signal_id}", response_model=schemas.Signal)
def get_signal(signal_id: int, db: Session = Depends(get_db)):
    signal = db.query(models.Signal).filter(models.Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal

@router.post("/generate")
async def generate_signals(
    request: schemas.SignalGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate signals using proper yfinance implementation"""
    # Get tickers based on request parameters
    query = db.query(models.Ticker).filter(models.Ticker.is_active == True)
    
    if request.market_type:
        query = query.filter(models.Ticker.market_type == request.market_type)
    if request.exchange:
        # Case-insensitive exchange filtering
        from sqlalchemy import func
        query = query.filter(func.lower(models.Ticker.exchange) == request.exchange.lower())
    if request.ticker_symbols:
        query = query.filter(models.Ticker.symbol.in_(request.ticker_symbols))
    
    tickers = query.all()
    
    if not tickers:
        raise HTTPException(status_code=404, detail="No tickers found matching criteria")
    
    # Start signal generation in background using the proper method
    background_tasks.add_task(
        signal_generator.generate_signals_for_tickers,
        tickers,
        db
    )
    
    return {
        "message": f"Started signal generation for {len(tickers)} tickers",
        "ticker_count": len(tickers),
        "status": "started"
    }

@router.post("/{signal_id}/process")
def process_signal(signal_id: int, action: str, db: Session = Depends(get_db)):
    """Mark signal as processed and take action (watchlist, trade, skip)"""
    signal = db.query(models.Signal).filter(models.Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    if action == "watchlist":
        # Add to watchlist
        watchlist_item = models.WatchlistItem(
            ticker_id=signal.ticker_id,
            signal_id=signal.id,
            expires_at=datetime.utcnow() + timedelta(days=10)
        )
        db.add(watchlist_item)
    elif action == "trade":
        # Create a trade entry (placeholder - manual entry for now)
        return {"message": "Trade creation interface needed", "signal_id": signal_id}
    elif action == "skip":
        # Just mark as processed
        pass
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    signal.is_processed = True
    db.commit()
    
    return {"message": f"Signal processed with action: {action}", "signal_id": signal_id}

@router.post("/generate-real")
async def generate_real_signals(
    request: schemas.SignalGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate real signals using actual market data (limited test implementation)"""
    # Get limited set of tickers for testing real data
    query = db.query(models.Ticker).filter(models.Ticker.is_active == True)
    
    if request.market_type:
        query = query.filter(models.Ticker.market_type == request.market_type)
    if request.exchange:
        from sqlalchemy import func
        query = query.filter(func.lower(models.Ticker.exchange) == request.exchange.lower())
    if request.ticker_symbols:
        query = query.filter(models.Ticker.symbol.in_(request.ticker_symbols))
    
    # Limit to maximum 5 tickers for real data testing
    tickers = query.limit(5).all()
    
    if not tickers:
        raise HTTPException(status_code=404, detail="No tickers found matching criteria")
    
    # Generate real signals using actual data
    try:
        await signal_generator.generate_signals_for_tickers(tickers, db)
        return {
            "message": f"Generated real signals for {len(tickers)} tickers using actual market data",
            "ticker_count": len(tickers),
            "status": "completed",
            "tickers": [{"symbol": t.symbol, "exchange": t.exchange, "market_type": t.market_type.value} for t in tickers]
        }
    except Exception as e:
        return {
            "message": f"Error generating real signals: {str(e)}",
            "ticker_count": len(tickers),
            "status": "error",
            "error": str(e)
        }

@router.post("/generate-confirmed-buy")
async def generate_confirmed_buy_signals(
    request: schemas.SignalGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate confirmed buy signals for all tickers in the selected market/exchange"""
    # Get tickers based on request parameters
    query = db.query(models.Ticker).filter(models.Ticker.is_active == True)
    
    if request.market_type:
        query = query.filter(models.Ticker.market_type == request.market_type)
    if request.exchange:
        from sqlalchemy import func
        query = query.filter(func.lower(models.Ticker.exchange) == request.exchange.lower())
    if request.ticker_symbols:
        query = query.filter(models.Ticker.symbol.in_(request.ticker_symbols))
    
    # Process all tickers in the selected market/exchange
    tickers = query.order_by(models.Ticker.symbol).all()
    
    if not tickers:
        raise HTTPException(status_code=404, detail="No tickers found matching criteria")
    
    # Create background task wrapper that uses its own DB session
    async def background_signal_generation():
        """Background task wrapper with its own database session"""
        from app.database import SessionLocal
        db_session = SessionLocal()
        
        # Update status to running
        generation_status.update({
            "is_running": True,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "ticker_count": len(tickers),
            "signals_generated": 0,
            "status": "running"
        })
        
        try:
            print(f"Starting background signal generation for {len(tickers)} tickers...")
            
            # Clear existing signals for these tickers to ensure fresh results
            ticker_ids = [t.id for t in tickers]
            deleted_count = db_session.query(models.Signal).filter(
                models.Signal.ticker_id.in_(ticker_ids)
            ).delete(synchronize_session=False)
            db_session.commit()
            print(f"Cleared {deleted_count} existing signals for selected tickers")
            
            # Add progress tracking for web interface
            print(f"Starting confirmed buy signal generation for {len(tickers)} ASX tickers...")
            print(f"Expected processing time: ~{len(tickers) * 12 / 60:.1f} minutes with aggressive rate limiting")
            
            await signal_generator.generate_signals_for_tickers(
                tickers,
                db_session,
                True,  # focus_confirmed_buy
                15     # batch_size - reduced to avoid rate limiting
            )
            
            # Final commit to ensure all changes are saved
            db_session.commit()
            print(f"Completed background signal generation for {len(tickers)} tickers")
            print(f"Background task finished successfully - server ready for new requests")
            
            # Count generated signals
            signal_count = db_session.query(models.Signal).filter(
                models.Signal.ticker_id.in_(ticker_ids)
            ).count()
            
            # Update status to completed
            generation_status.update({
                "is_running": False,
                "completed_at": datetime.utcnow().isoformat(),
                "signals_generated": signal_count,
                "status": "completed"
            })
            
        except Exception as e:
            print(f"Background signal generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            db_session.rollback()
            
            # Update status to error
            generation_status.update({
                "is_running": False,
                "completed_at": datetime.utcnow().isoformat(),
                "status": "error"
            })
        finally:
            try:
                db_session.close()
                print("Database session closed successfully")
            except Exception as e:
                print(f"Error closing database session: {e}")
            print("Background task cleanup completed")
    
    # Start confirmed buy signal generation in background
    background_tasks.add_task(background_signal_generation)
    
    return {
        "message": f"Started confirmed buy signal generation for {len(tickers)} tickers",
        "ticker_count": len(tickers),
        "status": "processing",
        "signal_type": "confirmed_buy",
        "tickers": [{"symbol": t.symbol, "exchange": t.exchange, "market_type": t.market_type.value} for t in tickers],
        "estimated_time": f"~{len(tickers) // 10 + 1} minutes"
    }

@router.post("/test-subprocess")
async def test_subprocess_yfinance():
    """Test subprocess yfinance call to avoid web server context issues"""
    try:
        import subprocess
        import tempfile
        import pickle
        import os
        
        test_symbols = ['CBA.AX', 'BHP.AX', 'WBC.AX']
        logger.info(f"Testing subprocess yfinance call with: {test_symbols}")
        
        # Create a temporary script
        script_content = f'''
import yfinance as yf
import pickle
import sys

symbols = {test_symbols}
print(f"Fetching {{len(symbols)}} symbols: {{symbols}}")

try:
    data = yf.download(
        symbols,
        period="60d",
        group_by='ticker',
        auto_adjust=False,
        threads=True,
        progress=False
    )
    
    print(f"Downloaded data shape: {{data.shape}}")
    print(f"Data empty: {{data.empty}}")
    
    # Save to pickle file
    with open(sys.argv[1], 'wb') as f:
        pickle.dump(data, f)
    print("Data saved successfully")
    
except Exception as e:
    print(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
        
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
            script_file.write(script_content)
            script_path = script_file.name
        
        # Create temporary file for data
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as data_file:
            data_path = data_file.name
        
        try:
            # Run the script in subprocess
            result = subprocess.run([
                r"C:\Users\pushp\AppData\Local\Programs\Python\Python310\python.exe",
                script_path,
                data_path
            ], capture_output=True, text=True, timeout=60)
            
            logger.info(f"Subprocess stdout: {result.stdout}")
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Subprocess failed with return code: {result.returncode}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            
            # Load the data
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
            
            response = {
                "success": True,
                "method": "subprocess",
                "symbols": test_symbols,
                "data_type": str(type(data)),
                "empty": data.empty if hasattr(data, 'empty') else False,
                "stdout": result.stdout
            }
            
            if not data.empty and hasattr(data, 'columns'):
                if hasattr(data.columns, 'levels'):
                    response["columns_levels"] = [list(level) for level in data.columns.levels]
                else:
                    response["columns"] = list(data.columns)
                
                response["shape"] = data.shape
                
                # Try to process one symbol
                if hasattr(data.columns, 'levels') and 'CBA.AX' in data.columns.levels[0]:
                    cba_data = data['CBA.AX']
                    response["cba_sample"] = {
                        "rows": len(cba_data),
                        "columns": list(cba_data.columns),
                        "latest_close": float(cba_data['Close'].iloc[-1]) if 'Close' in cba_data.columns else None
                    }
            
            return response
            
        finally:
            # Clean up temporary files
            if os.path.exists(script_path):
                os.unlink(script_path)
            if os.path.exists(data_path):
                os.unlink(data_path)
        
    except Exception as e:
        logger.error(f"Subprocess yfinance test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/statistics/summary")
def get_signal_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get signal generation statistics"""
    query = db.query(models.Signal)
    
    if start_date:
        query = query.filter(models.Signal.generated_at >= start_date)
    if end_date:
        query = query.filter(models.Signal.generated_at <= end_date)
    
    total_signals = query.count()
    buy_signals = query.filter(models.Signal.signal_type == "buy").count()
    sell_signals = query.filter(models.Signal.signal_type == "sell").count()
    processed_signals = query.filter(models.Signal.is_processed == True).count()
    
    return {
        "total_signals": total_signals,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "processed_signals": processed_signals,
        "pending_signals": total_signals - processed_signals
    }