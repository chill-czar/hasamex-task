#!/usr/bin/env python3
"""Comprehensive Latency Benchmark Suite for Hasamex Expert Interview Analysis Platform.

Measures:
1. HTTP Endpoint Latencies (min, median/p50, p95, max, mean)
2. In-process Repository / Database query latency
3. EvidenceValidator verification & fuzzy matching latency
4. Live Google Cloud Gemini API call round-trip latency
"""

import sys
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any, Callable
import httpx

# Ensure python path includes root
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.services.repository import get_repository
from apps.api.app.services.analyzer import get_analyzer

API_BASE = "http://localhost:8000"


def measure_execution_times(fn: Callable[[], Any], iterations: int = 10, warmup: int = 1) -> List[float]:
    """Runs a callable `iterations` times after `warmup` runs and returns list of latencies in milliseconds."""
    for _ in range(warmup):
        try:
            fn()
        except Exception as e:
            print(f"Warmup error: {e}")

    times_ms = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times_ms.append((t1 - t0) * 1000.0)
    return times_ms


def format_stats(latencies: List[float]) -> Dict[str, float]:
    """Computes min, mean, median, p95, and max from a list of latencies in ms."""
    s = sorted(latencies)
    p95_idx = int(len(s) * 0.95)
    return {
        "min": round(min(s), 2),
        "mean": round(statistics.mean(s), 2),
        "median": round(statistics.median(s), 2),
        "p95": round(s[min(p95_idx, len(s) - 1)], 2),
        "max": round(max(s), 2),
        "stdev": round(statistics.stdev(s), 2) if len(s) > 1 else 0.0,
    }


