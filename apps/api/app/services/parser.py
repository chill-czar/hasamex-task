"""Transcript parsing and canonical representation service."""

import re
from pathlib import Path
from typing import List, Tuple, Optional
from apps.api.app.models.canonical import Call, Expert, TranscriptSegment


TIMESTAMP_REGEX = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")


def parse_timestamp_to_seconds(ts: str) -> float:
    """Convert timestamp string (MM:SS or HH:MM:SS) to float seconds."""
    ts = ts.strip()
    match = TIMESTAMP_REGEX.match(ts)
    if not match:
        raise ValueError(f"Invalid timestamp format: '{ts}'")
    parts = [p for p in match.groups() if p is not None]
    if len(parts) == 2:
        minutes, seconds = int(parts[0]), int(parts[1])
        return float(minutes * 60 + seconds)
    elif len(parts) == 3:
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return float(hours * 3600 + minutes * 60 + seconds)
    raise ValueError(f"Unable to parse timestamp: '{ts}'")


def seconds_to_timestamp(seconds: float) -> str:
    """Convert float seconds to MM:SS formatted string."""
    total_sec = int(round(seconds))
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    sec = total_sec % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def _get_country_code(market: str) -> str:
    m = market.lower()
    if "france" in m:
        return "FR"
    elif "germany" in m:
        return "DE"
    elif "united kingdom" in m or "uk" in m:
        return "GB"
    return "EU"


def _generate_expert_id(name: str, country_code: str) -> str:
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", name.lower().replace("dr.", "").replace("dr", "").strip())
    # Take last name if available
    parts = name.replace("Dr.", "").replace("Dr", "").strip().split()
    last_name = parts[-1].lower() if parts else clean_name
    return f"expert_{country_code.lower()}_{last_name}"


def parse_transcript_file(file_path: Path, call_id: Optional[str] = None) -> Tuple[Call, Expert]:
    """Parses a raw transcript text file into a canonical Call and Expert."""
    text = file_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]

    # Parse header
    name = "Unknown Expert"
    role = "Unknown Role"
    market = "Europe"

    header_end_idx = 0
    for idx, line in enumerate(lines):
        if not line:
            continue
        if line.startswith("Expert"):
            # e.g. "Expert 1 – Dr. Jean Martin" or "Expert 2 – Anna Keller"
            parts = re.split(r"[–-]", line, maxsplit=1)
            if len(parts) == 2:
                name = parts[1].strip()
        elif line.startswith("Role:"):
            role = line.replace("Role:", "").strip()
        elif line.startswith("Market:"):
            market = line.replace("Market:", "").strip()
        elif TIMESTAMP_REGEX.match(line):
            header_end_idx = idx
            break

    country_code = _get_country_code(market)
    expert_id = _generate_expert_id(name, country_code)

    if not call_id:
        stem = file_path.stem.lower()
        if "france" in stem:
            call_id = "call_fr_01"
        elif "germany" in stem:
            call_id = "call_de_02"
        elif "uk" in stem:
            call_id = "call_uk_03"
        else:
            call_id = f"call_{country_code.lower()}_{stem.replace('transcript_', '')}"

    expert = Expert(
        expert_id=expert_id,
        name=name,
        role=role,
        market=market,
        country_code=country_code,
        bio=f"{role} based in {market}",
    )

    # Parse dialogue turns
    raw_segments = []
    current_timestamp = None
    current_lines = []

    for line in lines[header_end_idx:]:
        if not line:
            continue
        if TIMESTAMP_REGEX.match(line):
            if current_timestamp and current_lines:
                raw_segments.append((current_timestamp, " ".join(current_lines)))
                current_lines = []
            current_timestamp = line
        else:
            current_lines.append(line)

    if current_timestamp and current_lines:
        raw_segments.append((current_timestamp, " ".join(current_lines)))

    segments: List[TranscriptSegment] = []
    for i, (ts, content) in enumerate(raw_segments):
        start_seconds = parse_timestamp_to_seconds(ts)
        if i + 1 < len(raw_segments):
            next_ts = raw_segments[i + 1][0]
            end_seconds = parse_timestamp_to_seconds(next_ts)
        else:
            # Estimate end of last turn based on word count
            word_count = len(content.split())
            estimated_duration = max(20.0, word_count * 0.45)
            end_seconds = start_seconds + estimated_duration

        # Parse speaker from content
        speaker = "Speaker"
        turn_text = content
        if ":" in content:
            parts = content.split(":", 1)
            speaker = parts[0].strip()
            turn_text = parts[1].strip()

        is_expert = not (speaker.lower() == "interviewer" or "interviewer" in speaker.lower())

        seg_id = f"{call_id}_seg_{i+1:03d}"
        segments.append(
            TranscriptSegment(
                segment_id=seg_id,
                call_id=call_id,
                expert_id=expert_id,
                speaker=speaker,
                is_expert=is_expert,
                start_time_seconds=start_seconds,
                end_time_seconds=end_seconds,
                start_timestamp=ts,
                end_timestamp=seconds_to_timestamp(end_seconds),
                text=turn_text,
            )
        )

    total_duration = segments[-1].end_time_seconds if segments else 0.0

    call = Call(
        call_id=call_id,
        expert_id=expert_id,
        title=f"Expert Interview: {name} ({market})",
        market=market,
        source_file=file_path.name,
        total_duration_seconds=total_duration,
        segments=segments,
    )

    return call, expert


def parse_all_transcripts(directory: Path) -> Tuple[List[Call], List[Expert]]:
    """Parse all transcript files in directory sorted deterministically."""
    files = sorted(directory.glob("Transcript_*.txt"))
    calls: List[Call] = []
    experts: List[Expert] = []

    for file_path in files:
        call, expert = parse_transcript_file(file_path)
        calls.append(call)
        experts.append(expert)

    return calls, experts
