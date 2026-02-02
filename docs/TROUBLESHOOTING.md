# Troubleshooting

Common issues and their solutions.

## Table of Contents

1. [Application Won't Start](#application-wont-start)
2. [Login Issues](#login-issues)
3. [No Articles Displayed](#no-articles-displayed)
4. [EPUB Creation Fails](#epub-creation-fails)
5. [Email Sending Fails](#email-sending-fails)
6. [Kindle Not Receiving Documents](#kindle-not-receiving-documents)
7. [Deployment Issues](#deployment-issues)

---

## Application Won't Start

### ModuleNotFoundError

**Symptom**: Error like `ModuleNotFoundError: No module named 'flask'`

**Solution**: Ensure you've activated the virtual environment and installed dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Port Already in Use

**Symptom**: `Address already in use` error

**Solution**: Another process is using port 5000. Either:
- Stop the other process: `lsof -i :5000` then `kill <PID>`
- Or change the port in `app.py`: `app.run(port=5001)`

### Missing .env File

**Symptom**: Application starts but API calls fail

**Solution**: Create the configuration file:

```bash
cp .env.example .env
# Edit .env with your credentials
```

---

## Login Issues

### Password Not Working

**Possible Causes**:

1. **Server started before adding password to .env**
   - Environment variables are only loaded at startup
   - Solution: Restart the server after updating `.env`

2. **APP_PASSWORD not set**
   - Check that `APP_PASSWORD` is defined in your `.env` file
   - Ensure no typos in the variable name

3. **Extra whitespace**
   - Remove any leading/trailing spaces from the password value
   - Example: `APP_PASSWORD=mypassword` (no spaces)

### Redirected to Login After Every Request

**Cause**: Session not persisting

**Possible Solutions**:

1. **SECRET_KEY not set**
   - Add `SECRET_KEY=any_random_string` to `.env`
   - Restart the server

2. **Cookies blocked**
   - Ensure your browser accepts cookies from localhost
   - Try a different browser

3. **Using HTTP in production**
   - Session cookies are marked secure in production
   - Ensure you're using HTTPS (Railway provides this automatically)

### "Invalid password" Even With Correct Password

**Solution**: Check for hidden characters:

```bash
# View your .env file contents with hidden characters visible
cat -A .env | grep APP_PASSWORD
```

Look for unexpected `^M` (Windows line endings) or other characters.

---

## No Articles Displayed

### "Failed to fetch articles" Error

**Possible Causes**:

1. **Invalid API token**
   - Verify your token at [readwise.io/access_token](https://readwise.io/access_token)
   - Ensure no extra spaces in the `.env` file

2. **Network issues**
   - Check your internet connection
   - Verify Readwise is accessible: `curl https://readwise.io`

3. **Rate limiting**
   - Wait a minute and refresh
   - Readwise allows 20 requests per minute

### Only 3-4 Articles Showing

**Cause**: Default filter is set to "Inbox" which may have fewer items

**Solution**: Change the location filter dropdown to "All" to see everything, or check other locations like "Feed"

### Articles Missing Content

**Cause**: Some article types (highlights, notes) are filtered out

**Solution**: These are intentionally excluded as they don't have readable content

---

## EPUB Creation Fails

### "Document is empty" Error

**Cause**: HTML parsing issue with article content

**Solution**: This was a known bug that has been fixed. If you encounter it:
1. Pull the latest code: `git pull`
2. Restart the application

### "Failed to create EPUB" Error

**Possible Causes**:

1. **No articles selected**
   - Select at least one article before clicking "Create & Send to Kindle"

2. **Article content unavailable**
   - Some articles may not have HTML content available
   - Try selecting different articles

3. **Disk space**
   - Ensure your temp directory has space
   - EPUBs are created in `/tmp/` (or system temp folder)

---

## Email Sending Fails

### "SMTP authentication failed"

**Causes and Solutions**:

1. **Wrong password**
   - Use an App Password, not your regular Gmail password
   - Generate a new one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

2. **2FA not enabled**
   - App Passwords require 2FA
   - Enable at [myaccount.google.com/security](https://myaccount.google.com/security)

3. **Less secure apps blocked**
   - Google may block sign-in attempts
   - Check for security alerts in your Gmail

### "Email configuration incomplete"

**Solution**: Ensure all SMTP fields are set in `.env`:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### "Please configure your Kindle email"

**Solution**: Update `KINDLE_EMAIL` in `.env` from the placeholder value

### Connection Timeout

**Possible Causes**:

1. **Firewall blocking SMTP**
   - Some networks block port 587
   - Try a different network or VPN

2. **Wrong SMTP server/port**
   - Verify settings match your email provider

---

## Kindle Not Receiving Documents

### Email Sent Successfully But Nothing Arrives

**Most Common Cause**: Sender not approved

**Solution**:
1. Go to [amazon.com/myk](https://www.amazon.com/myk)
2. Select "Preferences" > "Personal Document Settings"
3. Add your Gmail address to "Approved Personal Document E-mail List"

### Check Spam/Junk

Amazon may filter documents. Check:
- Your Kindle's "Docs" section
- Amazon's "Manage Your Content and Devices" for pending documents

### Wrong Kindle Email

**Solution**: Verify the exact email address:
1. Go to [amazon.com/myk](https://www.amazon.com/myk)
2. Select "Devices" and click your Kindle
3. Copy the exact email address

### EPUB Not Supported (Older Kindles)

**Note**: Modern Kindles support EPUB natively. Very old Kindles (pre-2022) may require MOBI format. This application generates EPUB only.

---

## Getting More Help

### Enable Debug Logging

The Flask server runs in debug mode by default. Check the terminal for detailed error messages.

### Test API Connection

```bash
source venv/bin/activate
python3 -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('READWISE_API_TOKEN')
response = requests.get(
    'https://readwise.io/api/v3/list/',
    headers={'Authorization': f'Token {token}'},
    params={'pageSize': 1},
    timeout=30
)
print(f'Status: {response.status_code}')
print(f'Response: {response.text[:200]}')
"
```

### Test SMTP Connection

```bash
source venv/bin/activate
python3 -c "
import smtplib
import os
from dotenv import load_dotenv
load_dotenv()

try:
    with smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT'))) as server:
        server.starttls()
        server.login(os.getenv('SMTP_EMAIL'), os.getenv('SMTP_PASSWORD'))
        print('SMTP connection successful!')
except Exception as e:
    print(f'SMTP error: {e}')
"
```

---

## Deployment Issues

### Railway Deploy Fails

**Check the build logs** in Railway dashboard for specific errors.

**Common issues**:

1. **Missing Procfile**
   - Ensure `Procfile` exists with: `web: gunicorn app:app`

2. **Missing gunicorn in requirements.txt**
   - Add `gunicorn==21.2.0` to `requirements.txt`

3. **Python version issues**
   - Railway auto-detects Python; usually works out of the box

### App Crashes on Railway

**Check deployment logs** for errors.

**Common causes**:

1. **Missing environment variables**
   - Ensure all required variables are set in Railway dashboard
   - Required: `READWISE_API_TOKEN`, `KINDLE_EMAIL`, `SMTP_*`, `APP_PASSWORD`, `SECRET_KEY`

2. **Invalid SECRET_KEY**
   - Generate a new one: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### Login Works Locally But Not on Railway

**Cause**: Cookies not being set correctly

**Solutions**:

1. **Use HTTPS**
   - Railway provides free SSL; always use the HTTPS URL

2. **Check SESSION_COOKIE_SECURE setting**
   - The app automatically sets secure cookies when `FLASK_ENV=production`
   - Add `FLASK_ENV=production` to Railway environment variables

### EPUB Files Not Persisting

**Note**: This is expected behavior on cloud platforms.

- Temp files are stored in the container's `/tmp` directory
- Files may be cleared when the container restarts
- This is fine for normal use (create → send immediately)
- For long-term storage, consider adding cloud storage integration

---

## Getting More Help

### Enable Debug Logging

The Flask server runs in debug mode by default. Check the terminal for detailed error messages.

### Test API Connection

```bash
source venv/bin/activate
python3 -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('READWISE_API_TOKEN')
response = requests.get(
    'https://readwise.io/api/v3/list/',
    headers={'Authorization': f'Token {token}'},
    params={'pageSize': 1},
    timeout=30
)
print(f'Status: {response.status_code}')
print(f'Response: {response.text[:200]}')
"
```

### Test SMTP Connection

```bash
source venv/bin/activate
python3 -c "
import smtplib
import os
from dotenv import load_dotenv
load_dotenv()

try:
    with smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT'))) as server:
        server.starttls()
        server.login(os.getenv('SMTP_EMAIL'), os.getenv('SMTP_PASSWORD'))
        print('SMTP connection successful!')
except Exception as e:
    print(f'SMTP error: {e}')
"
```

### Report Issues

If you encounter a bug not covered here, please open an issue at:
[github.com/sabs90/readwise-to-kindle/issues](https://github.com/sabs90/readwise-to-kindle/issues)

Include:
- Error message (from browser and terminal)
- Steps to reproduce
- Python version (`python3 --version`)
- Operating system
- Deployment environment (local or Railway)
