# Glogos: A Consensus-Free Attestation Proposal

## What is Glogos?

Glogos is a proposal for **consensus-free attestation**. It defines how independent systems ("Zones") can create cryptographically-signed attestation records without requiring blockchain or network consensus.

## Status

**Experimental** — This is a personal project, not production-ready software.

See [disclaimer.md](disclaimer.md) for full disclaimer.

## Structure

```
proposal/
├── readme.md              # This file
├── license.md             # CC-BY-4.0 (docs), MIT (code)
├── disclaimer.md          # Experimental project disclaimer
├── proposal.md            # Core specification
├── genesis/
│   ├── witness.py         # Mainnet launch ceremony
│   └── test_vectors.py
└── zone-reference/        # Reference implementation
```

## GLSR (Glogos State Root)

```
GLSR = SHA256("")
     = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Anyone can verify this with a single SHA256 call. No private keys. No blockchain. Only mathematics.

## License

- Documentation: CC-BY-4.0
- Code: MIT

## Witness

Lê Mạnh Thành

## Genesis

Winter Solstice 2025 — December 21, 15:03:00 UTC
