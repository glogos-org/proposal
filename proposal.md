# Glogos: A Consensus-Free Attestation Proposal

**Version 1.0.0-rc.0**  
**Draft – December 2025**

---

## PREAMBLE

| Field   | Value                       |
| ------- | --------------------------- |
| Witness | Le Manh Thanh               |
| Status  | Release Candidate           |
| Type    | Standards Track             |
| Created | 2025-10                     |
| Updated | 2025-12-10                  |
| License | CC-BY-4.0 (doc), MIT (code) |

---

## ABSTRACT

Glogos is a proposal for **consensus-free attestation**. It defines how independent systems ("Zones") can create cryptographically-signed attestation records, organize them in Merkle trees, and anchor roots through various mechanisms—without requiring network consensus.

**Key insight:** Unlike blockchains that require network-wide agreement, Glogos records exist independently. Each Zone is sovereign. Trust is per-Zone, not protocol-wide.

This proposal builds on existing work: Merkle trees (1979) and standard cryptographic primitives (SHA-256, Ed25519).

**What this proposal provides:**

- A standard attestation record format
- Zone interface requirements for interoperability
- Merkle proof format for verification
- Anchoring format for Merkle roots (multiple methods supported)
- Error response format for APIs
- Optional federation patterns for cost sharing

**What this proposal does NOT provide:**

- A new blockchain or consensus mechanism
- Token economics or incentive design
- **Content verification** (Zones implement their own verification logic)
- **Trust guarantees** (trust is per-Zone, not protocol-enforced)
- Storage solutions (Zones choose their own)

**Target applications:**

- Long-term institutional archives
- Scientific research data timestamping and reproducibility verification
- Academic credential attestation in environments with limited trust infrastructure
- Document verification in low-connectivity or resource-constrained settings

**Status:** This is an experimental proposal with no production implementations. The author makes no claims about adoption or market demand.

---

## DESIGN PRINCIPLES

Glogos is built on four foundational principles that guide all design decisions:

### Eternity

Designed for long-term verification independent of infrastructure. The Glogos State Root (GLSR) remains verifiable with only:

- Mathematical knowledge (SHA256 algorithm, published and archived)
- The empty string (0 bytes)

No private keys, no blockchain access, no internet required for verification.

### Neutrality

Attestations are not controlled by any single entity:

- GLSR is derived from mathematics (SHA256 of empty string), not opinion
- Zones are sovereign and independent
- No protocol token, no foundation, no central coordinator

### Sovereignty

Each Zone defines its own:

- **Verification logic** — formal proofs, credential checks, editorial review, etc.
- **Economic model** — free, paid, subscription, token-gated
- **Governance** — individual, DAO, consortium, committee
- **Storage** — centralized, IPFS, Arweave, local files
- **Access control** — public, permissioned, private

### Simplicity

Minimal dependencies for maximum longevity:

- Core proposal uses only SHA256 (FIPS 180-4, 1995)
- No complex cryptography in base layer
- Zones may add complexity; base layer remains simple

---

## TERMINOLOGY

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

---

## TABLE OF CONTENTS

**PART I: CORE Proposal**

1. Proposal Architecture
2. Glogos State Root (GLSR)
3. Attestation Format
4. Merkle Proof Format
5. Zone Interface
6. Error Responses
7. Anchoring Methods

**PART II: OPTIONAL EXTENSIONS**

8. Canon Registry
9. Citation Protocol
10. Zone Discovery
11. Federation Interface

**PART III: SECURITY & OPERATIONS**

12. Security Considerations

**APPENDICES**

- A. Cryptographic proposals
- B. JSON Schemas
- C. Test Vectors
- D. Related Work
- Z. Invitation to Witness

---

# PART I: CORE PROPOSAL

## 1. Proposal Architecture

### 1.1 Three-Tier Mutability

This proposal distinguishes between components with different mutability properties:

| Tier                   | Mutability                     | Components                                                       |
| ---------------------- | ------------------------------ | ---------------------------------------------------------------- |
| **Foundational**       | Immutable forever              | Empty axiom, GLSR computation                                    |
| **Interface Standard** | Versioned, backward compatible | Endpoint proposals, JSON schemas, Merkle tree rules, error codes |
| **Recommendations**    | Non-binding, advisory          | Example implementations, best practices, discovery mechanisms    |

### 1.2 Version Evolution

**This proposal** follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR:** Breaking changes to mandatory interfaces
- **MINOR:** New optional features, backward compatible
- **PATCH:** Clarifications, test vector additions

The GLSR exists as a mathematical constant (`SHA256("")`) that requires no anchoring.
Anyone can verify it independently with a single hash computation.

Genesis witnesses the GLSR and creates an attestation for this proposal.
The attestation (not the GLSR) is anchored to external systems.

Once this proposal is finalized:

- The GLSR computation is immutable forever
- Core proposal (GLSR, Attestation Format) is frozen
- Only extensions and new Zone interfaces may be added

> **Note:** Zones are sovereign and may use any versioning scheme they choose. This section applies only to the Glogos Proposal itself.

### 1.3 GLSR Permanence Guarantee

The Glogos State Root (GLSR) is a single, immutable hash anchored via multiple methods. No proposal version change can ever modify the GLSR. This guarantee is absolute and unconditional.

**Long-Term Verification:**

GLSR can be verified indefinitely with:

1. The string "" (empty string)
2. Published SHA256 algorithm

