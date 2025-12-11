# Zone API Reference

**Spec Version:** v1.0.0-rc.0  
**Base URL:** `http://localhost:8000`

---

## Zone Interface (Spec §5)

### GET /zone/info

Returns Zone metadata and capabilities.

```json
{
  "zone_id": "sha256-hex-64",
  "name": "Reference Zone",
  "public_key": "ed25519-public-key-hex",
  "supported_canons": ["timestamp:1.0", "lean:4.x", "zk-groth16:1.0"],
  "api_version": "1.0.0-rc.0",
  "glsr_reference": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

---

### GET /attestation/{id}

Returns attestation with Merkle proof.

**Parameters:**

- `id` - 64-character hex attestation ID

```json
{
  "attestation": {
    "attestation_id": "sha256-hex-64",
    "zone_id": "sha256-hex-64",
    "canon_id": "sha256-hex-64",
    "claim_hash": "sha256-hex-64",
    "evidence_hash": "sha256-hex-64",
    "timestamp": 1733424000,
    "signature": "ed25519-signature-hex"
  },
  "proof": {
    "version": "1.0",
    "leaf_hash": "sha256-hex-64",
    "leaf_index": 42,
    "proof": ["hash1", "hash2"],
    "root": "sha256-hex-64"
  }
}
```

---

### GET /merkle/root

Returns current Merkle root.

```json
{
  "merkle_root": "sha256-hex-64",
  "attestation_count": 1000,
  "last_updated": 1733424000
}
```

---

### POST /verify

Create new attestation.

**Request:**

```json
{
  "claim": "Human-readable claim",
  "evidence": "Evidence content",
  "canon_id": "timestamp:1.0"
}
```

---

## Error Responses (RFC 9457)

```json
{
  "type": "https://glogos.org/errors/not-found",
  "title": "Attestation Not Found",
  "status": 404,
  "detail": "Attestation abc123... not found"
}
```

---

## Canon IDs

| Canon      | ID               | Purpose              |
| ---------- | ---------------- | -------------------- |
| Timestamp  | `timestamp:1.0`  | General attestations |
| Lean 4     | `lean:4.x`       | Formal verification  |
| ZK-Groth16 | `zk-groth16:1.0` | Privacy proofs       |

---

**GLSR:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
