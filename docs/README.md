# Readwise to Kindle

A local web application that fetches articles from your Readwise Reader library, lets you select which ones to include, bundles them into an EPUB, and sends it directly to your Kindle.

## Features

- **Fetch articles** from Readwise Reader API (Inbox, Later, Archive, or Feed)
- **Select articles** via checkboxes with select/deselect all
- **Search and filter** articles by title, author, source, or summary
- **Sort** by any column (title, author, source, word count, location, date)
- **Generate EPUB** with proper formatting and table of contents
- **Send to Kindle** via email or download locally
- **Reading time estimates** based on word count

## Quick Start

```bash
# Clone the repository
git clone https://github.com/sabs90/readwise-to-kindle.git
cd readwise-to-kindle

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials (see Configuration below)

# Run the application
python app.py
```

The browser will open automatically to `http://localhost:5000`.

## Deployment

The app can be deployed to Railway for cloud access with password protection.

```bash
# Test with gunicorn locally
gunicorn app:app

# Deploy to Railway
# 1. Push to GitHub
# 2. Connect repo in Railway dashboard
# 3. Set environment variables (see Configuration)
# 4. Deploy
```

See [SETUP.md](SETUP.md) for detailed deployment instructions.

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```
READWISE_API_TOKEN=your_token_here
KINDLE_EMAIL=your_kindle@kindle.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Authentication (required for deployment, optional for local)
APP_PASSWORD=your_secure_password
SECRET_KEY=generate_a_random_32_char_string
```

See [SETUP.md](SETUP.md) for detailed instructions on obtaining each credential.

## Documentation

- [Setup Guide](SETUP.md) - Detailed setup instructions for all services
- [API Reference](API.md) - Backend API endpoints documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

## How It Works

1. **Fetch**: The app calls the Readwise Reader API to get your saved articles (metadata only for speed)
2. **Select**: You choose which articles to include using the web interface
3. **Generate**: For selected articles, full HTML content is fetched and bundled into an EPUB
4. **Send**: The EPUB is emailed to your Kindle's personal document email address

## Tech Stack

- **Backend**: Python 3.12, Flask
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **EPUB Generation**: ebooklib
- **HTML Processing**: BeautifulSoup, lxml
- **Email**: smtplib (built-in)

## Requirements

- Python 3.9+
- Readwise Reader account with API access
- Email account with SMTP access (Gmail recommended)
- Kindle device with personal document email configured

## License

MIT