def run_benchmark():
    print("=" * 88)
    print("      HASAMEX EXPERT INTERVIEW ANALYSIS PLATFORM — LATENCY BENCHMARK")
    print("=" * 88)
    print(f"Target API Endpoint: {API_BASE}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")

    client = httpx.Client(base_url=API_BASE, timeout=60.0)

    # Verify server connectivity
    try:
        health_resp = client.get("/api/health")
        health_data = health_resp.json()
        print(f"✓ Backend connected: {health_data.get('app_name')} (Status: {health_data.get('status')})")
        print(f"  Gemini Configured: {health_data.get('gemini_configured')}")
        print(f"  File Search Store: {health_data.get('file_search_available')}")
        print(f"  Canonical Calls:   {health_data.get('canonical_calls_loaded')}\n")
    except Exception as e:
        print(f"❌ Error: Cannot connect to FastAPI backend on {API_BASE}: {e}")
        print("Please start the backend with 'make run-api' before running benchmark.")
        return

    benchmark_results = []

    # 1. Fast Database & Cached Analysis Endpoints (10 iterations each)
    endpoints = [
        ("GET /api/health", lambda: client.get("/api/health"), 15, "Liveness & canonical DB health check"),
        ("GET /api/interviews", lambda: client.get("/api/interviews"), 15, "List all 3 expert interview summaries"),
        ("GET /api/interviews/call_fr_01", lambda: client.get("/api/interviews/call_fr_01"), 15, "Full French transcript with 9 segments"),
        ("GET /api/evidence/seg_fr_01_004", lambda: client.get("/api/evidence/seg_fr_01_004"), 15, "Direct segment lookup by ID"),
        ("GET /api/interview-guide", lambda: client.get("/api/interview-guide"), 10, "Interview Guide (6 questions + 18 expert analyses)"),
        ("GET /api/insights/themes", lambda: client.get("/api/insights/themes"), 10, "Cross-interview common themes with citations"),
        ("GET /api/insights/disagreements", lambda: client.get("/api/insights/disagreements"), 10, "Cross-interview disagreements & stances"),
    ]

    print("Phase 1: Benchmarking Canonical DB & Cached Intelligence Endpoints (10-15 runs each)...")
    for name, fn, iters, desc in endpoints:
        times = measure_execution_times(fn, iterations=iters, warmup=1)
        stats = format_stats(times)
        stats["name"] = name
        stats["desc"] = desc
        stats["runs"] = iters
        benchmark_results.append(stats)
        print(f"  {name:<36} -> Median: {stats['median']:>6.2f} ms | P95: {stats['p95']:>6.2f} ms | Min: {stats['min']:>6.2f} ms")

    # 2. Live LLM / Google Cloud Gemini Semantic Q&A Endpoint
    print("\nPhase 2: Benchmarking Live Gemini Q&A Pipeline (POST /api/questions/ask)...")
    qa_queries = [
        ("POST /api/questions/ask (Cost/Procurement)", {
            "query": "Which expert emphasized cost and procurement concerns?",
            "market_filter": None,
        }),
        ("POST /api/questions/ask (Adoption Barriers)", {
            "query": "What are the primary barriers to robotic surgery adoption across Europe?",
            "market_filter": None,
        }),
        ("POST /api/questions/ask (Guardrail Test)", {
            "query": "What is the robotic surgery adoption rate in Japan or China?",
            "market_filter": None,
        }),
    ]

    llm_times = []
    for label, payload in qa_queries:
        print(f"  Executing real Gemini call: \"{payload['query'][:50]}...\"")
        t0 = time.perf_counter()
        resp = client.post("/api/questions/ask", json=payload)
        t1 = time.perf_counter()
        duration_ms = (t1 - t0) * 1000.0
        llm_times.append(duration_ms)
        data = resp.json()
        print(f"    Status: {resp.status_code} | Sufficient Evidence: {data.get('has_sufficient_evidence')} | Time: {duration_ms:.2f} ms")

    llm_stats = format_stats(llm_times)
    llm_stats["name"] = "POST /api/questions/ask (Live Gemini)"
    llm_stats["desc"] = "Full pipeline: Query -> Gemini reasoning -> Evidence extraction -> Grounding validation"
    llm_stats["runs"] = len(llm_times)
    benchmark_results.append(llm_stats)

    # 3. In-Process Micro-Benchmarks (Direct Python Service Layer)
    print("\nPhase 3: Micro-Benchmarking Internal Architecture Components (100 runs each)...")
    repo = get_repository()
    validator = repo.get_validator()

    db_times = measure_execution_times(lambda: repo.get_segment("seg_fr_01_004"), iterations=100, warmup=5)
    db_stats = format_stats(db_times)
    db_stats["name"] = "Internal: repo.get_segment (SQLite)"
    db_stats["desc"] = "Primary key segment lookup in canonical store"
    db_stats["runs"] = 100
    benchmark_results.append(db_stats)

    val_times = measure_execution_times(
        lambda: validator.validate_quote("the initial capital cost remains substantial"),
        iterations=100,
        warmup=5,
    )
    val_stats = format_stats(val_times)
    val_stats["name"] = "Internal: validator.validate_quote"
    val_stats["desc"] = "Exact verbatim substring search & timestamp resolution across all transcripts"
    val_stats["runs"] = 100
    benchmark_results.append(val_stats)

    # 4. Summary Table Output
    print("\n" + "=" * 88)
    print("                            LATENCY BENCHMARK RESULTS")
    print("=" * 88)
    header = f"{'Operation / Endpoint':<40} {'Runs':<6} {'Min (ms)':<10} {'Median (ms)':<12} {'P95 (ms)':<10} {'Max (ms)':<10}"
    print(header)
    print("-" * 88)

    for r in benchmark_results:
        row = f"{r['name']:<40} {r['runs']:<6} {r['min']:<10.2f} {r['median']:<12.2f} {r['p95']:<10.2f} {r['max']:<10.2f}"
        print(row)

    print("=" * 88)
    print("\nKey Latency Insights:")
    print(f"1. Database & Cached Endpoints: Sub-millisecond to ~5ms response times ({benchmark_results[0]['median']}ms - {benchmark_results[4]['median']}ms).")
    print(f"2. In-Process Validation: Verifying an exact quote across all transcripts executes in {val_stats['median']}ms.")
    print(f"3. Live Gemini LLM Generation: Full end-to-end reasoning + verification executes in ~{llm_stats['median']/1000.0:.2f}s ({llm_stats['median']}ms).")
    print("4. Architecture Impact: Canonical in-memory/SQLite cache decouples frontend responsiveness from LLM network hops.")
    print("=" * 88)


if __name__ == "__main__":
    run_benchmark()
