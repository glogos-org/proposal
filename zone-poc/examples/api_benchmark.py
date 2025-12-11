#!/usr/bin/env python3
"""
Glogos Zone API Benchmark
Tests API performance with RocksDB storage

Usage:
    1. Start Zone server: python -m zone.app_rocksdb
    2. Run benchmark: python examples/api_benchmark.py

Results saved to: examples/benchmark_results.md
"""

import time
import json
import hashlib
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List

try:
    import httpx
except ImportError:
    print("ERROR: httpx required. Run: pip install httpx")
    exit(1)


@dataclass
class BenchmarkResult:
    name: str
    total_requests: int
    successful: int
    failed: int
    duration_ms: float
    requests_per_sec: float
    avg_latency_ms: float
    p99_latency_ms: float


def generate_claim(i: int) -> dict:
    """Generate test claim"""
    return {
        "claim": f"Benchmark claim {i} - timestamp {time.time()}",
        "evidence": f"Evidence data for claim {i}",
        "citations": []
    }


def benchmark_create_attestations(
    base_url: str,
    count: int,
    concurrency: int = 10
) -> BenchmarkResult:
    """Benchmark POST /verify endpoint"""
    
    print(f"\n[BENCH] Creating {count} attestations (concurrency={concurrency})...")
    
    latencies = []
    successful = 0
    failed = 0
    
    def create_one(i: int) -> float:
        nonlocal successful, failed
        claim = generate_claim(i)
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(f"{base_url}/verify", json=claim)
                if response.status_code == 200:
                    successful += 1
                else:
                    failed += 1
                    print(f"[X] Request {i} failed: {response.status_code}")
        except Exception as e:
            failed += 1
            print(f"[X] Request {i} error: {e}")
        return (time.perf_counter() - start) * 1000
    
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(create_one, i) for i in range(count)]
        for future in as_completed(futures):
            latencies.append(future.result())
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    latencies.sort()
    p99_idx = int(len(latencies) * 0.99)
    
    return BenchmarkResult(
        name="POST /verify (Create Attestation)",
        total_requests=count,
        successful=successful,
        failed=failed,
        duration_ms=duration_ms,
        requests_per_sec=count / (duration_ms / 1000),
        avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0,
        p99_latency_ms=latencies[p99_idx] if latencies else 0
    )


def benchmark_get_attestations(
    base_url: str,
    attestation_ids: List[str],
    concurrency: int = 10
) -> BenchmarkResult:
    """Benchmark GET /attestation/{id} endpoint"""
    
    count = len(attestation_ids)
    print(f"\n[BENCH] Getting {count} attestations (concurrency={concurrency})...")
    
    latencies = []
    successful = 0
    failed = 0
    
    def get_one(att_id: str) -> float:
        nonlocal successful, failed
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(f"{base_url}/attestation/{att_id}")
                if response.status_code == 200:
                    successful += 1
                else:
                    failed += 1
        except Exception as e:
            failed += 1
        return (time.perf_counter() - start) * 1000
    
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(get_one, att_id) for att_id in attestation_ids]
        for future in as_completed(futures):
            latencies.append(future.result())
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    latencies.sort()
    p99_idx = int(len(latencies) * 0.99)
    
    return BenchmarkResult(
        name="GET /attestation/{id}",
        total_requests=count,
        successful=successful,
        failed=failed,
        duration_ms=duration_ms,
        requests_per_sec=count / (duration_ms / 1000),
        avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0,
        p99_latency_ms=latencies[p99_idx] if latencies else 0
    )


def benchmark_merkle_root(base_url: str, count: int = 100) -> BenchmarkResult:
    """Benchmark GET /merkle/root endpoint"""
    
    print(f"\n[BENCH] Getting Merkle root {count} times...")
    
    latencies = []
    successful = 0
    failed = 0
    
    start_time = time.perf_counter()
    
    with httpx.Client(timeout=30.0) as client:
        for i in range(count):
            start = time.perf_counter()
            try:
                response = client.get(f"{base_url}/merkle/root")
                if response.status_code == 200:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
            latencies.append((time.perf_counter() - start) * 1000)
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    latencies.sort()
    p99_idx = int(len(latencies) * 0.99)
    
    return BenchmarkResult(
        name="GET /merkle/root",
        total_requests=count,
        successful=successful,
        failed=failed,
        duration_ms=duration_ms,
        requests_per_sec=count / (duration_ms / 1000),
        avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0,
        p99_latency_ms=latencies[p99_idx] if latencies else 0
    )


