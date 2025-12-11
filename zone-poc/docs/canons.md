# Canon Implementation Guide

**Spec Version:** v1.0.0-rc.0

---

## What is a Canon?

A Canon defines rules for verifying a specific type of claim:

- Unique ID (e.g., `lean:4.x`)
- Claim structure
- Verification logic
- Attestation evidence

---

## Available Canons

### 1. Timestamp (`timestamp:1.0`)

General timestamping - "This data existed at time T"

```python
attestation = create_attestation(
    claim="Document hash: abc123...",
    evidence="Original document content",
    canon_id="timestamp:1.0"
)
```

---

### 2. Lean 4 (`lean:4.x`)

Formal verification - "This theorem is mathematically proven"

```python
from zone.canons import Lean4Canon, Lean4Proof

canon = Lean4Canon(simulation=True)
proof = Lean4Proof(
    theorem_name="glsr_determinism",
    theorem_statement="GLSR computation is deterministic",
    proof_code="theorem glsr_determinism : ... := by rfl"
)
attestation = canon.create_attestation(proof)
```

---

### 3. ZK-Groth16 (`zk-groth16:1.0`)

Privacy-preserving - "I prove X without revealing Y"

```python
from zone.canons import ZKGroth16Canon

canon = ZKGroth16Canon()
canon.register_circuit("age-verification", verification_key)
attestation = canon.create_attestation(
    claim="Age >= 18",
    circuit_id="age-verification",
    proof=groth16_proof,
    public_signals=["18"]
)
```

---

## Implementing a New Canon

```python
# zone/canons/my_canon.py

class MyCanon:
    CANON_ID = "my-canon:1.0"

    def verify(self, claim: str, evidence: dict) -> bool:
        return True

    def create_attestation(self, claim: str, evidence: dict):
        if not self.verify(claim, evidence):
            return None
        return MyCanonAttestation(...)
```

---

## Best Practices

1. **Clear Canon ID** - Use format `category:version`
2. **Immutable verification** - Same input → same result
3. **Error handling** - Return None on failure
4. **Testing** - Include simulation mode

---

**GLSR:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
