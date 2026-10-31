#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ $# -ne 1 ]]; then echo "Usage: ./deploy.sh sha-<full-git-commit-sha>"; exit 2; fi
TAG="$1"
[[ "$TAG" =~ ^sha-[a-f0-9]{40}$ ]] || { echo "Expected sha-<40 hex characters>"; exit 2; }
[[ -f .env ]] || { echo "Create .env from .env.example first"; exit 2; }
for f in mysql_root_password mysql_app_password flask_secret_key; do [[ -s "secrets/$f.txt" ]] || { echo "Missing secrets/$f.txt"; exit 2; }; done
OLD_TAG="$(sed -n 's/^IMAGE_TAG=//p' .env | tail -1)"
cp .env .env.pre-release
sed -i.bak "s/^IMAGE_TAG=.*/IMAGE_TAG=$TAG/" .env
rm -f .env.bak
if ! docker compose pull flask || ! docker compose up -d --wait --wait-timeout 180; then
  echo "Deployment failed. Restoring previous tag: $OLD_TAG"
  mv .env.pre-release .env
  docker compose up -d --wait --wait-timeout 180 || true
  exit 1
fi
printf '%s\n' "$OLD_TAG" > .previous-image-tag
rm -f .env.pre-release
echo "Deployed $TAG; previous tag: $OLD_TAG"
