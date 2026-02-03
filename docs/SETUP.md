# Setup Guide

This guide walks you through configuring all required services for Readwise to Kindle.

## Table of Contents

1. [Readwise API Token](#1-readwise-api-token)
2. [Kindle Email Address](#2-kindle-email-address)
3. [Gmail SMTP Configuration](#3-gmail-smtp-configuration)
4. [Amazon Approved Senders](#4-amazon-approved-senders)
5. [Environment Configuration](#5-environment-configuration)
6. [Authentication Setup](#6-authentication-setup)
7. [Deployment to Railway](#7-deployment-to-railway)
8. [Outstanding: Resend Setup for Cloud Deployment](#outstanding-resend-setup-for-cloud-deployment)

---

## 1. Readwise API Token

The Readwise API token allows the app to access your Reader library.

### Steps

1. Go to [readwise.io/access_token](https://readwise.io/access_token)
2. Log in to your Readwise account if prompted
3. Copy the displayed access token

### Notes

- The token provides read-only access to your library
- Tokens do not expire unless manually revoked
- Keep your token secure; do not commit it to version control

---

## 2. Kindle Email Address

Each Kindle device has a unique email address for receiving documents.

### Finding Your Kindle Email

**Method 1: Amazon Website**
1. Go to [amazon.com/myk](https://www.amazon.com/myk)
2. Select "Devices" tab
3. Click on your Kindle device
4. Find "Email Address" (format: `name@kindle.com`)

**Method 2: Kindle Device**
1. On your Kindle, go to Settings
2. Select "Your Account"
3. Find "Send-to-Kindle Email"

### Notes

- The email typically looks like `username_XXXXX@kindle.com`
- Each device has a unique email address
- You can also send to the Kindle app on phones/tablets

---

## 3. Gmail SMTP Configuration

Gmail requires an "App Password" for third-party applications.

### Prerequisites

- A Gmail account
- Two-Factor Authentication (2FA) enabled on your Google account

### Enabling 2FA (if not already enabled)

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click "2-Step Verification"
3. Follow the prompts to enable 2FA

### Creating an App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Sign in if prompted
3. Under "Select app", choose "Mail"
4. Under "Select device", choose "Other" and enter "Readwise to Kindle"
5. Click "Generate"
6. Copy the 16-character password (spaces are optional)

### SMTP Settings

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

### Alternative Email Providers

| Provider | SMTP Server | Port |
|----------|-------------|------|
| Gmail | smtp.gmail.com | 587 |
| Outlook | smtp-mail.outlook.com | 587 |
| Yahoo | smtp.mail.yahoo.com | 587 |
| iCloud | smtp.mail.me.com | 587 |

---

## 4. Amazon Approved Senders

Amazon blocks emails from unknown senders. You must whitelist your sending email.

### Steps

1. Go to [amazon.com/myk](https://www.amazon.com/myk)
2. Select "Preferences" tab
3. Scroll to "Personal Document Settings"
4. Under "Approved Personal Document E-mail List", click "Add a new approved e-mail address"
5. Enter your Gmail address (the one in `SMTP_EMAIL`)
6. Click "Add Address"

### Notes

- This is a one-time setup per email address
- Documents from unapproved senders are silently rejected
- You can add multiple approved addresses

---

## 5. Environment Configuration

### Creating the Configuration File

```bash
cp .env.example .env
```

### Editing the Configuration

Open `.env` in your preferred editor and fill in all values:

```bash
# Readwise API (from step 1)
READWISE_API_TOKEN=your_token_here

# Kindle (from step 2)
KINDLE_EMAIL=your_kindle@kindle.com

# SMTP (from step 3)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Validating Configuration

Run the app and check the console for any configuration errors:

```bash
python app.py
```

Common validation errors:
- "Email configuration incomplete" - One or more SMTP fields are missing
- "Please configure your Kindle email" - `KINDLE_EMAIL` still has the placeholder value

---

## Security Considerations

### What to Keep Secret

- **READWISE_API_TOKEN**: Provides access to your Readwise library
- **SMTP_PASSWORD**: Your Gmail app password
- **.env file**: Contains all sensitive credentials

### Best Practices

1. Never commit `.env` to version control (already in `.gitignore`)
2. Use app passwords instead of your main Gmail password
3. Revoke tokens/passwords if you suspect compromise
4. Consider using a dedicated email for sending documents

### Revoking Credentials

**Readwise Token**:
- Go to [readwise.io/access_token](https://readwise.io/access_token) and generate a new token

**Gmail App Password**:
- Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) and remove the app password

---

## 6. Authentication Setup

The app includes password protection for deployment. This is optional for local use but required when deploying to the web.

### Configuration

Add these variables to your `.env` file:

```bash
# Password for logging into the app
APP_PASSWORD=your_secure_password

# Secret key for session encryption (generate a random string)
SECRET_KEY=your_random_32_character_string
```

### Generating a Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Notes

- If `APP_PASSWORD` is not set, login will fail
- The `SECRET_KEY` should be unique and kept secret
- For local development, any values work; for production, use strong values
- Sessions use secure, httponly cookies with SameSite=Lax

---

## 7. Deployment to Railway

Railway is a cloud platform that auto-detects Python apps and provides free SSL.

**Important**: Railway blocks outbound SMTP connections. You must use Resend (email API) for cloud deployment.

### Prerequisites

- GitHub account with your repo pushed
- Railway account (sign up at [railway.app](https://railway.app))
- Resend account with verified domain (see "Outstanding Setup" below)

### Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Create Railway Project**
   - Go to [railway.app](https://railway.app) and sign in
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Configure Environment Variables**

   In Railway dashboard, go to your project → Variables → Add these:

   | Variable | Value |
   |----------|-------|
   | `READWISE_API_TOKEN` | Your Readwise token |
   | `KINDLE_EMAIL` | your_kindle@kindle.com |
   | `RESEND_API_KEY` | Your Resend API key |
   | `FROM_EMAIL` | noreply@yourdomain.com |
   | `APP_PASSWORD` | Your login password |
   | `SECRET_KEY` | Random 32+ char string |

4. **Deploy**
   - Railway auto-detects the `Procfile` and deploys
   - Click "Generate Domain" to get a public URL

### Railway Features

- **Free tier**: $5/month credit (sufficient for personal use)
- **No cold starts**: Unlike some free tiers, always responsive
- **Auto-deploy**: Pushes to GitHub trigger new deploys
- **Free SSL**: HTTPS enabled automatically

### Verification

1. Visit your Railway URL
2. You should see the login page
3. Enter your `APP_PASSWORD`
4. Verify articles load and EPUB creation works
5. Test sending to Kindle

---

## Outstanding: Resend Setup for Cloud Deployment

To deploy to the cloud (Railway), you need to set up Resend with a verified domain. SMTP is blocked on most cloud platforms.

### Steps

1. **Sign up at [resend.com](https://resend.com)**

2. **Verify a domain you own**
   - Go to [resend.com/domains](https://resend.com/domains)
   - Add your domain (e.g., `yourdomain.com`)
   - Add the DNS records Resend provides (SPF, DKIM)
   - Wait for verification (usually a few minutes)

3. **Get your API key**
   - Go to [resend.com/api-keys](https://resend.com/api-keys)
   - Create a new API key
   - Copy it for use in Railway

4. **Add sender to Amazon approved list**
   - Go to [amazon.com/myk](https://amazon.com/myk) → Preferences → Personal Document Settings
   - Add your verified email (e.g., `noreply@yourdomain.com`) to approved senders

5. **Configure Railway**
   - Add `RESEND_API_KEY` and `FROM_EMAIL` to Railway environment variables
   - Remove any SMTP variables (they won't work anyway)

### Notes

- Resend free tier: 3,000 emails/month (more than enough for personal use)
- The app automatically uses Resend when `RESEND_API_KEY` is set, otherwise falls back to SMTP
- You can test locally with SMTP, then deploy with Resend
