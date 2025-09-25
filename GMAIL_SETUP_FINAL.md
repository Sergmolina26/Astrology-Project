# 📧 Gmail Email Notifications - Final Setup Guide

## Current Status: **MOCKED** Email System
All email notifications are currently **mocked** - they print to console instead of sending real emails.

## 🚀 Enable Real Gmail Notifications

### Step 1: Create Gmail App Password
1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already enabled)
3. Go to **Security** → **App Passwords**
4. Generate an app password for "Mail" 
5. **IMPORTANT**: Copy the 16-character password (you'll only see it once)

### Step 2: Update Environment Variables
Edit `/app/backend/.env` and replace:
```
GMAIL_APP_PASSWORD="placeholder_will_need_real_password"
```
With your actual app password:
```
GMAIL_APP_PASSWORD="your_16_character_app_password_here"
```

### Step 3: Enable Gmail Provider
In `/app/backend/server.py`, uncomment these lines:

**Line 27:** Change from:
```python
# from utils.email_providers import send_email as email_send  # Will be enabled after Gmail setup
```
To:
```python
from utils.email_providers import send_email as email_send
```

**Lines 51-58:** Change from:
```python
def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email using configured provider"""
    try:
        # Temporarily disabled until Gmail setup is complete
        print(f"📧 EMAIL MOCK: Would send to {to_email} - Subject: {subject}")
        return True  # Mock success for now
        # return email_send(to_email, subject, html_content)  # Will be enabled after Gmail setup
```
To:
```python
def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email using configured provider"""
    try:
        return email_send(to_email, subject, html_content)
```

### Step 4: Restart Backend
```bash
sudo supervisorctl restart backend
```

## 📬 What Emails Will Be Sent

### For Clients:
1. **Booking Confirmation** - When session is requested
2. **Payment Confirmation** - When payment is completed  
3. **Session Updates** - When admin changes session status

### For Admin (lago.mistico11@gmail.com):
1. **New Booking Alert** - When client requests session
2. **Payment Received** - When client pays
3. **All session notifications** forwarded to your email

## 🔧 Email Configuration Details

- **Provider**: Gmail SMTP (Free - 500 emails/day)
- **Sender**: lago.mistico11@gmail.com
- **Admin Notifications**: All forwarded to lago.mistico11@gmail.com
- **Security**: App-specific password (not your main Gmail password)

## 📝 Test the Setup

After enabling, test by:
1. Creating a client account
2. Booking a session 
3. Check your Gmail inbox for notifications
4. Admin dashboard should show real email sending logs

## 🔄 Alternative: Keep Mocked System

If you prefer to keep the current **mocked** system (for testing/development), no changes needed. All email functionality works - it just prints to console instead of sending real emails.

---

**Your Celestia admin system is now fully functional with:**
- ✅ Complete admin dashboard with business analytics
- ✅ Session management (confirm, decline, reschedule, remove)
- ✅ Full bilingual support (English/Spanish)  
- ✅ Payment processing with Stripe integration
- ✅ Calendar blocking to prevent double bookings
- ✅ Email notifications (**mocked** - ready to enable with Gmail)