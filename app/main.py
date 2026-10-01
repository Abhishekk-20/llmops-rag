import os
import shutil
import time
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import settings
from app.ingestion import ingest_document
from app.llm import generate_answer
from app.metrics import (
    rag_request_latency_seconds,
    rag_requests_total,
)
from app.models import AskRequest, AskResponse
from app.retrieval import retrieve_chunks


app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)


# --------------------------------------------------
# Create required directories
# --------------------------------------------------

os.makedirs(settings.upload_path, exist_ok=True)
os.makedirs(settings.chroma_path, exist_ok=True)


# --------------------------------------------------
# Root
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "LLMOps RAG API is running"
    }


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# --------------------------------------------------
# Prometheus Metrics
# --------------------------------------------------

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# --------------------------------------------------
# Document Upload / Ingestion
# --------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    filename = file.filename or "uploaded_file"

    if not filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    doc_id = str(uuid.uuid4())

    file_path = os.path.join(
        settings.upload_path,
        f"{doc_id}_{filename}"
    )

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = ingest_document(
            file_path=file_path,
            doc_id=doc_id
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# --------------------------------------------------
# RAG Question Answering
# --------------------------------------------------

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):

    # Count every RAG request
    rag_requests_total.inc()

    # Start total RAG latency timer
    start_time = time.perf_counter()

    try:
        # Retrieve relevant chunks from ChromaDB
        chunks = retrieve_chunks(
            question=request.question,
            doc_id=request.doc_id,
            top_k=request.top_k
        )

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No document chunks found for this doc_id."
            )

        # Generate answer through:
        # FastAPI -> LiteLLM -> Ollama -> LLM
        answer = generate_answer(
            question=request.question,
            chunks=chunks
        )

        sources = []

        for chunk in chunks:
            sources.append(
                {
                    "chunk_index": chunk.metadata.get("chunk_index"),
                    "filename": chunk.metadata.get("filename"),
                    "excerpt": chunk.page_content[:300]
                }
            )

        return {
            "answer": answer,
            "sources": sources
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

    finally:
        # Record complete RAG request latency
        duration = time.perf_counter() - start_time
        rag_request_latency_seconds.observe(duration)
