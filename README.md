# Cryo-EM Metadata Screening

### [Open the Live Application →](https://abusuraihsakhri.github.io/cryo-em-density-validation-agent/)

A small, rule-based tool for screening user-supplied numerical quality metadata and descriptor keywords. Available as a browser interface, Python command-line tool, and optional FastAPI service.

> **Scientific limitation:** This repository does **not** read MRC/cryo-EM density maps or atomic models; it does not calculate Fourier shell correlation (FSC), map-to-model correlation, local resolution, or atomic clashes. Its scalar thresholds are illustrative, **not** validated wwPDB/EMDB acceptance criteria or clinical decision support.

## Browser interface

Use the [live browser application](https://abusuraihsakhri.github.io/cryo-em-density-validation-agent/) or open [web/index.html](web/index.html) locally.

- **Browser mode (default):** evaluates rules entirely in JavaScript; entered measurements are not uploaded.
- **Server mode (optional):** sends inputs to a same-origin FastAPI server. Failed requests show an error, not fabricated reports.
- Inspect JSON results and download a report. Browser results are not cryptographically signed.

The static application uses JavaScript, not Pyodide, because the current rules do not need Python scientific libraries. GitHub Pages cannot run the Python API.

## Rules and outputs

The main Python implementation and browser interface apply the following example rules:

| Input | Rule | Result |
| --- | --- | --- |
| Primary metric | Greater than 25 | Elevated alert |
| Secondary metric | Greater than 12 | Elevated alert |
| Critical flag | True | Critical alert |
| Descriptor | Contains DISCORDANT, ANOMALY, MUTANT, VIOLATION, FAIL or REJECT (case-insensitive) | Elevated alert |

Overall urgency is CRITICAL_STAT_PANIC if a critical alert exists, ELEVATED_RISK if an elevated alert exists, and ROUTINE otherwise. The integrity status is a **rule category**, not evidence of cryo-EM reconstruction quality.

The legacy **cryo_em_validator/** implementation remains for backward compatibility. It uses a separate example secondary limit (10), alert labels and output schema; it is likewise **not** an FSC calculator.

## Install and run

Python 3.10–3.12 are tested in CI. The package metadata allows Python 3.9+.

~~~bash
git clone https://github.com/abusuraihsakhri/cryo-em-density-validation-agent.git
cd cryo-em-density-validation-agent
python -m pip install -e ".[api,test]"
python cli.py audit --task-id T1 --target SAMPLE-1 --primary 29 --secondary 14 --status DISCORDANT
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
~~~

The installed command **cryo-em-density-validation-agent** runs the main CLI; **cryo-em-density-validation-engine** runs the separate legacy CLI. The API serves the web interface at http://127.0.0.1:8000/.

| Endpoint | Function |
| --- | --- |
| GET /health | Health check |
| GET /metrics | In-process task and audit counts (JSON) |
| POST /api/audit | Screen supplied metadata |
| POST /api/chat | Deterministic mock response, not model inference |
| GET /api/audit/logs | Ledger metadata; requires configured AUDIT_LOGS_TOKEN and X-Audit-Token request header |

The HMAC audit ledger is in memory. It uses AUDIT_SECRET_KEY when set, otherwise generates an ephemeral random key, and entries do not persist across restarts.

~~~bash
export AUDIT_SECRET_KEY="replace-with-a-long-random-secret"
export AUDIT_LOGS_TOKEN="replace-with-a-separate-long-random-token"
docker compose up --build
~~~

## Privacy and security

Browser-only mode evaluates inputs locally without analytics or external services. Server mode transmits inputs to the chosen server, which keeps an in-memory registry and audit ledger. Basic regex matching detects some identifying strings but does **not** constitute complete PHI de-identification or HIPAA Safe Harbor compliance. **Do not enter real patient identifiers or protected health information.**

The public API is unauthenticated for local development; production deployments require TLS, authentication, traffic limits and appropriate network access restrictions. The audit-log endpoint is separately token-protected. The app is not a clinical or scientifically validated cryo-EM assessment system.

## Development and tests

~~~bash
python -m pip install -e ".[api,test]"
python -m compileall -q agents cryo_em_validator cli.py simulator.py enrichment.py
python -m pytest -q
node --check web/app.js
node --test tests/test_web.cjs
~~~

GitHub Actions runs Python and Node tests for pull requests and master. The separate Pages workflow deploys and smoke-tests the static browser app. A synthetic workload utility is available in simulator.py.

## Technology and browser compatibility

Python, Pydantic, FastAPI, pytest, vanilla HTML/CSS/JavaScript and Node for browser tests. The browser interface targets current Chromium, Firefox and Safari releases. Its standalone mode requires no backend or browser-Python runtime.

## License

MIT; see [LICENSE](LICENSE).