No private keys. No blockchain access. No internet. Only mathematics.

---

## 2. Glogos State Root (GLSR)

### 2.1 Purpose

The GLSR is a 32-byte hash that serves as a unique identifier for this proposal. It is computed once and anchored via multiple methods to establish a verifiable timestamp for the proposal's existence.

### 2.2 Computation

The GLSR is a single, immutable hash:

```
GLSR = H("")
```

Where:

- `H` is SHA256
- `""` is the empty string (0 bytes)

**Result:**

```
GLSR = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

This is the SHA256 hash of the empty string — the simplest possible genesis.

**Immutability guarantee:** The GLSR is fixed forever. No external data, no private keys, no dependencies. Anyone can verify it with a single SHA256 call. The mainnet ceremony anchors this value to a specific timestamp but does not compute it.

---

## 3. Attestation Format

### 3.1 Structure

An attestation is a JSON object representing an Zone's verification of some claim:

```json
{
  "attestation_id": "a1b2c3d4...",
  "zone_id": "e5f6a7b8...",
  "canon_id": "c9d0e1f2...",
  "claim_hash": "1234abcd...",
  "evidence_hash": "5678efgh...",
  "evidence_location": "ipfs://Qm... or https://...",
  "citations": ["cited_id_1", "cited_id_2"],
  "timestamp": 1766329380,
  "signature": "base64_signature"
}
```

### 3.2 Field Definitions

| Field             | Required | Type    | Description                                                          |
| ----------------- | -------- | ------- | -------------------------------------------------------------------- |
| attestation_id    | MUST     | hex64   | `SHA256(zone_id \|\| canon_id \|\| claim_hash \|\| timestamp_bytes)` |
| zone_id           | MUST     | hex64   | `SHA256(public_key_bytes)` — cryptographic binding to Zone identity  |
| canon_id          | MUST     | hex64   | Identifier for the verification system used                          |
| claim_hash        | MUST     | hex64   | SHA256 of the claim content being attested                           |
| evidence_hash     | MUST     | hex64   | SHA256 of supporting evidence                                        |
| evidence_location | MAY      | string  | URI where evidence can be retrieved                                  |
| citations         | MAY      | array   | Array of attestation_ids being referenced                            |
| timestamp         | MUST     | integer | Unix epoch seconds when attestation was created                      |
| signature         | MUST     | base64  | Zone's Ed25519 or secp256k1 signature over attestation fields        |

> **Zone ID Security:** The `zone_id` is computed as `SHA256(public_key_bytes)` where `public_key_bytes` is the raw 32-byte Ed25519 public key (or 33-byte compressed secp256k1 key). This creates a cryptographic binding that prevents identity spoofing — anyone can verify that a claimed Zone ID matches the public key without trusting external lookups.

### 3.3 Attestation ID Computation

```
FUNCTION compute_attestation_id(zone_id, canon_id, claim_hash, timestamp):
    INPUT:  zone_id, canon_id, claim_hash as 32-byte values
            timestamp as unsigned 64-bit integer

    timestamp_bytes ← timestamp encoded as 8-byte big-endian
    preimage ← zone_id || canon_id || claim_hash || timestamp_bytes
    RETURN SHA256(preimage) as lowercase hexadecimal string
```

### 3.4 Signature Coverage

The signature MUST cover the following fields in order:

```
sign_data = attestation_id || claim_hash || evidence_hash || timestamp_bytes || citations_hash
```

Where `citations_hash = SHA256(sorted(citations).join(""))` or `SHA256("")` if empty.

### 3.5 Attestation Semantics

**What an attestation proves:**

- "Zone X recorded claim Y at time T"
- The attestation is cryptographically signed by Zone X
- The attestation is included in a Merkle tree
- The Merkle root is anchored (timestamped)

**What an attestation does NOT prove:**

- ❌ The claim Y is true
- ❌ The verification was performed correctly
- ❌ Zone X is trustworthy

**Trust model:** Users must evaluate each Zone's reputation, verification logic, and track record independently. Glogos provides the record-keeping infrastructure, not the verification guarantees.

---

## 4. Merkle Proof Format

### 4.1 Proof Structure

Zones MUST return Merkle proofs using the following JSON structure:

```json
{
  "version": "1.0",
  "leaf_hash": "a1b2c3d4e5f6...",
  "leaf_index": 42,
  "proof": ["sibling_hash_1", "sibling_hash_2", "*", "sibling_hash_4"],
  "root": "merkle_root_hash",
  "anchor": {
    "type": "newspaper",
    "publications": ["NYT", "Guardian"],
    "date": "2025-12-21"
  }
}
```

### 4.2 Field Definitions

| Field      | Required | Description                                      |
| ---------- | -------- | ------------------------------------------------ |
| version    | MUST     | Proof format version, currently "1.0"            |
| leaf_hash  | MUST     | The attestation_id being proven                  |
| leaf_index | MUST     | Position in the sorted leaf array (0-indexed)    |
| proof      | MUST     | Array of sibling hashes from leaf to root        |
| root       | MUST     | Expected Merkle root                             |
| anchor     | SHOULD   | Anchor information (newspaper, blockchain, etc.) |

### 4.3 Positional Index Algorithm

Direction is computed from leaf_index, eliminating explicit left/right flags:

```
FUNCTION verify_merkle_proof(leaf_hash, leaf_index, proof, expected_root):
    INPUT:  leaf_hash as 32-byte value (hex string)
            leaf_index as integer (0-indexed position in sorted leaves)
            proof as array of sibling hashes (hex strings, or "*" for duplicate)
            expected_root as 32-byte value (hex string)
    OUTPUT: TRUE if proof is valid, FALSE otherwise

    current ← decode_hex(leaf_hash)
    index ← leaf_index

    FOR EACH sibling IN proof:
        IF sibling = "*" THEN
            sibling_hash ← current  // Duplicate marker
        ELSE
            sibling_hash ← decode_hex(sibling)
        END IF

        IF index MOD 2 = 0 THEN
            // Current is LEFT child
            current ← SHA256(current || sibling_hash)
        ELSE
            // Current is RIGHT child
            current ← SHA256(sibling_hash || current)
        END IF

        index ← FLOOR(index / 2)
    END FOR

    RETURN current = decode_hex(expected_root)
