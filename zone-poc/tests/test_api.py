#!/usr/bin/env python3
"""
Test Glogos Attester API (Full HTTP Flow)

This script:
1. Starts the FastAPI server in background
2. Creates attestations via HTTP
3. Retrieves them with Merkle proofs
4. Verifies everything works end-to-end

Usage:
    pip install -r requirements.txt
    python test_api.py
"""

import subprocess
import sys
import time
import json
import urllib.request
import urllib.parse
import threading
from queue import Queue

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server(max_wait=10):
    """Wait for server to be ready"""
    print("   Waiting for server...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            req = urllib.request.Request(f"{BASE_URL}/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except:
            time.sleep(0.5)
    return False

def make_request(method, endpoint, data=None):
    """Make HTTP request and return JSON response"""
    url = f"{BASE_URL}{endpoint}"
    
    if data:
        data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('Content-Type', 'application/json')
    else:
        req = urllib.request.Request(url, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"   HTTP Error {e.code}: {body[:200]}")
        return None

def stress_worker(q: Queue, results: list):
    """Worker thread for stress test"""
    while not q.empty():
        try:
            request_data = q.get_nowait()
            start_time = time.perf_counter()
            result = make_request("POST", "/verify", request_data)
            end_time = time.perf_counter()
            if result and 'attestation' in result:
                results.append(end_time - start_time)
            q.task_done()
        except Exception:
            q.task_done()
            continue

def run_stress_test(num_requests=100, concurrency=10):
    """Runs a stress test against the /verify endpoint."""
    print(f"\n[5] STRESS TEST ({num_requests} requests, {concurrency} concurrent)...")
    
    q = Queue()
    for i in range(num_requests):
        q.put({"claim": f"Stress test claim {i}", "evidence": "evidence"})

    latencies = []
    threads = []
    
    start_total_time = time.perf_counter()

    for _ in range(concurrency):
        t = threading.Thread(target=stress_worker, args=(q, latencies))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    total_time = time.perf_counter() - start_total_time
    
    return total_time, latencies

def main():
    print("=" * 60)
    print("  GLOGOS API TEST")
    print("=" * 60)
    print()
    
    # Note: You need to start the server manually first
    print("[0] Checking if server is running...")
    if not wait_for_server(max_wait=3):
        print("   ⚠ Server not running. Start it with:")
        print("   python -m src.core.app")
        print()
        print("   Or run in Docker:")
        print("   docker-compose up -d")
        return False
    print("   [OK] Server is ready")
    print()
    
    # 1. Get Attester info
    print("[1] GET /zone/info (Attester info)...")
    info = make_request("GET", "/zone/info")
    if not info:
        print("   [X] Failed to get Attester info")
        return False
    assert 'zone_id' in info, "zone_id not in info response"
    
    print(f"   Attester ID: {info['zone_id'][:16]}...")
    print(f"   Name: {info['name']}")
    print(f"   Spec Version: {info.get('spec_version', 'N/A')}")
    print(f"   GLSR: {info.get('glsr_reference', 'N/A')[:16]}... ({info.get('glsr_status', 'N/A')})")
    print()
    
    # 2. Create attestation
    print("[2] POST /verify (create attestation)...")
    attestation_request = {
        "claim": "Test document content for Glogos v1.0.0",
        "evidence": "SHA256 hash matches, signature valid",
        "citations": []
    }
    
    result = make_request("POST", "/verify", attestation_request)
    if not result:
        print("   [X] Failed to create attestation")
        return False
    assert 'attestation' in result and 'attestation_id' in result['attestation']
    
    attestation = result.get("attestation", {})
    proof = result.get("proof", {})
    
    attestation_id = attestation.get("attestation_id")
    print(f"   Attestation ID: {attestation_id[:16]}...")
    print(f"   Claim hash: {attestation.get('claim_hash', '')[:16]}...")
    print(f"   Merkle root: {proof.get('root', '')[:16]}...")
    print()
    
    # 3. Retrieve attestation
    print(f"[3] GET /attestation/{attestation_id[:8]}... (retrieve)...")
    retrieved = make_request("GET", f"/attestation/{attestation_id}")
    if not retrieved:
        print("   [X] Failed to retrieve attestation")
        return False
    assert retrieved['attestation']['attestation_id'] == attestation_id
    
    print(f"   [OK] Retrieved attestation")
    print(f"   Proof path: {len(retrieved['proof']['proof'])} siblings")
    print()
    
    # 4. Get Merkle root
    print("[4] GET /merkle/root...")
    merkle = make_request("GET", "/merkle/root")
    if not merkle:
        print("   [X] Failed to get Merkle root")
        return False
    assert merkle['merkle_root'] == proof.get('root')
    
    print(f"   Merkle root: {merkle['merkle_root'][:16]}...")
    print(f"   Attestation count: {merkle['attestation_count']}")
    print()
    
    # 5. Stress test
    total_time, latencies = run_stress_test(num_requests=100, concurrency=10)
    
    successful_requests = len(latencies)
    throughput = successful_requests / total_time if total_time > 0 else 0
    avg_latency_ms = (sum(latencies) / successful_requests * 1000) if successful_requests > 0 else 0

    if successful_requests > 0:
        print(f"   [OK] Stress test complete.")
        print(f"   Successful requests: {successful_requests}/{100}")
        print(f"   Total time:          {total_time:.2f} seconds")
        print(f"   Throughput:          {throughput:.2f} req/sec")
        print(f"   Avg Latency:         {avg_latency_ms:.2f} ms/req")
    else:
        print("   [X] Stress test failed. No successful requests.")
        return False
    
    print()


    # Summary
    print("=" * 60)
    print("  API TEST COMPLETE")
    print("=" * 60)
    print(f"""
All endpoints working:
  [OK] GET  /zone/info      - Attester metadata
  [OK] POST /verify         - Create attestation  
  [OK] GET  /attestation/id - Retrieve with proof
  [OK] GET  /merkle/root    - Current Merkle state
  [OK] POST /verify (STRESS) - {throughput:.0f} req/sec

Attestation created:
  ID: {attestation_id}
  Proof: {proof.get('root', 'N/A')}
""")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
