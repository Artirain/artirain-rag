import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    llm_engine: str = "codex"
    qdrant_url: str = "http://localhost:6333"
    collection: str = "portfolio"
    embed_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    top_k: int = 4
    chunk_size: int = 900
    chunk_overlap: int = 150
    data_dir: str = "data"


def load_config() -> Config:
    return Config(
        llm_engine=os.getenv("LLM_ENGINE", "codex"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        collection=os.getenv("QDRANT_COLLECTION", "portfolio"),
        embed_model=os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
        top_k=int(os.getenv("TOP_K", "4")),
        chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
        data_dir=os.getenv("DATA_DIR", "data"),
    )
