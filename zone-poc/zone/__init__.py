"""
Glogos Attester - Reference Implementation
Aligned with Glogos Specification v1.0-rc.0

Usage:
    from attester import MerkleEngine, SigningService
    from attester.models import SignedAttestation, MerkleProof
"""

__version__ = "0.9.0-rc.0"
__spec_version__ = "0.9.0-rc.0"

from .merkle import MerkleEngine, sha256_hex, sha256_bytes
from .signer import SigningService, compute_hash
from .models import (
    SignedAttestation,
    MerkleProof,
    AttestationResponse,
    ZoneInfoResponse,
    MerkleRootResponse,
    ProblemDetail,
)

__all__ = [
    "MerkleEngine",
    "SigningService",
    "SignedAttestation",
    "MerkleProof",
    "AttestationResponse",
    "ZoneInfoResponse",
    "MerkleRootResponse",
    "ProblemDetail",
    "sha256_hex",
    "sha256_bytes",
    "compute_hash",
]
