# Security and observability

## Secrets
Compose file-backed secrets are mounted at `/run/secrets/...`. Flask reads `*_FILE`; MySQL uses `MYSQL_*_FILE`. Secret text files and `.env` are ignored by Git. CI uses disposable values for mocked tests and GitHub Actions secrets for Docker Hub login. Compose secrets are file mounts, not a cloud secret manager: protect host filesystem permissions and backups. Rotate compromised credentials; changing MySQL initialization env vars alone does not rotate passwords in an existing volume.

## Least privilege
Flask Dockerfile runs as UID 10001. Flask connects as `appuser`, not root. MySQL has no published host port. App binds host port to localhost only. CI token has `contents: read`; Docker Hub token should be scoped to minimum required repository write. Root MySQL credential is not mounted in Flask.

## Scanning
`.github/workflows/security.yml` runs `pip-audit` and Trivy; HIGH/CRITICAL fixable image vulnerabilities fail that job. Scans may expose vulnerabilities in pinned legacy packages; update and retest rather than bypass failures. Security workflow is separate from the existing publishing CI, so it does NOT currently gate image publication. To make scans a release gate, add both scans as dependencies of the publishing job or consolidate workflows.

## Metrics / alerts proposal (not deployed)
- Availability: `/readiness` failing for >2 minutes -> page operator.
- HTTP 5xx: >5% for 5 minutes -> warning.
- P95 request latency: >1 second for 5 minutes -> warning.
- Disk: >80% volume use -> warning.
- DB connectivity: readiness failure -> page operator.
Collect via reverse proxy/application metrics and host agent when moving beyond local demo. JSON app logs go to stdout; Docker log rotation is configured.
