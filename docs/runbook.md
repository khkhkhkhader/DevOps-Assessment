# Operations runbook

## First deployment
1. Install Docker Engine and Compose v2. Clone repository.
2. `cp .env.example .env`; set Docker Hub username and an existing `sha-<full commit SHA>` tag.
3. Create `secrets/mysql_root_password.txt`, `secrets/mysql_app_password.txt`, `secrets/flask_secret_key.txt` locally with strong random values; do not commit them.
4. `docker compose pull flask && docker compose up -d --wait --wait-timeout 180`.
5. `docker compose ps`; `curl -fsS http://127.0.0.1:5002/healthz`; `curl -fsS http://127.0.0.1:5002/readiness`.
6. Create a user and wish in the UI. `docker compose restart`; confirm wish persists. Never use `docker compose down -v` unless intentionally deleting DB data.

## Release and rollback
- Save current working SHA and verify the new SHA exists in Docker Hub.
- `./deploy.sh sha-<new full commit SHA>`; script pulls image, waits for health and restores previous tag on failure.
- To roll back: `./rollback.sh sha-<previous full commit SHA>` (or `./rollback.sh` if a prior release was recorded).
- Confirm health and application behavior. Database schema rollback is NOT automatic; maintain backward-compatible migrations and backups.

## Failure investigation (reproducible demonstration)
1. Baseline: `curl -i http://127.0.0.1:5002/readiness` => 200.
2. `docker compose stop mysql`.
3. `curl -i http://127.0.0.1:5002/readiness` => 503; Flask healthcheck becomes unhealthy after its retry window.
4. `docker compose logs --tail=100 flask mysql` to see JSON event `readiness_failed` and DB shutdown.
5. `docker compose start mysql`; wait for healthy; readiness should return 200.
6. Save terminal output/screenshots with timestamps as evidence. This procedure is documented, not claimed as executed here.

## Troubleshooting
- `docker compose ps`; `docker compose logs --tail=200 flask mysql`.
- Check local secrets exist, .env SHA and username are correct, Docker Hub image is accessible, and MySQL volume is writable.
- Never paste secret contents into tickets or logs.
