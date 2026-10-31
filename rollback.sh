#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
TAG="${1:-$(cat .previous-image-tag 2>/dev/null || true)}"
[[ "$TAG" =~ ^sha-[a-f0-9]{40}$ ]] || { echo "Usage: ./rollback.sh sha-<full-git-commit-sha> (or previous release must be recorded)"; exit 2; }
./deploy.sh "$TAG"
