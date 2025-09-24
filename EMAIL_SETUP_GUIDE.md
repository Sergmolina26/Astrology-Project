# Email Provider Setup Guide for Celestia

Your app now supports multiple email providers! Choose the one that works best for you.

## 🏆 RECOMMENDED: Brevo (formerly Sendinblue) - FREE FOREVER

**Why Brevo?**
- ✅ 300 emails/day FREE forever (no trial expiration)
- ✅ Easy setup, good deliverability
- ✅ No credit card required

**Setup Steps:**
1. Go to [brevo.com](https://brevo.com) and create free account
2. Go to SMTP & API → API Keys → Create new API key
3. Copy your API key
4. Add to your backend `.env` file:
```
EMAIL_PROVIDER=brevo
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=Lago.mistico11@gmail.com
```

---

## Option 2: Gmail SMTP - FREE (500 emails/day)

**Setup Steps:**
1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account Settings → Security → App Passwords
3. Generate an app-specific password for "Mail"
4. Add to your backend `.env` file:
```
EMAIL_PROVIDER=gmail
GMAIL_EMAIL=Lago.mistico11@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password
SENDER_EMAIL=Lago.mistico11@gmail.com
```

---

## Option 3: Mailgun - FREE (5000 emails/month for 3 months)

**Setup Steps:**
1. Go to [mailgun.com](https://mailgun.com) and create account
2. Verify your domain or use sandbox domain for testing
3. Get your API key from Dashboard → API Keys
4. Add to your backend `.env` file:
```
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=your_domain_or_sandbox.mailgun.org
SENDER_EMAIL=Lago.mistico11@gmail.com
```

---

## Option 4: Amazon SES - VERY CHEAP

**Setup Steps:**
1. Go to AWS Console → SES
2. Verify your email address
3. Get your SMTP credentials
4. Add to your backend `.env` file:
```
EMAIL_PROVIDER=aws_ses
AWS_SES_ACCESS_KEY=your_access_key
AWS_SES_SECRET_KEY=your_secret_key
AWS_SES_REGION=us-east-1
SENDER_EMAIL=Lago.mistico11@gmail.com
```

---

## Current Setup (SendGrid - expires soon)

Your current `.env` file has:
```
EMAIL_PROVIDER=sendgrid  # You can change this to any option above
SENDGRID_API_KEY=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
SENDER_EMAIL=Lago.mistico11@gmail.com
```

## 🚀 Quick Switch Instructions

1. **Choose your preferred provider** (I recommend Brevo)
2. **Get the API key** from the provider
3. **Update your `.env` file** with the new provider settings
4. **Restart the backend**: `sudo supervisorctl restart backend`
5. **Test by creating a session** - you should receive emails!

## Testing Your Email Setup

After switching providers, test it by:
1. Creating a new session booking in your app
2. Check your email inbox for confirmation
3. Complete the payment flow to test payment confirmations

## Which Provider Should You Choose?

- **For simplicity & reliability**: Brevo (300/day free forever)
- **If you already use Gmail**: Gmail SMTP (500/day free)
- **For high volume**: Mailgun or Amazon SES (pay-per-use)

Let me know which provider you'd like to set up and I can help you configure it!