```

### 4.4 Merkle Tree Construction Rules

1. Collect all attestation_ids as leaf nodes
2. Sort leaves lexicographically (lowercase hex)
3. Build binary tree: `internal_node = SHA256(left || right)`
4. Odd leaf count: duplicate the last leaf to create a pair for hashing (e.g., `node = SHA256(last_leaf || last_leaf)`). The proof for this leaf MAY use `"*"` as a shorthand for its sibling hash.
5. Empty tree: `root = SHA256("")`

> **Note:** The `"*"` marker in proofs is shorthand for "duplicate this hash". Implementations MAY also use explicit duplication (writing the hash twice) per RFC 6962. Both approaches produce identical Merkle roots.

**Duplicate marker rules:**

1. The `"*"` marker MUST only appear when handling odd leaf count at the bottom layer
2. Internal tree layers MUST NOT use `"*"` (odd nodes at internal layers are handled by tree construction, not proof encoding)
3. A proof array MUST contain at most one `"*"` marker
4. Zones MAY require explicit-only proofs (no `"*"` allowed) by declaring this in their Zone info

---

## 5. Zone Interface

### 5.1 Definition

An **Zone** is any system that:

1. Creates attestations following this proposal
2. Maintains a Merkle tree of attestations
3. Periodically anchors Merkle roots
4. Exposes the required HTTP endpoints

Zones are fully sovereign and may operate in different modes:

| Mode            | Description                   | Characteristics                                                   |
| --------------- | ----------------------------- | ----------------------------------------------------------------- |
| **Independent** | Single entity operation       | Own keys, policies, verification logic                            |
| **Federated**   | Multiple entities cooperating | Shared anchoring costs, independent attestations (see Section 11) |
| **Hub-based**   | Centralized service           | Multiple clients, shared infrastructure                           |

**Sovereignty principle:** Zones choose their own verification logic, storage systems, economic model, and policies. The protocol provides the interface, not the implementation.

**Trust model:** Trust is per-Zone, not protocol-wide. Verifiers evaluate each Zone's reputation independently.

**Terminology note:** The term "Zone" applies to the system as a whole, regardless of whether it operates independently, as part of a federation, or as a centralized hub.

### 5.2 Required Endpoints

| Endpoint            | Method | Description                         |
| ------------------- | ------ | ----------------------------------- |
| `/zone/info`        | GET    | Zone metadata and capabilities      |
| `/attestation/{id}` | GET    | Attestation with Merkle proof       |
| `/merkle/root`      | GET    | Current Merkle root and anchor info |

### 5.3 Zone Info Response

```json
{
  "zone_id": "e5f6a7b8...",
  "name": "Example Verification Zone",
  "description": "Verifies Lean 4 mathematical proofs",
  "public_key": "ed25519_public_key_hex",
  "public_key_type": "ed25519",
  "supported_canons": ["canon_id_1", "canon_id_2"],
  "api_version": "1.0.0",
  "latest_anchor": {
    "merkle_root": "abcd1234...",
    "anchor_type": "newspaper",
    "anchor_ref": "NYT 2025-12-21",
    "timestamp": 1766329380
  },
  "endpoints": {
    "attestation": "/attestation/{id}",
    "merkle_root": "/merkle/root",
    "submit": "/verify"
  }
}
```

### 5.4 Attestation Response

```json
{
  "attestation": {
    "attestation_id": "...",
    "zone_id": "...",
    "canon_id": "...",
    "claim_hash": "...",
    "evidence_hash": "...",
    "evidence_location": "...",
    "citations": [],
    "timestamp": 1766329380,
    "signature": "..."
  },
  "proof": {
    "version": "1.0",
    "leaf_hash": "...",
    "leaf_index": 42,
    "proof": ["...", "...", "*"],
    "root": "...",
    "anchor": {
      "type": "newspaper",
      "date": "2025-12-21",
      "publications": ["NYT", "Guardian"]
    }
  }
}
```

### 5.5 Zone Economic Models

Zones have complete sovereignty over their economic model. The protocol does not impose any fee structure or token requirement at the protocol level—this is intentional to maximize flexibility and accessibility.

#### 5.5.1 Common Economic Models

| Model                   | Description               | Use Case                                   |
| ----------------------- | ------------------------- | ------------------------------------------ |
| **Free/Public Good**    | No fees, open access      | Archives, academic institutions            |
| **Pay-per-Attestation** | Fixed fee per attestation | Commercial verification services           |
| **Subscription**        | Recurring fee for access  | Enterprise clients, research organizations |
| **Token-Gated**         | Requires token stake/burn | Community-managed Zones, verified networks |
| **Freemium**            | Free basic, paid premium  | Startups, developer platforms              |

#### 5.5.2 Cross-Zone Payment Flows

When an attestation cites another Zone's attestation, the citing Zone MAY be charged by the cited Zone:

```
Zone A (citing)                    Zone B (cited)
     │                                  │
     │ 1. POST /citation/quote          │
     │ ─────────────────────────────────>
     │                                  │
     │ 2. { "fee": "0.01", "currency": "USD" }
     │ <─────────────────────────────────
     │                                  │
     │ 3. Payment (off-chain/on-chain)  │
     │ ─────────────────────────────────>
     │                                  │
     │ 4. GET /attestation/{id}         │
     │ ─────────────────────────────────>
     │                                  │
     │ 5. Attestation + Proof           │
     │ <─────────────────────────────────
