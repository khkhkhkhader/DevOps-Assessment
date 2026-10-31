
# BucketList — Flask & MySQL | Junior DevOps Assessment

A containerized Flask web application backed by MySQL.

This project demonstrates Docker Compose deployment, GitHub Actions CI, automated testing, security scanning, Docker Hub image publishing, secure secret management, and manual deployment and rollback.

## 1. Architecture

```text
Developer
   |
   v
GitHub Repository (main)
   |
   v
GitHub Actions
   |
   +-- Ruff Lint
   +-- Unit Tests
   +-- pip-audit
   +-- Trivy Security Scan
   |
   v
Docker Build & Push
   |
   v
Docker Hub
   |
   v
Docker Compose (Deployment Server)
   |
   +-- Flask Application
   |
   +-- MySQL Database
         |
         +-- Persistent Docker Volume
```

The application uses Docker Compose rather than Kubernetes.

GitHub Actions builds and publishes the Flask Docker image after successful tests. Deployment and rollback are performed manually on the target server.

Security scans are report-only and do not block image publishing.

## 2. Project Structure

```text
.github/
  workflows/
    ci.yml

flaskapp/
  app.py
  Dockerfile
  requirements.txt
  tests/
    test_app.py
  templates/
  static/

mysql/
  Dockerfile
  BucketList.sql

secrets/
  mysql_root_password.txt
  mysql_app_password.txt
  flask_secret_key.txt

compose.yaml
README.md
```

The files inside `secrets/` are created locally and must never be committed to GitHub.

## 3. Prerequisites

Before deploying, ensure the following tools are available:

- Docker Engine
- Docker Compose v2
- Git
- OpenSSL
- Docker Hub account
- Access to the project repository

Verify Docker and Docker Compose:

```bash
docker --version
docker compose version
```

## 4. Clone the Repository

Clone the project onto the deployment server:

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY_DIRECTORY
```

## 5. Create Docker Secrets

The project uses Docker Compose Secrets to keep database passwords and the Flask secret key out of the source code and Docker images.

### Step 1 — Create the Secrets Directory

From the project root:

```bash
mkdir -p secrets
chmod 700 secrets
```

### Step 2 — Generate the Secret Files

Generate three random secret values:

```bash
openssl rand -hex 32 > secrets/mysql_root_password.txt

openssl rand -hex 32 > secrets/mysql_app_password.txt

