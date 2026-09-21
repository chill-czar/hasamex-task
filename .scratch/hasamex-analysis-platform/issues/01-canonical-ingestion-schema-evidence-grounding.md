# 01: Canonical Ingestion, Schema & Evidence Grounding Core

**What to build:**
The canonical data pipeline and evidence validation engine. Parses the 3 transcripts into structured segments with deterministic IDs, speaker labels, and timestamps in seconds. Validates quotes verbatim against canonical source text and attaches true timestamps from metadata.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Parse `Transcript_1_France.txt`, `Transcript_2_Germany.txt`, `Transcript_3_UK.txt`
- [ ] Implement canonical data models (`TranscriptSegment`, `Call`, `Expert`)
- [ ] Implement `EvidenceValidator` with verbatim quote verification and timestamp mapping
- [ ] Unit tests for ingestion and validation