```

**Payment methods** are Zone-defined and MAY include:

- Traditional invoicing (USD, EUR)
- Cryptocurrency (BTC, ETH, stablecoins)
- Zone-specific tokens
- Barter/reciprocal citation agreements

#### 5.5.3 Token-Gated Zone Pattern

Zones MAY require token ownership for access:

```json
{
  "zone_id": "...",
  "access_requirements": {
    "type": "token_gated",
    "token_contract": "0x...",
    "chain_id": 1,
    "minimum_balance": "100",
    "token_symbol": "VERIFY"
  }
}
```

**Common token utility patterns:**

- **Stake to Submit**: Attestation submitters stake tokens (slashed for spam/abuse)
- **Burn to Attest**: Small token amount burned per attestation
- **Hold to Access**: Token balance required to query attestations
- **Voting**: Token holders vote on Zone policies

> **Protocol Neutrality:** The base protocol has no token. Zone-level tokens are entirely optional and Zone-specific. An Zone with no token has equal protocol standing as one with complex token economics.

---

## 6. Error Responses

### 6.1 Error Format

Zones MUST return errors following RFC 9457 Problem Details format:

```json
{
  "type": "https://example.org/errors/attestation-not-found",
  "title": "Attestation Not Found",
  "status": 404,
  "detail": "No attestation exists with ID a1b2c3d4...",
  "instance": "/attestation/a1b2c3d4..."
}
```

### 6.2 Standard Error Types

| HTTP Status | Type Suffix               | Title                      | When to Use                    |
| ----------- | ------------------------- | -------------------------- | ------------------------------ |
| 400         | `/invalid-request`        | Invalid Request            | Malformed JSON, missing fields |
| 400         | `/invalid-attestation-id` | Invalid Attestation ID     | ID not 64 hex characters       |
| 404         | `/attestation-not-found`  | Attestation Not Found      | ID doesn't exist               |
| 404         | `/zone-not-found`         | Zone Not Found             | Unknown zone_id in citation    |
| 409         | `/attestation-exists`     | Attestation Already Exists | Duplicate submission           |
| 422         | `/verification-failed`    | Verification Failed        | Proof didn't verify            |
| 429         | `/rate-limit-exceeded`    | Rate Limit Exceeded        | Too many requests              |
| 500         | `/internal-error`         | Internal Error             | Server-side failure            |
| 503         | `/anchoring-in-progress`  | Anchoring In Progress      | Merkle root being updated      |

### 6.3 Error Response Examples

**Attestation not found:**

```json
{
  "type": "https://example.org/errors/attestation-not-found",
  "title": "Attestation Not Found",
  "status": 404,
  "detail": "No attestation with ID a1b2c3d4e5f6... exists in this Zone",
  "instance": "/attestation/a1b2c3d4e5f6..."
}
```

**Rate limit exceeded:**

```json
{
  "type": "https://example.org/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Request limit of 100/minute exceeded. Retry after 45 seconds.",
  "instance": "/verify",
  "retry_after": 45
}
```

### 6.4 Error Handling Requirements

- Zones MUST return appropriate HTTP status codes
- Zones MUST include `Content-Type: application/problem+json` header
- Zones SHOULD include `retry_after` for 429 responses
- Zones SHOULD NOT expose internal implementation details in error messages

---

## 7. Anchoring Methods

### 7.1 Purpose

Zones anchor their Merkle roots to provide timestamping and integrity verification. Multiple anchoring methods are supported.

### 7.2 Supported Anchor Types

| Type               | Description                    | Verification          | Cost   |
| ------------------ | ------------------------------ | --------------------- | ------ |
| **opentimestamps** | Bitcoin anchor via OTS         | opentimestamps.org    | Free   |
| **nist_beacon**    | NIST Randomness Beacon         | beacon.nist.gov       | Free   |
| **ipfs**           | IPFS content addressing        | Any IPFS gateway      | Free   |
| **arweave**        | Permanent storage              | arweave.net           | ~$0.01 |
| **social_media**   | Public posts (X, GitHub)       | Archived URLs         | Free   |
| **astronomical**   | Celestial position             | Ephemeris calculation | Free   |
| **blockchain**     | Direct chain anchor (optional) | Chain verification    | Varies |
| **newspaper**      | Published print media          | Library archives      | Varies |
| **people**         | Witness attestation by people  | Signed statement      | Varies |

#### 7.2.1 People Witness Anchor Format

People witness anchors enable human attestation — the most fundamental form of witnessing.

```json
{
  "anchor": {
    "type": "people",
    "witnesses": [
      {
        "name": "Alice",
        "identity_url": "https://github.com/alice",
        "public_key_url": "https://github.com/alice/.public_key",
        "signature": "base64_signature_here",
        "signature_type": "ed25519"
      }
    ],
    "statement": "I witness merkle_root abcd1234... at 2025-12-21T15:03:00Z",
    "statement_url": "https://example.com/witness/alice-20251221.txt",
    "merkle_root": "abcd1234...",
    "timestamp": "2025-12-21T15:03:00Z"
  }
}
```

**Field Definitions:**

| Field                      | Required | Description                                        |
| -------------------------- | -------- | -------------------------------------------------- |
| witnesses                  | MUST     | Array of witness objects                           |
| witnesses[].name           | MUST     | Human-readable name or pseudonym                   |
| witnesses[].identity_url   | SHOULD   | URL to verifiable identity (GitHub, Twitter, etc.) |
| witnesses[].public_key_url | MUST     | URL to public key for signature verification       |
| witnesses[].signature      | MUST     | Signature over statement content                   |
| witnesses[].signature_type | MUST     | Algorithm: ed25519, secp256k1, or pgp              |
| statement                  | MUST     | Plain text statement containing merkle_root        |
| statement_url              | SHOULD   | Persistent URL where statement is published        |
| merkle_root                | MUST     | The Merkle root being witnessed                    |
| timestamp                  | MUST     | ISO 8601 timestamp of witnessing                   |

**Verification:**

1. Fetch public key from `public_key_url`
2. Verify `signature` over `statement` using fetched key
3. Verify `statement` contains the claimed `merkle_root`
4. Verifier MUST independently trust that the public key belongs to the named witness
5. Trust is established socially: verified profiles, web of trust, reputation

**Multiple Witnesses:**

Multiple witnesses strengthen the anchor. A Merkle root witnessed by N independent people provides N-of-N social proof.

#### 7.2.2 Newspaper Anchor Format

Newspaper anchors use published print media as timestamp proof:

```json
{
  "anchor": {
    "type": "newspaper",
    "publications": ["New York Times", "The Guardian"],
    "date": "2025-12-21",
    "section": "Technology",
    "merkle_root": "abcd1234...",
    "archive_urls": ["https://archive.org/...", "https://library.example.com/..."]
  }
}
```

**Verification:** Newspaper anchors are verified by checking archived copies in library systems or web archives. Multiple publications provide redundancy.

### 7.3 Anchor Format

```json
{
  "anchor": {
    "type": "opentimestamps",
    "ots_file": "witness.json.ots",
    "btc_block": 876543,
    "merkle_root": "abcd1234..."
  }
}
```

Or for IPFS:

```json
{
  "anchor": {
    "type": "ipfs",
    "cid": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
    "gateway": "https://ipfs.io/ipfs/"
  }
}
```

Or for astronomical:

```json
{
  "anchor": {
    "type": "astronomical",
    "timestamp": "2025-12-21T15:03:00Z",
    "julian_day": 2461031.1270833333,
    "event": "Winter Solstice",
    "merkle_root": "abcd1234..."
  }
}
```

### 7.4 Anchoring Frequency

Zones SHOULD anchor at least once every 24 hours or every 1000 attestations, whichever comes first.

### 7.5 Verification Chain

To verify an attestation is properly anchored:

```
1. Obtain attestation and Merkle proof from Zone
2. Verify proof computes to claimed Merkle root (Section 4.3)
3. Verify anchor exists (newspaper archive, library record, etc.)
4. Verify anchor timestamp matches claimed time
```

---

# PART II: OPTIONAL EXTENSIONS

## 8. Canon Registry

### 8.1 Definition

A Canon defines a verification system. Canon ID is computed as:

```
canon_id = SHA256(name || ":" || version)
```

### 8.2 Example Canons

These are example canons that Zones MAY choose to support. This is NOT an authoritative registry:

| Name        | Version | Canon ID (first 16 chars)   | Description                              |
| ----------- | ------- | --------------------------- | ---------------------------------------- |
| timestamp   | 1.0     | `SHA256("timestamp:1.0")`   | Simple existence proof (no verification) |
| test-result | 1.0     | `SHA256("test-result:1.0")` | CI/CD test suite results                 |
| document    | 1.0     | `SHA256("document:1.0")`    | Document hash attestation                |

### 8.3 Canon Registration

There is no central registry. Canons become recognized through use—when multiple independent Zones declare support and cross-cite attestations using them.

### 8.4 Canon ID Collision

In the unlikely event of SHA256 collision:

1. Both Canons remain valid
2. Zones SHOULD include `canon_name` and `canon_version` in Zone info
3. Attestation validity is determined by Zone, not Canon ID alone

---

## 9. Citation Protocol

### 9.1 Cross-Zone Citations

An attestation MAY cite other attestations by including their `attestation_id` values in the `citations` array.

### 9.2 Citation Verification Requirements

To verify a citation is valid, verifiers MUST:

1. Fetch the cited attestation from its Zone
2. Verify the cited attestation has a valid Merkle proof
3. **Verify the cited attestation's Merkle root is anchored**
4. **Verify the anchor timestamp is BEFORE the citing attestation's anchor timestamp**

**IMPORTANT:** Timestamp comparison alone is insufficient. An attacker could backdate timestamps. The anchor verification provides objective temporal ordering.

### 9.3 Citation Verification Algorithm

```
FUNCTION verify_citation(citing_attestation, cited_id, cited_Zone_endpoint):
    INPUT:  citing_attestation, cited_id, cited_Zone_endpoint
    OUTPUT: TRUE if citation is valid, FALSE otherwise

    1. Fetch cited attestation with proof from cited_Zone_endpoint
    2. IF Merkle proof is invalid THEN RETURN FALSE
    3. IF cited attestation has no anchor THEN RETURN FALSE
    4. IF citing attestation has no anchor THEN RETURN FALSE
    5. cited_time ← cited attestation's anchor timestamp
    6. citing_time ← citing attestation's anchor timestamp
    7. RETURN (cited_time < citing_time)
