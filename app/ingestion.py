import os
import uuid

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from app.config import settings


def extract_text(file_path: str) -> str:
    """Extract text from a PDF or TXT document."""

    if file_path.lower().endswith(".pdf"):
        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    if file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    raise ValueError("Only PDF and TXT files are supported.")


def ingest_document(file_path: str, doc_id: str | None = None):
    """Chunk, embed and store a document in ChromaDB."""

    if not doc_id:
        doc_id = str(uuid.uuid4())

    text = extract_text(file_path)

    if not text.strip():
        raise ValueError("No text could be extracted from document.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    chunks = splitter.create_documents(
        [text],
        metadatas=[
            {
                "doc_id": doc_id,
                "filename": os.path.basename(file_path)
            }
        ]
    )

    embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url
    )

    vector_store = Chroma(
        collection_name="documents",
        embedding_function=embeddings,
        persist_directory=settings.chroma_path
    )

    ids = [
        f"{doc_id}-{index}"
        for index in range(len(chunks))
    ]

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    vector_store.add_documents(
        documents=chunks,
        ids=ids
    )

    return {
        "doc_id": doc_id,
        "chunks_created": len(chunks),
        "status": "indexed"
    }
