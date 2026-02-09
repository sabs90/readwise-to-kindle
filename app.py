import base64
import os
import smtplib
import tempfile
import uuid
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

import fitz  # PyMuPDF
import requests
import resend
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from ebooklib import epub
from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
app.config.update(
    SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB upload limit
)

APP_PASSWORD = os.getenv("APP_PASSWORD")
READWISE_API_TOKEN = os.getenv("READWISE_API_TOKEN")
KINDLE_EMAIL = os.getenv("KINDLE_EMAIL")

# Resend (for cloud deployment)
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# SMTP (for local use)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Groq LLM (for digest title keywords)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

READWISE_API_BASE = "https://readwise.io/api/v3"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if APP_PASSWORD and password == APP_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        error = "Invalid password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def get_headers():
    return {"Authorization": f"Token {READWISE_API_TOKEN}"}


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/articles")
@login_required
def get_articles():
    """Fetch articles from Readwise Reader API."""
    location = request.args.get("location", "")

    params = {
        "pageCursor": None,
        "pageSize": 50,
        "withHtmlContent": "false",
    }

    if location:
        params["location"] = location

    try:
        response = requests.get(
            f"{READWISE_API_BASE}/list/",
            headers=get_headers(),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("results", []):
            # Include all readable content types
            category = item.get("category", "")
            if category not in ("highlight", "note"):  # Exclude non-readable types
                articles.append({
                    "id": item.get("id"),
                    "title": item.get("title", "Untitled"),
                    "author": item.get("author", "Unknown"),
                    "published_date": item.get("published_date"),
                    "word_count": item.get("word_count", 0),
                    "reading_time": item.get("reading_progress", 0),
                    "summary": item.get("summary", ""),
                    "site_name": item.get("site_name", ""),
                    "source_url": item.get("source_url", ""),
                    "location": item.get("location", ""),
                    "created_at": item.get("created_at", ""),
                    "category": category,
                })

        # Sort by created_at descending (most recent first)
        articles.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jsonify({"articles": articles})

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return jsonify({"error": "Rate limited. Please wait a moment and try again."}), 429
        return jsonify({"error": f"API error: {str(e)}"}), e.response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch articles: {str(e)}"}), 500


@app.route("/api/article/<article_id>")
@login_required
def get_article_content(article_id):
    """Fetch full HTML content for a specific article."""
    try:
        response = requests.get(
            f"{READWISE_API_BASE}/list/",
            headers=get_headers(),
            params={"id": article_id, "withHtmlContent": "true"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if results:
            return jsonify({
                "id": article_id,
                "html_content": results[0].get("html_content", ""),
                "title": results[0].get("title", "Untitled"),
                "author": results[0].get("author", "Unknown"),
            })

        return jsonify({"error": "Article not found"}), 404

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch article: {str(e)}"}), 500


def extract_pdf_content(filepath):
    """Extract text content from a PDF file as HTML."""
    doc = fitz.open(filepath)
    all_paragraphs = []

    for page in doc:
        # Use block-level extraction to get natural paragraph groupings
        blocks = page.get_text("blocks")
        for block in blocks:
            if block[6] != 0:  # skip non-text blocks (images)
                continue
            text = block[4].strip()
            if not text:
                continue

            # Join lines within each block, handling hyphenation
            lines = text.split("\n")
            paragraphs = []
            current = ""
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    if current:
                        paragraphs.append(current)
                        current = ""
                    continue
                if current.endswith("-") and stripped and stripped[0].islower():
                    current = current[:-1] + stripped
                elif current:
                    current += " " + stripped
                else:
                    current = stripped
            if current:
                paragraphs.append(current)

            all_paragraphs.extend(paragraphs)

    doc.close()

    # Merge paragraphs split across blocks: if a paragraph starts with a
    # lowercase letter, it's a continuation of the previous one.
    merged = []
    for para in all_paragraphs:
        if merged and para and para[0].islower():
            if merged[-1].endswith("-"):
                merged[-1] = merged[-1][:-1] + para
            else:
                merged[-1] += " " + para
        else:
            merged.append(para)

    html_content = "\n".join(f"<p>{p}</p>" for p in merged)
    word_count = len(" ".join(merged).split())
    return {"html_content": html_content, "word_count": word_count}


@app.route("/api/upload-pdf", methods=["POST"])
@login_required
def upload_pdf():
    """Upload a PDF file and extract its text content."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    tmp_path = None
    try:
        # Save to temp file
        fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        file.save(tmp_path)

        result = extract_pdf_content(tmp_path)

        title = os.path.splitext(file.filename)[0]
        return jsonify({
            "id": f"pdf-{uuid.uuid4().hex[:8]}",
            "title": title,
            "author": "",
            "html_content": result["html_content"],
            "word_count": result["word_count"],
            "source": "pdf",
        })

    except Exception as e:
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def clean_html_for_epub(html_content, title, author=None):
    """Clean and prepare HTML content for EPUB."""
    if not html_content:
        html_content = "<p>No content available.</p>"

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style tags
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    # Get the body content or use the whole thing
    body = soup.find("body")
    if body:
        body_content = body.decode_contents()
    else:
        body_content = str(soup)

    # Build header
    header = f"<h1>{title}</h1>"
    if author:
        header += f"<p><em>By {author}</em></p><hr/>"

    # Wrap in proper HTML structure
    return f"""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{title}</title></head>
<body>
{header}
{body_content}
</body>
</html>"""


def generate_keywords(titles):
    """Use Groq LLM to generate a 1-2 word keyword per article title."""
    if not GROQ_API_KEY or not titles:
        return None

    titles_text = "\n".join(f"- {t}" for t in titles)
    prompt = (
        f"For each article title below, produce exactly one keyword (1-2 words) "
        f"that captures its core topic. Output one keyword per line, no numbering, "
        f"no extra text.\n\n{titles_text}"
    )

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            },
            timeout=10,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()

        keywords = []
        for line in text.splitlines():
            line = line.strip().lstrip("0123456789.-) ").strip()
            if not line:
                continue
            # Enforce 2-word max
            words = line.split()[:2]
            keywords.append(" ".join(words))

        if len(keywords) != len(titles):
            return None
        return keywords
    except Exception:
        return None


def build_digest_title(articles_data):
    """Build a digest title with LLM-generated keywords. Returns (display_title, safe_filename)."""
    date_str = datetime.now().strftime("%Y%m%d")
    titles = [a.get("title", "Untitled") for a in articles_data]
    keywords = generate_keywords(titles)

    if keywords:
        # Truncate keywords to keep total title ~80 chars
        prefix = f"R2K - {date_str}"
        parts = []
        length = len(prefix)
        for kw in keywords:
            addition = f" - {kw}"
            if length + len(addition) > 80:
                break
            parts.append(kw)
            length += len(addition)
        if parts:
            display_title = prefix + " - " + " - ".join(parts)
        else:
            display_title = prefix
    else:
        display_title = f"R2K - {date_str}"

    safe_filename = display_title.replace(" ", "-") + ".epub"
    return display_title, safe_filename


def create_epub(articles_data, book_title, filename):
    """Create an EPUB file from the given articles."""
    book = epub.EpubBook()

    # Set metadata
    date_str = datetime.now().strftime("%Y-%m-%d")
    book.set_identifier(f"readwise-digest-{date_str}")
    book.set_title(book_title)
    book.set_language("en")
    book.add_author("Readwise")

    chapters = []

    for i, article in enumerate(articles_data):
        # Create chapter
        chapter = epub.EpubHtml(
            title=article["title"],
            file_name=f"chapter_{i+1}.xhtml",
            lang="en"
        )

        # Clean and set content as bytes
        clean_content = clean_html_for_epub(
            article.get("html_content", ""),
            article["title"],
            article.get("author")
        )
        chapter.content = clean_content.encode("utf-8")

        book.add_item(chapter)
        chapters.append(chapter)

    # Create table of contents
    book.toc = [(chapter, []) for chapter in chapters]

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Create spine
    book.spine = ["nav"] + chapters

    # Add CSS
    style = """
    body { font-family: serif; line-height: 1.6; padding: 1em; }
    h1 { margin-bottom: 0.5em; }
    img { max-width: 100%; height: auto; }
    pre, code { font-family: monospace; background: #f4f4f4; padding: 0.2em; }
    blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 1em; }
    """
    css = epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=style
    )
    book.add_item(css)

    # Write to temp file
    filepath = os.path.join(tempfile.gettempdir(), filename)
    epub.write_epub(filepath, book)

    return filepath


@app.route("/api/create-epub", methods=["POST"])
@login_required
def create_epub_endpoint():
    """Fetch content for selected articles and create EPUB."""
    data = request.get_json()
    article_ids = data.get("article_ids", [])
    pdf_articles = data.get("pdf_articles", [])

    if not article_ids and not pdf_articles:
        return jsonify({"error": "No articles selected"}), 400

    articles_data = []

    for article_id in article_ids:
        try:
            response = requests.get(
                f"{READWISE_API_BASE}/list/",
                headers=get_headers(),
                params={"id": article_id, "withHtmlContent": "true"},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json().get("results", [])

            if result:
                articles_data.append({
                    "id": article_id,
                    "title": result[0].get("title", "Untitled"),
                    "author": result[0].get("author", ""),
                    "html_content": result[0].get("html_content", ""),
                })
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Failed to fetch article {article_id}: {str(e)}"}), 500

    # Append uploaded PDF articles
    for pdf in pdf_articles:
        articles_data.append({
            "id": pdf.get("id", ""),
            "title": pdf.get("title", "Untitled"),
            "author": pdf.get("author", ""),
            "html_content": pdf.get("html_content", ""),
        })

    if not articles_data:
        return jsonify({"error": "No article content found"}), 404

    try:
        display_title, filename = build_digest_title(articles_data)
        filepath = create_epub(articles_data, display_title, filename)
        return jsonify({
            "success": True,
            "filepath": filepath,
            "filename": filename,
            "digest_title": display_title,
            "article_count": len(articles_data),
        })
    except Exception as e:
        return jsonify({"error": f"Failed to create EPUB: {str(e)}"}), 500


@app.route("/api/download-epub", methods=["POST"])
@login_required
def download_epub():
    """Download the generated EPUB file."""
    data = request.get_json()
    filepath = data.get("filepath")
    filename = data.get("filename")

    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "EPUB file not found"}), 404

    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route("/api/send-to-kindle", methods=["POST"])
@login_required
def send_to_kindle():
    """Send the EPUB file to Kindle via Resend (cloud) or SMTP (local)."""
    data = request.get_json()
    filepath = data.get("filepath")
    filename = data.get("filename")
    digest_title = data.get("digest_title", f"R2K - {datetime.now().strftime('%Y%m%d')}")

    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "EPUB file not found"}), 404

    if not KINDLE_EMAIL or KINDLE_EMAIL == "your_kindle@kindle.com":
        return jsonify({"error": "Please configure your Kindle email."}), 400

    # Use Resend if API key is set, otherwise use SMTP
    if RESEND_API_KEY:
        return send_via_resend(filepath, filename, digest_title)
    else:
        return send_via_smtp(filepath, filename, digest_title)


def send_via_resend(filepath, filename, subject):
    """Send email using Resend API (for cloud deployment)."""
    try:
        with open(filepath, "rb") as f:
            epub_content = base64.b64encode(f.read()).decode("utf-8")

        params = {
            "from": FROM_EMAIL,
            "to": [KINDLE_EMAIL],
            "subject": subject,
            "text": "Your Readwise digest is attached.",
            "attachments": [
                {
                    "filename": filename,
                    "content": epub_content,
                }
            ],
        }

        resend.Emails.send(params)
        return jsonify({"success": True, "message": f"Sent to {KINDLE_EMAIL}"})

    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500


def send_via_smtp(filepath, filename, subject):
    """Send email using SMTP (for local use)."""
    if not all([SMTP_SERVER, SMTP_EMAIL, SMTP_PASSWORD]):
        return jsonify({"error": "SMTP configuration incomplete. Check your .env file."}), 400

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = KINDLE_EMAIL
        msg["Subject"] = subject

        body = "Your Readwise digest is attached."
        msg.attach(MIMEText(body, "plain"))

        with open(filepath, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="epub+zip")
            attachment.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(attachment)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        return jsonify({"success": True, "message": f"Sent to {KINDLE_EMAIL}"})

    except smtplib.SMTPAuthenticationError:
        return jsonify({"error": "SMTP authentication failed. Check your email credentials."}), 401
    except smtplib.SMTPException as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500
    except TimeoutError:
        return jsonify({"error": "SMTP connection timed out."}), 504
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    import webbrowser
    from threading import Timer

    port = int(os.getenv("PORT", 5001))

    def open_browser():
        webbrowser.open(f"http://localhost:{port}")

    Timer(1.5, open_browser).start()
    app.run(debug=True, host="0.0.0.0", port=port)
