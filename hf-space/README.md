---
title: DocuMind AI API
emoji: 📚
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
---

# DocuMind AI API

FastAPI backend for the DocuMind AI app (RAG over uploaded PDFs).

This Space builds the backend straight from the GitHub repo
`nikhilpatel2004/DocuMindAI` at image build time, so `main` is the single
source of truth.

Required Space secrets:

- `KIE_API_KEY` — LLM API key
- `JWT_SECRET` — long random string
- `CORS_ORIGINS` — comma-separated frontend origins, e.g. `https://documindai-7va9.onrender.com`

Storage inside the Space is ephemeral: SQLite, Qdrant and uploads live under
`/app/data` and reset when the Space restarts.
