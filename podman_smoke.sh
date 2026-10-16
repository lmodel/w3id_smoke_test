#!/usr/bin/env bash
# Spin up a local Apache 2.4 with a namespace's .htaccess mounted under its
# own name, then run w3id_smoke_test.py against it. Cleans up on exit.
#
# Usage:   ./podman_smoke.sh [path/to/ids/<namespace>/.htaccess]
# Default: ../w3id.org/ids/lmodel/.htaccess beside this repository.
# The namespace is the .htaccess file's folder name (lmodel, ktl), which is
# both the URL path it is served at and the SUITE of cases that runs.
#
# Requires: podman (or docker; set ENGINE=docker to switch), curl, bash.
# Pin image tag to keep [N]-restart and AllowOverride semantics reproducible.

set -euo pipefail

ENGINE="${ENGINE:-podman}"
IMAGE="${IMAGE:-docker.io/library/httpd:2.4.62}"
PORT="${PORT:-18080}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HTACCESS="${1:-$SCRIPT_DIR/../w3id.org/ids/lmodel/.htaccess}"

if [[ ! -f "$HTACCESS" ]]; then
  echo "ERROR: .htaccess not found at: $HTACCESS" >&2
  echo "Pass the path as the first argument." >&2
  exit 2
fi
HTACCESS="$(realpath "$HTACCESS")"
NS="$(basename "$(dirname "$HTACCESS")")"
NAME="${NAME:-$NS-smoke}"

SMOKE="${SMOKE:-$SCRIPT_DIR/w3id_smoke_test.py}"
[[ -f "$SMOKE" ]] || { echo "ERROR: smoke test not found: $SMOKE" >&2; exit 2; }

# Pick a Python >= 3.7 for the runner. Override with PYTHON=python3.11.
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  for cand in python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3; do
    if command -v "$cand" >/dev/null 2>&1; then PYTHON="$cand"; break; fi
  done
fi
[[ -n "$PYTHON" ]] || { echo "ERROR: no python3 found (set PYTHON=...)" >&2; exit 2; }

# httpd:2.4 default DocumentRoot is /usr/local/apache2/htdocs.
# We mount the .htaccess into a /$NS/ subdirectory so URLs match
# the w3id.org layout: BASE="http://localhost:$PORT/$NS".
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"; "$ENGINE" rm -f "$NAME" >/dev/null 2>&1 || true' EXIT

mkdir -p "$WORK/$NS"
cp "$HTACCESS" "$WORK/$NS/.htaccess"
# mktemp -d creates 0700; the container's httpd runs as a different UID and
# needs +rX on the mount, or every request 403s with "pcfg_openfile: ... is executable".
chmod -R a+rX "$WORK"

# Minimal httpd.conf override: enable mod_rewrite + AllowOverride All.
cat > "$WORK/smoke.conf" <<'CONF'
LoadModule rewrite_module modules/mod_rewrite.so
<Directory "/usr/local/apache2/htdocs">
    AllowOverride All
    Require all granted
    Options +FollowSymLinks -MultiViews
</Directory>
CONF

echo "Starting $ENGINE container '$NAME' on :$PORT (image: $IMAGE)..."
"$ENGINE" rm -f "$NAME" >/dev/null 2>&1 || true
"$ENGINE" run -d --rm --name "$NAME" \
  -p "$PORT:80" \
  -v "$WORK:/usr/local/apache2/htdocs:ro,Z" \
  -v "$WORK/smoke.conf:/usr/local/apache2/conf/extra/smoke.conf:ro,Z" \
  "$IMAGE" \
  sh -c 'echo "Include conf/extra/smoke.conf" >> /usr/local/apache2/conf/httpd.conf && httpd-foreground' \
  >/dev/null

# Wait for Apache to come up (max ~10s).
for _ in $(seq 1 50); do
  if curl -sf -o /dev/null "http://localhost:$PORT/$NS/" || \
     [[ $(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/$NS/") =~ ^[23]0[0-9]$ ]]; then
    break
  fi
  sleep 0.2
done

echo "Running the $NS suite against http://localhost:$PORT/$NS ..."
echo "  runner: $PYTHON $SMOKE"
echo
SUITE="$NS" BASE="http://localhost:$PORT/$NS" "$PYTHON" "$SMOKE"
