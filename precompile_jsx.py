#!/usr/bin/env python3
"""
precompile_jsx.py - Replace the in-browser Babel JSX block with precompiled JS,
and inline React/ReactDOM so the file is fully self-contained (no unpkg CDN).

Steps performed on the HTML file:
  1. Find the <script type="text/babel"> ... </script> block.
  2. Save its JSX to a temp file (the rebuild.sh script compiles it with Babel).
  3. Replace that block with a plain <script> holding the compiled JS, between
     PC:START / PC:END markers (so re-runs replace cleanly).
  4. Replace the three unpkg React/ReactDOM/Babel <script> tags with two inline
     <script> blocks holding the React + ReactDOM UMD source.

Safe to run repeatedly.

Usage:
  python precompile_jsx.py extract  <html_file> <out_jsx_file>
  python precompile_jsx.py inject   <html_file> <compiled_js_file> \
                                    <react_umd_file> <reactdom_umd_file>
"""
import re
import sys

PC_START = "<!-- PC:START (auto-generated app script, do not edit by hand) -->"
PC_END = "<!-- PC:END -->"
RC_START = "<!-- RC:START (auto-generated React runtime, do not edit by hand) -->"
RC_END = "<!-- RC:END -->"

BABEL_BLOCK_RE = re.compile(
    r'<script\s+type="text/babel"\s*>(.*?)</script>', re.DOTALL
)
PC_BLOCK_RE = re.compile(
    re.escape(PC_START) + r".*?" + re.escape(PC_END), re.DOTALL
)
RC_BLOCK_RE = re.compile(
    re.escape(RC_START) + r".*?" + re.escape(RC_END), re.DOTALL
)

# The three CDN runtime <script> tags we replace (matched loosely on src host).
CDN_RUNTIME_RE = re.compile(
    r'[ \t]*<script[^>]*src="https://unpkg\.com/(?:react|react-dom|@babel/standalone)[^"]*"[^>]*>\s*</script>\s*\n',
    re.IGNORECASE,
)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def get_jsx(html):
    # Prefer the already-marked precompiled block on re-runs; if absent, the
    # original babel block.
    m = PC_BLOCK_RE.search(html)
    if m:
        # Extract the JS we previously injected so we can recompile from... no:
        # we cannot recover original JSX from compiled JS. So on re-runs we read
        # JSX from the sibling .jsx file instead (rebuild.sh keeps it). Signal
        # that here by returning None.
        return None
    m = BABEL_BLOCK_RE.search(html)
    if not m:
        return None
    return m.group(1)


def cmd_extract(html_file, out_jsx):
    html = read(html_file)
    jsx = get_jsx(html)
    if jsx is None:
        print("NO_BABEL_BLOCK")  # rebuild.sh interprets this
        return 0
    write(out_jsx, jsx)
    print("EXTRACTED")
    return 0


def cmd_inject(html_file, js_file, react_umd, reactdom_umd):
    html = read(html_file)
    compiled = read(js_file).strip()
    react_src = read(react_umd).strip()
    reactdom_src = read(reactdom_umd).strip()

    app_block = (
        f"{PC_START}\n"
        f'  <script>\n{compiled}\n  </script>\n'
        f"  {PC_END}"
    )
    runtime_block = (
        f"{RC_START}\n"
        f"  <script>\n{react_src}\n  </script>\n"
        f"  <script>\n{reactdom_src}\n  </script>\n"
        f"  {RC_END}"
    )

    # --- replace the app script (babel block on first run, PC block after) ---
    if PC_BLOCK_RE.search(html):
        html = PC_BLOCK_RE.sub(lambda _: app_block, html, count=1)
        print("Updated existing precompiled app block.")
    elif BABEL_BLOCK_RE.search(html):
        html = BABEL_BLOCK_RE.sub(lambda _: app_block, html, count=1)
        print("Replaced in-browser Babel block with precompiled JS.")
    else:
        print("ERROR: no Babel block and no PC marker found in HTML.")
        return 1

    # --- replace the React runtime ---
    if RC_BLOCK_RE.search(html):
        html = RC_BLOCK_RE.sub(lambda _: runtime_block, html, count=1)
        print("Updated existing inlined React runtime.")
    elif CDN_RUNTIME_RE.search(html):
        # Replace the first CDN runtime tag with the whole runtime block, then
        # delete any remaining CDN runtime tags.
        html = CDN_RUNTIME_RE.sub(
            lambda _: "  " + runtime_block + "\n", html, count=1
        )
        html = CDN_RUNTIME_RE.sub("", html)
        print("Replaced unpkg React/Babel CDN tags with inlined runtime.")
    else:
        print("WARNING: no React CDN tags and no RC marker. App script updated,")
        print("but React runtime not found - check the file manually.")

    # --- safety checks ---
    leftovers = re.findall(
        r'https://unpkg\.com/(?:react|react-dom|@babel/standalone)', html
    )
    if leftovers:
        print(f"ERROR: {len(leftovers)} unpkg runtime ref(s) still present.")
        return 1
    if 'type="text/babel"' in html:
        print("ERROR: a type=text/babel script is still present.")
        return 1

    write(html_file, html)
    print(f"Done. Wrote {html_file} ({len(html):,} bytes).")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    mode = sys.argv[1]
    if mode == "extract" and len(sys.argv) == 4:
        return cmd_extract(sys.argv[2], sys.argv[3])
    if mode == "inject" and len(sys.argv) == 6:
        return cmd_inject(
            sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        )
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
