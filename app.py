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

# ── Sanity GROQ projection for media assets ──────────────────────────────
SANITY_MEDIA_PROJECTION = (
    '{ ...,'
    ' videos[]{title, "url": file.asset->url, "originalFilename": file.asset->originalFilename},'
    ' images[]{title, "url": image.asset->url, "originalFilename": image.asset->originalFilename},'
    ' documents[]{title, "url": file.asset->url, "originalFilename": file.asset->originalFilename}'
    ' }'
)

def fetch_sanity_cards(year=None):
    import requests as req
    if not hasattr(fetch_sanity_cards, '_cache'):
        fetch_sanity_cards._cache = {}
    cache = fetch_sanity_cards._cache
    cache_key = year or 'all'
    now = time.time()
    # Cache for 5 minutes (300 seconds) to handle high concurrent traffic
    if cache_key not in cache or now - cache.get(cache_key + '_ts', 0) > 300:
        try:
            if year:
                query = f'*[_type == "indexCard" && active == true && year == "{year}"] | order(number asc) ' + SANITY_MEDIA_PROJECTION
            else:
                query = '*[_type == "indexCard" && active == true] | order(number asc) ' + SANITY_MEDIA_PROJECTION
            project_id = os.environ.get('SANITY_PROJECT_ID', '31sea43n')
            dataset = os.environ.get('SANITY_DATASET', 'production')
            url = f"https://{project_id}.api.sanity.io/v2021-10-21/data/query/{dataset}?query={req.utils.quote(query)}"
            res = req.get(url, timeout=5)
            fetched_cards = res.json().get('result', [])
            
            # Sort numerically since Sanity sorts them as strings (e.g. 100 comes before 99)
            def sort_key(card):
                try:
                    return float(card.get('number', 0))
                except (ValueError, TypeError):
                    return 0
                    
            fetched_cards.sort(key=sort_key)
            cache[cache_key] = fetched_cards
            cache[cache_key + '_ts'] = now
        except Exception as e:
            print(f"Sanity error: {e}")
            cache[cache_key] = cache.get(cache_key, [])
    return cache.get(cache_key, [])

def fetch_sanity_media(media_type):
    """Fetch all media of a given type (videos/images/documents) from all active index cards."""
    import requests as req
    if not hasattr(fetch_sanity_media, '_cache'):
        fetch_sanity_media._cache = {}
    cache = fetch_sanity_media._cache
    now = time.time()
    # Cache for 5 minutes (300 seconds)
    if media_type not in cache or now - cache.get(media_type + '_ts', 0) > 300:
        try:
            project_id = os.environ.get('SANITY_PROJECT_ID', '31sea43n')
            dataset = os.environ.get('SANITY_DATASET', 'production')

            if media_type == 'videos':
                query = ('*[_type == "indexCard" && active == true && defined(videos) && count(videos) > 0]'
                         ' | order(number asc)'
                         ' { number, titleSi, titleEn, year,'
                         '   videos[]{title, "url": file.asset->url, "originalFilename": file.asset->originalFilename}'
                         ' }')
            elif media_type == 'images':
                query = ('*[_type == "indexCard" && active == true && defined(images) && count(images) > 0]'
                         ' | order(number asc)'
                         ' { number, titleSi, titleEn, year,'
                         '   images[]{title, "url": image.asset->url, "originalFilename": image.asset->originalFilename}'
                         ' }')
            elif media_type == 'documents':
                query = ('*[_type == "indexCard" && active == true && defined(documents) && count(documents) > 0]'
                         ' | order(number asc)'
                         ' { number, titleSi, titleEn, year,'
                         '   documents[]{title, "url": file.asset->url, "originalFilename": file.asset->originalFilename}'
                         ' }')
            else:
                cache[media_type] = []
                cache[media_type + '_ts'] = now
                return []

            url = f"https://{project_id}.api.sanity.io/v2021-10-21/data/query/{dataset}?query={req.utils.quote(query)}"
            res = req.get(url, timeout=10)
            cards = res.json().get('result', [])

            # Flatten: extract each media item with its parent card context
            items = []
            for card in cards:
                media_list = card.get(media_type, []) or []
                for item in media_list:
                    if item and item.get('url'):
                        item['cardNumber'] = card.get('number', '')
                        item['cardTitle'] = card.get('titleEn', '') or card.get('titleSi', '')
                        item['cardYear'] = card.get('year', '')
                        items.append(item)
            cache[media_type] = items
            cache[media_type + '_ts'] = now
        except Exception as e:
            print(f"Sanity media error ({media_type}): {e}")
            cache[media_type] = cache.get(media_type, [])
    return cache.get(media_type, [])

