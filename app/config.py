from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LLMOps RAG API"

    # Ollama - used directly for embeddings
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"

    # LiteLLM - used for LLM generation
    litellm_base_url: str = "http://localhost:4000/v1"
    litellm_master_key: str = ""
    litellm_model: str = "llama-local"

    llm_input_cost_per_million_tokens: float = 0.0
    llm_output_cost_per_million_tokens: float = 0.0


    chroma_path: str = "./data/chroma"
    upload_path: str = "./data/uploads"

    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
