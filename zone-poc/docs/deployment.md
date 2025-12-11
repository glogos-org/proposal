# Development Deployment Guide

**Spec Version:** v1.0.0-rc.0

---

## Quick Start

### Development

```bash
cd zone-poc
pip install -r requirements.txt
python -m zone.app
```

### Docker

```bash
cd zone-poc/deploy
docker-compose up -d
```

---

## Configuration

### Environment Variables

| Variable    | Default                 | Description  |
| ----------- | ----------------------- | ------------ |
| `ZONE_NAME` | "Glogos Reference Zone" | Zone name    |
| `HOST`      | "0.0.0.0"               | Bind address |
| `PORT`      | "8000"                  | Port         |

### GLSR

The GLSR is fixed and immutable:

```bash
# GLSR = SHA256("") — the simplest possible genesis
GLSR=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

---

## Development Checklist

### Security

- [ ] Use HSM for private keys
- [ ] Enable HTTPS (TLS 1.3)
- [ ] Rate limiting configured
- [ ] Authentication enabled

### Storage

- [ ] RocksDB volume mounted
- [ ] Backup strategy defined
- [ ] Monitoring enabled

### Anchoring

- [ ] OpenTimestamps configured
- [ ] IPFS node accessible

---

## Architecture

```text
        ┌─────────────┐
        │   Clients   │
        └──────┬──────┘
               │ HTTPS
        ┌──────▼──────┐
        │   Nginx     │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │   FastAPI   │
        │  (app.py)   │
        └──────┬──────┘
               │
  ┌────────────┼────────────┐
  ▼            ▼            ▼
┌───────┐  ┌───────┐  ┌───────┐
│Signing│  │Merkle │  │Storage│
└───────┘  └───────┘  └───────┘
```

---

## Health Check

```bash
curl http://localhost:8000/health
```

---

**GLSR:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
