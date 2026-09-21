"""Application configuration settings."""

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Hasamex Interview Analysis Platform"
    app_version: str = "1.0.0"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///hasamex.db")
    data_dir: Path = Path(os.getenv("DATA_DIR", "data/transcripts"))
    guide_file: Path = Path(os.getenv("GUIDE_FILE", "data/guide/Interview_Guide.txt"))
    file_search_store_id: str = os.getenv("FILE_SEARCH_STORE_ID", "")
    environment: str = os.getenv("ENVIRONMENT", "development")

    @property
    def is_gemini_available(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key != "dummy_key")


settings = Settings()
