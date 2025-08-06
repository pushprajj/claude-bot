from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.email_service import EmailService

router = APIRouter()
email_service = EmailService()

@router.post("/send-daily-report")
async def send_daily_report(
    to_email: str,
    db: Session = Depends(get_db)
):
    """Send daily signals report to email"""
    success = email_service.send_daily_report(to_email, db)
    
    if success:
        return {"message": "Daily report sent successfully", "email": to_email}
    else:
        return {"message": "Failed to send daily report", "email": to_email}

@router.post("/send-portfolio-summary")
async def send_portfolio_summary(
    to_email: str,
    db: Session = Depends(get_db)
):
    """Send portfolio summary to email"""
    success = email_service.send_portfolio_summary(to_email, db)
    
    if success:
        return {"message": "Portfolio summary sent successfully", "email": to_email}
    else:
        return {"message": "Failed to send portfolio summary", "email": to_email}

@router.get("/preview-daily-report")
async def preview_daily_report(db: Session = Depends(get_db)):
    """Preview daily report HTML (for testing)"""
    html_content = email_service.generate_daily_signals_report(db)
    return {"html_content": html_content}

@router.get("/preview-portfolio-summary")
async def preview_portfolio_summary(db: Session = Depends(get_db)):
    """Preview portfolio summary HTML (for testing)"""
    html_content = email_service.generate_portfolio_summary(db)
    return {"html_content": html_content}