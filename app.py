from models import db, AdminUser, IndexCard
from auth import auth, login_manager
from admin_views import init_admin
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io
import os
import json
import time
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ministry.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
app.register_blueprint(auth)
init_admin(app)

with app.app_context():
    db.create_all()
    if not AdminUser.query.filter_by(username='admin').first():
        superadmin = AdminUser(username='admin', email='admin@ministryoffailures.lk', role='superadmin', active=True)
        superadmin.set_password('Admin@2025!')
        db.session.add(superadmin)
        db.session.commit()
        print("✅ Default superadmin created: admin / Admin@2025!")

def get_drive_service():
    creds_info = Config.get_credentials_info()
    if creds_info:
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/drive"])
    else:
        creds = service_account.Credentials.from_service_account_file(Config.SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)

def list_drive_files(mime_filter=None, folder_id=None):
    try:
        service = get_drive_service()
        fid = folder_id or Config.DRIVE_FOLDER_ID
        query = f"'{fid}' in parents and trashed=false"
        if mime_filter:
            mime_parts = " or ".join([f"mimeType='{m}'" for m in mime_filter])
            query += f" and ({mime_parts})"
        results = service.files().list(q=query, pageSize=100, fields="files(id, name, mimeType, size, createdTime, thumbnailLink, webViewLink, webContentLink)").execute()
        return results.get("files", [])
    except Exception as e:
        print(f"Drive error: {e}")
        return []

def fetch_sanity_cards(year=None):
    import requests as req
    if not hasattr(fetch_sanity_cards, '_cache'):
        fetch_sanity_cards._cache = {}
    cache = fetch_sanity_cards._cache
    cache_key = year or 'all'
    now = time.time()
    if cache_key not in cache or now - cache.get(cache_key + '_ts', 0) > 30:
        try:
            if year:
                query = f'*[_type == "indexCard" && active == true && year == "{year}"] | order(number asc)'
            else:
                query = '*[_type == "indexCard" && active == true] | order(number asc)'
            project_id = os.environ.get('SANITY_PROJECT_ID', '31sea43n')
            dataset = os.environ.get('SANITY_DATASET', 'production')
            url = f"https://{project_id}.api.sanity.io/v2021-10-21/data/query/{dataset}?query={req.utils.quote(query)}"
            res = req.get(url, timeout=5)
            cache[cache_key] = res.json().get('result', [])
            cache[cache_key + '_ts'] = now
        except Exception as e:
            print(f"Sanity error: {e}")
            cache[cache_key] = cache.get(cache_key, [])
    return cache.get(cache_key, [])

@app.route('/')
def index():
    cards = fetch_sanity_cards('2025')
    return render_template('index.html', cards=cards, year='2025')

@app.route('/index/2025')
def index_2025():
    cards = fetch_sanity_cards('2025')
    return render_template('index.html', cards=cards, year='2025')

@app.route('/index/2026')
def index_2026():
    cards = fetch_sanity_cards('2026')
    return render_template('index.html', cards=cards, year='2026')

@app.route('/index/2027')
def index_2027():
    cards = fetch_sanity_cards('2027')
    return render_template('index.html', cards=cards, year='2027')

@app.route("/videos")
def videos():
    files = list_drive_files(mime_filter=["video/mp4", "video/avi", "video/mov", "video/quicktime", "video/x-msvideo", "video/webm"])
    return render_template("videos.html", files=files)

@app.route("/documents")
def documents():
    files = list_drive_files(mime_filter=["application/pdf"])
    return render_template("documents.html", files=files)

@app.route("/images")
def images():
    files = list_drive_files(mime_filter=["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"])
    return render_template("images.html", files=files)

@app.route("/gallery")
def gallery():
    files = list_drive_files(mime_filter=["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"])
    return render_template("gallery.html", files=files)

@app.route('/debug-sanity')
def debug_sanity():
    import requests
    query = '*[_type == "indexCard"]'
    project_id = os.environ.get('SANITY_PROJECT_ID', '31sea43n')
    dataset = os.environ.get('SANITY_DATASET', 'production')
    url = f"https://{project_id}.api.sanity.io/v2021-10-21/data/query/{dataset}?query={requests.utils.quote(query)}"
    res = requests.get(url)
    return res.text

@app.route("/api/files")
def api_files():
    all_files = list_drive_files()
    grouped = {"videos": [], "documents": [], "images": [], "other": []}
    for f in all_files:
        mt = f.get("mimeType", "")
        if mt.startswith("video/"): grouped["videos"].append(f)
        elif mt == "application/pdf": grouped["documents"].append(f)
        elif mt.startswith("image/"): grouped["images"].append(f)
        else: grouped["other"].append(f)
    return jsonify(grouped)

@app.route("/pdf/page/<int:num>")
def pdf_page(num):
    try:
        import fitz
        pdf_path = os.path.join(app.static_folder, "pdf", "NPP_Failures_size_redue.pdf")
        if not os.path.exists(pdf_path): return "PDF not found", 404
        doc = fitz.open(pdf_path)
        if num < 1 or num > len(doc): return "Page out of range", 404
        page = doc[num - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
        jpg = pix.tobytes("jpeg", jpg_quality=75)
        doc.close()
        response = app.response_class(jpg, mimetype="image/jpeg")
        response.headers['Cache-Control'] = 'public, max-age=86400'
        return response
    except Exception as e:
        return str(e), 500

@app.route("/pdf/count")
def pdf_count():
    try:
        import fitz
        pdf_path = os.path.join(app.static_folder, "pdf", "NPP_Failures_size_redue.pdf")
        if not os.path.exists(pdf_path): return jsonify({"count": 0})
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return jsonify({"count": count})
    except Exception as e:
        print(f"PDF count error: {e}")
        return jsonify({"count": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=False, host="0.0.0.0", port=port)