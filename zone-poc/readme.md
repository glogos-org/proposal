# Glogos Reference Zone

**Spec Version:** v1.0.0-rc.0

Reference Zone implementation for the Glogos Protocol.

---

## Structure

```text
zone-poc/
├── zone/               # Core package
│   ├── app.py         # FastAPI application
│   ├── models.py      # Pydantic models
│   ├── merkle.py      # Merkle tree engine
│   ├── signer.py      # Ed25519 signing
│   └── canons/        # Canon implementations
├── examples/           # Working examples
├── tests/              # Test suite
├── deploy/             # Docker deployment
└── docs/               # Documentation
```

---

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (Git Bash)
source .venv/Scripts/activate

# Linux/Mac
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Windows) Set encoding for emoji support
export PYTHONIOENCODING=utf-8

# 4. Run Zone API
python -m zone.app
# → http://localhost:8000/docs

# 5. Run Tests
python tests/test_quick.py

# 6. Run Benchmark (100K attestations)
python examples/cross_zone_demo.py
```

---

## Benchmark

```bash
# Full Merkle cycle benchmark (100K attestations)
python examples/cross_zone_demo_rocksdb.py
```

Results saved to:

- `examples/rocksdb_benchmark_results.md`
- `examples/rocksdb_benchmark_results.json`

---

## API Endpoints

| Endpoint            | Method | Description             |
| ------------------- | ------ | ----------------------- |
| `/zone/info`        | GET    | Zone metadata           |
| `/attestation/{id}` | GET    | Get attestation + proof |
| `/merkle/root`      | GET    | Current Merkle root     |
| `/verify`           | POST   | Create attestation      |

---

## GLSR

```text
GLSR = SHA256("")
     = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

---

## License

CC-BY-4.0 (doc), MIT (code)
