"""
Market Schedule and Signal Generation Scheduler
Handles automated signal generation 10 minutes after market close for different exchanges.
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime, time as dt_time, timezone, timedelta
from typing import List, Dict
import pytz
from threading import Thread
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Ticker, MarketType
from app.services.signal_generator import SignalGenerator
from app.services.email_service import EmailService
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class MarketScheduler:
    """Handles scheduling of signal generation and email delivery based on market close times"""
    
    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.email_service = EmailService()
        self.is_running = False
        self.scheduler_thread = None
        
        # Market close times (in their local timezone)
        self.market_schedules = {
            'US_MARKETS': {
                'exchanges': ['NYSE', 'NASDAQ'],
                'timezone': pytz.timezone('US/Eastern'),
                'close_time': dt_time(16, 0),  # 4:00 PM ET market close
                'signal_delay_minutes': 10,  # 10 minutes delay = 4:10 PM ET
                'email_recipients': self._get_email_recipients('US_MARKETS')
            },
            'ASX': {
                'exchanges': ['ASX'],
                'timezone': pytz.timezone('Australia/Sydney'),
                'close_time': dt_time(16, 0),  # 4:00 PM AEST market close
                'signal_delay_minutes': 10,  # 10 minutes delay = 4:10 PM AEST
                'email_recipients': self._get_email_recipients('ASX')
            }
        }
        
        self._setup_schedules()
    
    def _get_email_recipients(self, market: str) -> List[str]:
        """Get email recipients from environment variables"""
        # You can configure different recipient lists per market
        env_key = f"EMAIL_RECIPIENTS_{market}"
        recipients = os.getenv(env_key, os.getenv("EMAIL_RECIPIENTS", ""))
        
        if recipients:
            return [email.strip() for email in recipients.split(',') if email.strip()]
        return []
    
    def _setup_schedules(self):
        """Setup scheduled tasks for each market"""
        for market_name, config in self.market_schedules.items():
            # Calculate signal generation time (market close + delay)
            close_time = config['close_time']
            delay_minutes = config['signal_delay_minutes']
            
            signal_time = (datetime.combine(datetime.today(), close_time) + 
                          timedelta(minutes=delay_minutes)).time()
            
            # Schedule signal generation and email
            schedule_time = signal_time.strftime('%H:%M')
            
            logger.info(f"Scheduling {market_name} signal generation at {schedule_time} local time")
            
            # Create a closure to capture the current values
            def create_market_job(market_name=market_name, config=config):
                def job():
                    asyncio.run(self._process_market_signals(market_name, config))
                return job
            
            schedule.every().day.at(schedule_time).do(create_market_job())
    
    async def _process_market_signals(self, market_name: str, config: Dict):
        """Process signal generation and email for a specific market"""
        try:
            logger.info(f"Starting signal generation for {market_name}")
            
            # Get database session
            db = SessionLocal()
            
            try:
                # Get tickers for this market's exchanges
                tickers = db.query(Ticker).filter(
                    Ticker.is_active == True,
                    Ticker.market_type == MarketType.STOCK,
                    Ticker.exchange.in_(config['exchanges'])
                ).all()
                
                if not tickers:
                    logger.warning(f"No active tickers found for {market_name}")
                    return
                
                logger.info(f"Generating signals for {len(tickers)} tickers in {market_name}")
                
                # Generate signals
                await self.signal_generator.generate_signals_for_tickers(
                    tickers, 
                    db, 
                    focus_confirmed_buy=True,  # Only generate confirmed buy signals
                    batch_size=20
                )
                
                # Send email report
                if config['email_recipients']:
                    logger.info(f"Sending email report to {len(config['email_recipients'])} recipients")
                    
                    success = self.email_service.send_market_close_report(
                        config['email_recipients'],
                        db,
                        config['exchanges']
                    )
                    
                    if success:
                        logger.info(f"Email report sent successfully for {market_name}")
                    else:
                        logger.error(f"Failed to send email report for {market_name}")
                else:
                    logger.warning(f"No email recipients configured for {market_name}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing market signals for {market_name}: {str(e)}")
    
    def start(self):
        """Start the scheduler in a separate thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        
        def run_scheduler():
            logger.info("Market scheduler started")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            logger.info("Market scheduler stopped")
        
        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Scheduler started with {len(self.market_schedules)} market schedules")
        self._log_scheduled_jobs()
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Market scheduler stopped")
    
    def _log_scheduled_jobs(self):
        """Log all scheduled jobs for debugging"""
        logger.info("Scheduled jobs:")
        for job in schedule.jobs:
            logger.info(f"  - {job}")
    
    def get_next_runs(self) -> List[Dict]:
        """Get information about next scheduled runs"""
        next_runs = []
        
        for market_name, config in self.market_schedules.items():
            # Find the scheduled job for this market
            market_jobs = [job for job in schedule.jobs 
                          if market_name.lower() in str(job.job_func).lower()]
            
            if market_jobs:
                job = market_jobs[0]
                next_run = job.next_run
                
                next_runs.append({
                    'market': market_name,
                    'exchanges': config['exchanges'],
                    'next_run': next_run,
                    'recipients': len(config['email_recipients'])
                })
        
        return next_runs
    
    async def test_market_signals(self, market_name: str) -> Dict:
        """Test signal generation for a specific market (for testing)"""
        if market_name not in self.market_schedules:
            raise ValueError(f"Unknown market: {market_name}")
        
        config = self.market_schedules[market_name]
        
        try:
            await self._process_market_signals(market_name, config)
            return {
                'success': True,
                'message': f"Test completed for {market_name}",
                'exchanges': config['exchanges']
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Test failed for {market_name}: {str(e)}",
                'exchanges': config['exchanges']
            }
    
    def update_email_recipients(self, market_name: str, recipients: List[str]):
        """Update email recipients for a specific market"""
        if market_name in self.market_schedules:
            self.market_schedules[market_name]['email_recipients'] = recipients
            logger.info(f"Updated email recipients for {market_name}: {recipients}")
        else:
            raise ValueError(f"Unknown market: {market_name}")

# Global scheduler instance
market_scheduler = MarketScheduler()