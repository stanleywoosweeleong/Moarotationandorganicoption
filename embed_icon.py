#!/usr/bin/env python3
"""
embed_icon.py — Embed icon.svg into index.html as the favicon + apple-touch-icon,
and inject a brand boot/splash overlay that shows the icon while the app loads.

Re-run after editing make_icon.py -> icon.svg. Safe to run repeatedly (idempotent:
it replaces previously-embedded blocks between markers).

Usage: python embed_icon.py [index.html]
"""
import base64, re, sys, urllib.parse

try:
    import cairosvg
except ImportError:
    cairosvg = None

ICON_START = "<!-- ICON:START (auto-embedded, do not edit by hand) -->"
ICON_END   = "<!-- ICON:END -->"
BOOT_START = "<!-- BOOT:START (auto-embedded, do not edit by hand) -->"
BOOT_END   = "<!-- BOOT:END -->"

def main():
    html_path = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    svg = open("icon.svg", encoding="utf-8").read().strip()

    # favicon: SVG as URL-encoded data URI (crisp at any size)
    svg_uri = "data:image/svg+xml," + urllib.parse.quote(svg)

    # apple-touch-icon: needs PNG. Render 180px if cairosvg available, else reuse SVG.
    if cairosvg:
        png = cairosvg.svg2png(bytestring=svg.encode(), output_width=180, output_height=180)
        png_b64 = base64.b64encode(png).decode()
        apple = f'data:image/png;base64,{png_b64}'
    else:
        apple = svg_uri  # fallback; iOS prefers PNG but this still works in most cases

    icon_block = (
        f'{ICON_START}\n'
        f'  <link rel="icon" type="image/svg+xml" href="{svg_uri}" />\n'
        f'  <link rel="apple-touch-icon" href="{apple}" />\n'
        f'  {ICON_END}'
    )

    # Boot overlay: full-screen brand-green, centered icon + name, fades out on load.
    boot_block = f'''{BOOT_START}
  <div id="boot-splash" aria-hidden="true">
    <div class="boot-inner">
      <div class="boot-icon">{svg}</div>
      <div class="boot-title">虫药轮替 · Pest MoA</div>
      <div class="boot-sub">Chemical Once, Organic Once · 一次化学 · 一次有机</div>
    </div>
  </div>
  <style>
    #boot-splash{{position:fixed;inset:0;z-index:9999;background:#114b2d;
      display:flex;align-items:center;justify-content:center;
      transition:opacity .45s ease;opacity:1;}}
    #boot-splash.hide{{opacity:0;pointer-events:none;}}
    #boot-splash .boot-inner{{display:flex;flex-direction:column;align-items:center;gap:18px;padding:24px;text-align:center;}}
    #boot-splash .boot-icon{{width:128px;height:128px;animation:bootpop .5s ease;}}
    #boot-splash .boot-icon svg{{width:100%;height:100%;display:block;
      filter:drop-shadow(0 6px 20px rgba(0,0,0,.35));}}
    #boot-splash .boot-title{{color:#f4f2ea;font-weight:800;font-size:22px;
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans SC",sans-serif;}}
    #boot-splash .boot-sub{{color:#a7d7c0;font-weight:600;font-size:12.5px;letter-spacing:.02em;
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans SC",sans-serif;}}
    @keyframes bootpop{{0%{{transform:scale(.82);opacity:0;}}100%{{transform:scale(1);opacity:1;}}}}
    @media (prefers-reduced-motion:reduce){{
      #boot-splash{{transition:none;}} #boot-splash .boot-icon{{animation:none;}}
    }}
  </style>
  <script>
    // Hide the splash once the app has mounted (or after a safety timeout).
    (function(){{
      function hide(){{var s=document.getElementById('boot-splash');
        if(s&&!s.classList.contains('hide')){{s.classList.add('hide');
          setTimeout(function(){{if(s&&s.parentNode)s.parentNode.removeChild(s);}},600);}}}}
      var root=document.getElementById('root');
      var done=false;
      function check(){{
        if(done) return true;
        if(root&&root.children.length>0){{ done=true; setTimeout(hide,250); return true; }}
        return false;
      }}
      // Poll for React mount (reliable across browsers); also observe as a fast path.
      if(!check()){{
        var iv=setInterval(function(){{ if(check()) clearInterval(iv); }},60);
        try{{
          var mo=new MutationObserver(function(){{ if(check()){{mo.disconnect();clearInterval(iv);}} }});
          mo.observe(root,{{childList:true}});
        }}catch(e){{}}
      }}
      // Safety net: never let the splash get stuck.
      setTimeout(hide,5000);
    }})();
  </script>
  {BOOT_END}'''

    html = open(html_path, encoding="utf-8").read()

    # --- icon block: replace existing markered block, else replace old icon links ---
    if ICON_START in html and ICON_END in html:
        html = re.sub(re.escape(ICON_START) + r".*?" + re.escape(ICON_END),
                      lambda _: icon_block, html, count=1, flags=re.DOTALL)
        print("Updated existing ICON block.")
    else:
        # remove the legacy hand-embedded favicon + apple-touch-icon links, insert before </head>
        html = re.sub(r'\s*<link rel="icon"[^>]*?/>', '', html, count=1, flags=re.DOTALL)
        html = re.sub(r'\s*<link rel="apple-touch-icon"[^>]*?/>', '', html, count=1, flags=re.DOTALL)
        html = html.replace("</head>", "  " + icon_block + "\n</head>", 1)
        print("Inserted new ICON block (replaced legacy links).")

    # --- boot block: replace existing, else insert right after <body> ---
    if BOOT_START in html and BOOT_END in html:
        html = re.sub(re.escape(BOOT_START) + r".*?" + re.escape(BOOT_END),
                      lambda _: boot_block, html, count=1, flags=re.DOTALL)
        print("Updated existing BOOT block.")
    else:
        html = re.sub(r'(<body>)', r'\1\n  ' + boot_block.replace('\\', '\\\\'), html, count=1)
        print("Inserted new BOOT splash block after <body>.")

    open(html_path, "w", encoding="utf-8").write(html)
    print(f"Done. Wrote {html_path}.")

if __name__ == "__main__":
    main()
