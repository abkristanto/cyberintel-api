# 🛰️ Cyberintel API

This API is used for crawling popular cybersecurity websites' RSS feeds and scraping content to provide the most updated news to the **Cyberintel Dashboard**.  
It is built using **FastAPI** and performs **keyword-based tagging** on article content to automatically classify news by topic (e.g., ransomware, phishing, AI).  

The script is scheduled to **run weekly** using **APScheduler**, automatically fetching and storing the latest cybersecurity news into a PostgreSQL database.

---

## ⚙️ Tech Stack

- **FastAPI** — RESTful API framework  
- **PostgreSQL** — Database backend  
- **psycopg2** — PostgreSQL driver  
- **CORS Middleware** — Enables frontend access (e.g., Vite app)  
- **APScheduler** — Automates weekly data fetching from RSS feeds  

---

## 🗄️ Database Connection

All endpoints connect to the PostgreSQL database using the following configuration:

```python
DB_CONFIG = {
    "dbname": "cybernews",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
}
```

## Usage

Start the FastAPI app locally:

`uvicorn api:app --reload --port 8080`


Then open:

http://localhost:8000/docs

to access the interactive Swagger UI for testing endpoints.