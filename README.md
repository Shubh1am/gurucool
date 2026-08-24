# Ghar Ka Guru — Phase 1 Text RAG Sandbox

Ghar Ka Guru is an AI-powered academic tutor and parent-mentorship platform focused on rural Indian students preparing for competitive exams (UPSC/IAS, NEET, JEE). This repository contains a production-minded Phase 1 implementation: a text-first Chat & Syllabus RAG sandbox built with FastAPI, Pinecone, OpenAI embeddings, and a Streamlit UI for quick experimentation.

**Architectural Vision (two-tier)**
- Student tier: Adaptive tutoring (text-first in Phase 1), planned voice loop in Phase 2.
- Parent tier: Syllabus ingestion, automated timetable generation, and analytics logging.

**Phased Roadmap**
- Phase 1 (this repo): Text-first RAG sandbox with PDF syllabus ingestion, vector search in Pinecone, and localized, analogy-driven system prompts.
- Phase 2 (blueprint): Low-latency bidirectional audio streaming using Sarvam AI (saaras STT + bulbul TTS), client VAD, and WebSocket loops for natural voice tutoring.
- Phase 3 (integrations): Alexa Custom Skill webhook to expose the tutor via Amazon Alexa as an optional secondary voice channel.

**Why this matters for rural India**
- Localized analogies: Lessons framed with village-life imagery (farming, irrigation canals, markets) increase comprehension and retention for rural learners.
- Low-bandwidth readiness: Text-first architecture keeps Phase 1 lightweight and accessible over common mobile networks.
- Parent involvement: Structured timetables and progress logs help guardians support students who may not be in formal coaching.

**Repository Contents**
- `main.py` — FastAPI backend with endpoints:
  - `POST /api/v1/ingest-syllabus` — ingest PDFs, chunk text, create embeddings (OpenAI), and upsert into Pinecone with `student_id` metadata.
  - `POST /api/v1/chat` — metadata-filtered similarity search + system prompt orchestration + LLM answer generation.
  - `POST /api/v1/generate-timetable` — simple weekly micro-roadmap generator for planning study time.
- `ui.py` — Streamlit sandbox app for quick testing (upload PDFs, generate timetables, chat with the tutor).
- `database.py` & `models.py` — SQLModel/Postgres schemas for student profiles, syllabus nodes, timetables, and parent analytics logs (JSONB fields).
- `Dockerfile`, `docker-compose.yml` — multi-service compose with Postgres, FastAPI backend, and Streamlit UI for local development.
- `requirements.txt`, `.env.example`, `.gitignore` — environment and dependency references.

**Security & Compliance Notes**
- Keep API keys out of source control; copy `.env.example` to `.env` and fill values.
- Data residency: Using Pinecone and OpenAI implies cloud-hosted vector and LLM services. For production deployments in India, evaluate data residency requirements and pick compliant regions/providers.

Getting Started — Phase 1 (local development)

1) Prerequisites
- Docker & Docker Compose
- A Pinecone account and API key
- An OpenAI API key

2) Copy env and configure

```bash
cp .env.example .env
# Edit .env and add your keys
```

3) Start services with Docker Compose

```bash
docker compose up --build
```

4) Access
- FastAPI docs: http://localhost:8000/docs
- Streamlit sandbox UI: http://localhost:8501

Kubernetes (optional/staging)
--------------------------------
This repo keeps `docker-compose.yml` as the local developer workflow and adds a `k8s/` folder with template manifests for staging/cluster deployments. The `k8s/` manifests include:

- `namespace.yaml` — creates `gharuka-guru` namespace
- `secret-env.yaml` — template Kubernetes Secret for `OPENAI_API_KEY`, `PINECONE_API_KEY`, and DB password (replace values before apply)
- `configmap.yaml` — non-sensitive config values
- `postgres-statefulset.yaml` — Postgres StatefulSet with PVC
- `backend-deployment.yaml` + `backend-service.yaml`
- `ui-deployment.yaml` + `ui-service.yaml`
- `ingress.yaml` — example ingress (NGINX) routing to the UI