@app.route('/')
def index():
    cards = fetch_sanity_cards('2025')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_pages = (len(cards) + per_page - 1) // per_page
    paginated_cards = cards[(page - 1) * per_page : page * per_page]
    return render_template('index.html', cards=paginated_cards, year='2025', page=page, total_pages=total_pages)

@app.route('/index/2025')
def index_2025():
    cards = fetch_sanity_cards('2025')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_pages = (len(cards) + per_page - 1) // per_page
    paginated_cards = cards[(page - 1) * per_page : page * per_page]
    return render_template('index.html', cards=paginated_cards, year='2025', page=page, total_pages=total_pages)

@app.route('/index/2026')
def index_2026():
    cards = fetch_sanity_cards('2026')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_pages = (len(cards) + per_page - 1) // per_page
    paginated_cards = cards[(page - 1) * per_page : page * per_page]
    return render_template('index.html', cards=paginated_cards, year='2026', page=page, total_pages=total_pages)

@app.route('/index/2027')
def index_2027():
    cards = fetch_sanity_cards('2027')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_pages = (len(cards) + per_page - 1) // per_page
    paginated_cards = cards[(page - 1) * per_page : page * per_page]
    return render_template('index.html', cards=paginated_cards, year='2027', page=page, total_pages=total_pages)

@app.route("/videos")
def videos():
    files = fetch_sanity_media('videos')
    return render_template("videos.html", files=files)

@app.route("/documents")
def documents():
    files = fetch_sanity_media('documents')
    return render_template("documents.html", files=files)

@app.route("/images")
def images():
    files = fetch_sanity_media('images')
    return render_template("images.html", files=files)

@app.route("/gallery")
def gallery():
    files = fetch_sanity_media('images')
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
    videos = fetch_sanity_media('videos')
    images = fetch_sanity_media('images')
    documents = fetch_sanity_media('documents')
    return jsonify({"videos": videos, "documents": documents, "images": images})

@app.route("/pdf/page/<int:num>")
def pdf_page(num):
    try:
        # Pre-rendered images are stored in static/pdf_pages/
        images_dir = os.path.join(app.static_folder, "pdf_pages")
        filename = f"page_{num}.jpg"
        
        # Verify the file exists before sending
        if not os.path.exists(os.path.join(images_dir, filename)):
            return "Page out of range", 404
            
        from flask import send_from_directory
        response = send_from_directory(images_dir, filename, mimetype="image/jpeg")
        response.headers['Cache-Control'] = 'public, max-age=864000' # Cache for 10 days
        return response
    except Exception as e:
        return str(e), 500

@app.route("/pdf/count")
def pdf_count():
    try:
        images_dir = os.path.join(app.static_folder, "pdf_pages")
        if not os.path.exists(images_dir): 
            return jsonify({"count": 0})
        
        # Count the number of .jpg files in the directory
        count = len([f for f in os.listdir(images_dir) if f.endswith('.jpg')])
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/card/<year>/<number>')
def card_detail(year, number):
    """Share-friendly URL: renders the main index page on the correct pagination page,
    highlights the target card, and injects OG meta tags for social media previews."""
    cards = fetch_sanity_cards(year)
    card = None
    card_index = 0
    for i, c in enumerate(cards):
        if str(c.get('number', '')).lstrip('0') == str(number).lstrip('0') or c.get('number', '') == number:
            card = c
            card_index = i
            break
    if not card:
        return redirect(url_for('index'))

    # Calculate which page this card is on
    per_page = 10
    page = (card_index // per_page) + 1
    total_pages = (len(cards) + per_page - 1) // per_page
    paginated_cards = cards[(page - 1) * per_page : page * per_page]

    # Build OG image URL from the card's image if available
    og_image = None
    if card.get('image') and card['image'].get('asset'):
        ref = card['image']['asset']['_ref']
        og_image = 'https://cdn.sanity.io/images/31sea43n/production/' + ref.replace('image-','').replace('-jpg','.jpg').replace('-png','.png').replace('-webp','.webp')

    return render_template('index.html',
        cards=paginated_cards, year=year, page=page, total_pages=total_pages,
        highlight_card=card.get('number', ''),
        og_title=card.get('titleSi', '') + ' — ' + card.get('titleEn', ''),
        og_description=card.get('body', '')[:200],
        og_image=og_image,
        og_url=request.url
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=False, host="0.0.0.0", port=port)