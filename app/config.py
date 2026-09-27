from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LLMOps RAG API"

    ollama_base_url: str = "http://localhost:11434"

    llm_model: str = "llama3.2:1b"
    embedding_model: str = "nomic-embed-text"

    chroma_path: str = "./data/chroma"
    upload_path: str = "./data/uploads"

    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