```

### 9.4 Fee Negotiation (Optional)

Zones MAY charge for citation access. Fee structures are entirely Zone-defined.

---

## 10. Zone Discovery

### 10.1 Discovery Mechanisms

Zones MAY be discovered through multiple mechanisms, in order of preference:

| Priority | Mechanism            | Trust Level | Description                |
| -------- | -------------------- | ----------- | -------------------------- |
| 1        | Direct URL           | Highest     | Known Zone endpoint        |
| 2        | Federation directory | High        | Curated Zone list          |
| 3        | DNS TXT record       | Medium      | `_glogos.zone.example.com` |
| 4        | On-chain registry    | Medium      | Smart contract lookup      |
| 5        | Web search           | Low         | Manual discovery           |

### 10.2 DNS-Based Discovery

Zones MAY publish discovery information via DNS TXT records:

```
_glogos.zone.example.com. IN TXT "v=glogos1 endpoint=https://zone.example.com pubkey=ed25519:abc123..."
```

### 10.3 Federation Directory

Federations (Section 11) SHOULD provide Zone discovery via `GET /federation/zones`.

### 10.4 Public Key Verification

When discovering a Zone, verifiers SHOULD fetch `/zone/info`, verify the `public_key`, and cache with expiration (recommended: 24 hours).

---

## 11. Federation Interface

### 11.1 Purpose

Federations are optional aggregation layers providing:

- Zone discovery and directory services
- Batched anchoring (cost reduction)
- Cross-Zone query routing
- Trust signals (membership criteria)

> **IMPORTANT:** Federations are allowed but MUST NOT be mandatory. Independent Zones forever have equal standing in the protocol. An Zone that never joins any federation has the same protocol-level status as one that joins multiple federations. No Zone may be excluded from the protocol for refusing to join a federation.

### 11.2 Aggregated Anchoring

A Federation collects Merkle roots from member Zones, builds a Federation Merkle tree, and anchors one root via chosen method.

```
Zone A Root ─┐
Zone B Root ─┼─→ Federation Merkle Tree → Federation Root → Anchor
Zone C Root ─┘
```

Zones receive:

- Federation Merkle root
- Inclusion proof for their Zone root
- Anchor reference

### 11.3 Federation Anchor Format

Federations MAY use any anchor method. If using blockchain:

| Blockchain | Format                             |
| ---------- | ---------------------------------- |
| Bitcoin    | OP_RETURN with `GLOGOS_FED` prefix |
| Ethereum   | Contract event or calldata         |
| Solana     | Memo or account data               |

### 11.4 Federation Zone Proof

Zones in a Federation provide two-level proofs: attestation proof (attestation → Zone root) and federation proof (Zone root → Federation root). Both use the standard Merkle proof format from Section 4.

---

# PART III: SECURITY & OPERATIONS

## 12. Security Considerations

### 12.1 Threat Model

#### 12.1.1 Attacker Capabilities

| Capability       | Assumed                                            |
| ---------------- | -------------------------------------------------- |
| Network position | Off-path (cannot intercept all traffic)            |
| Computational    | Polynomial time, classical computing               |
| Anchor access    | Can observe public anchors, cannot rewrite history |
| Zone compromise  | May compromise individual Zones                    |

#### 12.1.2 Trust Assumptions

- SHA-256 is collision-resistant and preimage-resistant
- Ed25519/secp256k1 signatures are unforgeable
- Anchors (newspaper, library, blockchain) provide independent timestamp verification
- Zones are trusted for their own attestations (trust is per-Zone, not protocol-wide)

#### 12.1.3 Out of Scope

- Physical access attacks on Zone infrastructure
- Side-channel attacks on cryptographic implementations
- Quantum computing attacks (see Appendix A.1 Future Considerations)

### 12.2 Attack Surface Analysis

| Attack                        | Vector                          | Mitigation                        | Residual Risk |
| ----------------------------- | ------------------------------- | --------------------------------- | ------------- |
| **Attestation forgery**       | Forge Zone signature            | Ed25519 security                  | Negligible    |
| **Merkle proof manipulation** | Invalid proof                   | Deterministic verification        | None          |
| **Timestamp manipulation**    | Backdate attestation            | Require anchor verification       | Low           |
| **Citation to non-existent**  | Cite fake attestation           | Require anchor verification       | None          |
| **Zone impersonation**        | Fake Zone endpoint              | Public key verification           | Low           |
| **Eclipse attack**            | Isolate verifier from real Zone | Multiple discovery mechanisms     | Medium        |
| **Replay attack**             | Resubmit attestation            | attestation_id includes timestamp | None          |

### 12.3 Implementation Requirements

Implementations:

- MUST use constant-time comparison for cryptographic values
- MUST validate all signatures before processing attestations
- MUST verify Merkle proofs before trusting attestation inclusion
- MUST NOT log or expose private keys
- MUST NOT trust timestamps alone for temporal ordering
- SHOULD implement rate limiting on public endpoints
- SHOULD validate all input lengths before processing

### 12.4 Zone Compromise Recovery

If an Zone's signing key is compromised:

1. Zone MUST stop signing new attestations immediately
2. Zone SHOULD publish key revocation notice
3. Zone MAY migrate to new key with transition period
4. Existing attestations remain valid (they reference the old key)
5. New attestations MUST use new key

---

# APPENDICES

## A. Cryptographic proposals

### A.1 Hash Function

**Proposal (v1.0.0):** SHA-256 as defined in FIPS 180-4

**Function Properties:**

- Output size: 256 bits (32 bytes)
- Collision resistance: ~2^128 security level
- Preimage resistance: ~2^256 security level
- Second preimage resistance: ~2^256 security level

**Rationale for SHA-256:**

1. **Universal availability**: Implemented in every major programming language and cryptographic library
2. **Bitcoin ecosystem alignment**: Same hash function used in Bitcoin for consistency with anchoring mechanism
3. **Battle-tested**: 20+ years of cryptanalysis with no practical attacks
4. **Hardware acceleration**: Supported by modern CPU instruction sets (Intel SHA-NI, ARM Cryptography Extensions)
5. **NIST standardization**: FIPS 180-4 approved, ensuring long-term standardization support

**Known Weaknesses:**

- Quantum computing: Grover's algorithm reduces collision resistance from 2^128 to 2^64 (still secure for foreseeable future)
- Not post-quantum secure against Grover's algorithm

**Future Considerations:**

- Version 2.0 may adopt post-quantum hash functions (e.g., SHA3-256, BLAKE3)
- Any future version MUST chain to GLSR to preserve provenance
- Hash function choice is fixed for each version and cannot be changed post-Genesis

**Test Vectors:**

```
Empty axiom (GLSR):
  Input:  "" (0 bytes)
  SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

