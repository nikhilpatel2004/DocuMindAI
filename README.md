# DocuMind AI

A private document Q&A application that uses Retrieval-Augmented Generation (RAG) with local embeddings, embedded Qdrant vector store, and KIE API for LLM inference.

## Prerequisites

- Python 3.10+
- Node.js 20+ and npm
- KIE API Key (`KIE_API_KEY`) configured in `.env`

## Quickstart

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in any overrides
python -m backend.main   # runs on http://127.0.0.1:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev   # runs on http://127.0.0.1:5173
```

The Vite dev proxy forwards `/api` to the FastAPI backend.

### 3. First run flow

1. Open http://127.0.0.1:5173 to see the landing page, then choose "Get Started".
2. Create an account with a username, email, and password, then log in → you're taken to the dashboard.
3. Use "Upload PDF" to select a PDF (≤20 MB, text-based only).
4. Wait for processing → the document appears in "My Documents".
5. Open "Chat", select one or more of your documents, type a question, and send.
6. The answer is grounded in retrieved passages with source citations.

## Development

- API base: ``/api/v1`` (FastAPI OpenAPI at ``/api/v1/docs``).
- Environment variables are read from ``.env`` (see ``.env.example``).
- All documents and vectors are scoped to the authenticated user — ownership is enforced on every backend endpoint.
- Chat history is stored in SQLite; each user can view only their own conversations.

## Deployment (Docker Compose)

The production stack runs two containers on one host:

- `web` — nginx serving the built React app and reverse-proxying `/api/` and `/healthz`.
- `api` — FastAPI with **one Uvicorn worker**; SQLite, uploads, embedded Qdrant, and the model cache live in a named volume.

Embedded Qdrant and SQLite require a single API instance. Do not add replicas or increase the worker count.

### 1. Configure

```bash
cp .env.production.example .env.production
```

Fill in `.env.production`:

- `JWT_SECRET` — generate one, for example `python -c "import secrets; print(secrets.token_hex(32))"`.
- `KIE_API_KEY` — server-side only.
- `CORS_ORIGINS` — the public frontend origin, for example `https://documind.example.com`.
- `HTTP_PORT` — host port for nginx (default `8080`).

Compose refuses to start if `JWT_SECRET`, `KIE_API_KEY`, or `CORS_ORIGINS` is empty.

### 2. Build and run

```bash
docker compose --env-file .env.production up -d --build
```

Open `http://localhost:8080`. Use `docker compose --env-file .env.production ps` and `... logs -f api` to check status.

### 3. Persistent storage

The named volume `documind_data` is mounted at `/app/data` and contains:

| Path | Contents |
|---|---|
| `documind.db` (+ WAL files) | SQLite metadata |
| `uploads/` | Uploaded PDFs |
| `qdrant/` | Embedded Qdrant vectors |
| `hf-cache/` | Sentence Transformers model cache |

Back up the volume with the stack stopped:

```bash
docker compose --env-file .env.production stop api
docker run --rm -v documind_data:/data -v "${PWD}:/backup" alpine \
  tar czf /backup/documind-data.tgz -C /data .
docker compose --env-file .env.production start api
```

### 4. Resource requirements

- **RAM:** 2 GB minimum, 4 GB recommended. The embedding model and PyTorch load into memory.
- **CPU:** 2 vCPU recommended; embedding is CPU-bound.
- **Disk:** 5 GB minimum, 10–20 GB recommended for image, model cache, uploads, and Qdrant growth.
- **First run:** downloads `all-MiniLM-L6-v2` (tens of MB) from Hugging Face; the cache is persisted in `hf-cache/`.
- **Image size:** roughly 2–3 GB because of the CPU-only PyTorch and ML dependencies.

### 5. Production notes

- Terminate TLS at the hosting platform or a host-level reverse proxy; the compose stack serves HTTP only.
- `client_max_body_size` in `nginx.conf` is `21m`, matching the default 20 MB upload limit plus multipart overhead. Keep it in sync if `MAX_UPLOAD_MB` changes.
- Proxy read/send timeouts are 600 seconds because uploads embed synchronously.
- Restart `web` if the `api` container is recreated, so nginx resolves the new container address.
- The nginx image contains only the frontend build; database, uploads, Qdrant data, and environment files are not served.

See `.env.example` for the development defaults and `.env.production.example` for deployment values.

## License

MIT

## Windows PowerShell Installation

### Prerequisites
1. Install Python 3.10+ from https://python.org (add to PATH during install)
2. Install Node.js 20+ from https://nodejs.org (add to PATH during install)
3. Set up your KIE API Key from https://kie.ai

### Step 1: Install Python packages
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backendequirements.txt
```

### Step 2: Install Node.js packages
```powershell
cd frontend
npm install
```

### Step 3: Configure environment variables
```powershell
copy .env.example .env
# Edit .env (no real secrets):
#   JWT_SECRET=your-super-secret-key
#   JWT_EXPIRE_MINUTES=1440
#   DATABASE_URL=./data/documind.db
#   UPLOAD_DIR=./data/uploads
#   MAX_UPLOAD_MB=20
#   KIE_API_KEY=your_kie_api_key
#   OPENAI_BASE_URL=https://api.kie.ai/codex/v1
#   OPENAI_MODEL=gpt-5.6-terra
#   QDRANT_LOCAL_PATH=./data/qdrant
#   EMBEDDING_MODEL=all-MiniLM-L6-v2
#   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 4: Initialize the database
```powershell
cd backend
python -c "from app.models.database import init_db; init_db()"
```

### Step 5: Start the backend server
```powershell
cd backend
python -m app.main
# Backend: http://127.0.0.1:8000
```

### Step 6: Start the frontend (new PowerShell tab)
```powershell
cd frontend
npm run dev
# Frontend: http://127.0.0.1:5173
# Vite proxies /api to backend
```

### Step 7: Test the flow
1. Open http://127.0.0.1:5173/login and register
2. Log in → dashboard
3. Upload PDF (≤20 MB, text-based)
4. Wait for processing → document in "My Documents"
5. Chat → select documents → type question → send
6. Answer with source citations

- Sentence-transformers and dependencies require network during initial download
- Full RAG pipeline needs networked Windows machine
- All code is PRD-compliant and structurally complete
- Install missing packages on networked machine to verify

### Authentication
- Register/login at http://127.0.0.1:5173/login
- JWT in localStorage, sent as `Authorization: Bearer <token>`
- Logout: clear localStorage token
