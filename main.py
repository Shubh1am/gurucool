import os
import io
import asyncio
from typing import List, Optional

import pymupdf as fitz
from database import create_db_and_tables
from pinecone import Pinecone
import openai
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-west1-gcp")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ghar-ka-guru-index")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required in environment")
openai.api_key = OPENAI_API_KEY

if not PINECONE_API_KEY:
    raise RuntimeError("PINECONE_API_KEY is required in environment")

# Initialize Pinecone client (v3+)
pc = Pinecone(api_key=PINECONE_API_KEY)

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

# ensure index exists (v3 client)
existing_indexes = pc.list_indexes()
if PINECONE_INDEX_NAME not in existing_indexes:
    pc.create_index(name=PINECONE_INDEX_NAME, dimension=EMBED_DIM)

# Get index handle
index = pc.Index(PINECONE_INDEX_NAME)

app = FastAPI(title="Ghar Ka Guru - Phase 1 Text RAG Sandbox")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB tables exist on startup (best-effort)
try:
    create_db_and_tables()
except Exception:
    pass


class IngestResponse(BaseModel):
    ingested_chunks: int


class ChatQuery(BaseModel):
    student_id: str
    target_exam: str
    language: str = "English"
    query_text: str


class TimetableRequest(BaseModel):
    student_id: str
    baseline_hours_per_week: int
    prep_weeks: int
    target_exam: Optional[str] = None


def chunk_text(text: str, chunk_size_chars: int = 2048, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size_chars, length)
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


async def embed_texts(texts: List[str]) -> List[List[float]]:
    loop = asyncio.get_event_loop()

    def sync_embed(ts):
        resp = openai.Embedding.create(input=ts, model=EMBED_MODEL)
        return [r["embedding"] for r in resp["data"]]

    return await loop.run_in_executor(None, sync_embed, texts)


@app.post("/api/v1/ingest-syllabus", response_model=IngestResponse)
async def ingest_syllabus(student_id: str, file: UploadFile = File(...)):
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    data = await file.read()
    doc = fitz.open(stream=data, filetype="pdf")
    full_text = []
    for page in doc:
        try:
            txt = page.get_text()
        except Exception:
            txt = ""
        if txt:
            full_text.append(txt)
    text = "\n\n".join(full_text)
    if not text.strip():
        raise HTTPException(status_code=400, detail="PDF contained no extractable text")

    chunks = chunk_text(text, chunk_size_chars=2048, overlap=256)
    embeddings = await embed_texts(chunks)

    # prepare upsert
    records = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        uid = f"{student_id}::syllabus::{i}"
        meta = {"student_id": student_id, "source": "syllabus_pdf", "chunk_index": i, "chunk_text": chunk}
        records.append((uid, emb, meta))

    # Pinecone accepts batches
    batch_size = 50
    for i in range(0, len(records), batch_size):
        to_upsert = records[i : i + batch_size]
        index.upsert(vectors=[{"id": r[0], "values": r[1], "metadata": r[2]} for r in to_upsert])

    return {"ingested_chunks": len(chunks)}


def build_system_prompt(target_exam: str, language: str) -> str:
    prompt = (
        "You are Ghar Ka Guru, an empathetic academic tutor for rural Indian students preparing for "
        f"{target_exam}. Use simple, practical analogies drawn from village life (farming, markets, canals, cycles) "
        "and avoid jargon. Provide step-by-step answers, small practice tasks, and quick memory aids. "
    )
    if language.lower() != "english":
        prompt += f"Respond in {language}."
    return prompt


@app.post("/api/v1/chat")
async def chat(q: ChatQuery):
    # embed the query
    q_emb = (await embed_texts([q.query_text]))[0]

    # similarity search filtered by student_id
    try:
        res = index.query(vector=q_emb, top_k=5, include_metadata=True, include_values=False, filter={"student_id": {"$eq": q.student_id}})
    except Exception:
        # fallback: search without filter
        res = index.query(vector=q_emb, top_k=5, include_metadata=True, include_values=False)

    contexts = []
    matches = res.get("matches") if isinstance(res, dict) else (res.matches if hasattr(res, 'matches') else [])
    ids = []
    for m in matches:
        if isinstance(m, dict):
            meta = m.get("metadata", {})
            ids.append(m.get("id"))
            contexts.append(meta.get("chunk_text", ""))
        else:
            ids.append(m.id)

    retrieved_texts = contexts

    # assemble prompt for LLM
    system_prompt = build_system_prompt(q.target_exam, q.language)
    context_block = "\n\n".join(retrieved_texts[:5])

    user_prompt = (
        f"Context:\n{context_block}\n\nQ: {q.query_text}\n\nInstructions: Answer concisely, use village/farming analogies, include a 2-step practice suggestion."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, max_tokens=512)
    answer = resp["choices"][0]["message"]["content"]

    return {"answer": answer}


@app.post("/api/v1/generate-timetable")
async def generate_timetable(req: TimetableRequest):
    total_hours = req.baseline_hours_per_week * req.prep_weeks
    hours_per_day = max(1, req.baseline_hours_per_week // 7)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    timetable = {}
    for w in range(1, req.prep_weeks + 1):
        week_key = f"Week {w}"
        timetable[week_key] = {}
        for d in days:
            timetable[week_key][d] = {
                "study_hours": hours_per_day,
                "focus": f"Core topic {(w - 1) * 7 + days.index(d) + 1}",
                "micro_tasks": ["Read summary (30 min)", "Practice 5 MCQs", "Recall key analogy"],
            }

    return {"student_id": req.student_id, "timetable": timetable}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
