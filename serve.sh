#!/usr/bin/env bash
# serve.sh - Serve the current folder over http://localhost so the page runs
# from a real origin (not file://). This is needed for service workers, the
# Anthropic API, and anything else browsers block on file:// pages.
#
# Usage:   ./serve.sh [port]
# Default: port 8000  ->  http://localhost:8000/
#
# Stop the server with Ctrl+C.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${1:-8000}"

# locate Python
if command -v python >/dev/null 2>&1; then PY=python
elif command -v py >/dev/null 2>&1; then PY=py
elif command -v python3 >/dev/null 2>&1; then PY=python3
else
  echo "ERROR: Python not found. Install from https://www.python.org/"
  exit 1
fi

echo "Serving $SCRIPT_DIR"
echo "Open:  http://localhost:$PORT/"
echo "       (then click your .html file, e.g. http://localhost:$PORT/new_1.html)"
echo "Press Ctrl+C to stop."
echo

"$PY" -m http.server "$PORT"
