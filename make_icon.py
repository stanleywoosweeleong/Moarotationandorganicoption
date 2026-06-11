import math

# ============================================================================
# App icon — a central pest (cream) inside a TWO-ARROW rotation cycle, where the
# two arrows are different colours to express the app's core idea:
#   GREEN arrow  = organic spray   (一次有机)
#   BLUE  arrow  = chemical spray  (一次化学)
# i.e. "Chemical Once, Organic Once" — rotate between the two.
# Brand-green rounded-square background ties it to the rest of the UI.
# ============================================================================

CX, CY = 256, 256
GREEN_BG = "#114b2d"   # brand background (rounded square)
ORGANIC  = "#34d399"   # organic arrow — bright emerald (reads on dark bg)
CHEMICAL = "#38bdf8"   # chemical arrow — sky blue
CREAM    = "#f4f2ea"   # the bug

def pt(a_deg, r):
    a = math.radians(a_deg)
    return (CX + r*math.sin(a), CY - r*math.cos(a))   # 0=top, clockwise

def arc(a1, a2, r):
    x1, y1 = pt(a1, r); x2, y2 = pt(a2, r)
    large = 1 if (a2 - a1) % 360 > 180 else 0
    return f"M {x1:.1f} {y1:.1f} A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f}"

R = 150
SW = 30

# Two ~120-degree arcs forming a clockwise cycle, gaps at top & bottom.
arc_right = arc(30, 150, R)    # right side, top -> bottom   (CHEMICAL, blue)
arc_left  = arc(210, 330, R)   # left side, bottom -> top    (ORGANIC, green)

def arrowhead(ae):
    tipx, tipy = pt(ae + 12, R)
    bx, by     = pt(ae - 4,  R + SW * 0.95)
    ix, iy     = pt(ae - 4,  R - SW * 0.95)
    return f"M {tipx:.1f} {tipy:.1f} L {bx:.1f} {by:.1f} L {ix:.1f} {iy:.1f} Z"

ah_right = arrowhead(150)   # leading end of the blue (chemical) arrow, at bottom
ah_left  = arrowhead(330)   # leading end of the green (organic) arrow, at top

# --- center bug (cream) ---
body  = f'<ellipse cx="{CX}" cy="285" rx="40" ry="54" fill="{CREAM}"/>'
head  = f'<circle cx="{CX}" cy="226" r="24" fill="{CREAM}"/>'
split = f'<line x1="{CX}" y1="240" x2="{CX}" y2="335" stroke="{GREEN_BG}" stroke-width="7" stroke-linecap="round"/>'
ant   = (f'<path d="M {CX-10} 210 Q {CX-26} 190 {CX-30} 178" stroke="{CREAM}" stroke-width="7" fill="none" stroke-linecap="round"/>'
         f'<path d="M {CX+10} 210 Q {CX+26} 190 {CX+30} 178" stroke="{CREAM}" stroke-width="7" fill="none" stroke-linecap="round"/>')
legs = ""
for ly in (262, 290, 318):
    legs += (f'<line x1="{CX-36}" y1="{ly}" x2="{CX-66}" y2="{ly-10}" stroke="{CREAM}" stroke-width="8" stroke-linecap="round"/>'
             f'<line x1="{CX+36}" y1="{ly}" x2="{CX+66}" y2="{ly-10}" stroke="{CREAM}" stroke-width="8" stroke-linecap="round"/>')

svg = f'''<svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" rx="115" fill="{GREEN_BG}"/>
  <path d="{arc_right}" fill="none" stroke="{CHEMICAL}" stroke-width="{SW}" stroke-linecap="round"/>
  <path d="{arc_left}"  fill="none" stroke="{ORGANIC}"  stroke-width="{SW}" stroke-linecap="round"/>
  <path d="{ah_right}" fill="{CHEMICAL}"/>
  <path d="{ah_left}"  fill="{ORGANIC}"/>
  {legs}
  {ant}
  {body}
  {head}
  {split}
</svg>'''
open("icon.svg", "w").write(svg)
print("wrote icon.svg (pest + two-tone green/blue rotation)")