---

### A.2 Signature Algorithms

| Component                | proposal           | Notes                           |
| ------------------------ | ------------------ | ------------------------------- |
| Signatures (primary)     | Ed25519 (RFC 8032) | Recommended for new Zones       |
| Signatures (alternative) | secp256k1 (SEC 2)  | Bitcoin ecosystem compatibility |
| Signature encoding       | Base64 (RFC 4648)  | Standard alphabet               |

---

### A.3 Other proposals

| Component     | proposal              | Notes                         |
| ------------- | --------------------- | ----------------------------- |
| Merkle tree   | Binary, sorted leaves | Hash function per A.1         |
| Hash encoding | Lowercase hexadecimal | 64 characters for 32 bytes    |
| Timestamp     | Unix epoch seconds    | 8-byte big-endian for hashing |

---

## B. JSON Schemas

### B.1 Attestation Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/attestation.json",
  "type": "object",
  "required": [
    "attestation_id",
    "zone_id",
    "canon_id",
    "claim_hash",
    "evidence_hash",
    "timestamp",
    "signature"
  ],
  "properties": {
    "attestation_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "zone_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "canon_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "claim_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "evidence_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "evidence_location": {
      "type": "string",
      "format": "uri"
    },
    "citations": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^[a-f0-9]{64}$"
      }
    },
    "timestamp": {
      "type": "integer",
      "minimum": 0
    },
    "signature": {
      "type": "string",
      "contentEncoding": "base64"
    }
  }
}
```

### B.2 Merkle Proof Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/merkle-proof.json",
  "type": "object",
  "required": ["version", "leaf_hash", "leaf_index", "proof", "root"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "leaf_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "leaf_index": {
      "type": "integer",
      "minimum": 0
    },
    "proof": {
      "type": "array",
      "items": {
        "oneOf": [
          { "type": "string", "pattern": "^[a-f0-9]{64}$" },
          { "type": "string", "const": "*" }
        ]
      }
    },
    "root": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "anchor": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": [
            "opentimestamps",
            "nist_beacon",
            "ipfs",
            "arweave",
            "social_media",
            "astronomical",
            "blockchain",
            "newspaper",
            "human"
          ]
        },
        "txid": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
        "block_height": { "type": "integer", "minimum": 0 },
        "confirmations": { "type": "integer", "minimum": 0 }
      }
    }
  }
}
```

