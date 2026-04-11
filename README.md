# SentiScope

Full-stack sentiment analysis dashboard built with FastAPI, Hugging Face Transformers, Redis, React, and Tailwind CSS.

SentiScope lets a user paste text or submit an article URL, then returns a sentiment classification with confidence breakdowns in a polished dashboard UI. The project is designed as a production-style monorepo with backend security hardening, frontend resilience, API validation, automated tests, and Docker support.

## Why This Project

This project was built to demonstrate:

- end-to-end product thinking across backend, frontend, and deployment
- applied NLP integration using a real transformer model
- secure URL ingestion with SSRF protection and request tracing
- practical production concerns like caching, health checks, Dockerization, and error handling
- clean TypeScript + Python code backed by automated tests

## Core Features

- Analyze free-form text as positive, neutral, or negative
- Scrape article content from a URL and analyze the extracted body text
- Show confidence breakdowns for all sentiment classes
- Support long-text chunking with aggregated inference
- Cache repeated analysis requests in Redis
- Persist the latest result across refresh and store history locally
- Expose health/readiness information for the backend service

## Tech Stack

### Backend

- FastAPI
- Hugging Face Transformers
- PyTorch
- Redis
- SlowAPI
- Trafilatura
- HTTPX
- BeautifulSoup4
- Pytest + Ruff

### Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS v4
- React Query
- Axios
- React Router
- Vitest + Testing Library

## Architecture Overview

```text
Frontend (React + Vite)
        |
        v
FastAPI API
  |- /api/sentiment/analyze
  |- /api/url/analyze
  |- /health
        |
        +--> Hugging Face sentiment pipeline
        +--> Redis cache
        +--> URL scraper (Trafilatura -> HTTPX fallback)
```

## Project Structure

```text
sentiment-dashboard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── ml/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## Engineering Notes

### Backend

- Uses `cardiffnlp/twitter-roberta-base-sentiment-latest` for classification
- Loads the model once and reuses it across requests
- Splits long text into overlapping chunks and averages scores
- Adds request correlation IDs via `X-Request-ID`
- Guards URL scraping against localhost/private-network access
- Falls back gracefully when Redis or primary extraction is unavailable

### Frontend

- Built as a responsive single-page app
- Preserves the latest result after refresh using session storage
- Stores previous analyses in local history
- Includes an app-level error boundary for safer recovery
- Keeps routing lightweight and client-side

## API Summary

### `GET /health`

Returns backend readiness and cache connectivity:

```json
{
  "status": "ok",
  "model_loaded": true,
  "redis_connected": true
}
```

### `POST /api/sentiment/analyze`

Request:

```json
{
  "text": "The product launch went smoothly and customers responded positively."
}
```

### `POST /api/url/analyze`

Request:

```json
{
  "url": "https://example.com/article"
}
```

## Environment Variables

Create `backend/.env` from the root template:

```bash
cp .env.example backend/.env
```

Example:

```env
HF_TOKEN=your_hf_token_here
REDIS_URL=redis://localhost:6379
BACKEND_PORT=8000
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

## Run Locally

### Prerequisites

- Python 3.11
- Node.js 20+
- npm
- Redis

### 1. Start Redis

```bash
docker run -d --name sentiment-redis -p 6379:6379 redis:7-alpine
```

If the container already exists:

```bash
docker start sentiment-redis
```

### 2. Start the Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

### 3. Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

App URL:

- [http://localhost:5173](http://localhost:5173)

## Run with Docker Compose

```bash
docker-compose up --build
```

Services:

- Frontend: [http://localhost](http://localhost)
- Backend: [http://localhost:8000](http://localhost:8000)
- Redis: `localhost:6379`

## Testing

### Backend

```bash
cd backend
source .venv/bin/activate
python -m pytest
python -m ruff check .
```

### Frontend

```bash
cd frontend
npm run lint
npm run test
npm run build
```

## Production Readiness

- Non-root backend container
- nginx-based frontend container with SPA routing
- Security headers configured at the frontend proxy layer
- Health checks for backend readiness
- Configurable CORS origins
- Redis connection cleanup on shutdown
- API-level request size limits

## Portfolio Value

SentiScope is a strong showcase project because it demonstrates more than just UI work or model integration in isolation. It shows the full path from user input to inference, caching, secure scraping, API design, resilient client behavior, test coverage, and deployable infrastructure.

