import os
import shutil
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException

from app.config import settings
from app.ingestion import ingest_document
from app.models import AskRequest, AskResponse
from app.retrieval import retrieve_chunks
from app.llm import generate_answer


app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)


os.makedirs(settings.upload_path, exist_ok=True)
os.makedirs(settings.chroma_path, exist_ok=True)


@app.get("/")
def root():
    return {
        "message": "LLMOps RAG API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


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


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):

    try:
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
