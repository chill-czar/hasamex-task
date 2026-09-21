"""Google Managed File Search Store integration for transcript retrieval."""

import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from google.genai import types
from apps.api.app.config import settings
from apps.api.app.services.repository import get_repository

logger = logging.getLogger("hasamex.file_search")


class FileSearchService:
    """Manages Google Gen AI File Search Store indexing and retrieval."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.client = None
        self.store_name: Optional[str] = settings.file_search_store_id or None

        if self.api_key and self.api_key != "dummy_key":
            try:
                import google.genai as genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Google GenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI client: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def prepare_formatted_transcript(self, call_id: str) -> str:
        """Formats a transcript with rich metadata and timestamp markers for File Search ingestion."""
        repo = get_repository()
        call = repo.get_call(call_id)
        if not call:
            raise ValueError(f"Call {call_id} not found in canonical repository")

        expert = repo.get_expert(call.expert_id)
        expert_name = expert.name if expert else "Expert"
        market = expert.market if expert else call.market
        role = expert.role if expert else "Healthcare Professional"

        lines = [
            f"CALL_ID: {call.call_id}",
            f"EXPERT: {expert_name}",
            f"MARKET: {market}",
            f"ROLE: {role}",
            f"TOTAL_DURATION_SECONDS: {call.total_duration_seconds}",
            "---",
            "",
        ]

        for seg in call.segments:
            lines.append(f"[{seg.start_timestamp} - {seg.end_timestamp}] (Segment {seg.segment_id})")
            lines.append(f"{seg.speaker}: {seg.text}")
            lines.append("")

        return "\n".join(lines)

    def initialize_store_and_index_transcripts(self) -> Dict[str, Any]:
        """Creates a dedicated File Search Store and indexes all 3 transcripts."""
        if not self.is_available():
            logger.info("Live Google File Search is inactive (no API key). Using local canonical index.")
            return {
                "status": "offline_fallback",
                "message": "Google GenAI API key not set. Transcripts indexed in canonical repository.",
                "store_name": "local_canonical_store",
                "indexed_calls": ["call_fr_01", "call_de_02", "call_uk_03"],
            }

        try:
            # Create File Search Store if not already created
            if not self.store_name:
                store = self.client.file_search_stores.create(
                    config=types.CreateFileSearchStoreConfig(
                        display_name="hasamex-interview-transcripts"
                    )
                )
                self.store_name = store.name
                logger.info(f"Created Google File Search Store: {self.store_name}")

            repo = get_repository()
            indexed_calls = []

            for call in repo.get_all_calls():
                formatted_content = self.prepare_formatted_transcript(call.call_id)
                expert = repo.get_expert(call.expert_id)

                with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp_f:
                    tmp_f.write(formatted_content)
                    tmp_path = tmp_f.name

                try:
                    custom_metadata = [
                        types.CustomMetadata(key="call_id", string_value=call.call_id),
                        types.CustomMetadata(key="market", string_value=call.market),
                        types.CustomMetadata(key="expert_id", string_value=call.expert_id),
                        types.CustomMetadata(key="role", string_value=expert.role if expert else ""),
                    ]

                    upload_config = types.UploadToFileSearchStoreConfig(
                        display_name=f"{call.call_id}_{call.market.lower()}",
                        custom_metadata=custom_metadata,
                        mime_type="text/plain",
                    )

                    op = self.client.file_search_stores.upload_to_file_search_store(
                        file_search_store_name=self.store_name,
                        file=tmp_path,
                        config=upload_config,
                    )
                    indexed_calls.append(call.call_id)
                    logger.info(f"Uploaded {call.call_id} to File Search Store {self.store_name}")
                finally:
                    Path(tmp_path).unlink(missing_ok=True)

            return {
                "status": "success",
                "store_name": self.store_name,
                "indexed_calls": indexed_calls,
            }

        except Exception as e:
            logger.error(f"Error indexing transcripts to Google File Search: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fallback": "canonical_local_store",
            }

    def search_file_search_store(self, query: str, market: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches canonical segments for relevant context keywords."""
        stop_words = {
            "what", "when", "where", "which", "who", "whom", "this", "that", "these", "those",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
            "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "because",
            "as", "until", "while", "of", "at", "by", "for", "with", "about", "into", "through",
            "during", "before", "after", "to", "from", "in", "out", "on", "off", "over", "under",
            "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
            "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will", "should"
        }
        raw_tokens = [w.strip("?,.:;\"'()[]{}") for w in query.lower().split()]
        words = [w for w in raw_tokens if w and w not in stop_words]
        if not words:
            words = [w for w in raw_tokens if w]

        repo = get_repository()
        matches = repo.search_segments(words, market=market, only_expert=True)
        return [
            {
                "segment_id": s.segment_id,
                "call_id": s.call_id,
                "expert_id": s.expert_id,
                "speaker": s.speaker,
                "start_timestamp": s.start_timestamp,
                "start_time_seconds": s.start_time_seconds,
                "text": s.text,
            }
            for s in matches[:5]
        ]


_file_search_instance: Optional[FileSearchService] = None


def get_file_search_service() -> FileSearchService:
    global _file_search_instance
    if _file_search_instance is None:
        _file_search_instance = FileSearchService()
    return _file_search_instance
