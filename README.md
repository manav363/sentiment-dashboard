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

[![CI](https://img.shields.io/github/actions/workflow/status/manav363/sentiment-dashboard/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/manav363/sentiment-dashboard/actions/workflows/ci.yml)
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

SentiScope runs your text or any article URL through a pretrained RoBERTa sentiment model ([`cardiffnlp/twitter-roberta-base-sentiment-latest`](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest), used as published, not trained here) and returns a **positive / neutral / negative** classification with per-class confidence scores, shown in a gauge and confidence bars. Results can be cached server-side in Upstash Redis (optional) and are kept in the browser's local history.

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
| Scraping | httpx (redirect-validated fetch) → Trafilatura (primary) / BeautifulSoup4 (fallback) extraction |
| Rate Limiting | SlowAPI — 30 req/min text · 10 req/min URL |
| Frontend | React 19 · TypeScript 5.4 · Vite 5 · Tailwind CSS 4 |
| State | TanStack React Query v5 · Axios · React Router v6 |
| Testing / CI | pytest + pytest-asyncio (backend) · Vitest + Testing Library (frontend) · GitHub Actions (lint, tests, build, dependency audit) |
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
│  │           │     ├── fetch (SSRF check on every redirect hop)│
│  │           │     ├── trafilatura extract (primary)           │
│  │           │     └── BeautifulSoup4 (fallback)               │
│  │           └── sentiment_engine                              │
│  │                                                              │
│  └── GET /health (model + Redis status)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Engineering highlights

### Chunked inference with bounded concurrency
Long texts are split into 400-word overlapping chunks (50-word overlap), which keeps each chunk near the model's 512-token window; the pipeline is called with `truncation=True` so a chunk that tokenizes slightly longer is cut rather than rejected. Chunks are processed concurrently with `asyncio.Semaphore(4)` to cap parallel threads, then scores are averaged across chunks.

```python
# sentiment_engine.py
async def _run_chunk(chunk: str, semaphore: asyncio.Semaphore) -> list[dict]:
    async with semaphore:
        return await asyncio.to_thread(get_pipeline(), chunk, truncation=True, max_length=512)

semaphore = asyncio.Semaphore(4)
results = await asyncio.gather(*[_run_chunk(c, semaphore) for c in chunks])
```

### SSRF protection on the URL scraper
A URL-fetching endpoint can be turned into a way to reach internal services, so every URL is checked before it is fetched: scheme must be http(s), `localhost` names are refused, and the hostname is resolved and rejected if any address is private, loopback, link-local, multicast, reserved or unspecified.

Checking only the URL the user typed is not enough, because a public page can answer `302 Location: http://169.254.169.254/...`. Redirects are therefore followed by hand and **each hop is validated again** (capped at 5):

```python
# scraper_service.py
for _ in range(MAX_REDIRECTS + 1):
    await validate_public_url(current)
    response = await client.get(current, headers={"User-Agent": USER_AGENT})
    if not response.is_redirect:
        response.raise_for_status()
        return response.text
    current = str(response.url.join(response.headers["location"]))
```

This was a real bug that the project originally had (the client followed redirects automatically). It is now covered by tests that serve a redirect to the cloud-metadata address and to `localhost` and assert the internal URL is never requested. One gap remains and is listed under [Known limitations](#known-limitations).

### Singleton model loading with lifespan warm-up
The ~500 MB RoBERTa model is loaded once at startup, in a worker thread so the event loop is not blocked, and the server only starts accepting traffic after it is ready. The first user request therefore never pays the model-load cost.

```python
# main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(load_pipeline)   # finish loading before accepting traffic
    yield
    # Upstash uses stateless HTTP — no connection teardown needed
```

### Graceful Redis degradation
The cache is optional by design. With no Upstash credentials, or if Upstash is unreachable, cache reads and writes quietly become no-ops and `/health` reports `redis_connected: false`; requests are still served, just uncached. `tests/test_cache_service.py` covers both the failing-backend and the no-credentials cases.

### Request correlation
Every request carries an `X-Request-ID` — either echoed from the client header or auto-generated as a UUID — propagated through a `ContextVar` for structured log correlation.

---

## Project structure

```
sentiment-dashboard/
├── backend/
│   ├── main.py                          # App factory, lifespan, all middleware
│   ├── requirements.txt                 # Runtime dependencies (pinned)
│   ├── requirements-dev.txt             # pytest, ruff
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
├── .github/workflows/ci.yml             # Lint, tests, build, dependency audit
├── docker-compose.yml                   # Local dev: backend + frontend
├── LICENSE
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
- *(Optional)* a free [Upstash](https://upstash.com) Redis database, for response caching

### 1. Clone and configure

```bash
git clone https://github.com/manav363/sentiment-dashboard.git
cd sentiment-dashboard
cp .env.example backend/.env
```

### 2. (Optional) Enable caching

Put your Upstash REST URL and token in `backend/.env` (`UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`). Skip this step and the app runs without a cache.

### 3. Start the backend

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> First startup downloads the RoBERTa model (~500 MB). Subsequent starts use the local cache.

```bash
curl http://localhost:8000/health
# {"status":"ok","model_loaded":true,"redis_connected":false}   # true once Upstash is configured
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
cp .env.example backend/.env
docker compose up --build
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
pytest -v        # or `python -m pytest` from the repo root
```

| Test file | What it covers |
|---|---|
| `test_main.py` | Health endpoint, `X-Request-ID` presence and passthrough |
| `test_sentiment_engine.py` | Parallel chunk inference, semaphore concurrency, label ordering |
| `test_scraper_service.py` | SSRF blocking (localhost, private IPs, DNS-resolved privates), redirects into internal addresses refused, redirect loops cut off, trafilatura → BeautifulSoup fallback |
| `test_cache_service.py` | Cache is optional: failing backend and missing credentials both degrade to "no cache"; normal set/get round trip |
| `test_text_preprocessor.py` | `clean_text` HTML stripping, whitespace normalisation, truncation; `chunk_text` overlap and size bounds |
| `test_api_routes.py` | Full round-trip integration tests for both endpoints, 413 body limit, request ID echo |

### Frontend

```bash
cd frontend
npm run test
npm run build
npm run lint
```

GitHub Actions runs backend lint and tests, frontend lint, tests and build, and a dependency audit on every push and pull request.

---

## Security

| Area | Implementation |
|---|---|
| SSRF | Hostname blocklist + resolved-IP validation (private, loopback, link-local, multicast, reserved), re-applied to every redirect hop |
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
| `UPSTASH_REDIS_REST_URL` | *(empty)* | Upstash Redis REST endpoint — leave empty to disable caching |
| `UPSTASH_REDIS_REST_TOKEN` | *(empty)* | Upstash Redis REST token |
| `BACKEND_PORT` | `8000` | Uvicorn port |
| `ALLOWED_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | CORS allowed origins (JSON array) |
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

## Known limitations

- **The model is not tuned for this use and is not evaluated here.** It is a third-party model trained on tweets, and this repository contains no accuracy benchmark. News articles are a different kind of text, so treat results as indicative rather than measured.
- **One label per article.** URL mode splits the text into chunks and averages their scores, which hides mixed sentiment inside a single article.
- **DNS rebinding is not fully closed.** The scraper validates the resolved addresses, but the HTTP client resolves the name again when it connects. Closing that race means pinning the validated IP for the connection, or filtering egress at the network level.
- **Rate limiting is per process and per client address.** SlowAPI keeps counters in memory and keys on the address the app sees, so it does not coordinate across several instances, and behind a reverse proxy it needs forwarded-header handling to tell clients apart.
- **Known dependency advisories in the ML stack.** As of October 2026, `pip-audit` reports 20 advisories against the pinned `torch==2.3.0` and 26 against `transformers==4.40.0`. They were not upgraded because the fixes land in much newer releases and the model's behaviour would need to be re-checked against them (download access to the model was not available while preparing this change). CI audits every other dependency and fails on findings, but excludes these two. On the frontend, `react-router` 6.x has moderate advisories whose fix is the v7 major upgrade.

---

## How this was built

SentiScope was built with AI coding assistance (Claude). The behaviour described above is covered by the backend and frontend test suites, which CI runs on every push, and the limitations listed here are the ones found while auditing the code before publishing this version.

## License

[MIT](LICENSE)

---

<div align="center">

Built by [Manav Garg](https://github.com/manav363)

</div>
