import smtplib
import ssl
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import logging

from app.models import Signal, Ticker, Trade, WatchlistItem, SignalType

load_dotenv()
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.from_email = self.email_username
        
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send HTML email"""
        try:
            message = MimeMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            html_part = MimeText(html_content, "html")
            message.attach(html_part)
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_username, self.email_password)
                server.sendmail(self.from_email, to_email, message.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def generate_market_signals_report(self, db: Session, exchanges: List[str], date: datetime = None) -> str:
        """Generate signals report for specific exchanges (markets)"""
        if not date:
            date = datetime.utcnow().date()
        
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        # Get signals from today for specified exchanges
        signals = db.query(Signal).join(Ticker).filter(
            Signal.generated_at >= start_date,
            Signal.generated_at < end_date,
            Ticker.exchange.in_(exchanges)
        ).order_by(Signal.confidence_score.desc()).all()
        
        # Filter for strong signals only
        strong_signals = [s for s in signals if s.signal_strength.value == 'strong']
        
        # Group by exchange
        signals_by_exchange = {}
        for signal in strong_signals:
            exchange = signal.ticker.exchange
            if exchange not in signals_by_exchange:
                signals_by_exchange[exchange] = []
            signals_by_exchange[exchange].append(signal)
        
        # Market display names
        market_names = {
            'NYSE': 'NYSE',
            'NASDAQ': 'NASDAQ', 
            'ASX': 'ASX (Australian Securities Exchange)'
        }
        
        market_display = ' & '.join([market_names.get(ex, ex) for ex in exchanges])
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f9fafb; color: #111827; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .header {{ background-color: #374151; color: white; padding: 24px; }}
                .header h1 {{ margin: 0; font-size: 20px; font-weight: 600; }}
                .header p {{ margin: 8px 0 0; opacity: 0.9; font-size: 14px; }}
                .content {{ padding: 24px; }}
                .summary {{ margin-bottom: 24px; padding: 16px; background-color: #f3f4f6; border-radius: 6px; }}
                .summary-text {{ margin: 0; font-size: 14px; color: #6b7280; }}
                .section {{ margin-bottom: 32px; }}
                .section h2 {{ color: #374151; font-size: 16px; font-weight: 600; margin: 0 0 12px; }}
                .signal-table {{ width: 100%; border-collapse: collapse; }}
                .signal-table th {{ background-color: #f9fafb; padding: 12px; text-align: left; font-size: 12px; font-weight: 500; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #e5e7eb; }}
                .signal-table td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; font-size: 14px; }}
                .signal-table tr:hover {{ background-color: #f9fafb; }}
                .symbol {{ font-weight: 600; color: #111827; }}
                .price {{ font-family: monospace; color: #111827; }}
                .exchange-badge {{ background-color: #e5e7eb; color: #374151; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }}
                .footer {{ background-color: #f9fafb; padding: 16px; text-align: center; color: #6b7280; font-size: 12px; }}
                .no-signals {{ text-align: center; padding: 32px; color: #6b7280; }}
                @media (max-width: 600px) {{
                    .signal-table {{ font-size: 12px; }}
                    .signal-table th, .signal-table td {{ padding: 8px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Trading Signals Alert</h1>
                    <p>{market_display} • {date.strftime('%B %d, %Y')} • Generated: {datetime.utcnow().strftime('%H:%M UTC')}</p>
                </div>
                
                <div class="content">
                    <div class="summary">
                        <p class="summary-text">{len(strong_signals)} confirmed buy signal{'s' if len(strong_signals) != 1 else ''} found across {len(set(s.ticker.symbol for s in strong_signals))} ticker{'s' if len(set(s.ticker.symbol for s in strong_signals)) != 1 else ''}</p>
                    </div>
        """
        
        if strong_signals:
            for exchange in exchanges:
                exchange_signals = signals_by_exchange.get(exchange, [])
                if exchange_signals:
                    html_content += f"""
                    <div class="section">
                        <h2>{market_names.get(exchange, exchange)} Signals</h2>
                        <table class="signal-table">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Exchange</th>
                                    <th>Price</th>
                                    <th>Volume Ratio</th>
                                    <th>Signal Date</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                    
                    for signal in exchange_signals:
                        # Extract volume ratio from signal data
                        volume_ratio = "N/A"
                        try:
                            if signal.signal_data:
                                import json
                                signal_details = json.loads(signal.signal_data)
                                if 'volume_ratio' in signal_details:
                                    volume_ratio = f"{signal_details['volume_ratio']:.2f}x"
                                elif 'current_volume_ratio' in signal_details:
                                    volume_ratio = f"{signal_details['current_volume_ratio']:.2f}x"
                        except Exception as e:
                            volume_ratio = "N/A"
                        
                        # Format signal date
                        signal_date_str = signal.signal_date.strftime('%Y-%m-%d') if signal.signal_date else signal.generated_at.strftime('%Y-%m-%d')
                        
                        html_content += f"""
                                <tr>
                                    <td class="symbol">{signal.ticker.symbol}</td>
                                    <td><span class="exchange-badge">{signal.ticker.exchange}</span></td>
                                    <td class="price">${signal.price:.2f}</td>
                                    <td>{volume_ratio}</td>
                                    <td>{signal_date_str}</td>
                                </tr>
                        """
                    
                    html_content += """
                            </tbody>
                        </table>
                    </div>
                    """
        else:
            html_content += """
            <div class="no-signals">
                <p>No confirmed buy signals found for today's session.</p>
            </div>
            """
        
        html_content += f"""
                </div>
                
                <div class="footer">
                    <p>Trading Bot • Confirmed buy signals only • Always conduct your own research</p>
                    <p>Generated automatically 10 minutes after market close</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_market_close_report(self, to_emails: List[str], db: Session, exchanges: List[str]) -> bool:
        """Send market close signals report to multiple recipients"""
        try:
            html_content = self.generate_market_signals_report(db, exchanges)
            
            # Create subject based on exchanges
            exchange_names = {
                'NYSE': 'US Markets (NYSE)',
                'NASDAQ': 'US Markets (NASDAQ)', 
                'ASX': 'Australian Market (ASX)'
            }
            
            if 'NYSE' in exchanges and 'NASDAQ' in exchanges:
                subject_market = "US Markets (NYSE & NASDAQ)"
            else:
                subject_market = exchange_names.get(exchanges[0], exchanges[0]) if exchanges else "Markets"
            
            subject = f"🚀 Strong Signals Alert - {subject_market} - {datetime.utcnow().strftime('%Y-%m-%d')}"
            
            success = True
            for email in to_emails:
                if not self.send_email(email, subject, html_content):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send market close report: {str(e)}")
            return False

    def preview_daily_report(self, db: Session, exchanges: List[str]) -> str:
        """Preview the daily report HTML for testing"""
        return self.generate_market_signals_report(db, exchanges)