Notes:
- Replace image placeholders `ghcr.io/<yourorg>/...` with images you build and push to your container registry before applying manifests.
- For local k8s testing use `kind` or `minikube` and enable an ingress controller if you use the example `ingress.yaml`.
- Apply manifests:

```bash
kubectl apply -f gurucool/k8s/namespace.yaml
kubectl apply -f gurucool/k8s/secret-env.yaml
kubectl apply -f gurucool/k8s/configmap.yaml
kubectl apply -f gurucool/k8s/postgres-statefulset.yaml
kubectl apply -f gurucool/k8s/backend-deployment.yaml
kubectl apply -f gurucool/k8s/backend-service.yaml
kubectl apply -f gurucool/k8s/ui-deployment.yaml
kubectl apply -f gurucool/k8s/ui-service.yaml
kubectl apply -f gurucool/k8s/ingress.yaml
```

Keep `docker-compose.yml` for local dev and use the `k8s/` folder for staging or production deployments.

Component Details — Phase 1 Implementation Notes

1) Syllabus ingestion (`/api/v1/ingest-syllabus`)
- PDF parsing: `PyMuPDF` (`fitz`) extracts page text.
- Chunking: text is split into ~2048-character chunks with overlap to approximate 512-token nodes.
- Embeddings: OpenAI embedding API (`text-embedding-3-small`).
- Vector store: Pinecone index; each vector is stored with `student_id` metadata to scope retrieval per student.

2) Chat flow (`/api/v1/chat`)
- Query embedding → Pinecone metadata-filtered similarity search (student-scoped) → assemble context snippets → construct system prompt that instructs the LLM to use rural/village analogies and local language → call OpenAI ChatCompletion to produce localized answers.

3) Timetable generation (`/api/v1/generate-timetable`)
- A simple, explainable algorithm creates a weekly micro-plan. In Phase 2/3 this will be replaced with a syllabus-aware planner that maps topics to calendar slots and parent notifications.

Phase 2 Blueprint — Real-time Voice Loop (high level)
- Replace text input/output with a bidirectional low-latency WebSocket stream.
- Client side: lightweight VAD, capture audio chunks, and send compressed audio frames.
- Server side: Sarvam AI (saaras STT) consumes audio frames → transcribes to text → uses the Phase 1 RAG pipeline to produce a response → bulbul TTS generates audio → stream audio frames back to the client.
- Add conversational state management and incremental partial responses for natural turn-taking.

Phase 3 Blueprint — Alexa Integration (high level)
- Expose a webhook endpoint following Alexa's request/response schema.
- Map Alexa intents to the Phase 1 endpoints (ingest, chat, timetable).
- Implement authentication layer and parental consent workflow for voice access.

Developer Notes
- Local DB: `docker-compose.yml` brings up a Postgres container at `db:5432` with the default `DATABASE_URL` from `.env`.
- DB schema: `database.create_db_and_tables()` exists to initialize SQLModel tables; in production integrate Alembic for migrations.
- Embeddings: this repo stores chunk text as metadata in Pinecone for convenience; for large scale store canonical source in Postgres/S3 and keep small metadata in the vector store.

Troubleshooting
- Pinecone index creation: the backend attempts to create the configured index if it does not exist. Ensure the key and environment have access.
- Timeouts: large PDF ingest may take time—use increased timeouts and monitor resource usage.

Next Steps / Suggested Improvements
- Phase 1 stability: add batching, retries, and background ingestion worker (Celery/RQ) for large files.
- Add user authentication, encryption at rest, and role-based access for parents vs students.
- Phase 2: implement the WebSocket audio loop, client-side PWA with native mic access, and offline caching of syllabus content.

Git: initialize and push

```bash
git init
git add .
git commit -m "chore: initial Phase 1 Ghar Ka Guru text RAG sandbox"
git branch -M main
# create repo on GitHub then push (replace URL)
git remote add origin git@github.com:youruser/ghar-ka-guru.git
git push -u origin main
```

If you'd like, I can:
- run a Docker Compose up locally and validate the services,
- wire a small sample PDF and demonstrate an end-to-end ingest + chat session,
- or extend the timetable generator to be syllabus-aware using the indexed nodes.
