"""
PDF Splitter - Split PDF files into individual pages
"""
import os
import uuid
import zipfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from pypdf import PdfReader, PdfWriter

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

app = Flask(__name__)
app.secret_key = 'pdf-splitter-secret-key'

# Configuration
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def split_pdf(input_path, output_folder):
    """Split PDF into individual pages"""
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

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
    """Create a zip file containing all split pages"""
    zip_path = os.path.join(output_folder, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for page_file in page_files:
            file_path = os.path.join(output_folder, page_file)
            zipf.write(file_path, page_file)
    
    return zip_path


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and splitting"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        
        # Create session-specific output folder
        session_output_folder = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        os.makedirs(session_output_folder, exist_ok=True)
        
        # Save uploaded file
        original_filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{original_filename}")
        file.save(upload_path)
        
        try:
            # Split the PDF
            page_files, total_pages = split_pdf(upload_path, session_output_folder)
            
            # Create zip file
            zip_filename = f"split_pages_{session_id}.zip"
            create_zip(session_output_folder, page_files, zip_filename)
            
            # Clean up uploaded file
            os.remove(upload_path)
            
            return render_template('index.html', 
                                 success=True,
                                 session_id=session_id,
                                 total_pages=total_pages,
                                 original_filename=original_filename,
                                 page_files=page_files)
        
        except Exception as e:
            flash(f'Error processing PDF: {str(e)}', 'error')
            # Clean up on error
            if os.path.exists(upload_path):
                os.remove(upload_path)
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload a PDF file.', 'error')
        return redirect(url_for('index'))


@app.route('/download/<session_id>')
def download_zip(session_id):
    """Download the zip file containing all pages"""
    zip_filename = f"split_pages_{session_id}.zip"
    zip_path = os.path.join(app.config['OUTPUT_FOLDER'], session_id, zip_filename)
    
    if os.path.exists(zip_path):
        return send_file(zip_path, 
                        as_attachment=True,
                        download_name=f"split_pages_{session_id}.zip",
                        mimetype='application/zip')
    else:
        flash('ZIP file not found. Please split the PDF again.', 'error')
        return redirect(url_for('index'))


@app.route('/download_page/<session_id>/<page_file>')
def download_single_page(session_id, page_file):
    """Download a single page"""
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], session_id, page_file)
    
    if os.path.exists(file_path):
        return send_file(file_path,
                        as_attachment=True,
                        download_name=page_file,
                        mimetype='application/pdf')
    else:
        flash('Page file not found.', 'error')
        return redirect(url_for('index'))


@app.route('/file-location/<session_id>')
def file_location(session_id):
    """Return file location info"""
    session_folder = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    
    if not os.path.exists(session_folder):
        return {'error': 'Folder not found'}, 404
    
    # Also copy to Downloads for easy access
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    zip_file = os.path.join(session_folder, f"split_pages_{session_id}.zip")
    
    if os.path.exists(zip_file):
        dest_file = os.path.join(downloads_path, f"split_pages_{session_id}.zip")
        import shutil
        shutil.copy2(zip_file, dest_file)
        return {
            'output_folder': session_folder,
            'downloads_location': dest_file,
            'message': f'File copied to your Downloads folder: {dest_file}'
        }
    
    return {
        'output_folder': session_folder,
        'message': 'Files are in the output folder'
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
