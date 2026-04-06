"""
PDF Splitter - Split PDF files into individual pages
"""
import os
import re
import time
import uuid
import shutil
import logging
import secrets
import zipfile
import threading
from flask import (
    Flask, render_template, request, send_file, flash, redirect, url_for, abort
)
from werkzeug.utils import secure_filename
from pypdf import PdfReader, PdfWriter
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

# Limits
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_MB', '200')) * 1024 * 1024
MAX_PAGES = int(os.environ.get('MAX_PAGES', '2000'))
SESSION_TTL_SECONDS = int(os.environ.get('SESSION_TTL', '3600'))  # 1 hour

# Validators
SESSION_ID_RE = re.compile(r'^[A-Za-z0-9_-]{16,64}$')
PAGE_FILE_RE = re.compile(r'^page_\d{3,}\.pdf$')

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'

csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["60 per hour"])

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ---------- Security helpers ----------

def safe_join(base, *paths):
    """Join paths and ensure result stays within base. Returns absolute path or None."""
    base_real = os.path.realpath(base)
    target = os.path.realpath(os.path.join(base_real, *paths))
    if target != base_real and not target.startswith(base_real + os.sep):
        return None
    return target


def valid_session_id(session_id):
    return bool(SESSION_ID_RE.match(session_id or ''))


def valid_page_file(page_file):
    return bool(PAGE_FILE_RE.match(page_file or ''))


def is_pdf_stream(stream):
    """Check magic bytes; restore stream position."""
    pos = stream.tell()
    head = stream.read(5)
    stream.seek(pos)
    return head.startswith(b'%PDF-')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- Core logic ----------

def split_pdf(input_path, output_folder):
    """Split PDF into individual pages."""
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    if total_pages > MAX_PAGES:
        raise ValueError(f"PDF has too many pages (max {MAX_PAGES}).")

    page_files = []
    for page_num, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        output_filename = f"page_{page_num:03d}.pdf"
        output_path = os.path.join(output_folder, output_filename)
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        page_files.append(output_filename)

    return page_files, total_pages


def create_zip(output_folder, page_files, zip_filename):
    zip_path = os.path.join(output_folder, zip_filename)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for page_file in page_files:
            zipf.write(os.path.join(output_folder, page_file), page_file)
    return zip_path


# ---------- Background cleanup ----------

def cleanup_old_sessions():
    """Periodically remove session folders older than SESSION_TTL_SECONDS."""
    while True:
        try:
            now = time.time()
            for entry in os.listdir(OUTPUT_FOLDER):
                path = os.path.join(OUTPUT_FOLDER, entry)
                if os.path.isdir(path) and now - os.path.getmtime(path) > SESSION_TTL_SECONDS:
                    shutil.rmtree(path, ignore_errors=True)
            for entry in os.listdir(UPLOAD_FOLDER):
                path = os.path.join(UPLOAD_FOLDER, entry)
                if os.path.isfile(path) and now - os.path.getmtime(path) > SESSION_TTL_SECONDS:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
        except Exception:
            logger.exception("Cleanup error")
        time.sleep(600)  # every 10 minutes


threading.Thread(target=cleanup_old_sessions, daemon=True).start()


# ---------- Security headers ----------

@app.after_request
def set_security_headers(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    resp.headers['Content-Security-Policy'] = (
        "default-src 'self'; img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self'"
    )
    return resp


# ---------- Routes ----------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a PDF file.', 'error')
        return redirect(url_for('index'))

    if not is_pdf_stream(file.stream):
        flash('File does not appear to be a valid PDF.', 'error')
        return redirect(url_for('index'))

    session_id = secrets.token_urlsafe(16)
    session_output_folder = safe_join(OUTPUT_FOLDER, session_id)
    if session_output_folder is None:
        abort(400)
    os.makedirs(session_output_folder, exist_ok=True)

    original_filename = secure_filename(file.filename) or 'upload.pdf'
    upload_path = safe_join(UPLOAD_FOLDER, f"{session_id}_{original_filename}")
    if upload_path is None:
        abort(400)
    file.save(upload_path)

    try:
        page_files, total_pages = split_pdf(upload_path, session_output_folder)
        zip_filename = f"split_pages_{session_id}.zip"
        create_zip(session_output_folder, page_files, zip_filename)
        os.remove(upload_path)

        return render_template(
            'index.html',
            success=True,
            session_id=session_id,
            total_pages=total_pages,
            original_filename=original_filename,
            page_files=page_files,
        )
    except ValueError as e:
        # Safe-to-show validation errors
        if os.path.exists(upload_path):
            os.remove(upload_path)
        shutil.rmtree(session_output_folder, ignore_errors=True)
        flash(str(e), 'error')
        return redirect(url_for('index'))
    except Exception:
        logger.exception("PDF processing failed")
        if os.path.exists(upload_path):
            os.remove(upload_path)
        shutil.rmtree(session_output_folder, ignore_errors=True)
        flash('Could not process this PDF.', 'error')
        return redirect(url_for('index'))


@app.route('/download/<session_id>')
@limiter.limit("30 per minute")
def download_zip(session_id):
    if not valid_session_id(session_id):
        abort(404)

    session_folder = safe_join(OUTPUT_FOLDER, session_id)
    if session_folder is None or not os.path.isdir(session_folder):
        abort(404)

    zip_filename = f"split_pages_{session_id}.zip"
    zip_path = safe_join(session_folder, zip_filename)
    if zip_path is None or not os.path.isfile(zip_path):
        abort(404)

    return send_file(
        zip_path,
        as_attachment=True,
        download_name="split_pages.zip",
        mimetype='application/zip',
    )


@app.route('/download_page/<session_id>/<page_file>')
@limiter.limit("60 per minute")
def download_single_page(session_id, page_file):
    if not valid_session_id(session_id) or not valid_page_file(page_file):
        abort(404)

    session_folder = safe_join(OUTPUT_FOLDER, session_id)
    if session_folder is None:
        abort(404)

    file_path = safe_join(session_folder, page_file)
    if file_path is None or not os.path.isfile(file_path):
        abort(404)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=page_file,
        mimetype='application/pdf',
    )


@app.errorhandler(413)
def too_large(e):
    flash(f'File too large. Maximum size is {MAX_CONTENT_LENGTH // (1024 * 1024)}MB.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(429)
def rate_limited(e):
    flash('Too many requests. Please slow down and try again.', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Local development only. For production, run via gunicorn/waitress.
    app.run(debug=False, host='127.0.0.1', port=5000)
