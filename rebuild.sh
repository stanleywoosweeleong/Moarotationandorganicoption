#!/usr/bin/env bash
# rebuild.sh - Build a single-file HTML app for production:
#   1. Precompile Tailwind CSS (only used classes, minified) and inline it.
#   2. Precompile the JSX (in-browser Babel -> plain JS) and inline it.
#   3. Self-host React/ReactDOM inline (no unpkg CDN).
#
# Result: one self-contained .html with NO cdn.tailwindcss.com, NO unpkg,
# NO in-browser Babel. Faster load, works offline, no console warnings.
#
# Usage:   ./rebuild.sh [path/to/file.html]
# Default: new_1.html
#
# Requires: Node.js + npx, and Python 3. First run downloads tooling into
# ./node_modules (one time); after that it works offline.
#
# ---------------------------------------------------------------------------
# IMPORTANT - JSX source of truth:
# On the FIRST run, your JSX is read from the <script type="text/babel"> block
# in the HTML and saved to a sibling file: <name>.app.jsx
# After that, the HTML no longer contains JSX (it holds compiled JS), so on
# every later run the JSX is read FROM <name>.app.jsx. ===> Edit your app code
# in <name>.app.jsx from then on, NOT inside the HTML. <===
# ---------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

HTML_FILE="${1:-new_1.html}"

if [[ ! -f "$HTML_FILE" ]]; then
  echo "ERROR: '$HTML_FILE' not found in $SCRIPT_DIR"
  exit 1
fi
echo ">> Target: $HTML_FILE"

# --- locate Python ---
if command -v python >/dev/null 2>&1; then PY=python
elif command -v py >/dev/null 2>&1; then PY=py
elif command -v python3 >/dev/null 2>&1; then PY=python3
else
  echo "ERROR: Python not found. Install from https://www.python.org/ (tick 'Add Python to PATH')."
  exit 1
fi

# --- one-time tooling install ---
if [[ ! -d node_modules/tailwindcss || ! -d node_modules/@babel/cli || ! -d node_modules/react ]]; then
  echo ">> Installing tooling (one-time): Tailwind, Babel, React..."
  npm install -D tailwindcss@3 @babel/core@7 @babel/cli@7 @babel/preset-react@7
  npm install react@18 react-dom@18
fi

# Derived names
BASE="${HTML_FILE%.html}"
JSX_FILE="${BASE}.app.jsx"
JS_FILE="$(mktemp).js"

# ===========================================================================
# STEP 1: TAILWIND
# ===========================================================================
cat > tailwind.config.js <<EOF
module.exports = {
  content: ["./$HTML_FILE", "./$JSX_FILE"],
  theme: { extend: {} },
  plugins: [],
}
EOF
[[ -f input.css ]] || printf '@tailwind base;\n@tailwind components;\n@tailwind utilities;\n' > input.css

echo ">> [1/2] Compiling Tailwind..."
npx tailwindcss -c tailwind.config.js -i input.css -o tailwind.css --minify
"$PY" inline_tw.py "$HTML_FILE" tailwind.css
rm -f tailwind.css

# ===========================================================================
# STEP 2: JSX PRECOMPILE + REACT RUNTIME
# ===========================================================================
echo ">> [2/2] Precompiling JSX..."

EXTRACT_RESULT="$("$PY" precompile_jsx.py extract "$HTML_FILE" "$JSX_FILE")"
if [[ "$EXTRACT_RESULT" == *"EXTRACTED"* ]]; then
  echo "   Extracted JSX from HTML -> $JSX_FILE (edit your app here from now on)."
elif [[ "$EXTRACT_RESULT" == *"NO_BABEL_BLOCK"* ]]; then
  if [[ -f "$JSX_FILE" ]]; then
    echo "   Using existing $JSX_FILE as JSX source."
  else
    echo "ERROR: HTML has no Babel block AND no $JSX_FILE exists."
    exit 1
  fi
else
  echo "$EXTRACT_RESULT"
  exit 1
fi

npx babel "$JSX_FILE" \
  --presets @babel/preset-react \
  --no-babelrc \
  -o "$JS_FILE"

"$PY" precompile_jsx.py inject "$HTML_FILE" "$JS_FILE" \
  node_modules/react/umd/react.production.min.js \
  node_modules/react-dom/umd/react-dom.production.min.js

rm -f "$JS_FILE"
echo ">> All done. $HTML_FILE is fully self-contained."
