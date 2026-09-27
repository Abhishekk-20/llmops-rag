from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from app.config import settings


def get_vector_store():
    embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url
    )

    return Chroma(
        collection_name="documents",
        embedding_function=embeddings,
        persist_directory=settings.chroma_path
    )


def retrieve_chunks(
    question: str,
    doc_id: str,
    top_k: int | None = None
):
    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query=question,
        k=top_k or settings.top_k,
        filter={
            "doc_id": doc_id
        }
    )

    return results
