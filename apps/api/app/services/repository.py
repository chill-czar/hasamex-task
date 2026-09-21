"""Canonical repository for managing calls, experts, and transcript segments."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, text
from apps.api.app.config import settings
from apps.api.app.models.canonical import Call, Expert, TranscriptSegment
from apps.api.app.services.parser import parse_all_transcripts
from apps.api.app.services.validator import EvidenceValidator

logger = logging.getLogger("hasamex.repository")


class CanonicalRepository:
    """In-memory, SQLite, and PostgreSQL-backed canonical transcript repository."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        db_path: Optional[str] = None,
        database_url: Optional[str] = None,
    ):
        self.data_dir = data_dir or Path("data/transcripts")
        self.db_path = db_path

        # Determine database URL: parameter > db_path > settings.database_url
        if database_url:
            self.database_url = database_url
        elif db_path:
            self.database_url = f"sqlite:///{db_path}"
        else:
            self.database_url = settings.database_url

        # Format Postgres URL for SQLAlchemy psycopg2 driver if needed
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

        connect_args = {}
        if self.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self.engine = create_engine(self.database_url, connect_args=connect_args, future=True)
        self.calls: List[Call] = []
        self.experts: List[Expert] = []
        self.calls_by_id: Dict[str, Call] = {}
        self.experts_by_id: Dict[str, Expert] = {}
        self.segments_by_id: Dict[str, TranscriptSegment] = {}
        self.validator: Optional[EvidenceValidator] = None

        self._initialize()

    def _initialize(self):
        """Parse raw transcripts and index in memory and database."""
        if self.data_dir.exists():
            self.calls, self.experts = parse_all_transcripts(self.data_dir)
            self.calls_by_id = {c.call_id: c for c in self.calls}
            self.experts_by_id = {e.expert_id: e for e in self.experts}

            for c in self.calls:
                for seg in c.segments:
                    self.segments_by_id[seg.segment_id] = seg

            self.validator = EvidenceValidator(self.calls, self.experts)
            self._sync_to_db()

    def reload(self):
        """Public method to reload canonical transcripts and re-sync metadata."""
        self._initialize()

    def _sync_to_db(self):
        """Persist metadata and tables to SQL database for audit and analysis caching."""
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS experts (
                        expert_id VARCHAR(64) PRIMARY KEY,
                        name VARCHAR(128) NOT NULL,
                        role VARCHAR(128) NOT NULL,
                        market VARCHAR(64) NOT NULL,
                        country_code VARCHAR(8) NOT NULL,
                        bio TEXT
                    )
                """
                )
            )

            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS calls (
                        call_id VARCHAR(64) PRIMARY KEY,
                        expert_id VARCHAR(64) NOT NULL,
                        title VARCHAR(256) NOT NULL,
                        market VARCHAR(64) NOT NULL,
                        source_file VARCHAR(256) NOT NULL,
                        total_duration_seconds REAL NOT NULL,
                        FOREIGN KEY (expert_id) REFERENCES experts(expert_id)
                    )
                """
                )
            )

            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS segments (
                        segment_id VARCHAR(64) PRIMARY KEY,
                        call_id VARCHAR(64) NOT NULL,
                        expert_id VARCHAR(64) NOT NULL,
                        speaker VARCHAR(128) NOT NULL,
                        is_expert BOOLEAN NOT NULL,
                        start_time_seconds REAL NOT NULL,
                        end_time_seconds REAL NOT NULL,
                        start_timestamp VARCHAR(16) NOT NULL,
                        end_timestamp VARCHAR(16) NOT NULL,
                        text TEXT NOT NULL,
                        FOREIGN KEY (call_id) REFERENCES calls(call_id)
                    )
                """
                )
            )

            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS materialized_analyses (
                        key VARCHAR(64) PRIMARY KEY,
                        content_hash VARCHAR(64) NOT NULL,
                        payload_json TEXT NOT NULL,
                        updated_at VARCHAR(32) NOT NULL
                    )
                """
                )
            )

            for e in self.experts:
                conn.execute(
                    text(
                        """
                        INSERT INTO experts (expert_id, name, role, market, country_code, bio)
                        VALUES (:expert_id, :name, :role, :market, :country_code, :bio)
                        ON CONFLICT (expert_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            role = EXCLUDED.role,
                            market = EXCLUDED.market,
                            country_code = EXCLUDED.country_code,
                            bio = EXCLUDED.bio
                    """
                    ),
                    {
                        "expert_id": e.expert_id,
                        "name": e.name,
                        "role": e.role,
                        "market": e.market,
                        "country_code": e.country_code,
                        "bio": e.bio,
                    },
                )

            for c in self.calls:
                conn.execute(
                    text(
                        """
                        INSERT INTO calls (call_id, expert_id, title, market, source_file, total_duration_seconds)
                        VALUES (:call_id, :expert_id, :title, :market, :source_file, :total_duration_seconds)
                        ON CONFLICT (call_id) DO UPDATE SET
                            expert_id = EXCLUDED.expert_id,
                            title = EXCLUDED.title,
                            market = EXCLUDED.market,
                            source_file = EXCLUDED.source_file,
                            total_duration_seconds = EXCLUDED.total_duration_seconds
                    """
                    ),
                    {
                        "call_id": c.call_id,
                        "expert_id": c.expert_id,
                        "title": c.title,
                        "market": c.market,
                        "source_file": c.source_file,
                        "total_duration_seconds": c.total_duration_seconds,
                    },
                )

                for s in c.segments:
                    conn.execute(
                        text(
                            """
                            INSERT INTO segments (
                                segment_id, call_id, expert_id, speaker, is_expert,
                                start_time_seconds, end_time_seconds, start_timestamp, end_timestamp, text
                            ) VALUES (
                                :segment_id, :call_id, :expert_id, :speaker, :is_expert,
                                :start_time_seconds, :end_time_seconds, :start_timestamp, :end_timestamp, :text
                            ) ON CONFLICT (segment_id) DO UPDATE SET
                                call_id = EXCLUDED.call_id,
                                expert_id = EXCLUDED.expert_id,
                                speaker = EXCLUDED.speaker,
                                is_expert = EXCLUDED.is_expert,
                                start_time_seconds = EXCLUDED.start_time_seconds,
                                end_time_seconds = EXCLUDED.end_time_seconds,
                                start_timestamp = EXCLUDED.start_timestamp,
                                end_timestamp = EXCLUDED.end_timestamp,
                                text = EXCLUDED.text
                        """
                        ),
                        {
                            "segment_id": s.segment_id,
                            "call_id": s.call_id,
                            "expert_id": s.expert_id,
                            "speaker": s.speaker,
                            "is_expert": s.is_expert,
                            "start_time_seconds": s.start_time_seconds,
                            "end_time_seconds": s.end_time_seconds,
                            "start_timestamp": s.start_timestamp,
                            "end_timestamp": s.end_timestamp,
                            "text": s.text,
                        },
                    )

    def save_materialized_analysis(self, key: str, content_hash: str, payload_json: str) -> None:
        """Persists a precomputed analysis in the database."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO materialized_analyses (key, content_hash, payload_json, updated_at)
                    VALUES (:key, :content_hash, :payload_json, :updated_at)
                    ON CONFLICT (key) DO UPDATE SET
                        content_hash = EXCLUDED.content_hash,
                        payload_json = EXCLUDED.payload_json,
                        updated_at = EXCLUDED.updated_at
                """
                ),
                {
                    "key": key,
                    "content_hash": content_hash,
                    "payload_json": payload_json,
                    "updated_at": now_str,
                },
            )

    def get_materialized_analysis(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a materialized analysis by key from the database."""
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT key, content_hash, payload_json, updated_at FROM materialized_analyses WHERE key = :key"),
                {"key": key},
            ).fetchone()
            if not row:
                return None
            return {
                "key": row[0],
                "content_hash": row[1],
                "payload_json": row[2],
                "updated_at": row[3],
            }

    def get_all_materialized_analyses(self) -> Dict[str, Dict[str, Any]]:
        """Retrieves all materialized analyses currently stored."""
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT key, content_hash, payload_json, updated_at FROM materialized_analyses")
            ).fetchall()
            return {
                r[0]: {
                    "key": r[0],
                    "content_hash": r[1],
                    "payload_json": r[2],
                    "updated_at": r[3],
                }
                for r in rows
            }

    def get_all_calls(self) -> List[Call]:
        return self.calls

    def get_call(self, call_id: str) -> Optional[Call]:
        return self.calls_by_id.get(call_id)

    def get_all_experts(self) -> List[Expert]:
        return self.experts

    def get_expert(self, expert_id: str) -> Optional[Expert]:
        return self.experts_by_id.get(expert_id)

    def get_segment(self, segment_id: str) -> Optional[TranscriptSegment]:
        return self.segments_by_id.get(segment_id)

    def get_validator(self) -> EvidenceValidator:
        if not self.validator:
            self.validator = EvidenceValidator(self.calls, self.experts)
        return self.validator

    def search_segments(
        self,
        keywords: List[str],
        market: Optional[str] = None,
        only_expert: bool = True,
    ) -> List[TranscriptSegment]:
        """Simple keyword ranking across canonical segments."""
        matches = []
        lower_keywords = [k.lower() for k in keywords if k]

        for call in self.calls:
            if market and market.lower() not in call.market.lower():
                continue
            for seg in call.segments:
                if only_expert and not seg.is_expert:
                    continue
                seg_lower = seg.text.lower()
                score = sum(1 for kw in lower_keywords if kw in seg_lower)
                if score > 0:
                    matches.append((score, seg))

        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches]


# Singleton instance for application access
_repository_instance: Optional[CanonicalRepository] = None


def get_repository() -> CanonicalRepository:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = CanonicalRepository()
    return _repository_instance
