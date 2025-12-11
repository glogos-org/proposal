#!/usr/bin/env python3
"""
Quick test script for Glogos Zone Reference
Run this to verify the attestation flow works correctly.

Usage:
    cd zone-poc
    pip install -r requirements.txt
    python -m tests.test_quick
"""

import sys
import os

# Add parent to path for zone import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from zone.signer import SigningService, compute_hash, compute_canon_id, CANON_IDS
from zone.merkle import MerkleEngine

def main():
    print("=" * 60)
    print("  GLOGOS ATTESTATION FLOW TEST")
    print("=" * 60)
    print()
    
    # 1. Initialize signer
    print("[1] Creating Attester identity...")
    signer = SigningService(auto_generate=True)
    print(f"    Attester ID: {signer.zone_id[:16]}...")
    print(f"    Public Key:  {signer.public_key_hex[:16]}...")
    print()
    
    # 2. Create a test attestation
    print("[2] Creating test attestation...")
    
    claim = "This is a test claim for Glogos v1.0.0"
    evidence = "Test evidence data"
    
    claim_hash = compute_hash(claim)
    evidence_hash = compute_hash(evidence)
    timestamp = 1733558400  # Fixed timestamp for reproducibility
    canon_id = CANON_IDS["timestamp:1.0"]
    
    print(f"    Claim hash:    {claim_hash[:16]}...")
    print(f"    Evidence hash: {evidence_hash[:16]}...")
    print(f"    Canon ID:      {canon_id[:16]}...")
    print()
    
    # 3. Compute attestation ID
    print("[3] Computing attestation ID...")
    attestation_id = signer.compute_attestation_id(
        canon_id=canon_id,
        claim_hash=claim_hash,
        timestamp=timestamp
    )
    print(f"    Attestation ID: {attestation_id}")
    print()
    
    # 4. Sign attestation
    print("[4] Signing attestation...")
    signature = signer.sign_attestation(
        attestation_id=attestation_id,
        claim_hash=claim_hash,
        evidence_hash=evidence_hash,
        timestamp=timestamp,
        citations=[]
    )
    print(f"    Signature: {signature[:32]}...")
    print()
    
    # 5. Verify signature
    print("[5] Verifying signature...")
    is_valid = signer.verify_attestation(
        attestation_id=attestation_id,
        claim_hash=claim_hash,
        evidence_hash=evidence_hash,
        timestamp=timestamp,
        citations=[],
        signature_b64=signature
    )
    print(f"    Valid: {is_valid}")
    print()
    
    # 6. Add to Merkle tree
    print("[6] Building Merkle tree...")
    merkle = MerkleEngine()
    
    # Add multiple attestations for realistic tree
    attestation_ids = [attestation_id]
    for i in range(4):
        aid = compute_hash(f"additional_attestation_{i}")
        attestation_ids.append(aid)
        merkle.add_leaf(aid)
    
    merkle.add_leaf(attestation_id)
    
    root = merkle.compute_root()
    print(f"    Leaf count:  {merkle.leaf_count}")
    print(f"    Merkle root: {root}")
    print()
    
    # 7. Generate Merkle proof
    print("[7] Generating Merkle proof...")
    proof = merkle.generate_proof(attestation_id)
    print(f"    Leaf index: {proof['leaf_index']}")
    print(f"    Proof path: {len(proof['proof'])} siblings")
    print()
    
    # 8. Verify Merkle proof
    print("[8] Verifying Merkle proof...")
    proof_valid = MerkleEngine.verify_proof(
        leaf_hash=proof['leaf_hash'],
        leaf_index=proof['leaf_index'],
        proof=proof['proof'],
        expected_root=proof['root']
    )
    print(f"    Valid: {proof_valid}")
    print()
    
    # Summary
    print("=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)
    print(f"""
Results:
  [OK] Attester identity created
  [OK] Attestation ID computed
  [OK] Signature: {'VALID' if is_valid else 'INVALID'}
  [OK] Merkle root: {root[:16]}...
  [OK] Proof: {'VALID' if proof_valid else 'INVALID'}

Full Attestation:
{{
  "attestation_id": "{attestation_id}",
  "attester_id": "{signer.zone_id}",
  "canon_id": "{canon_id}",
  "claim_hash": "{claim_hash}",
  "evidence_hash": "{evidence_hash}",
  "timestamp": {timestamp},
  "signature": "{signature[:40]}..."
}}
""")
    
    return is_valid and proof_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
