# 📧 Email Service Configuration Guide

This guide will help you configure a free email provider to send PDF reports from the Company Research API.

## 🚀 Quick Setup (Recommended)

### Option 1: Gmail (Free & Reliable)

**Step 1: Create/Use Gmail Account**
1. Go to [gmail.com](https://gmail.com) and create an account (or use existing)
2. Enable 2-Factor Authentication in your Google Account settings

**Step 2: Generate App Password**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Click "Security" → "2-Step Verification"
3. Scroll down and click "App passwords"
4. Select "Mail" and generate a password
5. Copy the 16-character app password (format: xxxx xxxx xxxx xxxx)

**Step 3: Set Environment Variables**
```bash
export EMAIL_USER="your.email@gmail.com"
export EMAIL_PASSWORD="your_16_character_app_password"
export FROM_EMAIL="your.email@gmail.com"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
```

### Option 2: Outlook/Hotmail (Free Alternative)

**Step 1: Create Outlook Account**
1. Go to [outlook.com](https://outlook.com) and create account

**Step 2: Set Environment Variables**
```bash
export EMAIL_USER="your.email@outlook.com"
export EMAIL_PASSWORD="your_password"
export FROM_EMAIL="your.email@outlook.com"
export SMTP_SERVER="smtp-mail.outlook.com"
export SMTP_PORT="587"
```

### Option 3: Yahoo Mail (Free)

**Step 1: Create Yahoo Account**
1. Go to [yahoo.com](https://yahoo.com) and create account

**Step 2: Generate App Password**
1. Go to Yahoo Account Settings
2. Enable 2-Factor Authentication
3. Generate App Password for "Mail"

**Step 3: Set Environment Variables**
```bash
export EMAIL_USER="your.email@yahoo.com"
export EMAIL_PASSWORD="your_app_password"
export FROM_EMAIL="your.email@yahoo.com"
export SMTP_SERVER="smtp.mail.yahoo.com"
export SMTP_PORT="587"
```

## 🐳 Docker Environment Setup

If using Docker, add these to your `docker-compose.yml`:

```yaml
version: '3.8'
services:
  company-research-api:
    # ... other configuration
    environment:
      # Gmail Configuration
      - EMAIL_USER=your.email@gmail.com
      - EMAIL_PASSWORD=your_16_character_app_password
      - FROM_EMAIL=your.email@gmail.com
      - SMTP_SERVER=smtp.gmail.com
      - SMTP_PORT=587
```

## 🌐 Cloud Deployment

### Railway
```bash
railway variables set EMAIL_USER="your.email@gmail.com"
railway variables set EMAIL_PASSWORD="your_app_password"
railway variables set FROM_EMAIL="your.email@gmail.com"
railway variables set SMTP_SERVER="smtp.gmail.com"
railway variables set SMTP_PORT="587"
```

### Render
Add in Render dashboard environment variables:
```
EMAIL_USER = your.email@gmail.com
EMAIL_PASSWORD = your_app_password
FROM_EMAIL = your.email@gmail.com
SMTP_SERVER = smtp.gmail.com
SMTP_PORT = 587
```

## 🔒 Security Best Practices

### App Passwords (Recommended)
- **Gmail**: Use App Passwords instead of main password
- **Yahoo**: Use App Passwords with 2FA enabled
- **Outlook**: Regular password works, but 2FA recommended

### Environment Variables
- Never commit email credentials to git
- Use `.env` files for local development
- Use platform-specific secrets for cloud deployment

### Sample .env File
```bash
# Email Configuration
EMAIL_USER=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
FROM_EMAIL=Company Research API <your.email@gmail.com>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Optional: Custom display name
FROM_EMAIL="Company Research API <your.email@gmail.com>"
```

## 📋 Configuration Reference

| Provider | SMTP Server           | Port | Security | Notes                         |
| -------- | --------------------- | ---- | -------- | ----------------------------- |
| Gmail    | smtp.gmail.com        | 587  | TLS      | Requires App Password         |
| Outlook  | smtp-mail.outlook.com | 587  | TLS      | Works with regular password   |
| Yahoo    | smtp.mail.yahoo.com   | 587  | TLS      | Requires App Password         |
| SendGrid | smtp.sendgrid.net     | 587  | TLS      | Free tier: 100 emails/day     |
| Mailgun  | smtp.mailgun.org      | 587  | TLS      | Free tier: 5,000 emails/month |

## 🧪 Testing Your Configuration

### Method 1: Health Check API
```bash
curl http://localhost:8080/health
```
Look for `"email_configured": true` in the response.

### Method 2: Test Email Send
Generate a report through the web interface to test email delivery.

### Method 3: Manual Test
```python
from api.email_service import EmailService

email_service = EmailService()
print("Email configured:", email_service.is_configured())
```

## 🛠️ Troubleshooting

### Common Issues

**❌ "Email service not configured"**
- Check all environment variables are set
- Verify EMAIL_USER and EMAIL_PASSWORD are not empty

**❌ "Authentication failed"**
- Gmail: Use App Password, not regular password
- Enable 2-Factor Authentication first
- Check username/password for typos

**❌ "Connection timed out"**
- Check SMTP_SERVER and SMTP_PORT
- Verify firewall/network allows outbound SMTP
- Try port 465 with SSL instead of 587 with TLS

**❌ "Email too large"**
- PDFs over 25MB won't be attached
- Large reports will include Google Drive link instead

### Debug Mode
Set environment variable for detailed logging:
```bash
export LOG_LEVEL=DEBUG
```

## 🎯 Recommended Setup

For most users, we recommend **Gmail with App Password**:

1. ✅ Free and reliable
2. ✅ High delivery rates
3. ✅ 15GB storage quota
4. ✅ Good spam filtering
5. ✅ Easy app password setup

## 📞 Support

If you encounter issues:
1. Check the `/health` endpoint for configuration status
2. Review server logs for detailed error messages
3. Verify environment variables are properly set
4. Test with a simple email client first

---

🎉 **Once configured, your API will automatically send beautiful HTML email reports with PDF attachments!** 