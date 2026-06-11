#!/usr/bin/env python3
"""
inline_tw.py - Inline compiled Tailwind CSS into a single-file HTML.

Replaces EITHER the Tailwind CDN <script> OR a previously-inlined Tailwind
<style> block with a fresh compiled <style> block. Safe to run repeatedly.

Usage: python inline_tw.py <html_file> <compiled_css_file>
"""
import re
import sys

START = "<!-- TW:START (auto-generated, do not edit by hand) -->"
END = "<!-- TW:END -->"
CDN = '<script src="https://cdn.tailwindcss.com"></script>'


def build_block(css: str) -> str:
    return f"{START}\n  <style>\n{css}\n  </style>\n  {END}"


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python inline_tw.py <html_file> <compiled_css_file>")
        return 2

    html_path, css_path = sys.argv[1], sys.argv[2]

    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    with open(css_path, encoding="utf-8") as f:
        css = f.read().strip()

    block = build_block(css)

    # Case 1: already inlined -> replace the old generated block.
    if START in html and END in html:
        html = re.sub(
            re.escape(START) + r".*?" + re.escape(END),
            block.replace("\\", "\\\\"),  # protect backrefs in replacement
            html,
            count=1,
            flags=re.DOTALL,
        )
        print("Updated existing inlined Tailwind block.")
    # Case 2: CDN present -> swap it for the inlined block.
    elif CDN in html:
        html = html.replace(CDN, block, 1)
        print("Replaced Tailwind CDN script with inlined block.")
    else:
        print("ERROR: found neither the TW:START marker nor the Tailwind CDN")
        print("script. Add the CDN line back once, then re-run.")
        return 1

    # Safety: the CDN must be gone afterwards.
    if "cdn.tailwindcss.com" in html:
        print("ERROR: CDN reference still present after processing. Aborted.")
        return 1

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Done. Wrote {html_path} ({len(html):,} bytes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
