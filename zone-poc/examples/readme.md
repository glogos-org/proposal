# Glogos Examples - v1.0.0-rc.0

Examples for Glogos Protocol.

---

## Examples

| File                                 | Description                       |
| ------------------------------------ | --------------------------------- |
| `merkle_examples.py`                 | Merkle tree construction + proofs |
| `cross_cite_demo/cross_zone_demo.py` | Cross-zone citation demonstration |
| `academic/degree_demo.py`            | Academic credential (Lean 4)      |
| `healthcare/vaccine_demo.py`         | Mass vaccination certs            |
| `privacy/zk_demo.py`                 | ZK privacy-preserving proofs      |

---

## Quick Start

```bash
# Windows users - set encoding first
export PYTHONIOENCODING=utf-8

# Cross-zone citation demo (main example)
python cross_zone_demo.py

# Other examples
python merkle_examples.py
python academic/degree_demo.py
python healthcare/vaccine_demo.py
python privacy/zk_demo.py
```

---

## Merkle Tree Rules (Spec §4.4)

1. **Collect** all attestation_ids as leaves
2. **Sort** lexicographically (lowercase hex)
3. **Build** binary tree: `node = SHA256(left || right)`
4. **Odd count**: duplicate last leaf (marker `"*"`)
5. **Empty tree**: `root = SHA256("")`

---

## GLSR

```text
GLSR = SHA256("") = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```
