"""
Glogos High-Throughput Attester - FastAPI Application
Aligned with Glogos Specification v1.0-rc.0

Implements Attester Interface (Spec §5):
- GET /attester/info
- GET /attestation/{id}
- GET /merkle/root
- POST /verify

Additional endpoints:
- GET /health
"""

import hashlib
import time
import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .models import (
    AttestationCreate,
    SignedAttestation,
    MerkleProof,
    BitcoinAnchor,
    AttestationResponse,
    ZoneInfoResponse,
    MerkleRootResponse,
    ProblemDetail,
)
from .signer import SigningService, compute_hash, DEFAULT_CANON_ID, CANON_IDS
from .merkle import MerkleEngine


# =============================================================================
# In-Memory Storage (Replace with RocksDB for development)
# =============================================================================

class Storage:
    """Simple in-memory storage for MVP"""
    
    def __init__(self):
        self.attestations: dict[str, SignedAttestation] = {}
        self.evidence: dict[str, str] = {}  # attestation_id -> evidence content
        self.anchors: list[BitcoinAnchor] = []


# =============================================================================
# Application Lifespan
# =============================================================================

storage = Storage()
signer = SigningService(auto_generate=True)
merkle = MerkleEngine()

# Zone configuration
ZONE_NAME = os.environ.get("ZONE_NAME", "Glogos High-Throughput Zone")
ZONE_DESCRIPTION = os.environ.get(
    "ZONE_DESCRIPTION", 
    "Development-ready Zone implementing Glogos Specification v1.0.0-rc.0"
)

# GLSR configuration - SHA256("") = e3b0c44298fc1c14...
# This is the IMMUTABLE Glogos State Root per Spec §2.2
GLSR = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
GLSR_STATUS = "official"  # GLSR is fixed forever (mathematical constant)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown"""
    print(f"[GO] Starting {ZONE_NAME}")
    print(f"   Zone ID: {signer.zone_id}")
    print(f"   Public Key: {signer.public_key_hex[:16]}...")
    print(f"   Spec Version: 1.0-rc.0")
    print(f"   GLSR: {GLSR[:16]}... ({GLSR_STATUS})")
    yield
    print(f"👋 Shutting down {ZONE_NAME}")


app = FastAPI(
    title="Glogos High-Throughput Attester",
    description="Implementation of Glogos Specification v1.0-rc.0",
    version="1.0-rc.0",
    lifespan=lifespan
)


# =============================================================================
# RFC 9457 Error Handling (Spec §6)
# =============================================================================

def create_problem_detail(
    type_suffix: str,
    title: str,
    status: int,
    detail: str,
    instance: Optional[str] = None,
    retry_after: Optional[int] = None
) -> ProblemDetail:
    """Create RFC 9457 Problem Detail"""
    return ProblemDetail(
        type=f"https://glogos.org/errors{type_suffix}",
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        retry_after=retry_after
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTPException to RFC 9457 format"""
    problem = create_problem_detail(
        type_suffix="/http-error",
        title=str(exc.detail) if isinstance(exc.detail, str) else "Error",
        status=exc.status_code,
        detail=str(exc.detail),
        instance=str(request.url.path)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(exclude_none=True),
        headers={"Content-Type": "application/problem+json"}
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    problem = create_problem_detail(
        type_suffix="/invalid-request",
        title="Invalid Request",
        status=400,
        detail=str(exc),
        instance=str(request.url.path)
    )
    return JSONResponse(
        status_code=400,
        content=problem.model_dump(exclude_none=True),
        headers={"Content-Type": "application/problem+json"}
    )


# =============================================================================
# Zone Interface Endpoints (Spec §5)
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API overview"""
    return {
        "name": ZONE_NAME,
        "version": "1.0-rc.0",
        "specification": "Glogos Protocol v1.0-rc.0",
        "zone_id": signer.zone_id,
        "glsr": GLSR,
        "glsr_status": GLSR_STATUS,
        "endpoints": {
            "zone_info": "/zone/info",
            "attestation": "/attestation/{id}",
            "merkle_root": "/merkle/root",
            "verify": "/verify",
            "health": "/health"
        }
    }


@app.get("/zone/info", response_model=ZoneInfoResponse, tags=["Zone Interface"])
async def get_zone_info():
    """
    GET /zone/info - Specification §5.3
    
    Returns Zone metadata and capabilities.
    """
    latest_anchor = storage.anchors[-1] if storage.anchors else None
    
    return ZoneInfoResponse(
        zone_id=signer.zone_id,
        name=ZONE_NAME,
        description=ZONE_DESCRIPTION,
        public_key=signer.public_key_hex,
        public_key_type="ed25519",
        supported_canons=list(CANON_IDS.keys()),
        api_version="0.5.1",
        spec_version="0.5.1",
        glsr_reference=GLSR,
        glsr_status=GLSR_STATUS,
        latest_anchor=latest_anchor,
        endpoints={
            "attestation": "/attestation/{id}",
            "merkle_root": "/merkle/root",
            "submit": "/verify"
        }
    )


@app.get("/attestation/{attestation_id}", response_model=AttestationResponse, tags=["Zone Interface"])
async def get_attestation(attestation_id: str):
    """
    GET /attestation/{id} - Specification §5.4
    
    Returns attestation with Merkle proof.
    """
    attestation_id = attestation_id.lower()
    
    # Validate format
    if len(attestation_id) != 64:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid attestation ID format. Expected 64 hex characters, got {len(attestation_id)}"
        )
    
    # Lookup attestation
    print(f"[DEBUG] Looking up: {attestation_id[:16]}... in {len(storage.attestations)} attestations")
    print(f"[DEBUG] Storage keys: {list(storage.attestations.keys())[:3] if storage.attestations else 'empty'}")
    attestation = storage.attestations.get(attestation_id)
    if not attestation:
        raise HTTPException(
            status_code=404,
            detail=f"Attestation {attestation_id[:16]}... not found"
        )
    
    # Generate Merkle proof
    proof_data = merkle.generate_proof(attestation_id)
    if not proof_data:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate Merkle proof"
        )
    
    # Get anchor info
    anchor = storage.anchors[-1] if storage.anchors else BitcoinAnchor(
        type="bitcoin",
        confirmations=0
    )
    
    proof = MerkleProof(
        version=proof_data["version"],
        leaf_hash=proof_data["leaf_hash"],
        leaf_index=proof_data["leaf_index"],
        proof=proof_data["proof"],
        root=proof_data["root"],
        anchor=anchor
    )
    
    return AttestationResponse(
        attestation=attestation,
        proof=proof
    )


