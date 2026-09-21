"""Canonical repository for managing calls, experts, and transcript segments."""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from apps.api.app.models.canonical import Call, Expert, TranscriptSegment
from apps.api.app.services.parser import parse_all_transcripts
from apps.api.app.services.validator import EvidenceValidator


class CanonicalRepository:
    """In-memory and SQLite-backed canonical transcript repository."""

    def __init__(self, data_dir: Optional[Path] = None, db_path: Optional[str] = None):
        self.data_dir = data_dir or Path("data/transcripts")
        self.db_path = db_path or "hasamex.db"
        self.calls: List[Call] = []
        self.experts: List[Expert] = []
        self.calls_by_id: Dict[str, Call] = {}
        self.experts_by_id: Dict[str, Expert] = {}
        self.segments_by_id: Dict[str, TranscriptSegment] = {}
        self.validator: Optional[EvidenceValidator] = None

        self._initialize()

    def _initialize(self):
        """Parse raw transcripts and index in memory and sqlite."""
        if self.data_dir.exists():
            self.calls, self.experts = parse_all_transcripts(self.data_dir)
            self.calls_by_id = {c.call_id: c for c in self.calls}
            self.experts_by_id = {e.expert_id: e for e in self.experts}

            for c in self.calls:
                for seg in c.segments:
                    self.segments_by_id[seg.segment_id] = seg

            self.validator = EvidenceValidator(self.calls, self.experts)
            self._sync_to_sqlite()

    def reload(self):
        """Public method to reload canonical transcripts and re-sync metadata."""
        self._initialize()

    def _sync_to_sqlite(self):
        """Persist metadata to SQLite database for audit and local queries."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS experts (
                expert_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                market TEXT NOT NULL,
                country_code TEXT NOT NULL,
                bio TEXT
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS calls (
                call_id TEXT PRIMARY KEY,
                expert_id TEXT NOT NULL,
                title TEXT NOT NULL,
                market TEXT NOT NULL,
                source_file TEXT NOT NULL,
                total_duration_seconds REAL NOT NULL,
                FOREIGN KEY (expert_id) REFERENCES experts(expert_id)
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS segments (
                segment_id TEXT PRIMARY KEY,
                call_id TEXT NOT NULL,
                expert_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                is_expert BOOLEAN NOT NULL,
                start_time_seconds REAL NOT NULL,
                end_time_seconds REAL NOT NULL,
                start_timestamp TEXT NOT NULL,
                end_timestamp TEXT NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY (call_id) REFERENCES calls(call_id)
            )
        """
        )

        for e in self.experts:
            cur.execute(
                """
                INSERT OR REPLACE INTO experts (expert_id, name, role, market, country_code, bio)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (e.expert_id, e.name, e.role, e.market, e.country_code, e.bio),
            )

        for c in self.calls:
            cur.execute(
                """
                INSERT OR REPLACE INTO calls (call_id, expert_id, title, market, source_file, total_duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (c.call_id, c.expert_id, c.title, c.market, c.source_file, c.total_duration_seconds),
            )

            for s in c.segments:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO segments (
                        segment_id, call_id, expert_id, speaker, is_expert,
                        start_time_seconds, end_time_seconds, start_timestamp, end_timestamp, text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        s.segment_id,
                        s.call_id,
                        s.expert_id,
                        s.speaker,
                        s.is_expert,
                        s.start_time_seconds,
                        s.end_time_seconds,
                        s.start_timestamp,
                        s.end_timestamp,
                        s.text,
                    ),
                )

        conn.commit()
        conn.close()

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
