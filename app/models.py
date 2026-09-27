from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    doc_id: str
    question: str
    top_k: int = Field(default=5, ge=1, le=20)


class Source(BaseModel):
    chunk_index: int | None = None
    filename: str | None = None
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
