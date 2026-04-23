"""
PrimeOS — Django 5.0 Monolith Backend (Port 8020)
Single Django application serving ALL functionality (auth, content, search, streaming, recommendations).
This is the architectural CONTRAST to Netflix's microservices — one pod dies = entire site dies.
"""
import os, json, uuid, hashlib
from datetime import datetime, timedelta

from django.conf import settings
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection

# ─── Django Inline Configuration ─────────────────────────────
if not settings.configured:
    settings.configure(
        DEBUG=os.getenv('DEBUG', 'True') == 'True',
        SECRET_KEY=os.getenv('DJANGO_SECRET_KEY', 'sentinels-prime-secret-key-2024'),
        ALLOWED_HOSTS=['*'],
        ROOT_URLCONF=__name__,
        DATABASES={'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(os.path.dirname(__file__), 'prime.db'),
        }},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
        ],
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    )

import django
django.setup()

# ─── Database Setup ──────────────────────────────────────────
def init_database():
    """Create tables and seed data."""
    with connection.cursor() as cursor:
        cursor.execute('''CREATE TABLE IF NOT EXISTS prime_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, display_name TEXT NOT NULL,
            is_prime_member INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS prime_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            description TEXT, category TEXT NOT NULL, youtube_id TEXT NOT NULL,
            thumbnail_url TEXT, release_year INTEGER, rating REAL DEFAULT 0.0,
            is_prime_exclusive INTEGER DEFAULT 0, duration_minutes INTEGER DEFAULT 120
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS prime_watch_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            content_id INTEGER, progress_percent REAL DEFAULT 0.0,
            watched_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # Seed content if empty
        cursor.execute("SELECT COUNT(*) FROM prime_content")
        if cursor.fetchone()[0] == 0:
            movies = [
                ('The Boys', 'Supes have been committing horrible acts. Butcher and the Boys take them down.', 'Action', 'tcrNsIaQkb4', 2019, 8.7, 1),
                ('Reacher', 'Jack Reacher arrives in a small town where he finds a community struggling.', 'Action', 'GSycMV-_Csw', 2022, 8.1, 1),
                ('The Terminal List', 'A Navy SEAL uncovers a conspiracy after his platoon is ambushed.', 'Action', 'GKwEJqzSFOY', 2022, 7.9, 1),
                ('Citadel', 'A global spy agency fights to prevent a rival organization from chaos.', 'Action', 'oB1GFm-4bQQ', 2023, 6.5, 1),
                ('Jack Ryan', 'CIA analyst Jack Ryan uncovers a pattern in terrorist financing.', 'Action', 'Lkaxo-gNEPg', 2018, 8.1, 1),
                ('The Wheel of Time', 'A magical woman arrives in a small village and changes destiny.', 'Sci-Fi', '11nYoamaEFE', 2021, 7.1, 1),
                ('The Expanse', 'In a future where humanity has colonized the solar system.', 'Sci-Fi', 'kQuMFBbm3Fs', 2015, 8.5, 1),
                ('Upload', 'A man can choose to be uploaded to a virtual afterlife.', 'Comedy', '0ZfZj2bn_xg', 2020, 7.9, 1),
                ('Fleabag', 'A young woman navigates London while dealing with tragedy.', 'Comedy', 'I5Uv6cb9YRs', 2016, 8.7, 1),
                ('Good Omens', 'An angel and a demon team up to stop the Apocalypse.', 'Comedy', 'On5dO_MdT40', 2019, 8.0, 1),
                ('The Marvelous Mrs. Maisel', 'A 1958 housewife discovers she has a talent for stand-up.', 'Drama', 'fOmwkTrW4OQ', 2017, 8.7, 1),
                ('Hunters', 'A diverse band of Nazi hunters discover hundreds of high-ranking Nazis.', 'Drama', 'HocJgstb5yM', 2020, 7.2, 0),
                ('Invincible', 'An adult animated superhero show with intense drama.', 'Action', '-bfAVpuko5o', 2021, 8.7, 1),
                ('The Lord of the Rings: The Rings of Power', 'Set in Middle-earth''s Second Age.', 'Sci-Fi', 'v7v1hIkYH24', 2022, 6.9, 1),
                ('Fallout', 'In a post-nuclear America, a vault dweller steps outside.', 'Sci-Fi', 'V-mugKDQDlg', 2024, 8.5, 1),
                ('The Grand Tour', 'Clarkson, Hammond and May explore the world in cars.', 'Documentary', 'NePR_D0hb6s', 2016, 8.7, 1),
                ('All or Nothing', 'Behind the scenes of elite sports teams.', 'Documentary', 'tpbfVFABBWE', 2016, 8.1, 1),
                ('Clarkson''s Farm', 'Jeremy Clarkson attempts to run a farm in the Cotswolds.', 'Documentary', 'w1fhJYWcQIg', 2021, 8.8, 1),
                ('LOL: Last One Laughing', 'Comedians compete to make each other laugh.', 'Comedy', 'qNaLr-wUUHM', 2021, 7.5, 1),
                ('Outer Range', 'A rancher discovers an unfathomable mystery on the edge of his land.', 'Drama', 'Wdnt9JxU-Zg', 2022, 7.1, 1),
            ]
            for m in movies:
                cursor.execute(
                    "INSERT INTO prime_content (title, description, category, youtube_id, release_year, rating, is_prime_exclusive) VALUES (?,?,?,?,?,?,?)",
                    (m[0], m[1], m[2], m[3], m[4], m[5], m[6])
                )
            # Seed demo user
            cursor.execute(
                "INSERT OR IGNORE INTO prime_users (email, password_hash, display_name, is_prime_member) VALUES (?,?,?,?)",
                ('user1@prime.com', hashlib.sha256(b'sentinels123').hexdigest(), 'Ayush Prime', 1)
            )

# ─── Helper ──────────────────────────────────────────────────
def json_body(request):
    try: return json.loads(request.body)
    except: return {}

# ─── Views ───────────────────────────────────────────────────
def health(request):
    return JsonResponse({"status": "healthy", "service": "prime-backend", "architecture": "monolith",
        "timestamp": datetime.utcnow().isoformat()})

def ready(request):
    try:
        with connection.cursor() as c:
            c.execute("SELECT COUNT(*) FROM prime_content")
            count = c.fetchone()[0]
        return JsonResponse({"status": "ready", "content_count": count})
    except Exception as e:
        return JsonResponse({"status": "not_ready", "error": str(e)}, status=503)

@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)
    data = json_body(request)
    email = data.get('email', '')
    pwd_hash = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    with connection.cursor() as c:
        c.execute("SELECT id, email, display_name, is_prime_member FROM prime_users WHERE email=? AND password_hash=?",
            [email, pwd_hash])
        row = c.fetchone()
    if not row:
        return JsonResponse({"error": "Invalid credentials"}, status=401)
    token = str(uuid.uuid4())
    return JsonResponse({"access_token": token, "user": {
        "id": row[0], "email": row[1], "display_name": row[2], "is_prime_member": bool(row[3])
    }})

def browse_content(request):
    category = request.GET.get('category', '')
    with connection.cursor() as c:
        if category:
            c.execute("SELECT * FROM prime_content WHERE category=? ORDER BY rating DESC", [category])
        else:
            c.execute("SELECT * FROM prime_content ORDER BY category, rating DESC")
        cols = [d[0] for d in c.description]
        rows = [dict(zip(cols, r)) for r in c.fetchall()]
    # Group by category
    grouped = {}
    for r in rows:
        cat = r['category']
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(r)
    return JsonResponse([{"category": k, "items": v, "total": len(v)} for k, v in grouped.items()], safe=False)

def get_content(request, content_id):
    with connection.cursor() as c:
        c.execute("SELECT * FROM prime_content WHERE id=?", [content_id])
        cols = [d[0] for d in c.description]
        row = c.fetchone()
    if not row:
        return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse(dict(zip(cols, row)))

def search_content(request):
    q = request.GET.get('q', '')
    if len(q) < 1:
        return JsonResponse({"error": "Query required"}, status=400)
    with connection.cursor() as c:
        c.execute("SELECT * FROM prime_content WHERE title LIKE ? OR description LIKE ? ORDER BY rating DESC LIMIT 20",
            [f'%{q}%', f'%{q}%'])
        cols = [d[0] for d in c.description]
        rows = [dict(zip(cols, r)) for r in c.fetchall()]
    return JsonResponse(rows, safe=False)

def featured(request):
    with connection.cursor() as c:
        c.execute("SELECT * FROM prime_content ORDER BY rating DESC LIMIT 5")
        cols = [d[0] for d in c.description]
        rows = [dict(zip(cols, r)) for r in c.fetchall()]
    return JsonResponse(rows, safe=False)

def categories(request):
    with connection.cursor() as c:
        c.execute("SELECT category, COUNT(*) as count FROM prime_content GROUP BY category")
        rows = [{"category": r[0], "count": r[1]} for r in c.fetchall()]
    return JsonResponse(rows, safe=False)

@csrf_exempt
def play(request):
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)
    data = json_body(request)
    content_id = data.get('content_id')
    with connection.cursor() as c:
        c.execute("SELECT id, title, youtube_id FROM prime_content WHERE id=?", [content_id])
        row = c.fetchone()
    if not row:
        return JsonResponse({"error": "Content not found"}, status=404)
    return JsonResponse({
        "content_id": row[0], "title": row[1], "youtube_id": row[2],
        "embed_url": f"https://www.youtube-nocookie.com/embed/{row[2]}?autoplay=1&rel=0",
        "session_id": str(uuid.uuid4())[:12]
    })

def metrics(request):
    """Prometheus-compatible metrics endpoint."""
    lines = [
        '# HELP http_requests_total Total HTTP requests',
        '# TYPE http_requests_total counter',
        'http_requests_total{service="prime-backend"} 0',
        '# HELP up Service up status',
        '# TYPE up gauge',
        'up{service="prime-backend"} 1',
    ]
    from django.http import HttpResponse
    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')

# ─── URL Configuration ──────────────────────────────────────
urlpatterns = [
    path('health', health),
    path('ready', ready),
    path('metrics', metrics),
    path('api/auth/login', login),
    path('api/content/browse', browse_content),
    path('api/content/featured', featured),
    path('api/content/categories', categories),
    path('api/content/<int:content_id>', get_content),
    path('api/search', search_content),
    path('api/stream/play', play),
]

# ─── Initialize on import ───────────────────────────────────
init_database()

# ─── WSGI / Run ──────────────────────────────────────────────
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    import sys
    sys.argv = ['manage.py', 'runserver', '0.0.0.0:8020']
    execute_from_command_line(sys.argv)
