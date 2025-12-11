"""
Glogos High-Throughput Zone - Ed25519 Signing Service
Aligned with Glogos Specification v1.0.0-rc.0 §3.4

Provides:
- Key generation/loading
- Attestation signing per Spec
- Zone ID computation (SHA256 of public key)
"""

import os
import hashlib
import struct
import base64
from typing import Optional, Tuple, List
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


class SigningService:
    """
    Ed25519 signing service for Glogos Zone.
    
    Key can be loaded from:
    1. Environment variable (ZONE_PRIVATE_KEY as hex)
    2. PEM file on disk
    3. Auto-generated (for development)
    """
    
    def __init__(
        self,
        key_path: Optional[str] = None,
        key_env: str = "ZONE_PRIVATE_KEY",
        auto_generate: bool = True
    ):
        self._private_key: Optional[Ed25519PrivateKey] = None
        self._public_key_bytes: Optional[bytes] = None
        self._zone_id: Optional[str] = None
        
        # Try loading key from various sources
        loaded = False
        
        # 1. Try environment variable
        if key_env and os.environ.get(key_env):
            self._load_from_hex(os.environ[key_env])
            loaded = True
        
        # 2. Try file path
        elif key_path and Path(key_path).exists():
            self._load_from_pem(key_path)
            loaded = True
        
        # 3. Auto-generate for development
        elif auto_generate:
            self._generate_new_key()
            loaded = True
        
        if not loaded:
            raise ValueError("No private key available. Set ZONE_PRIVATE_KEY env or provide key_path.")
        
        # Compute derived values
        self._compute_derived_values()
    
    def _load_from_hex(self, hex_key: str) -> None:
        """Load private key from hex string"""
        key_bytes = bytes.fromhex(hex_key)
        self._private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
    
    def _load_from_pem(self, path: str) -> None:
        """Load private key from PEM file"""
        with open(path, 'rb') as f:
            self._private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
    
    def _generate_new_key(self) -> None:
        """Generate new Ed25519 keypair"""
        self._private_key = Ed25519PrivateKey.generate()
    
    def _compute_derived_values(self) -> None:
        """Compute public key bytes and zone ID"""
        public_key = self._private_key.public_key()
        self._public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        # Zone ID = SHA256(public_key_bytes) per Spec §3.2
        self._zone_id = hashlib.sha256(self._public_key_bytes).hexdigest()
    
    @property
    def public_key_hex(self) -> str:
        """Return 64-char hex public key for /zone/info"""
        return self._public_key_bytes.hex()
    
    @property
    def zone_id(self) -> str:
        """Zone ID = SHA256(public_key_bytes)"""
        return self._zone_id
    
    def save_keys(self, private_path: str, public_path: Optional[str] = None) -> None:
        """Save keypair to PEM files"""
        # Private key
        private_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(private_path, 'wb') as f:
            f.write(private_pem)
        
        # Public key (optional)
        if public_path:
            public_key = self._private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open(public_path, 'wb') as f:
                f.write(public_pem)
    
    def compute_attestation_id(
        self,
        canon_id: str,
        claim_hash: str,
        timestamp: int
    ) -> str:
        """
        Compute attestation ID per Spec §3.3
        
        attestation_id = SHA256(zone_id || canon_id || claim_hash || timestamp_bytes)
        """
        timestamp_bytes = struct.pack('>Q', timestamp)  # 8 bytes, big-endian
        preimage = (
            bytes.fromhex(self._zone_id) +
            bytes.fromhex(canon_id) +
            bytes.fromhex(claim_hash) +
            timestamp_bytes
        )
        return hashlib.sha256(preimage).hexdigest()
    
    def compute_sign_data(
        self,
        attestation_id: str,
        claim_hash: str,
        evidence_hash: str,
        timestamp: int,
        citations: Optional[List[str]] = None
    ) -> bytes:
        """
        Compute data to be signed per Spec §3.4
        
        sign_data = attestation_id || claim_hash || evidence_hash || 
                    timestamp_bytes || citations_hash
        """
        timestamp_bytes = struct.pack('>Q', timestamp)
        
        # Compute citations hash
        if citations:
            sorted_citations = sorted(citations)
            citations_concat = "".join(sorted_citations)
            citations_hash = hashlib.sha256(citations_concat.encode('utf-8')).digest()
        else:
            citations_hash = hashlib.sha256(b"").digest()
        
        sign_data = (
            bytes.fromhex(attestation_id) +
            bytes.fromhex(claim_hash) +
            bytes.fromhex(evidence_hash) +
            timestamp_bytes +
            citations_hash
        )
        return sign_data
    
    def sign_attestation(
        self,
        attestation_id: str,
        claim_hash: str,
        evidence_hash: str,
        timestamp: int,
        citations: Optional[List[str]] = None
    ) -> str:
        """
        Sign attestation fields and return base64-encoded signature.
        """
        sign_data = self.compute_sign_data(
            attestation_id, claim_hash, evidence_hash, timestamp, citations
        )
        signature_bytes = self._private_key.sign(sign_data)
        return base64.b64encode(signature_bytes).decode('ascii')
    
    def verify_attestation(
        self,
        attestation_id: str,
        claim_hash: str,
        evidence_hash: str,
        timestamp: int,
        citations: Optional[List[str]],
        signature_b64: str,
        public_key_hex: Optional[str] = None
    ) -> bool:
        """
        Verify an attestation signature.
        
        If public_key_hex is provided, use that key.
        Otherwise, use this Zone's public key.
        """
        sign_data = self.compute_sign_data(
            attestation_id, claim_hash, evidence_hash, timestamp, citations
        )
        signature_bytes = base64.b64decode(signature_b64)
        
        # Get public key
        if public_key_hex:
            public_key_bytes = bytes.fromhex(public_key_hex)
            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        else:
            public_key = self._private_key.public_key()
        
        try:
            public_key.verify(signature_bytes, sign_data)
            return True
        except InvalidSignature:
            return False


# =============================================================================
# Convenience functions
# =============================================================================

def compute_hash(data: str) -> str:
    """Compute SHA256 hash of string data"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_canon_id(name: str, version: str) -> str:
    """
    Compute Canon ID per Spec §8.1
    
    canon_id = SHA256(name || ":" || version)
    """
    input_str = f"{name}:{version}"
    return hashlib.sha256(input_str.encode('utf-8')).hexdigest()


# Pre-computed Canon IDs (Spec §8.2)
CANON_IDS = {
    "timestamp:1.0": compute_canon_id("timestamp", "1.0"),
    "lean:4.x": compute_canon_id("lean", "4.x"),
    "coq:8.x": compute_canon_id("coq", "8.x"),
    "test-result:1.0": compute_canon_id("test-result", "1.0"),
    "livelihoods:1.0": compute_canon_id("livelihoods", "1.0"),  # v1.0.0-rc.0: Sinh kế
    "medical:1.0": compute_canon_id("medical", "1.0"),          # v1.0.0-rc.0: Y tế
}

# Default Canon for simple attestations
DEFAULT_CANON_ID = CANON_IDS["timestamp:1.0"]
