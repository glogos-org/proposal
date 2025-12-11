"""
Glogos High-Throughput Attester - Pydantic v2 Models
Aligned with Glogos Specification v1.0-rc.0

These models support:
- Attestation creation, storage, and verification
- Merkle proof generation and validation
- RFC 9457 error responses
- GLSR (Glogos State Root) anchoring
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
import hashlib
import struct
import time


# =============================================================================
# Core Models (Spec §3)
# =============================================================================

class AttestationCreate(BaseModel):
    """Request to create an attestation"""
    claim: str = Field(..., description="The claim content to be verified")
    evidence: str = Field(..., description="Supporting evidence/proof data")
    canon_id: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$", description="Canon identifier (optional)")
    citations: List[str] = Field(default_factory=list, description="Referenced attestation IDs")


class SignedAttestation(BaseModel):
    """Complete attestation with signature (Spec §3.2)"""
    model_config = ConfigDict(populate_by_name=True)
    
    attestation_id: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    zone_id: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    canon_id: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    claim_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    evidence_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    evidence_location: Optional[str] = Field(None, description="URI where evidence can be retrieved")
    citations: List[str] = Field(default_factory=list)
    timestamp: int = Field(..., ge=0)
    signature: str = Field(..., description="Base64-encoded Ed25519 signature")
    glsr_anchor: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$", description="Glogos State Root reference (optional)")
    
    @staticmethod
    def compute_attestation_id(zone_id: str, canon_id: str, claim_hash: str, timestamp: int) -> str:
        """Compute attestation ID per Spec §3.3"""
        timestamp_bytes = struct.pack('>Q', timestamp)  # 8 bytes, big-endian
        preimage = (
            bytes.fromhex(zone_id) +
            bytes.fromhex(canon_id) +
            bytes.fromhex(claim_hash) +
            timestamp_bytes
        )
        return hashlib.sha256(preimage).hexdigest()
    
    @staticmethod
    def compute_citations_hash(citations: List[str]) -> str:
        """Compute citations hash for signature per Spec §3.4"""
        if not citations:
            return hashlib.sha256(b"").hexdigest()
        sorted_citations = sorted(citations)
        concatenated = "".join(sorted_citations)
        return hashlib.sha256(concatenated.encode('utf-8')).hexdigest()


# =============================================================================
# Bitcoin Anchor Models (Spec §7)
# =============================================================================

class BitcoinAnchor(BaseModel):
    """Bitcoin anchor information (Spec §7.1)"""
    type: Literal["bitcoin"] = "bitcoin"
    txid: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$")
    block_height: Optional[int] = Field(None, ge=0)
    confirmations: int = Field(default=0, ge=0)


# =============================================================================
# Merkle Proof Models (Spec §4)
# =============================================================================

class MerkleProof(BaseModel):
    """Merkle proof format (Spec §4.1)"""
    version: str = Field(default="1.0", pattern=r"^\d+\.\d+$")
    leaf_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    leaf_index: int = Field(..., ge=0)
    proof: List[str] = Field(..., description="Sibling hashes or '*' for duplicate")
    root: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    anchor: Optional[BitcoinAnchor] = None


# =============================================================================
# Response Models (Spec §5)
# =============================================================================

class AttestationResponse(BaseModel):
    """GET /attestation/{id} response (Spec §5.4)"""
    attestation: SignedAttestation
    proof: MerkleProof


class ZoneInfoResponse(BaseModel):
    """GET /zone/info response (Spec §5.3)"""
    zone_id: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    name: str
    description: str
    public_key: str = Field(..., description="Hex-encoded public key")
    public_key_type: Literal["ed25519", "secp256k1"] = "ed25519"
    supported_canons: List[str] = Field(default_factory=list)
    api_version: str = "1.0-rc.0"
    spec_version: str = "1.0-rc.0"
    glsr_reference: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$", description="Glogos State Root")
    glsr_status: Optional[Literal["test", "official"]] = Field(None, description="GLSR status: test or official")
    latest_anchor: Optional[BitcoinAnchor] = None
    endpoints: dict = Field(default_factory=lambda: {
        "attestation": "/attestation/{id}",
        "merkle_root": "/merkle/root",
        "submit": "/verify"
    })


class MerkleRootResponse(BaseModel):
    """GET /merkle/root response"""
    merkle_root: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    attestation_count: int = Field(..., ge=0)
    last_updated: int = Field(default_factory=lambda: int(time.time()))
    anchor: Optional[BitcoinAnchor] = None


# =============================================================================
# Error Models (Spec §6 - RFC 9457)
# =============================================================================

class ProblemDetail(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs (Spec §6.1)"""
    type: str = Field(..., description="Error type URI")
    title: str = Field(..., description="Short, human-readable summary")
    status: int = Field(..., ge=400, le=599, description="HTTP status code")
    detail: Optional[str] = Field(None, description="Detailed explanation")
    instance: Optional[str] = Field(None, description="URI reference for this occurrence")
    retry_after: Optional[int] = Field(None, ge=0, description="Seconds to wait before retry")

