"""
Scheduler management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.services.market_scheduler import market_scheduler
from app.services.email_service import EmailService

router = APIRouter()
email_service = EmailService()

class EmailRecipientsUpdate(BaseModel):
    market: str
    recipients: List[str]

class TestMarketRequest(BaseModel):
    market: str

@router.get("/status")
def get_scheduler_status():
    """Get current scheduler status and next scheduled runs"""
    try:
        next_runs = market_scheduler.get_next_runs()
        
        return {
            "is_running": market_scheduler.is_running,
            "markets_configured": len(market_scheduler.market_schedules),
            "next_runs": next_runs,
            "current_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@router.post("/start")
def start_scheduler():
    """Start the market scheduler"""
    try:
        market_scheduler.start()
        return {
            "message": "Scheduler started successfully",
            "is_running": market_scheduler.is_running,
            "markets": list(market_scheduler.market_schedules.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/stop")
def stop_scheduler():
    """Stop the market scheduler"""
    try:
        market_scheduler.stop()
        return {
            "message": "Scheduler stopped successfully",
            "is_running": market_scheduler.is_running
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.post("/test-market")
async def test_market_signals(request: TestMarketRequest, db: Session = Depends(get_db)):
    """Test signal generation and email for a specific market"""
    try:
        result = await market_scheduler.test_market_signals(request.market)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.put("/email-recipients")
def update_email_recipients(request: EmailRecipientsUpdate):
    """Update email recipients for a specific market"""
    try:
        market_scheduler.update_email_recipients(request.market, request.recipients)
        return {
            "message": f"Email recipients updated for {request.market}",
            "market": request.market,
            "recipients": request.recipients
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update recipients: {str(e)}")

@router.get("/email-preview/{market}")
def preview_email_report(market: str, db: Session = Depends(get_db)):
    """Preview the email report for a specific market"""
    try:
        # Map market names to exchanges
        market_exchanges = {
            'US_MARKETS': ['NYSE', 'NASDAQ'],
            'ASX': ['ASX']
        }
        
        if market not in market_exchanges:
            raise HTTPException(status_code=400, detail=f"Unknown market: {market}")
        
        exchanges = market_exchanges[market]
        html_content = email_service.preview_daily_report(db, exchanges)
        
        return {
            "market": market,
            "exchanges": exchanges,
            "html_content": html_content,
            "preview_url": "data:text/html;charset=utf-8," + html_content.replace('\n', '').replace('"', '%22')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")

@router.get("/markets")
def get_configured_markets():
    """Get all configured markets and their settings"""
    try:
        markets_info = []
        
        for market_name, config in market_scheduler.market_schedules.items():
            markets_info.append({
                "name": market_name,
                "exchanges": config['exchanges'],
                "timezone": str(config['timezone']),
                "close_time": config['close_time'].strftime('%H:%M'),
                "signal_delay_minutes": config['signal_delay_minutes'],
                "email_recipients_count": len(config['email_recipients'])
            })
        
        return {
            "markets": markets_info,
            "total_markets": len(markets_info)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get markets info: {str(e)}")