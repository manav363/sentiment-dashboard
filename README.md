<div align="center">

```
███████╗███████╗███╗   ██╗████████╗██╗███████╗ ██████╗ ██████╗ ██████╗ ███████╗
██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║██╔════╝██╔════╝██╔════╝██╔═══██╗██╔════╝
███████╗█████╗  ██╔██╗ ██║   ██║   ██║███████╗██║     ██║     ██║   ██║███████╗
╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║╚════██║██║     ██║     ██║   ██║╚════██║
███████║███████╗██║ ╚████║   ██║   ██║███████║╚██████╗╚██████╗╚██████╔╝███████║
╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
```

**Full-stack NLP sentiment dashboard — paste text or drop a URL, get instant AI-powered sentiment analysis.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![License](https://img.shields.io/badge/License-MIT-00D4AA?style=flat-square)](LICENSE)

</div>

---

## What it does

SentiScope runs your text or any article URL through a fine-tuned RoBERTa transformer and returns a **positive / neutral / negative** classification with per-class confidence scores — visualised in a real-time gauge and animated confidence bars. Results are cached server-side in Redis and persisted locally in browser history.

```
Input: "The product launch exceeded all expectations and customers are thrilled."

Output:
  ● Positive  ████████████████████  92.4%
  ○ Neutral   ██░░░░░░░░░░░░░░░░░░   5.9%
  ○ Negative  █░░░░░░░░░░░░░░░░░░░   1.7%
```

**Two input modes:**
- **Text** — paste any text up to 5,000 characters
- **URL** — paste a news article link; the backend scrapes, cleans, and chunks the body text automatically

---

## Tech stack

| Layer | Technology |
|---|---|
| ML Model | `cardiffnlp/twitter-roberta-base-sentiment-latest` (HuggingFace Transformers) |
| Backend | FastAPI 0.111 · Uvicorn · PyTorch (CPU) · Pydantic v2 |
| Caching | Redis 7 (async, graceful degradation if unavailable) |
| Scraping | Trafilatura (primary) → httpx + BeautifulSoup4 (fallback) |
| Rate Limiting | SlowAPI — 30 req/min text · 10 req/min URL |
| Frontend | React 19 · TypeScript 5.4 · Vite 5 · Tailwind CSS 4 |
| State | TanStack React Query v5 · Axios · React Router v6 |
| Testing | pytest + pytest-asyncio (backend) · Vitest + Testing Library (frontend) |
| Infra | Docker Compose · nginx reverse proxy · multi-stage builds |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                        │
│                                                                 │
│   Home (Text / URL tabs)                                        │
│       │  useMutation (React Query)                              │
│       ▼                                                         │
│   Axios client (/api proxy)                                     │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  nginx (prod) / Vite proxy (dev)                                │
│                        │                                        │
│                        ▼                                        │
│  FastAPI                                                        │
│  ├── BodySizeLimitMiddleware (64 KB cap)                        │
│  ├── CORSMiddleware (env-configured origins)                    │
│  ├── RequestIDMiddleware (X-Request-ID tracing)                 │
│  ├── SlowAPI rate limiter                                       │
│  │                                                              │
│  ├── POST /api/sentiment/analyze                                │
│  │     └── cache_service (Redis SHA-256 key)                   │
│  │           └── sentiment_engine                              │
│  │                 ├── text_preprocessor (clean + chunk)       │
│  │                 └── pipeline_loader (RoBERTa singleton)     │
│  │                                                              │
│  ├── POST /api/url/analyze                                      │
│  │     └── cache_service                                        │
│  │           ├── scraper_service                               │
│  │           │     ├── SSRF validation (hostname + DNS check)  │
│  │           │     ├── trafilatura (primary)                   │
│  │           │     └── httpx + BS4 (fallback)                  │
│  │           └── sentiment_engine                              │
│  │                                                              │
│  └── GET /health (model + Redis status)                        │
│                                                                 │
│  Infrastructure                                                 │
│  ├── Redis 7 Alpine (response cache, TTL 3600s)                │
│  └── HuggingFace Model Hub (downloaded once, volume-cached)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Engineering highlights

### Chunked inference with bounded concurrency
Long texts are split into 400-word overlapping chunks (50-word overlap) so each fits within the model's 512-token window. Chunks are processed concurrently with `asyncio.Semaphore(4)` to cap parallel threads, then scores are averaged across chunks.

```python
# sentiment_engine.py
async def _run_chunk(chunk: str, semaphore: asyncio.Semaphore) -> list[dict]:
    async with semaphore:
        return await asyncio.to_thread(get_pipeline(), chunk)

semaphore = asyncio.Semaphore(4)
results = await asyncio.gather(*[_run_chunk(c, semaphore) for c in chunks])
```

### SSRF protection on the URL scraper
URL submissions are validated against private/loopback/link-local IP ranges before any HTTP request is made — including DNS resolution to catch rebinding attempts.

```python
# scraper_service.py
async def _validate_url(url: str) -> None:
    hostname = urlparse(url).hostname
    if hostname in BLOCKED_HOSTNAMES:
        raise HTTPException(422, "URL target is not allowed")
    for _, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise HTTPException(422, "URL resolves to a private address")
```

### Singleton model loading with lifespan warm-up
The 500MB RoBERTa model loads once on startup in a background thread — not on the first request. This avoids a 10-second cold hit on the first user interaction.

```python
# main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(load_pipeline)   # warm up before accepting traffic
    yield
    redis = await get_redis()
    await redis.aclose()                     # clean shutdown
```

### Graceful Redis degradation
All cache operations are wrapped in try/except. If Redis is unavailable, the app continues without caching — no `500` errors, no user-facing impact.

### Request correlation
Every request carries an `X-Request-ID` — either echoed from the client header or auto-generated as a UUID — propagated through a `ContextVar` for structured log correlation.

---

## Project structure

```
sentiment-dashboard/
├── backend/
│   ├── main.py                          # App factory, lifespan, all middleware
│   ├── requirements.txt
│   ├── Dockerfile                       # Multi-stage build, non-root user
│   └── app/
│       ├── api/
│       │   ├── sentiment.py             # POST /api/sentiment/analyze
│       │   └── url_scraper.py           # POST /api/url/analyze
│       ├── core/
│       │   ├── config.py                # pydantic-settings (env vars)
│       │   ├── rate_limiter.py          # SlowAPI limiter
│       │   └── request_context.py       # X-Request-ID ContextVar
│       ├── ml/
│       │   ├── model_config.py          # Model name, chunk sizes, TTL constants
│       │   ├── pipeline_loader.py       # HuggingFace singleton loader
│       │   └── text_preprocessor.py    # HTML strip, normalise, chunk
│       ├── models/
│       │   ├── request.py               # Pydantic request schemas
│       │   └── response.py             # Pydantic response schemas
│       └── services/
│           ├── cache_service.py         # Redis get/set with fallback
│           ├── scraper_service.py       # SSRF-safe scraper (trafilatura + httpx)
│           └── sentiment_engine.py      # Chunked concurrent inference
│
├── frontend/
│   ├── Dockerfile                       # Multi-stage nginx production build
│   ├── nginx.conf                       # SPA routing + API proxy + CSP headers
│   └── src/
│       ├── api/                         # Axios client + typed API functions
│       ├── components/
│       │   ├── input/                   # TextInput, URLInput
│       │   ├── results/                 # SentimentGauge (SVG), ConfidenceBar
│       │   └── ui/                      # Button, Tabs, Loader, ErrorBanner, ErrorBoundary
│       ├── hooks/                       # useSentiment (React Query), useHistory (localStorage)
│       ├── pages/                       # Home, Results, History, NotFound
│       └── types/                       # TypeScript interfaces
│
├── docker-compose.yml                   # Redis + backend + frontend, healthchecks
└── .env.example
```

---

## API reference

### `GET /health`
Returns backend readiness. Polled by the frontend before enabling form submission.

```json
{
  "status": "ok",
  "model_loaded": true,
  "redis_connected": true
}
```

### `POST /api/sentiment/analyze`
Classifies plain text. Rate limited to 30 requests/minute.

**Request**
```json
{ "text": "The conference was well-organised and the talks were insightful." }
```

**Response**
```json
{
  "label": "positive",
  "score": 0.891,
  "breakdown": [
    { "label": "positive", "score": 0.891 },
    { "label": "neutral",  "score": 0.094 },
    { "label": "negative", "score": 0.015 }
  ],
  "text_preview": "The conference was well-organised and the talks..."
}
```

### `POST /api/url/analyze`
Scrapes an article URL, extracts body text, and classifies it. Rate limited to 10 requests/minute.

**Request**
```json
{ "url": "https://example.com/article" }
```

**Response**
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "chunk_count": 3,
  "result": { ...same shape as sentiment response... }
}
```

**Error responses**

| Status | Reason |
|---|---|
| `413` | Request body exceeds 64 KB |
| `422` | Validation failure (text too short, invalid URL, private IP target) |
| `429` | Rate limit exceeded |
| `503` | Model not yet loaded |

---

## Running locally

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (for Redis) or a local Redis instance

### 1. Clone and configure

```bash
git clone https://github.com/manav363/sentiment-dashboard.git
cd sentiment-dashboard
cp .env.example backend/.env
```

Edit `backend/.env` — the defaults work for local dev with no API keys required.

### 2. Start Redis

```bash
docker run -d --name sentiment-redis -p 6379:6379 redis:7-alpine
```

### 3. Start the backend

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> The first startup downloads the RoBERTa model (~500 MB). Subsequent starts use the cached model.

Verify readiness:
```bash
curl http://localhost:8000/health
# {"status":"ok","model_loaded":true,"redis_connected":true}
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Running with Docker Compose