### B.3 Error Response Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/error.json",
  "type": "object",
  "required": ["type", "title", "status"],
  "properties": {
    "type": {
      "type": "string",
      "format": "uri"
    },
    "title": {
      "type": "string"
    },
    "status": {
      "type": "integer",
      "minimum": 400,
      "maximum": 599
    },
    "detail": {
      "type": "string"
    },
    "instance": {
      "type": "string"
    }
  }
}
```

---

## C. Test Vectors

### C.1 Empty Axiom

```
Input:  "" (0 bytes)
Output: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Verification:

```bash
printf '' | sha256sum
# e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
```

### C.2 Merkle Proof Verification

Given three attestation IDs (64-character hex strings):

```
Leaves (sorted lexicographically):
  leaf_a = a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd
  leaf_b = b2c3d4e5f6789012345678901234567890123456789012345678901234bcde
  leaf_c = c3d4e5f6789012345678901234567890123456789012345678901234cdef

Tree structure (3 leaves -> duplicate last):
             root
            /    \
       node_ab    node_cc
        /   \       |
     leaf_a leaf_b  SHA256(leaf_c || leaf_c)
```

> **Note:** When duplicating an odd leaf, we compute `node_cc = SHA256(leaf_c || leaf_c)`, NOT just use `leaf_c` directly.

