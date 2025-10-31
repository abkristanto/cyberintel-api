from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras

app = FastAPI(title="CyberNews API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # your Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

DB_CONFIG = {
    "dbname": "cybernews",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@app.get("/articles/latest")
def latest_articles(limit: int = 20, offset: int = 0):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, source, title, link, tags, digest_summary, published_at
        FROM articles
        ORDER BY published_at DESC
        LIMIT %s OFFSET %s;
    """, (limit, offset))
    rows = cur.fetchall()
    conn.close()
    return {"articles": rows}

@app.get("/articles/by_tag/{tag}")
def articles_by_tag(tag: str, limit: int = 20, offset: int = 0):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, source, title, link, tags, digest_summary, published_at
        FROM articles
        WHERE %s = ANY(tags)
        ORDER BY published_at DESC
        LIMIT %s OFFSET %s;
    """, (tag, limit, offset))
    rows = cur.fetchall()
    conn.close()
    return {"tag": tag, "articles": rows}

@app.get("/articles/search")
def search_articles(q: str = Query(..., min_length=2), limit: int = 25):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, source, title, link, tags, digest_summary, published_at
        FROM articles
        WHERE
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(content, ''))
            @@ plainto_tsquery('english', %s)
        ORDER BY published_at DESC
        LIMIT %s;
    """, (q, limit))
    rows = cur.fetchall()
    conn.close()
    return {"query": q, "articles": rows}

@app.get("/stats/tags")
def tag_distribution(days: int = 7):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT unnest(tags) AS tag, COUNT(*) AS count
        FROM articles
        WHERE published_at >= NOW() - (%s || ' days')::INTERVAL
        GROUP BY tag
        ORDER BY count DESC;
    """, (days,))
    rows = cur.fetchall()
    conn.close()
    return {"period_days": days, "tags": rows}

@app.get("/stats/sources")
def source_distribution(days: int = 30):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT source, COUNT(*) AS count
        FROM articles
        WHERE published_at >= NOW() - (%s || ' days')::INTERVAL
        GROUP BY source
        ORDER BY count DESC;
    """, (days,))
    rows = cur.fetchall()
    conn.close()
    return {"sources": rows}
