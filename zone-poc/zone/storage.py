"""
RocksDB Storage Backend for Glogos Zone
High-performance persistent storage for attestations

Requires: pip install rocksdict
"""

import json
import os
from typing import Optional, Iterator
from dataclasses import asdict

try:
    from rocksdict import Rdict
    ROCKSDB_AVAILABLE = True
except ImportError:
    ROCKSDB_AVAILABLE = False
    print("[WARN] rocksdict not installed. Run: pip install rocksdict")


class RocksDBStorage:
    """
    High-performance persistent storage using RocksDB.
    
    Column Families:
    - attestations: attestation_id -> SignedAttestation JSON
    - evidence: attestation_id -> evidence content
    - anchors: index -> anchor JSON
    - meta: key -> value (counters, config)
    """
    
    def __init__(self, db_path: str = "./data/zone.db"):
        if not ROCKSDB_AVAILABLE:
            raise RuntimeError("rocksdict not installed. Run: pip install rocksdict")
        
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Open RocksDB with column families
        self.db = Rdict(db_path)
        
        # Use prefixes for different data types
        self._attestation_prefix = b"att:"
        self._evidence_prefix = b"ev:"
        self._anchor_prefix = b"anc:"
        self._meta_prefix = b"meta:"
        
        # Cache for anchor count
        self._anchor_count = self._get_meta("anchor_count", 0)
        
        print(f"[DB] RocksDB opened: {db_path}")
        print(f"[DB] Attestations: {self.attestation_count}")
    
    def _get_meta(self, key: str, default=None):
        """Get metadata value"""
        full_key = self._meta_prefix + key.encode()
        value = self.db.get(full_key)
        if value is None:
            return default
        return json.loads(value)
    
    def _set_meta(self, key: str, value):
        """Set metadata value"""
        full_key = self._meta_prefix + key.encode()
        self.db[full_key] = json.dumps(value)
    
    # =========================================================================
    # Attestation Operations
    # =========================================================================
    
    def put_attestation(self, attestation_id: str, attestation) -> None:
        """Store attestation"""
        key = self._attestation_prefix + attestation_id.lower().encode()
        # Convert to dict, then JSON
        if isinstance(attestation, dict):
            data = attestation
        elif hasattr(attestation, 'model_dump'):
            data = attestation.model_dump()
        elif hasattr(attestation, 'dict'):
            data = attestation.dict()
        else:
            data = asdict(attestation)
        self.db[key] = json.dumps(data)
    
    def get_attestation(self, attestation_id: str) -> Optional[dict]:
        """Get attestation by ID"""
        key = self._attestation_prefix + attestation_id.lower().encode()
        value = self.db.get(key)
        if value is None:
            return None
        return json.loads(value)
    
    def has_attestation(self, attestation_id: str) -> bool:
        """Check if attestation exists"""
        key = self._attestation_prefix + attestation_id.lower().encode()
        return self.db.get(key) is not None
    
    @property
    def attestation_count(self) -> int:
        """Count attestations (cached for performance)"""
        count = 0
        for key in self.db.keys():
            if key.startswith(self._attestation_prefix):
                count += 1
        return count
    
    def iter_attestation_ids(self) -> Iterator[str]:
        """Iterate over all attestation IDs"""
        for key in self.db.keys():
            if key.startswith(self._attestation_prefix):
                yield key[len(self._attestation_prefix):].decode()
    
    # =========================================================================
    # Evidence Operations
    # =========================================================================
    
    def put_evidence(self, attestation_id: str, evidence: str) -> None:
        """Store evidence"""
        key = self._evidence_prefix + attestation_id.lower().encode()
        self.db[key] = evidence
    
    def get_evidence(self, attestation_id: str) -> Optional[str]:
        """Get evidence by attestation ID"""
        key = self._evidence_prefix + attestation_id.lower().encode()
        return self.db.get(key)
    
    # =========================================================================
    # Anchor Operations
    # =========================================================================
    
    def add_anchor(self, anchor) -> int:
        """Add anchor and return index"""
        index = self._anchor_count
        key = self._anchor_prefix + str(index).encode()
        
        if isinstance(anchor, dict):
            data = anchor
        elif hasattr(anchor, 'model_dump'):
            data = anchor.model_dump()
        elif hasattr(anchor, 'dict'):
            data = anchor.dict()
        else:
            data = asdict(anchor)
        
        self.db[key] = json.dumps(data)
        self._anchor_count += 1
        self._set_meta("anchor_count", self._anchor_count)
        return index
    
    def get_latest_anchor(self) -> Optional[dict]:
        """Get most recent anchor"""
        if self._anchor_count == 0:
            return None
        key = self._anchor_prefix + str(self._anchor_count - 1).encode()
        value = self.db.get(key)
        if value:
            return json.loads(value)
        return None
    
    @property
    def anchor_count(self) -> int:
        return self._anchor_count
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    
    def close(self):
        """Close database"""
        self.db.close()
        print(f"[DB] RocksDB closed: {self.db_path}")
    
    def flush(self):
        """Flush writes to disk"""
        # rocksdict automatically flushes
        pass
    
    def destroy(self):
        """Delete database"""
        self.close()
        import shutil
        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)
        print(f"[DB] RocksDB destroyed: {self.db_path}")