@app.get("/merkle/root", response_model=MerkleRootResponse, tags=["Zone Interface"])
async def get_merkle_root():
    """
    GET /merkle/root - Specification §5
    
    Returns current Merkle root and anchor info.
    """
    root = merkle.compute_root()
    anchor = storage.anchors[-1] if storage.anchors else None
    
    return MerkleRootResponse(
        merkle_root=root,
        attestation_count=merkle.leaf_count,
        last_updated=int(time.time()),
        anchor=anchor
    )


@app.post("/verify", response_model=AttestationResponse, tags=["Zone Interface"])
async def create_attestation(request: AttestationCreate):
    """
    POST /verify - Create new attestation
    
    This endpoint receives a claim and evidence, verifies them (Zone-specific),
    and creates a signed attestation.
    """
    start_time = time.perf_counter()
    
    # Compute hashes
    claim_hash = compute_hash(request.claim)
    evidence_hash = compute_hash(request.evidence)
    timestamp = int(time.time())
    
    # Determine Canon ID
    canon_id = request.canon_id or DEFAULT_CANON_ID
    
    # Compute attestation ID
    attestation_id = signer.compute_attestation_id(
        canon_id=canon_id,
        claim_hash=claim_hash,
        timestamp=timestamp
    )
    
    # Sign attestation
    signature = signer.sign_attestation(
        attestation_id=attestation_id,
        claim_hash=claim_hash,
        evidence_hash=evidence_hash,
        timestamp=timestamp,
        citations=request.citations
    )
    
    # Create attestation object
    attestation = SignedAttestation(
        attestation_id=attestation_id,
        zone_id=signer.zone_id,
        canon_id=canon_id,
        claim_hash=claim_hash,
        evidence_hash=evidence_hash,
        evidence_location=f"memory://{attestation_id}",
        citations=request.citations,
        timestamp=timestamp,
        signature=signature,
        glsr_anchor=GLSR  # Optional GLSR anchoring
    )
    
    # Store attestation and evidence (normalize to lowercase for consistent lookup)
    storage.attestations[attestation_id.lower()] = attestation
    storage.evidence[attestation_id.lower()] = request.evidence
    print(f"[DEBUG] Stored attestation: {attestation_id.lower()[:16]}... (total: {len(storage.attestations)})")
    
    # Add to Merkle tree
    merkle.add_leaf(attestation_id)
    
    # Generate proof
    proof_data = merkle.generate_proof(attestation_id)
    anchor = storage.anchors[-1] if storage.anchors else BitcoinAnchor(
        type="bitcoin",
        confirmations=0
    )
    
    proof = MerkleProof(
        version=proof_data["version"],
        leaf_hash=proof_data["leaf_hash"],
        leaf_index=proof_data["leaf_index"],
        proof=proof_data["proof"],
        root=proof_data["root"],
        anchor=anchor
    )
    
    return AttestationResponse(
        attestation=attestation,
        proof=proof
    )


# =============================================================================
# Additional Endpoints
# =============================================================================

@app.get("/health", tags=["Operations"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "zone_id": signer.zone_id,
        "attestation_count": len(storage.attestations),
        "merkle_root": merkle.compute_root(),
        "timestamp": int(time.time())
    }





# =============================================================================
# Run with Uvicorn
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"\n{'='*60}")
    print(f"  Glogos High-Throughput Zone v1.0.0-rc.0")
    print(f"{'='*60}")
    print(f"  Zone ID: {signer.zone_id}")
    print(f"  GLSR: {GLSR[:16]}... ({GLSR_STATUS})")
    print(f"  Listening: http://{host}:{port}")
    print(f"  Docs: http://{host}:{port}/docs")
    
    print(f"{'='*60}\n")
    
    uvicorn.run(app, host=host, port=port)