Proof for leaf_b at index 1:

```json
{
  "version": "1.0",
  "leaf_hash": "b2c3d4e5f6789012345678901234567890123456789012345678901234bcde",
  "leaf_index": 1,
  "proof": ["a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd", "<node_cc_hash>"],
  "root": "<root_hash>"
}
```

Where `node_cc = SHA256(leaf_c || leaf_c)`.

Verification steps:

```
1. index=1 -> 1%2=1 -> leaf_b is RIGHT child
   hash1 = SHA256(leaf_a || leaf_b)
2. index=0 -> 0%2=0 -> hash1 is LEFT child
   root = SHA256(hash1 || node_cc)
```

### C.3 Attestation ID Computation

```
Input:
  zone_id:    a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd
  canon_id:   b2c3d4e5f6789012345678901234567890123456789012345678901234abcdef
  claim_hash: c3d4e5f6789012345678901234567890123456789012345678901234abcdef01
  timestamp:  1766329380 (0x000000006947C024 big-endian)

Computation:
  preimage = zone_id || canon_id || claim_hash || timestamp_bytes (104 bytes)
  attestation_id = SHA256(preimage)
```

Verification:

```python
import hashlib
import struct

zone_id = bytes.fromhex("a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd")
canon_id = bytes.fromhex("b2c3d4e5f6789012345678901234567890123456789012345678901234abcdef")
claim_hash = bytes.fromhex("c3d4e5f6789012345678901234567890123456789012345678901234abcdef01")
timestamp = 1766329380

timestamp_bytes = struct.pack(">Q", timestamp)  # 8-byte big-endian
preimage = zone_id + canon_id + claim_hash + timestamp_bytes
attestation_id = hashlib.sha256(preimage).hexdigest()
print(attestation_id)
```

---

## D. Related Work

### D.1 Existing Timestamping & Anchoring

**OpenTimestamps** (2016) – Merkle-aggregated blockchain timestamping. Free, open-source, production-stable. Glogos Zones MAY use OpenTimestamps for cost-effective anchoring.

**Chainpoint** (2017) – Similar Merkle-based anchoring with JSON-LD proof format. Glogos Merkle proof format draws from Chainpoint patterns.

### D.2 Enterprise Distributed Ledgers

Several enterprise solutions provide record keeping with various trade-offs:

- **Hyperledger Fabric** – Consortium-based permissioned ledger, suitable for enterprise use cases requiring controlled membership.
- **Amazon QLDB** – Managed ledger database with centralized trust, ideal for AWS ecosystems.
- **Corda** – Enterprise blockchain for regulated industries with privacy features.

Glogos complements these solutions by providing an open protocol layer that requires no operator. Attestations from enterprise systems can be anchored to GLSR for long-term, offline-verifiable records.

**Design choices in Glogos:**

1. **No operator dependency** – Pure protocol with no central coordinator or consortium requirement.
2. **Open participation** – Anyone can create a Zone without permission.
3. **Offline verifiability** – Records can be verified with only mathematical knowledge and archived documents.

### D.3 Standards & Formats

**BIPs / EIPs** – Standard proposal formats (Bitcoin, Ethereum). Glogos proposal structure follows these templates.

**RFC 9457** (2023) – Problem Details for HTTP APIs. Glogos error format directly implements this standard.

**W3C Verifiable Credentials** – JSON-LD credential format. Glogos is simpler (plain JSON) and includes built-in timestamping.

### D.4 Formal Verification Tools

**Lean 4 / mathlib** (2021) – Modern proof assistant with 210,000+ formalized theorems. Primary target for formal verification Zones.

**Certora** (2018) – Formal verification for smart contracts. Recently open-sourced prover.

This proposal does not replace these tools—it provides a common attestation format that can reference verification performed by any of them.

---

## Z — Invitation to Witness

At 15:03:00 UTC on December 21, 2025 (Winter Solstice),
anyone may create an attestation.

**What this means technically:**

```
GLSR = SHA256("")
     = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

This is mathematics. Not opinion.
Anyone can verify with a single SHA256 call.

**What you CAN do:**

- Create your own Zone (no permission needed)
- Attest your own documents (no permission required)
- Cite other attestations (optional, not required)
- Join at the Solstice or any other time (all valid)

**What you DON'T need:**

- No token to purchase
- No stake to lock
- No vote to pass
- No community to join
- No foundation to contact

**Practical applications (working today):**

- Vaccine certificates: 95,929/sec verified
- Academic degrees: Lean 4 formal proofs
- Privacy proofs: ZK-Groth16 support
- Document attestation: instant

**If someone asks:**

| Question              | Answer                                    |
| --------------------- | ----------------------------------------- |
| "What is Glogos?"     | A hash-based record tool. Like SHA256.    |
| "Who controls it?"    | No one. SHA256("") is math.               |
| "Is this a movement?" | No. This is software. Like git. Like PGP. |
| "Why trust you?"      | Don't trust me. Verify the math.          |

**The script `witness.py` is one example.**
But it is merely one way among infinite ways.

From emptiness, all light is welcome.

— Winter Solstice 2025

---

## LICENSE

CC-BY-4.0

---

## CONTACT

GitHub: https://github.com/glogos-org/proposal
