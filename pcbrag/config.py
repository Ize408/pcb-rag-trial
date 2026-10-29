import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _get(name, default=""):
    return os.getenv(name, default).strip()


@dataclass
class Settings:
    data_dir: Path = ROOT / "data"
    index_dir: Path = ROOT / ".index"
    top_k: int = int(_get("TOP_K", "5"))

    # "local" = tf-idf on disk, "azure" = Azure AI Search
    retriever: str = _get("RETRIEVER", "local")

    aoai_endpoint: str = _get("AZURE_OPENAI_ENDPOINT")
    aoai_key: str = _get("AZURE_OPENAI_API_KEY")
    aoai_api_version: str = _get("AZURE_OPENAI_API_VERSION", "2024-10-21")
    chat_deployment: str = _get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
    embed_deployment: str = _get("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
    embed_dim: int = int(_get("EMBED_DIM", "1536"))

    search_endpoint: str = _get("AZURE_SEARCH_ENDPOINT")
    search_key: str = _get("AZURE_SEARCH_API_KEY")
    search_index: str = _get("AZURE_SEARCH_INDEX", "pcb-docs")

    @property
    def llm_enabled(self):
        # no keys -> answers are just the best matching passages, still useful for testing
        if _get("LLM", "") == "none":
            return False
        return bool(self.aoai_endpoint and self.aoai_key)
