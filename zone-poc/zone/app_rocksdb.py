"""
Glogos Zone with RocksDB Storage
High-performance Zone for benchmarking

Run:
    python -m zone.app_rocksdb

Or with environment variables:
    ZONE_NAME="My Zone" PORT=8001 python -m zone.app_rocksdb
"""

import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from zone.app import (
    app, signer, merkle, ZONE_NAME, GLSR, GLSR_STATUS,
    lifespan, create_problem_detail
)
from zone.storage import StorageAdapter

# Replace in-memory storage with RocksDB
DB_PATH = os.environ.get("ZONE_DB_PATH", "./data/zone.db")
storage = StorageAdapter(DB_PATH)

# Monkey-patch the storage in app module
import zone.app as app_module
app_module.storage = storage

print(f"[DB] Using RocksDB storage: {DB_PATH}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"\n{'='*60}")
    print(f"  Glogos Zone with RocksDB v1.0.0-rc.0")
    print(f"{'='*60}")
    print(f"  Zone ID: {signer.zone_id[:16]}...")
    print(f"  Storage: RocksDB @ {DB_PATH}")
    print(f"  GLSR: {GLSR[:16]}... ({GLSR_STATUS})")
    print(f"  Listening: http://{host}:{port}")
    print(f"  Docs: http://{host}:{port}/docs")
    print(f"{'='*60}\n")
    
    uvicorn.run(app, host=host, port=port)
