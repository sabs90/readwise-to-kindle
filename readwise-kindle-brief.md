# Readwise to Kindle - Project Brief

## Overview
Build a local web application that fetches articles from Readwise Reader API, allows user to select which articles to include via checkboxes, optionally upload local PDF documents, then bundles selected articles and PDFs into an EPUB and emails it to a Kindle device.

## Core Functionality

### 1. Fetch Articles from Readwise
- Use Readwise Reader API: `GET https://readwise.io/api/v3/list/`
- Fetch last 50 saved articles (sorted by most recent)
- Initial fetch should NOT include full HTML content (use `withHtmlContent=false` for speed)
- Display metadata for selection:
  - Title
  - Author
  - Published date
  - Word count
  - Reading time
  - Summary (if available)
  - Source/site name

### 2. PDF Upload
- "Add PDF" button to upload local PDF documents
- Text extracted automatically from text-based PDFs (no OCR)
- Uploaded PDFs displayed as removable chips with word count
- PDFs included as chapters in the EPUB alongside Readwise articles
- 16MB file size limit per PDF

### 3. Article Selection Interface
- Simple, clean web interface running locally
- Display articles in a list/table format with checkboxes
- Show key metadata for each article
- Allow user to select/deselect articles
- "Select All" / "Deselect All" buttons
- Show count of selected articles and uploaded PDFs
- Button to proceed: "Create & Send to Kindle"

### 4. EPUB Generation
- Once user confirms selection, fetch full HTML content for selected articles only (use `withHtmlContent=true`)
- Include any uploaded PDFs (text already extracted client-side)
- Create EPUB file with:
  - Each selected article and PDF as a separate chapter
  - Preserve article formatting from HTML
  - Include metadata: title, author
  - Generate table of contents
  - Clean filename: `readwise-digest-YYYY-MM-DD.epub`

### 5. Send to Kindle
- Email the EPUB to configured Kindle email address
- Use SMTP to send
- Subject line: "Readwise Digest - [date]"
- Attachment: the generated EPUB file

## Technical Requirements

### API Details
- **Readwise API Base**: `https://readwise.io/api/v3/`
- **Authentication**: Header `Authorization: Token XXX`
- **List endpoint**: `/list/?limit=50&withHtmlContent=false` (initial fetch)
- **List endpoint with content**: `/list/?id=<doc_id>&withHtmlContent=true` (for selected articles)

### Configuration
Create a simple config file (JSON or .env) for:
```
READWISE_API_TOKEN=your_token_here
KINDLE_EMAIL=your_kindle@kindle.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### EPUB Library
Use a Python library like:
- `ebooklib` - for EPUB generation
- OR `pypub` - simpler EPUB creation
- Ensure proper HTML cleaning and formatting

### PDF Extraction
- `pymupdf` (fitz) - for extracting text from PDF files
- Block-based extraction with paragraph merging and dehyphenation
- Only text-based PDFs supported (no OCR)

### Email Sending
- Use Python's `smtplib` for sending
- Support Gmail SMTP (most common)
- Handle authentication properly

## Tech Stack Suggestions
- **Backend**: Python (Flask for simple local web server)
- **Frontend**: Simple HTML/CSS/JavaScript (no framework needed)
- **EPUB**: `ebooklib` or `pypub` library
- **Email**: `smtplib` (built-in Python)
- **HTTP requests**: `requests` library

## User Flow

1. User runs the application (e.g., `python app.py`)
2. Browser opens automatically to `http://localhost:5000`
3. Page loads and automatically fetches last 50 articles from Readwise
4. Articles displayed in a clean table with checkboxes
5. User selects desired articles
6. *(Optional)* User uploads local PDFs via "Add PDF" button — PDFs appear as chips with word counts
7. User clicks "Create & Send to Kindle"
8. App shows progress: "Fetching full content...", "Creating EPUB...", "Sending to Kindle..."
9. Success message: "Sent X articles to your Kindle!"
10. User can refresh to start over

## Nice-to-Haves (if time permits)
- Loading spinner while fetching articles
- Error handling with clear messages
- Option to download EPUB locally instead of/in addition to sending
- Remember last successful send (timestamp)
- Filter articles by location (new/later/archive) or category
- Search/filter the article list

## Important Notes

1. **Amazon Kindle Email Setup**: User needs to:
   - Find their Kindle email address (in Amazon account settings)
   - Whitelist the sender email in Amazon's "Personal Document Settings"
   - This is a one-time setup

2. **Gmail App Passwords**: If using Gmail for SMTP:
   - User needs to generate an "App Password" (not regular Gmail password)
   - 2FA must be enabled on Gmail account
   - Instructions: https://support.google.com/accounts/answer/185833

3. **Rate Limiting**: Readwise API has rate limits (20 requests/min)
   - Should not be an issue with this use case
   - But add error handling for 429 responses

4. **EPUB Format**: 
   - Kindle supports EPUB natively (newer feature)
   - No need for MOBI conversion
   - Ensure EPUB is valid (use `ebooklib` validation if possible)

## Deliverables

1. Working Python application with web interface
2. Clear README with:
   - Setup instructions
   - How to get Readwise API token
   - How to configure Kindle email
   - How to set up Gmail app password (if using Gmail)
   - How to whitelist sender in Amazon settings
3. Requirements.txt for dependencies
4. Config file template

## Example API Response Structure

```json
{
    "count": 50,
    "nextPageCursor": null,
    "results": [
        {
            "id": "01gkqtdz9x...",
            "url": "https://readwise.io/new/read/01gkqtdz9x...",
            "source_url": "https://example.com/article",
            "title": "Article Title",
            "author": "Author Name",
            "category": "article",
            "location": "new",
            "word_count": 2678,
            "reading_time": "11 mins",
            "created_at": "2022-12-08T02:53:29.639650+00:00",
            "published_date": "2017-08-09",
            "summary": "Brief summary...",
            "site_name": "Example Site",
            "notes": "",
            // html_content only included when withHtmlContent=true
        }
    ]
}
```

## Priority Order
1. Core functionality: Fetch → Select → EPUB → Send
2. Clean, simple UI
3. Error handling and user feedback
4. Documentation

Build this as a self-contained project that's easy to set up and use.