openssl rand -hex 32 > secrets/flask_secret_key.txt
```

The generated files are:

| File | Purpose |
| --- | --- |
| `mysql_root_password.txt` | MySQL root password |
| `mysql_app_password.txt` | MySQL application user password |
| `flask_secret_key.txt` | Flask session signing secret |

### Step 3 — Configure File Permissions

```bash
chmod 644 secrets/*.txt
```

Verify:

```bash
ls -l secrets/
```

Expected file permissions:

```text
-rw-r--r-- mysql_root_password.txt
-rw-r--r-- mysql_app_password.txt
-rw-r--r-- flask_secret_key.txt
```

**Security note:** Permission `644` allows other local users to read these files if they can access their directory. The `secrets/` directory uses `700` to restrict access. Permission `600` is preferable when compatible with container access requirements.

### Step 4 — How Docker Compose Secrets Work

The Compose configuration references local secret files:

```yaml
secrets:
  mysql_root_password:
    file: ./secrets/mysql_root_password.txt

  mysql_app_password:
    file: ./secrets/mysql_app_password.txt

  flask_secret_key:
    file: ./secrets/flask_secret_key.txt
```

Docker Compose mounts the declared secrets into the containers that request them.

Inside the containers, secrets are available under:

```text
/run/secrets/
```

For example:

```text
/run/secrets/mysql_root_password
/run/secrets/mysql_app_password
/run/secrets/flask_secret_key
```

The application must read the relevant secret files. Docker Compose does not automatically convert their contents into environment variables.

The MySQL image can use supported `_FILE` environment variables, such as:

```yaml
environment:
  MYSQL_ROOT_PASSWORD_FILE: /run/secrets/mysql_root_password
```

### Important Notes

- Never commit secret values to GitHub.
- Never put passwords directly in the Dockerfile.
- Never include secret values in Docker image tags.
- Keep secret files out of logs and screenshots.
- Do not regenerate database passwords for an existing initialized database without a proper password rotation procedure.
- Ensure secret files are excluded by `.gitignore`.

### Troubleshooting Missing Secrets

If Docker Compose displays:

```text
secret file does not exist
```

or:

```text
invalid mount config for type "bind":
bind source path does not exist
```

Check:

```bash
ls -l secrets/
```

Create any missing secret files before starting the containers.

## 6. Docker Compose Deployment

The Flask service uses a Docker image published to Docker Hub.

Example configuration:

```yaml
services:
  flask:
    image: ${DOCKERHUB_USERNAME:?Set DOCKERHUB_USERNAME}/bucketlist:${IMAGE_TAG:?Set IMAGE_TAG}
```

The Docker Hub username and image tag are provided directly through the CLI.

### Deploy the Latest Image

On Linux:

```bash
DOCKERHUB_USERNAME=YOUR_USERNAME IMAGE_TAG=latest docker compose up -d --pull always
```

Replace `YOUR_USERNAME` with your Docker Hub username.

This command:

1. Resolves the Docker Hub image name.
2. Pulls the requested image.
3. Creates or updates the containers.
4. Starts the services in detached mode.

### Deploy a Specific Version

GitHub Actions publishes images using commit SHA tags.

Example:

```bash
DOCKERHUB_USERNAME=YOUR_USERNAME IMAGE_TAG=sha-FULL_COMMIT_SHA docker compose up -d --pull always
```

Use an actual image tag that exists in Docker Hub.

### Check Container Status

```bash
docker compose ps
```

### View Application Logs

```bash
docker compose logs --tail=100 flask
```

### View MySQL Logs

```bash
docker compose logs --tail=100 mysql
```

## 7. Health Checks

The application provides endpoints for health and readiness verification.

### Application Health

```bash
curl -i http://127.0.0.1:5002/healthz
```

This endpoint checks whether the Flask application is responding.

### Database Readiness

```bash
curl -i http://127.0.0.1:5002/readiness
```

This endpoint checks whether the application can connect to MySQL.

A successful readiness check returns HTTP `200`.

A failed readiness check may return HTTP `503`.

The examples assume Flask is published on localhost port `5002`. Adjust the address if the deployed Compose configuration uses a different port.

## 8. GitHub Actions CI Pipeline

The project uses a GitHub Actions workflow located at:

```text
.github/workflows/ci.yml
```

The pipeline runs when code is pushed to `main`, when a pull request targets `main`, or when manually triggered.

### CI Stages

| Stage | Tool | Behavior |
| --- | --- | --- |
| Code Linting | Ruff | Required |
| Unit Testing | Pytest | Required |
| Dependency Scanning | pip-audit | Report only |
| Container Scanning | Trivy | Report only |
| Docker Build | Docker Buildx | Required for publishing |
| Docker Push | Docker Hub | Runs after successful tests |

### Pipeline Rules

- Failed tests block Docker image publishing.
- Failed lint checks block publishing.
- Security findings are reported without blocking publishing.
- Docker images are pushed on successful qualifying pushes to `main`.
- Docker Hub authentication and image publishing must succeed.

### GitHub Actions Secrets

Configure the following repository secrets:

Navigate to:

```text
GitHub Repository
  -> Settings
  -> Secrets and variables
  -> Actions
  -> Repository secrets
```

Add:

| Secret | Description |
| --- | --- |
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token with push permission |

The Docker Hub token must have sufficient permissions to push images to the target repository.

### Published Image Tags

The pipeline publishes:

```text
YOUR_USERNAME/bucketlist:latest
```

and:

```text
YOUR_USERNAME/bucketlist:sha-FULL_COMMIT_SHA
```

`latest` is a normal Docker image tag maintained by the publishing workflow.

The `sha-...` tag identifies a specific Git commit.

## 9. Manual Rollback

Rollback is performed using Docker Compose without additional deployment scripts.

### Step 1 — Identify the Previous Image

Open Docker Hub and locate a previously published image tag.

Example:

```text
YOUR_USERNAME/bucketlist:sha-PREVIOUS_FULL_COMMIT_SHA
```

### Step 2 — Redeploy the Previous Version

```bash
DOCKERHUB_USERNAME=YOUR_USERNAME IMAGE_TAG=sha-PREVIOUS_FULL_COMMIT_SHA docker compose up -d --pull always
```

### Step 3 — Verify the Rollback

```bash
docker compose ps
```

```bash
docker compose logs --tail=100 flask
```

```bash
curl -i http://127.0.0.1:5002/readiness
```

**Important:** Rolling back the Flask image does not roll back MySQL database data or schema changes.

There is no automatic `previous` Docker tag unless the publishing workflow explicitly creates and maintains one.

## 10. Local Testing

Install the Python dependencies:

```bash
cd flaskapp

python -m pip install -r requirements.txt pytest ruff
```

Set temporary testing variables:

```bash
export FLASK_SECRET_KEY="$(openssl rand -hex 32)"
export MYSQL_DATABASE_PASSWORD="$(openssl rand -hex 32)"
export MYSQL_DATABASE_USER=appuser
export MYSQL_DATABASE_HOST=localhost
export MYSQL_DATABASE_DB=BucketList
```

Run Ruff:

```bash
ruff check . --select E4,E7,E9,F63,F7,F82
```

Run unit tests:

```bash
python -m pytest -q tests/
```

The unit tests mock database interactions and do not require a live MySQL database.

## 11. Troubleshooting

### Missing Docker Secrets

Error:

```text
secret file does not exist
```

Solution:

```bash
ls -l secrets/
```

Verify that all three secret files exist.

### Docker Hub Push Failed

Error:

```text
401 Unauthorized:
access token has insufficient scopes
```

Check:

- Docker Hub username
- Docker Hub access token
- Repository permissions
- GitHub Actions repository secrets

The access token must have write permission for the target repository.

### Flask Container Not Running

```bash
docker compose ps
docker compose logs --tail=100 flask
```

Check the application logs for startup failures.

### Database Connection Failed

```bash
docker compose logs --tail=100 mysql
```

Verify that the database is healthy and that the application uses the correct database credentials.

### Docker Image Not Found

Confirm that the requested image tag exists on Docker Hub and was published successfully.

## 12. Data Persistence

MySQL data is stored in a Docker named volume:

```text
mysql_data
```

Stopping or recreating containers normally preserves data in the volume.

To stop the project:

```bash
docker compose down
```

**Warning:** Do not run the following command unless you deliberately intend to delete the database volume:

```bash
docker compose down -v
```

The `-v` option removes named volumes declared in the Compose project and may cause permanent data loss.

## 13. Security Practices

The project implements or demonstrates the following security practices:

- Docker Compose Secrets for database credentials and Flask secret key.
- GitHub Actions Secrets for Docker Hub authentication.
- Non-root Flask container user.
- Dedicated MySQL application user instead of using root.
- Dependency vulnerability scanning using pip-audit.
- Container vulnerability scanning using Trivy.
- Separation between application and database services.
- Persistent database storage.
- Application health and readiness checks.

Security scans are configured as report-only.

A successful pipeline does not guarantee that the image is free of vulnerabilities. Security findings should be reviewed before production deployment.

## 14. Operational Considerations

This project is designed as a single-host Docker Compose deployment.

For production use, additional considerations include:

- HTTPS and reverse proxy configuration.
- Database backups and restore testing.
- Monitoring and alerting.
- Centralized log collection.
- Vulnerability remediation.
- Image version pinning.
- Disaster recovery planning.
- Safe database migrations.

## 15. Assessment Evidence

Recommended evidence for the assessment submission:

- GitHub Actions successful CI run.
- Unit test and lint output.
- Failed-test demonstration blocking image publishing.
- pip-audit security scan results.
- Trivy security scan results.
- Successful Docker Hub image push.
- Docker Compose running containers.
- Application health and readiness results.
- Manual rollback demonstration.
- Troubleshooting evidence showing diagnosis and resolution.

Only submit screenshots and logs from operations actually performed.

## 16. AI Assistance Disclosure

AI assistance was used to help draft documentation, explain Docker Compose and GitHub Actions concepts, and propose CI, security, and deployment commands.

All configuration changes, security settings, testing results, and deployment outcomes should be independently reviewed and validated.

## License

No license is currently declared for this repository.
