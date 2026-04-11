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

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20App-00D4AA?style=flat-square&logo=vercel&logoColor=white)](https://sentiment-dashboard-lac.vercel.app)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co)
[![Redis](https://img.shields.io/badge/Redis-Upstash-DC382D?style=flat-square&logo=redis&logoColor=white)](https://upstash.com)
[![License](https://img.shields.io/badge/License-MIT-00D4AA?style=flat-square)](LICENSE)

**[sentiment-dashboard-lac.vercel.app](https://sentiment-dashboard-lac.vercel.app)** · **[API Health](https://manavg1234567-sentiscope-api.hf.space/health)** · **[GitHub](https://github.com/manav363/sentiment-dashboard)**

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
- **Text** — paste any content up to 5,000 characters
- **URL** — paste a news article link; the backend scrapes, cleans, and chunks the body text automatically

---

## Deployment

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | https://sentiment-dashboard-lac.vercel.app |
| Backend API | HuggingFace Spaces (Docker) | https://manavg1234567-sentiscope-api.hf.space |
| Redis Cache | Upstash (REST API) | managed |

Zero cost. No credit card required.

---

## Tech stack

| Layer | Technology |
|---|---|
| ML Model | `cardiffnlp/twitter-roberta-base-sentiment-latest` (HuggingFace Transformers) |
| Backend | FastAPI 0.111 · Uvicorn · PyTorch (CPU) · Pydantic v2 |
| Caching | Upstash Redis REST API (async, graceful degradation) |
| Scraping | Trafilatura (primary) → httpx + BeautifulSoup4 (fallback) |
| Rate Limiting | SlowAPI — 30 req/min text · 10 req/min URL |
| Frontend | React 19 · TypeScript 5.4 · Vite 5 · Tailwind CSS 4 |
| State | TanStack React Query v5 · Axios · React Router v6 |
| Testing | pytest + pytest-asyncio (backend) · Vitest + Testing Library (frontend) |
| Infra | Docker · nginx reverse proxy · multi-stage builds · HuggingFace Spaces |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (Vercel)                                               │
│                                                                 │
│   Home (Text / URL tabs)                                        │
│       │  useMutation (React Query)                              │
│       ▼                                                         │
│   Axios client → VITE_API_BASE_URL                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTPS
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (HuggingFace Spaces — Docker)                          │
│  ├── BodySizeLimitMiddleware (64 KB cap)                        │
│  ├── CORSMiddleware (env-configured origins)                    │
│  ├── RequestIDMiddleware (X-Request-ID tracing)                 │
│  ├── SlowAPI rate limiter                                       │
│  │                                                              │
│  ├── POST /api/sentiment/analyze                                │
│  │     └── cache_service → Upstash Redis (SHA-256 key)         │
│  │           └── sentiment_engine                              │
│  │                 ├── text_preprocessor (clean + chunk)       │
│  │                 └── pipeline_loader (RoBERTa singleton)     │
│  │                                                              │
│  ├── POST /api/url/analyze                                      │
│  │     └── cache_service → Upstash Redis                       │
│  │           ├── scraper_service                               │
│  │           │     ├── SSRF validation (hostname + DNS check)  │
│  │           │     ├── trafilatura (primary)                   │
│  │           │     └── httpx + BS4 (fallback)                  │
│  │           └── sentiment_engine                              │
│  │                                                              │
│  └── GET /health (model + Redis status)                        │
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
    # Upstash uses stateless HTTP — no connection teardown needed
```

### Graceful Redis degradation
All cache operations are wrapped in try/except. If Upstash is unavailable, the app continues without caching — no `500` errors, no user-facing impact.

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
│           ├── cache_service.py         # Upstash Redis get/set with fallback
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
├── docker-compose.yml                   # Local dev: Redis + backend + frontend
└── .env.example
```

---

## API reference

### `GET /health`
Returns backend readiness. Polled by the frontend on load before enabling submissions.

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
  "result": { "label": "positive", "score": 0.874, "breakdown": [...] }
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
- Docker (for Redis)

### 1. Clone and configure

```bash
git clone https://github.com/manav363/sentiment-dashboard.git
cd sentiment-dashboard
cp .env.example backend/.env
```

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

> First startup downloads the RoBERTa model (~500 MB). Subsequent starts use the local cache.

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

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| Health check | http://localhost:8000/health |

---

## Tests

### Backend

```bash
cd backend && source .venv/bin/activate
pytest -v
```

| Test file | What it covers |
|---|---|
| `test_main.py` | Health endpoint, `X-Request-ID` presence and passthrough |
| `test_sentiment_engine.py` | Parallel chunk inference, semaphore concurrency, label ordering |
| `test_scraper_service.py` | SSRF blocking (localhost, private IPs, DNS-resolved privates), trafilatura → httpx fallback |
| `test_cache_service.py` | Redis failure resilience — no exception raised on connection error |
| `test_text_preprocessor.py` | `clean_text` HTML stripping, whitespace normalisation, truncation; `chunk_text` overlap and size bounds |
| `test_api_routes.py` | Full round-trip integration tests for both endpoints, 413 body limit, request ID echo |

### Frontend

```bash
cd frontend
npm run test
npm run build
npm run lint
```

---

## Security

| Area | Implementation |
|---|---|
| SSRF | Hostname blocklist + resolved IP validation (private, loopback, link-local, multicast, reserved) |
| CORS | Configurable via `ALLOWED_ORIGINS` env var — no wildcard `*` |
| Rate limiting | SlowAPI — 30/min text · 10/min URL |
| Body size | `BodySizeLimitMiddleware` — 64 KB hard cap, returns `413` |
| Input validation | Pydantic `min_length`, `max_length`, `HttpUrl` type enforcement |
| Container | Non-root user (`appuser`), multi-stage Docker builds |
| CSP | `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` via nginx |
| Secrets | `.env` gitignored, `.env.example` provided for all variables |

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `UPSTASH_REDIS_REST_URL` | — | Upstash Redis REST endpoint |
| `UPSTASH_REDIS_REST_TOKEN` | — | Upstash Redis REST token |
| `BACKEND_PORT` | `8000` | Uvicorn port |
| `ALLOWED_ORIGINS` | `["http://localhost:5173"]` | CORS allowed origins (JSON array) |
| `HF_TOKEN` | *(empty)* | HuggingFace token — only needed for gated models |

### Frontend

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend base URL (e.g. `https://your-space.hf.space`) — omit for local dev |

---

## Roadmap

- [ ] Twitter/X handle analysis (per-tweet sentiment + aggregate distribution)
- [ ] Batch file upload (CSV of texts → bulk classification)
- [ ] Confidence threshold alerts
- [ ] Export results as PDF report

---

<div align="center">

Built by [Manavgarg](https://github.com/manav363)

</div>