# 🚀 Automated Signal Generation & Email Scheduler

## Overview

The Trading Bot now includes automated signal generation and email delivery that runs **10 minutes after each market close**. It sends beautifully formatted email reports containing **strong confirmed buy signals only**.

## 📅 Schedule

### US Markets (NYSE & NASDAQ)
- **Market Close**: 4:00 PM ET (Eastern Time)
- **Signal Generation**: 4:10 PM ET (10 minutes after close)
- **Email Delivery**: Immediately after signal generation
- **Combined Report**: Single email for both NYSE and NASDAQ

### Australian Market (ASX)
- **Market Close**: 4:00 PM AEST/AEDT (Australian Time)
- **Signal Generation**: 4:10 PM AEST/AEDT (10 minutes after close)
- **Email Delivery**: Immediately after signal generation
- **Separate Report**: Independent from US markets

## 🔧 Setup & Configuration

### 1. Environment Variables

Create a `.env` file in the backend directory with:

```bash
# Email Configuration
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=your_app_password_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# US Markets Recipients (comma-separated)
EMAIL_RECIPIENTS_US_MARKETS=trader1@example.com,trader2@example.com,portfolio@company.com

# ASX Recipients (comma-separated)
EMAIL_RECIPIENTS_ASX=trader1@example.com,asx.specialist@company.com

# Fallback recipients (if market-specific not set)
EMAIL_RECIPIENTS=default@example.com
```

### 2. Gmail App Password Setup

For Gmail users:
1. Enable 2-Factor Authentication
2. Go to **Google Account Settings** → **Security** → **App Passwords**
3. Generate an **App Password** for "Mail"
4. Use this password in `EMAIL_PASSWORD` (not your regular Gmail password)

### 3. Server Configuration

The scheduler **starts automatically** when you run the server:

```bash
cd backend
uvicorn app.main_with_db:app --host 127.0.0.1 --port 8002
```

## 📧 Email Content

### What's Included
- **Strong Signals Only**: Filters to show only high-confidence signals
- **Professional Design**: Beautiful HTML email template
- **Market Breakdown**: Separate sections for each exchange
- **Key Metrics**: Signal count, confidence scores, volumes
- **Mobile Responsive**: Looks great on all devices

### Email Subject Examples
- `🚀 Strong Signals Alert - US Markets (NYSE & NASDAQ) - 2025-08-07`
- `🚀 Strong Signals Alert - Australian Market (ASX) - 2025-08-07`

## 🛠️ API Endpoints

### Check Scheduler Status
```bash
GET /api/scheduler/status
```
Response:
```json
{
  "is_running": true,
  "markets_configured": 2,
  "next_runs": [...],
  "current_time": "2025-08-07T10:00:00"
}
```

### Get Configured Markets
```bash
GET /api/scheduler/markets
```

### Preview Email Report
```bash
GET /api/scheduler/email-preview/US_MARKETS
GET /api/scheduler/email-preview/ASX
```

### Test Signal Generation
```bash
POST /api/scheduler/test-market
{
  "market": "US_MARKETS"
}
```

### Update Email Recipients
```bash
PUT /api/scheduler/email-recipients
{
  "market": "US_MARKETS",
  "recipients": ["new@example.com", "trader@company.com"]
}
```

### Manual Control
```bash
POST /api/scheduler/start    # Start scheduler
POST /api/scheduler/stop     # Stop scheduler
```

## 🧪 Testing

### Test the Complete System
```bash
cd backend
python test_scheduler.py
```

This will:
- ✅ Check scheduler configuration
- ✅ Generate email previews (saved as HTML files)
- ✅ Test signal generation for both markets
- ✅ Verify database connections

### Preview Email Templates
After running the test, check these files:
- `email_preview_us.html` - US Markets email
- `email_preview_asx.html` - ASX email

## 📊 Monitoring & Logs

### View Logs
The scheduler logs all activities:
- Signal generation start/completion
- Email delivery status
- Error messages
- Market timing information

### Check Next Scheduled Runs
```bash
curl http://127.0.0.1:8002/api/scheduler/status
```

Look for the `next_runs` field to see upcoming scheduled executions.

## 🚨 Important Notes

### Market Holidays
- The scheduler runs **every day** at the configured times
- It will generate signals even on weekends/holidays
- No signals will be generated if markets were closed (no new data)

### Time Zones
- **US Markets**: Eastern Time (automatically handles EST/EDT)
- **ASX**: Australian Time (automatically handles AEST/AEDT)
- Server can run in any timezone - the scheduler handles conversions

### Email Delivery
- Emails contain **strong signals only** (not all signals)
- If no strong signals exist, the email will show "No Strong Signals Today"
- Failed email deliveries are logged but don't stop the system

### Data Requirements
- Signals need sufficient historical data (50+ candles)
- Some tickers may be skipped due to insufficient data
- This is normal and doesn't indicate errors

## 🔍 Troubleshooting

### Scheduler Not Running
```bash
curl http://127.0.0.1:8002/api/scheduler/status
# If is_running: false, then:
curl -X POST http://127.0.0.1:8002/api/scheduler/start
```

### No Emails Received
1. Check email configuration in `.env`
2. Verify Gmail app password
3. Check recipient email addresses
4. Look at server logs for email errors

### Test Email Setup
```bash
curl -X POST http://127.0.0.1:8002/api/scheduler/test-market \
  -H "Content-Type: application/json" \
  -d '{"market": "US_MARKETS"}'
```

### View Email Preview
```bash
curl http://127.0.0.1:8002/api/scheduler/email-preview/US_MARKETS > preview.json
```
Then extract the `html_content` and save as `.html` to view in browser.

## 🎯 Production Deployment

### Recommended Setup
1. **Server**: Deploy on a server that runs 24/7
2. **Database**: Use PostgreSQL for production
3. **Email**: Use dedicated email service (SendGrid, AWS SES, etc.)
4. **Monitoring**: Set up log monitoring for email delivery
5. **Backup**: Regular database backups to preserve signal history

### Environment Variables for Production
```bash
# Production email service
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
EMAIL_USERNAME=apikey
EMAIL_PASSWORD=your_sendgrid_api_key

# Multiple recipient lists
EMAIL_RECIPIENTS_US_MARKETS=team@company.com,alerts@company.com
EMAIL_RECIPIENTS_ASX=intl@company.com,asx@company.com
```

---

## 🎉 Ready to Go!

Your automated signal generation and email system is now configured and running. It will:

1. ⏰ **Monitor market close times** automatically
2. 🔄 **Generate signals** 10 minutes after each market close
3. 📧 **Send professional email reports** with strong signals
4. 📊 **Maintain signal history** for up to 10 days
5. 🔄 **Run continuously** without manual intervention

**Happy Trading!** 🚀📈