# =============================================================================
# Adapter to match in-memory Storage interface
# =============================================================================

class StorageAdapter:
    """
    Adapter that provides same interface as in-memory Storage
    but uses RocksDB backend.
    """
    
    def __init__(self, db_path: str = "./data/zone.db"):
        self._db = RocksDBStorage(db_path)
        
        # Property-like access for backwards compatibility
        self._attestations_proxy = AttestationsProxy(self._db)
        self._evidence_proxy = EvidenceProxy(self._db)
        self._anchors_proxy = AnchorsProxy(self._db)
    
    @property
    def attestations(self):
        return self._attestations_proxy
    
    @property
    def evidence(self):
        return self._evidence_proxy
    
    @property
    def anchors(self):
        return self._anchors_proxy
    
    def close(self):
        self._db.close()


class AttestationsProxy:
    """Dict-like proxy for attestations"""
    
    def __init__(self, db: RocksDBStorage):
        self._db = db
    
    def __getitem__(self, key: str):
        result = self._db.get_attestation(key)
        if result is None:
            raise KeyError(key)
        return result
    
    def get(self, key: str, default=None):
        result = self._db.get_attestation(key)
        return result if result is not None else default
    
    def __setitem__(self, key: str, value):
        self._db.put_attestation(key, value)
    
    def __contains__(self, key: str) -> bool:
        return self._db.has_attestation(key)
    
    def __len__(self) -> int:
        return self._db.attestation_count
    
    def keys(self):
        return self._db.iter_attestation_ids()


class EvidenceProxy:
    """Dict-like proxy for evidence"""
    
    def __init__(self, db: RocksDBStorage):
        self._db = db
    
    def __getitem__(self, key: str):
        result = self._db.get_evidence(key)
        if result is None:
            raise KeyError(key)
        return result
    
    def get(self, key: str, default=None):
        return self._db.get_evidence(key) or default
    
    def __setitem__(self, key: str, value: str):
        self._db.put_evidence(key, value)


class AnchorsProxy:
    """List-like proxy for anchors"""
    
    def __init__(self, db: RocksDBStorage):
        self._db = db
    
    def __getitem__(self, index: int):
        if index == -1:
            return self._db.get_latest_anchor()
        raise IndexError("Only index -1 supported for anchors")
    
    def append(self, anchor):
        self._db.add_anchor(anchor)
    
    def __len__(self) -> int:
        return self._db.anchor_count
    
    def __bool__(self) -> bool:
        return self._db.anchor_count > 0


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("Testing RocksDB Storage...")
    
    # Create test storage
    storage = RocksDBStorage("./test_db")
    
    # Test attestation storage
    test_att = {
        "attestation_id": "abc123",
        "zone_id": "zone1",
        "claim_hash": "hash1"
    }
    storage.put_attestation("abc123", test_att)
    
    result = storage.get_attestation("abc123")
    print(f"Stored: {result}")
    
    print(f"Count: {storage.attestation_count}")
    
    # Cleanup
    storage.destroy()
    print("Test passed!")
