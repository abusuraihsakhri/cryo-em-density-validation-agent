# Cryo Em Density Validation Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Cryo Em Density Validation Agent** is an advanced analytical and computational platform implementing Fourier Shell Correlation (FSC 0.143) & local resolution cryo-EM map validation. It provides multi-worker consensus evaluation, tamper-evident audit logging, and zero-PHI outbound data protection.

The project contains two parallel validation subsystems:

1. **`agents/`** - Main enterprise system with FastAPI REST API, specialized workers, and HMAC-SHA256 audit trail
2. **`cryo_em_validator/`** - Frontier domain engine for FSC curve calculation and map-to-model fitting

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds
- **Multi-Worker Consensus**: InvariantQC, SafetyEscalation, and ProtocolConformance workers
- **Risk & Urgency Classification**: Multi-tier categorization (ROUTINE, ELEVATED, CRITICAL_STAT)
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection
- **Prometheus Telemetry**: Operational metrics export for monitoring

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/cryo-em-density-validation-agent.git
cd cryo-em-density-validation-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. System Configuration Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
| Flag | Description | Default |
|:-----|:------------|:--------|
| `--task-id` | Unique task/case identifier | TASK-2026-001 |
| `--target` | Entity or target identifier | KEY-TARGET-01 |
| `--primary` | Primary measurement value | 28.5 |
| `--secondary` | Secondary metric value | 14.2 |
| `--critical` | Emergency escalation flag | False |
| `--status` | Status/phenotype descriptor | DISCORDANT |

---

## 🌐 REST API Endpoints

When the server is running (`python cli.py serve`):

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Health and metadata check |
| `/metrics` | GET | Prometheus operational metrics |
| `/api/audit` | POST | Submit task for evaluation |
| `/api/chat` | POST | Supervisory conversational query |
| `/api/audit/logs` | GET | Retrieve and verify HMAC audit trail |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOBs, and patient identifiers
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs with signature verification for every evaluation
* **Path Traversal Protection:** Batch CLI validates all file paths remain within the working directory
* **Secure Defaults:** Audit key sourced from `AUDIT_SECRET_KEY` environment variable (ephemeral random key generated if unset)
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude, GPT-4o, and deterministic test mocks

---

## 🧪 Testing & Verification

Run the full automated test suite:

```bash
pytest -v
```

Run security-focused tests only:

```bash
pytest tests/test_security.py -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY="your-secure-key-here"
docker-compose up --build

# Or with Docker directly
docker build -t cryo-em-density-validation-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" cryo-em-density-validation-agent
```

---

## 📁 Project Structure

```
cryo-em-density-validation-agent/
├── agents/                      # Main enterprise subsystem
│   ├── __init__.py
│   ├── api.py                   # FastAPI REST server
│   ├── base.py                  # PHI guard, HMAC audit trail
│   ├── learning.py              # Bayesian calibration engine
│   ├── llm_factory.py           # LLM provider factory
│   ├── metrics.py               # Prometheus metrics collector
│   ├── models.py                # Pydantic data models
│   ├── streamer.py              # WebSocket telemetry broadcaster
│   ├── supervisor.py            # Master orchestrator
│   └── workers.py               # Specialized evaluation workers
├── cryo_em_validator/           # Frontier domain subsystem
│   ├── __init__.py
│   ├── agents.py                # FSC, Map-to-Model, Local Resolution agents
│   ├── cli.py                   # Frontier CLI
│   ├── engine.py                # Core algorithmic engine
│   ├── models.py                # Frontier data models
│   └── server.py                # Frontier FastAPI server
├── tests/                       # Test suite
│   ├── test_cryo_em_density_validation_agent.py
│   ├── test_cryo_em_validator.py
│   ├── test_enrichment.py
│   └── test_security.py         # Security-focused tests
├── web/                         # Operations console (HTML/JS)
├── cli.py                       # Main CLI entry point
├── cryo_em_validator_app.py     # Frontier CLI entry point
├── enrichment.py                # Enrichment feature engines
├── simulator.py                 # High-throughput simulation
├── pyproject.toml               # Project configuration
├── Dockerfile                   # Container build
├── docker-compose.yml           # Container orchestration
└── .github/workflows/ci.yml     # CI/CD pipeline
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
