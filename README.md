# AuditorSEC

**Crypto compliance & security audit platform for Ukrainian market**

> Open-source compliance templates + AI-powered API for crypto projects operating
> under Ukrainian jurisdiction (VASP, NIS2, AML/CFT, BRAVE1).

![TRL](https://img.shields.io/badge/TRL-4-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20Docker%20%7C%20Redis%20%7C%20MinIO-orange)

---

## Status / Roadmap

**Technology Readiness Level (TRL): 4**

AuditorSEC MVP is a running FastAPI microservice with Dockerized deployment on a production-grade VPS (PostgreSQL, Redis cache, MinIO object storage). The `/api/v1/audit` and `/api/v1/report` endpoints are live and can be integrated into defense and fintech infrastructures as a standalone compliance engine.

The BRAVE1 roadmap targets Tier 3 (UAH 2M) with TRL 4-5 validation and phased scaling to Tier 4a/4b, using AuditorSEC as the core security and compliance layer for defense-grade systems.

**Roadmap:**

| Timeline | Milestone | TRL |
|----------|-----------|-----|
| Now (April 2026) | MVP deployed: `/audit` + `/report` + full docs | **4** |
| April 24, 2026 | Domain auditorsec.com/ua + Hetzner deploy | 4 |
| May 2026 | 3-5 defense/crypto pilot audits + Diia.City reg | **5** |
| June 2026 | STANAG-4586 integration + Municipal Sentinel pilot (Bakhmach) | 5 |
| Q3 2026 | Multi-site defense deployments + PQC module + SaaS bundle | **6** |

---

## Why AuditorSEC

Ukrainian crypto and defense-tech projects operate without standardized security frameworks:

- No incident playbooks for DFRR/DBR enforcement scenarios
- No key management standards adapted to UA regulatory context
- AML/KYC gaps creating exposure to FATF grey list consequences
- NIS2 compliance required for EU-facing projects — no UA-specific tooling exists
- Drone, UGV and C2 systems deployed without formal security auditing

AuditorSEC closes this gap.

---

## Dual-Use by Design

AuditorSEC is a dual-use security layer: the same audit engine that protects BRAVE1 defense systems also secures municipal IoT and fintech infrastructures, ensuring that public and donor funds are spent on resilient, corruption-resistant digital systems.

**Defense impact:** Reduces time and cost of security audits for drone, UGV and battlefield IoT systems by providing an automated engine to scan configurations, logs and key-management policies before deployment.

**Civil/municipal impact:** Secures the Municipal Sentinel IoT environmental monitoring platform, enabling tamper-resistant audit trails for environmental data — qualifying communities for EU-backed climate financing.

---

## What's in this repo

| File | Description |
|------|-------------|
| `main.py` | FastAPI audit API (`/audit`, `/report`, `/health`) |
| `report.py` | PDF report generation + MinIO upload |
| `docker-compose.yml` | Self-hosted stack: API + PostgreSQL + Redis + MinIO |
| `Dockerfile` | Python 3.11 container |
| `requirements.txt` | Python dependencies |
| `setup.sh` | One-command VPS deploy script |
| `.env.example` | Environment variables template |
| `docs/BRAVE1_TRL4_demo.md` | TRL-4 proof document for BRAVE1 application |
| `docs/cover_letter_brave1.md` | BRAVE1 Tier 3 cover letter |
| `docs/outreach_templates.md` | Outreach templates (Telegram/LinkedIn/Email) |
| `docs/whitepaper-outline.md` | Whitepaper structure: UA crypto legal vacuum |

---

## Live API

### Run locally

```bash
git clone https://github.com/romanchaa997/auditorsec.git
cd auditorsec
cp .env.example .env  # add your OPENAI_API_KEY
docker compose up -d
```

### Health check

```bash
curl http://localhost:8000/health
```

### Run audit

```bash
curl -X POST http://localhost:8000/api/v1/audit \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "MyProject",
    "log_text": "Private key stored in .env on production. 5 devs have access. No backups.",
    "audit_type": "key_mgmt"
  }'
```

**Audit types:**

| Type | Description |
|------|-------------|
| `health_check` | General security health check |
| `threat_model` | Threat modeling for UA crypto context |
| `key_mgmt` | Key management NIS2-compliance audit |

### Example response

```json
{
  "project_name": "MyProject",
  "audit_type": "key_mgmt",
  "anomalies": [
    "Private key in .env on production — critical vulnerability",
    "5 people with access to single key — violates least privilege",
    "No key backups — single point of failure"
  ],
  "risk_level": "CRITICAL",
  "recommendations": [
    "Move keys to HashiCorp Vault or equivalent HSM",
    "Implement multi-sig: minimum 2-of-3",
    "Create encrypted offline backups in 2 separate locations",
    "Restrict access by least privilege principle",
    "Rotate all potentially compromised keys immediately"
  ],
  "token_count": 47,
  "cached": false,
  "timestamp": "2026-04-19T02:00:00"
}
```

---

## Architecture

```
[OpenAI API]
     |
[FastAPI backend] --> [PostgreSQL]  (structured audit logs)
     |
  [Redis]           --> cache, sessions (TTL 1h)
     |
  [MinIO]           --> PDF reports, raw log archive
```

**Memory optimization:** logs are never held in RAM — only anomaly summaries (<=3000 tokens) pass to LLM. Full logs go directly to tiered storage (PostgreSQL -> MinIO).

---

## Open-Source Templates

### Key Management Policy (NIS2-mapped)
`docs/auditorsec-key-mgmt-nis2.md`

Covers: key generation & storage, access control, backup & recovery, NIS2 Art. 21/23 mapping, Ukrainian VASP law context.

### Threat Model: Ukrainian State x Crypto
`docs/threat-model-ua-crypto.md`

Threat actors: DFRR, DBR, insider threats, sanctioned counterparty exposure, cross-border asset freeze risk.

### BRAVE1 TRL-4 Proof
`docs/BRAVE1_TRL4_demo.md`

One-page document proving TRL-4 status for BRAVE1 grant application.

---

## BRAVE1 / EU4UA / USAID Alignment

**Current Readiness Level: TRL-4**
AuditorSEC core API has been validated in a relevant environment as a deployed microservice (VPS, containerized stack, Redis/MinIO integration) processing real-world security logs from Ukrainian crypto/Web3 projects.

**Path to TRL-5 (BRAVE1 Tier 3):**
Structured pilots with at least one defense-related integrator (drone/UGV or cyber defense unit), demonstrating repeatable audit workflows on real incident data.

**Path to TRL-6 (BRAVE1 Tier 4a/4b):**
Multi-site deployments across defense partners, STANAG-4586 telemetry integration, PQC modules, and inclusion into a defense SaaS bundle.

---

## Security

- No sensitive data stored in plaintext
- All API keys via environment variables only
- Logs anonymized before LLM processing
- Redis cache TTL: 1 hour max
- MinIO reports: encrypted at rest

Found a vulnerability? Contact: **security@auditorsec.com**

---

## License

MIT License for templates and documentation.
API source: proprietary (source available for audit purposes).

---

## Contact

- Telegram: [@auditorsec](https://t.me/auditorsec)
- Email: hello@auditorsec.com
- GitHub: [github.com/romanchaa997/auditorsec](https://github.com/romanchaa997/auditorsec)
- Location: Bakhmach, Chernihiv Oblast, Ukraine

*Built in Ukraine. For Ukrainian crypto and defense market.*
*AuditorSEC v0.1 · April 2026*
