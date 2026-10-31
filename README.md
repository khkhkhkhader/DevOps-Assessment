# BucketList Flask DevOps Assessment

Flask 2.3.3 + MySQL 8.4 deployed with Docker Compose. CI tests and publishes SHA-tagged Flask images to Docker Hub on `main` pushes. See `docs/runbook.md` for setup, release, rollback, health checks and failure drill; `docs/security.md` for security, scans and alert proposal; `docs/cloud-plan.md` for hosting plan.

Quick start: copy `.env.example` to `.env`, enter Docker Hub username and published full SHA tag, create three local secret files listed in `docs/runbook.md`, then `docker compose pull flask && docker compose up -d --wait`. Browse `http://127.0.0.1:5002`. Requires Docker Compose v2. No real secrets are included in this repository.