Single command — spins up Redis, backend (with model warm-up health check), and nginx-fronted frontend:

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| Health check | http://localhost:8000/health |

The frontend container waits for the backend `service_healthy` condition before starting, so the UI is never served before the model is ready.

---

## Tests

### Backend

```bash
cd backend
source .venv/bin/activate
pytest -v
```

| Test file | What it covers |
|---|---|
| `test_main.py` | Health endpoint, `X-Request-ID` header presence and passthrough |
| `test_sentiment_engine.py` | Parallel chunk inference, semaphore concurrency, label ordering |
| `test_scraper_service.py` | SSRF blocking (localhost, private IPs, DNS-resolved privates), trafilatura → httpx fallback |
| `test_cache_service.py` | Redis failure resilience — no exception raised on connection error |
| `test_text_preprocessor.py` | `clean_text` HTML stripping, whitespace normalisation, truncation; `chunk_text` overlap and size bounds |
| `test_api_routes.py` | Full round-trip integration tests for both endpoints, 413 body limit, request ID echo |

### Frontend

```bash
cd frontend
npm run test
npm run build   # type-check + bundle
npm run lint
```

---

## Security

| Area | Implementation |
|---|---|
| SSRF | Hostname blocklist + resolved IP validation (private, loopback, link-local, multicast, reserved ranges) |
| CORS | Configurable via `ALLOWED_ORIGINS` env var — no wildcard `*` |
| Rate limiting | SlowAPI — 30/min text · 10/min URL |
| Body size | `BodySizeLimitMiddleware` — 64 KB hard cap, returns `413` |
| Input validation | Pydantic `min_length`, `max_length`, `HttpUrl` type enforcement |
| Container | Non-root user (`appuser`) in backend container, multi-stage builds |
| CSP | `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` via nginx |
| Secrets | `.env` gitignored, `.env.example` provided for all variables |

---

## Environment variables

All variables go in `backend/.env`. Copy from `.env.example` to get started.

| Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `BACKEND_PORT` | `8000` | Uvicorn port |
| `ALLOWED_ORIGINS` | `["http://localhost:5173"]` | CORS allowed origins (JSON array) |
| `HF_TOKEN` | *(empty)* | HuggingFace token — only needed for gated models |

---

## Roadmap

- [ ] Batch file upload (CSV of texts → bulk classification)
- [ ] Confidence threshold alerts ("flag anything below 70% confidence")
- [ ] Export results as PDF report
- [ ] Deploy to Railway / Render with persistent model volume

---

<div align="center">

Built by [Manavgarg](https://github.com/manav363)

</div>
