# API Reference

This document describes the backend API endpoints provided by the Flask application.

## Base URL

```
http://localhost:5000
```

---

## Endpoints

### GET /

Serves the main web interface.

**Response**: HTML page

---

### GET /api/articles

Fetches articles from Readwise Reader.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location` | string | No | Filter by location: `new`, `later`, `archive`, `feed` |

**Response**

```json
{
  "articles": [
    {
      "id": "01abc123...",
      "title": "Article Title",
      "author": "Author Name",
      "published_date": "2024-01-15",
      "word_count": 2500,
      "reading_time": 0,
      "summary": "Brief summary of the article...",
      "site_name": "Example Site",
      "source_url": "https://example.com/article",
      "location": "new",
      "created_at": "2024-01-15T10:30:00.000Z",
      "category": "article"
    }
  ]
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| 429 | Rate limited by Readwise API |
| 500 | Failed to fetch articles |

---

### GET /api/article/:article_id

Fetches full HTML content for a specific article.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `article_id` | string | Readwise document ID |

**Response**

```json
{
  "id": "01abc123...",
  "html_content": "<article>...</article>",
  "title": "Article Title",
  "author": "Author Name"
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| 404 | Article not found |
| 500 | Failed to fetch article |

---

### POST /api/create-epub

Creates an EPUB file from selected articles.

**Request Body**

```json
{
  "article_ids": ["01abc123...", "02def456...", "03ghi789..."]
}
```

**Response**

```json
{
  "success": true,
  "filepath": "/tmp/readwise-digest-2024-01-15.epub",
  "filename": "readwise-digest-2024-01-15.epub",
  "article_count": 3
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| 400 | No articles selected |
| 404 | No article content found |
| 500 | Failed to fetch article or create EPUB |

---

### POST /api/download-epub

Downloads a previously created EPUB file.

**Request Body**

```json
{
  "filepath": "/tmp/readwise-digest-2024-01-15.epub",
  "filename": "readwise-digest-2024-01-15.epub"
}
```

**Response**: Binary EPUB file download

**Error Responses**

| Status | Description |
|--------|-------------|
| 404 | EPUB file not found |

---

### POST /api/send-to-kindle

Sends the EPUB file to the configured Kindle email address.

**Request Body**

```json
{
  "filepath": "/tmp/readwise-digest-2024-01-15.epub",
  "filename": "readwise-digest-2024-01-15.epub"
}
```

**Response**

```json
{
  "success": true,
  "message": "Sent to your_kindle@kindle.com"
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| 400 | Email configuration incomplete or Kindle email not configured |
| 401 | SMTP authentication failed |
| 404 | EPUB file not found |
| 500 | Failed to send email |

---

## Readwise Reader API

The application uses the Readwise Reader API v3.

### Base URL

```
https://readwise.io/api/v3
```

### Authentication

All requests require the header:

```
Authorization: Token YOUR_API_TOKEN
```

### Rate Limits

- 20 requests per minute
- The application handles 429 responses gracefully

### Endpoints Used

**List Documents**

```
GET /list/
```

Parameters:
- `pageSize`: Number of results (default: 50)
- `location`: Filter by location
- `withHtmlContent`: Include full HTML (true/false)
- `id`: Fetch specific document by ID

### Documentation

- [Readwise Reader API Docs](https://readwise.io/reader_api)
