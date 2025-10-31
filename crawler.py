import feedparser
import trafilatura
import time
import psycopg2
import re
from psycopg2.extras import execute_values
from datetime import datetime
from textwrap import shorten

# --- RSS feeds ---
FEEDS = [
    ("Bleeping Computer", "https://www.bleepingcomputer.com/feed/"),
    ("Infosecurity Magazine", "https://www.infosecurity-magazine.com/rss/news/"),
    ("SecurityBrief Australia", "https://securitybrief.com.au/rss"),
]

# --- keyword tagging ---
def auto_tag(text):
    text = text.lower()
    tags = []

    # --- Ransomware ---
    if re.search(r"\bransomware\b", text):
        tags.append("ransomware")

    # --- Phishing ---
    if re.search(r"\bphishing\b", text):
        tags.append("phishing")

    # --- Vulnerability ---
    if re.search(r"\bvulnerability\b", text) or "cve-" in text:
        tags.append("vulnerability")

    # --- Data breach ---
    if re.search(r"\b(breach|leak|exposed|data\s+leak)\b", text):
        tags.append("data breach")

    # --- Exploit ---
    if re.search(r"\bexploit(s|ed|ing)?\b", text):
        tags.append("exploit")

    # --- Malware ---
    if re.search(r"\b(malware|trojan|virus|worm)\b", text):
        tags.append("malware")

    # --- Policy / Regulation ---
    if re.search(r"\b(policy|regulation|compliance|law|legal)\b", text):
        tags.append("policy")

    # --- AI / ML ---
    if re.search(r"\b(ai|artificial intelligence|machine learning)\b", text):
        tags.append("ai")

    return sorted(set(tags))


# --- fetch full article text ---
def get_full_text(url):
    try:
        html = trafilatura.fetch_url(url)
        text = trafilatura.extract(html, include_comments=False)
        return text or ""
    except Exception:
        return ""

# --- selective filter ---
PRIORITY_TAGS = {"ransomware", "data breach", "vulnerability", "exploit", "phishing"}
IGNORE_PATTERNS = ["sponsored", "webinar", "partner", "product release"]

def is_relevant(text, tags):
    # high-value tags or matching important keywords
    if any(tag in PRIORITY_TAGS for tag in tags):
        return True
    if any(word in text for word in PRIORITY_TAGS):
        return True
    return False

def is_noise(text):
    return any(p in text for p in IGNORE_PATTERNS)

# --- summarization for skimming ---
def summarize_text(text):
    # simple and fast: first 2 sentences, limited to 300 chars
    lines = text.split(". ")
    summary = ". ".join(lines[:2]) if lines else ""
    return shorten(summary, width=300, placeholder="...")

# --- database insertion ---
def store_articles(articles):
    if not articles:
        print("No articles to store.")
        return

    conn = psycopg2.connect(
        dbname="cybernews",
        user="postgres",      # ← change
        password="postgres",  # ← change
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    query = """
        INSERT INTO articles (
            source, title, link, published_at, summary, content, digest_summary, tags
        )
        VALUES %s
        ON CONFLICT (link) DO NOTHING;
    """

    values = [
        (
            art["source"],
            art["title"],
            art["link"],
            art["published"],
            art["rss_summary"],       # original RSS summary
            art["content"],           # full scraped article text
            art["digest_summary"],    # skimmable short version
            art["tags"],              # tag list
        )
        for art in articles
    ]

    execute_values(cur, query, values)
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Stored {len(values)} new articles.")

# --- main selective fetcher ---
def selective_fetch():
    selected = []
    for source, url in FEEDS:
        print(f"Fetching {source}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title.strip()
            rss_summary = getattr(entry, "summary", "")
            link = entry.link
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])

            full_text = get_full_text(link)
            combined_text = (title + " " + rss_summary + " " + full_text).lower()
            tags = auto_tag(combined_text)

            if is_noise(combined_text):
                continue
            if not is_relevant(combined_text, tags):
                continue

            digest_summary = summarize_text(full_text or rss_summary)
            selected.append({
                "source": source,
                "title": title,
                "tags": tags,
                "link": link,
                "rss_summary": rss_summary,
                "content": full_text,
                "digest_summary": digest_summary,
                "published": published,
            })
            time.sleep(0.5)  # polite delay
    return selected

# --- run everything ---
if __name__ == "__main__":
    digest = selective_fetch()

    print("\n=== Daily Cyber Digest ===")
    for art in digest:
        print(f"[{', '.join(art['tags'])}] {art['title']} — {art['source']}")
        print(f"  {art['digest_summary']}")
        print(f"  {art['link']}\n")

    store_articles(digest)
    
    