def generate_report(results: List[BenchmarkResult], zone_info: dict) -> str:
    """Generate markdown benchmark report"""
    
    report = f"""# Glogos Zone API Benchmark Results

**Zone:** {zone_info.get('name', 'Unknown')}  
**Zone ID:** `{zone_info.get('zone_id', 'Unknown')[:16]}...`  
**GLSR:** `{zone_info.get('glsr', 'Unknown')[:16]}...`  
**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

## Summary

| Endpoint | Requests | Success | RPS | Avg Latency | P99 Latency |
|----------|----------|---------|-----|-------------|-------------|
"""
    
    for r in results:
        report += f"| {r.name} | {r.total_requests:,} | {r.successful:,} | {r.requests_per_sec:.0f} | {r.avg_latency_ms:.2f}ms | {r.p99_latency_ms:.2f}ms |\n"
    
    report += f"""
---

## Detailed Results

"""
    
    for r in results:
        report += f"""### {r.name}

- **Total Requests:** {r.total_requests:,}
- **Successful:** {r.successful:,}
- **Failed:** {r.failed:,}
- **Duration:** {r.duration_ms:.2f}ms
- **Requests/sec:** {r.requests_per_sec:.0f}
- **Avg Latency:** {r.avg_latency_ms:.2f}ms
- **P99 Latency:** {r.p99_latency_ms:.2f}ms

"""
    
    report += """---

*Generated by api_benchmark.py*
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Glogos Zone API Benchmark")
    parser.add_argument("--url", default="http://localhost:8000", help="Zone API URL")
    parser.add_argument("--count", type=int, default=1000, help="Number of attestations to create")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    args = parser.parse_args()
    
    base_url = args.url
    
    print("=" * 60)
    print("Glogos Zone API Benchmark")
    print("=" * 60)
    print(f"Target: {base_url}")
    print(f"Attestations: {args.count}")
    print(f"Concurrency: {args.concurrency}")
    print("=" * 60)
    
    # Check Zone health
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{base_url}/")
            zone_info = response.json()
            print(f"\n[OK] Zone connected: {zone_info.get('name', 'Unknown')}")
    except Exception as e:
        print(f"\n[X] Cannot connect to Zone: {e}")
        print(f"    Make sure Zone is running: python -m zone.app_rocksdb")
        exit(1)
    
    results = []
    attestation_ids = []
    
    # Benchmark 1: Create attestations
    result1 = benchmark_create_attestations(base_url, args.count, args.concurrency)
    results.append(result1)
    print(f"   [OK] {result1.requests_per_sec:.0f} req/sec")
    
    # Get some attestation IDs for read benchmark
    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"{base_url}/health")
        health = response.json()
        print(f"\n[INFO] Zone has {health.get('attestation_count', 0)} attestations")
    
    # Create a few more to get IDs
    print("\n[BENCH] Getting attestation IDs for read test...")
    with httpx.Client(timeout=30.0) as client:
        for i in range(min(100, args.count)):
            claim = generate_claim(i + args.count)
            response = client.post(f"{base_url}/verify", json=claim)
            if response.status_code == 200:
                data = response.json()
                attestation_ids.append(data['attestation']['attestation_id'])
    
    # Benchmark 2: Get attestations
    if attestation_ids:
        result2 = benchmark_get_attestations(base_url, attestation_ids, args.concurrency)
        results.append(result2)
        print(f"   [OK] {result2.requests_per_sec:.0f} req/sec")
    
    # Benchmark 3: Merkle root
    result3 = benchmark_merkle_root(base_url, 100)
    results.append(result3)
    print(f"   [OK] {result3.requests_per_sec:.0f} req/sec")
    
    # Generate report
    report = generate_report(results, zone_info)
    
    import os
    report_path = os.path.join(os.path.dirname(__file__), "benchmark_results.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n{'='*60}")
    print("BENCHMARK COMPLETE")
    print(f"{'='*60}")
    print(f"\nResults saved to: {report_path}")
    
    # Print summary
    print("\n[SUMMARY]")
    for r in results:
        print(f"   {r.name}: {r.requests_per_sec:.0f} req/sec")


if __name__ == "__main__":
    main()
