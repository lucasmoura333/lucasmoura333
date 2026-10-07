#!/usr/bin/env python3
"""Elden Console - render.

Desenha a moldura (Erdtree) e as fatias do console como SVGs separados que,
empilhados no README, parecem uma janela unica e continua.

Truques de emenda:
- toda fatia tem altura multipla de 80 (grade de 40) -> a grade de fundo, o
  padrao de casca e a fase dos brilhos continuam atravessando os cortes;
- os gradients das laterais variam so em X -> invariantes na vertical;
- `align="top"` no HTML remove o gap de linha do <img>.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from xml.sax.saxutils import escape as esc

import theme as t

CXC = t.VIEW_W // 2
CX0 = t.RAIL_W + t.PAD
CX1 = t.VIEW_W - t.RAIL_W - t.PAD
CTOP = 0

BASE_CSS = """
@keyframes blink { 50% { opacity: 0 } }
@keyframes flicker { 0%,100% { opacity: .9 } 47% { opacity: .55 } 50% { opacity: 1 } 53% { opacity: .68 } }
@keyframes pulse { 0%,100% { opacity: .82 } 50% { opacity: 1 } }
.cursor { animation: blink 1.1s step-end infinite }
.mote { animation: flicker 4.2s ease-in-out infinite }
.glowpulse { animation: pulse 5.5s ease-in-out infinite }
"""


def defs() -> str:
    """Defs comuns a todas as fatias (ids locais a cada documento SVG)."""
    g = t.GRID_UNIT
    return f"""
<pattern id="grid" width="{g}" height="{g}" patternUnits="userSpaceOnUse">
  <path d="M {g} 0 L 0 0 0 {g}" fill="none" stroke="{t.GRID}" stroke-width="1"/>
</pattern>
<pattern id="bark" width="{t.RAIL_W}" height="40" patternUnits="userSpaceOnUse">
  <path d="M 0 20 H {t.RAIL_W}" stroke="{t.GOLD_DIM}" stroke-width="1" stroke-opacity="0.22"/>
  <path d="M {t.RAIL_W * 0.34:.0f} 0 V 40" stroke="{t.GOLD_DIM}" stroke-width="1" stroke-opacity="0.12"/>
  <path d="M {t.RAIL_W * 0.72:.0f} 0 V 40" stroke="{t.GOLD_DIM}" stroke-width="1" stroke-opacity="0.12"/>
</pattern>
<filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
  <feGaussianBlur stdDeviation="5" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="soft" x="-60%" y="-60%" width="220%" height="220%">
  <feGaussianBlur stdDeviation="3"/>
</filter>
<linearGradient id="railL" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{t.BG}"/>
  <stop offset="0.55" stop-color="{t.mix(t.BG, t.GOLD_DIM, 0.32)}"/>
  <stop offset="1" stop-color="{t.GOLD_DIM}"/>
</linearGradient>
<linearGradient id="railR" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{t.GOLD_DIM}"/>
  <stop offset="0.45" stop-color="{t.mix(t.BG, t.GOLD_DIM, 0.32)}"/>
  <stop offset="1" stop-color="{t.BG}"/>
</linearGradient>
<linearGradient id="treeGrad" x1="0" y1="1" x2="0" y2="0">
  <stop offset="0" stop-color="{t.GOLD_DIM}"/>
  <stop offset="1" stop-color="{t.GOLD_BRIGHT}"/>
</linearGradient>
<radialGradient id="halo">
  <stop offset="0" stop-color="{t.GRACE}" stop-opacity="0.20"/>
  <stop offset="1" stop-color="{t.GRACE}" stop-opacity="0"/>
</radialGradient>
<radialGradient id="mote">
  <stop offset="0" stop-color="{t.GRACE}"/>
  <stop offset="0.5" stop-color="{t.GOLD_BRIGHT}" stop-opacity="0.5"/>
  <stop offset="1" stop-color="{t.GOLD_BRIGHT}" stop-opacity="0"/>
</radialGradient>
"""


def svg(h: int, body: str, faces: str = "", css: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{t.VIEW_W}" height="{h}" '
        f'viewBox="0 0 {t.VIEW_W} {h}">'
        f"<style>{faces}{BASE_CSS}{css}</style>"
        f"<defs>{defs()}</defs>"
        f"{body}</svg>"
    )


def background(h: int) -> str:
    return (
        f'<rect width="{t.VIEW_W}" height="{h}" fill="{t.BG}"/>'
        f'<rect width="{t.VIEW_W}" height="{h}" fill="url(#grid)" opacity="0.55"/>'
        f'<ellipse cx="{CXC}" cy="{h / 2:.0f}" rx="{t.VIEW_W * 0.36:.0f}" ry="{h * 0.6:.0f}" '
        f'fill="url(#halo)" opacity="0.5"/>'
    )


def rails(h: int, motes: bool = True) -> str:
    """Laterais = tronco da Erdtree. Invariantes na vertical (emenda perfeita)."""
    L = t.RAIL_W
    R = t.VIEW_W - L
    out = [
        f'<rect x="0" y="0" width="{L}" height="{h}" fill="url(#railL)"/>',
        f'<rect x="{R}" y="0" width="{L}" height="{h}" fill="url(#railR)"/>',
        f'<rect x="0" y="0" width="{L}" height="{h}" fill="url(#bark)"/>',
        f'<rect x="{R}" y="0" width="{L}" height="{h}" fill="url(#bark)"/>',
    ]
    # brilho interno (borda viva) + fio nitido
    out.append(
        f'<rect x="{L - 8}" y="0" width="10" height="{h}" fill="{t.GOLD_BRIGHT}" '
        f'opacity="0.16" filter="url(#soft)"/>'
    )
    out.append(
        f'<rect x="{R - 2}" y="0" width="10" height="{h}" fill="{t.GOLD_BRIGHT}" '
        f'opacity="0.16" filter="url(#soft)"/>'
    )
    out.append(f'<line x1="{L}" y1="0" x2="{L}" y2="{h}" stroke="{t.GOLD}" stroke-width="1.4" opacity="0.8"/>')
    out.append(f'<line x1="{R}" y1="0" x2="{R}" y2="{h}" stroke="{t.GOLD}" stroke-width="1.4" opacity="0.8"/>')
    if motes:
        for y in range(0, h + 1, 80):
            for x in (L, R):
                out.append(
                    f'<circle class="mote" cx="{x}" cy="{y}" r="7" fill="url(#mote)"/>'
                )
    return "".join(out)


def top_bar() -> str:
    x0, x1 = t.RAIL_W, t.VIEW_W - t.RAIL_W
    bh = 44
    return f"""
<rect x="{x0}" y="0" width="{x1 - x0}" height="{bh}" fill="{t.mix(t.BG, t.GOLD_DIM, 0.16)}"/>
<line x1="{x0}" y1="{bh}" x2="{x1}" y2="{bh}" stroke="{t.GOLD}" stroke-width="2"/>
<line x1="{x0 + 90}" y1="{bh}" x2="{x1 - 90}" y2="{bh}" stroke="{t.GOLD_BRIGHT}" stroke-width="1" filter="url(#soft)"/>
<path d="M {CXC} {bh - 16} L {CXC + 10} {bh - 8} L {CXC} {bh} L {CXC - 10} {bh - 8} Z" fill="{t.GRACE}" filter="url(#glow)"/>
<path d="M {CXC} {bh - 15} L {CXC + 8} {bh - 8} L {CXC} {bh - 1} L {CXC - 8} {bh - 8} Z" fill="{t.GOLD_BRIGHT}"/>
"""


def divider(y: int, span: int = 360) -> str:
    x0, x1 = CXC - span, CXC + span
    return f"""
<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{t.GOLD_DIM}" stroke-width="1.4"/>
<line x1="{x0 + 60}" y1="{y}" x2="{x1 - 60}" y2="{y}" stroke="{t.GOLD}" stroke-width="1"/>
<path d="M {CXC} {y - 8} L {CXC + 8} {y} L {CXC} {y + 8} L {CXC - 8} {y} Z" fill="{t.GRACE}" filter="url(#glow)"/>
<path d="M {CXC} {y - 6} L {CXC + 6} {y} L {CXC} {y + 6} L {CXC - 6} {y} Z" fill="{t.GOLD_BRIGHT}"/>
"""


def erdtree(cx: int, top: int, base: int) -> str:
    mid = (top + base) / 2
    out = [
        f'<ellipse cx="{cx}" cy="{mid:.0f}" rx="130" ry="118" fill="url(#halo)"/>',
        '<g class="glowpulse">',
        '<g filter="url(#glow)">',
        f'<path d="M {cx - 9} {base} Q {cx - 4} {mid:.0f} {cx - 1.5} {top + 14} '
        f'L {cx + 1.5} {top + 14} Q {cx + 4} {mid:.0f} {cx + 9} {base} Z" fill="url(#treeGrad)"/>',
    ]
    branches = [(30, 54, -42, 5), (78, 66, -36, 4.5), (128, 60, -32, 5), (176, 72, -28, 4.5)]
    for yf, dx, dy, r in branches:
        y = top + yf
        for s in (1, -1):
            tx, ty = cx + s * dx, y + dy
            out.append(
                f'<path d="M {cx} {y} Q {cx + s * dx * 0.5:.0f} {y + dy * 0.35:.0f} {tx} {ty}" '
                f'fill="none" stroke="{t.GOLD}" stroke-width="2.4" stroke-linecap="round"/>'
            )
            out.append(f'<circle cx="{tx}" cy="{ty}" r="{r}" fill="{t.GRACE}"/>')
    # coroa
    for dx, dy, r in [(-26, 8, 3.4), (0, 2, 4), (26, 8, 3.4), (-12, -6, 3), (12, -6, 3)]:
        out.append(f'<circle cx="{cx + dx}" cy="{top + 12 + dy}" r="{r}" fill="{t.GRACE}"/>')
    out.append("</g></g>")
    return "".join(out)


def txt(x, y, s, *, family=t.FONT_MONO, weight=400, size=16, fill=t.TEXT, anchor="start", spacing=0, cls="", opacity=1.0):
    klass = f' class="{cls}"' if cls else ""
    return (
        f'<text x="{x}" y="{y}" font-family="\'{family}\', monospace" font-weight="{weight}" '
        f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}" '
        f'opacity="{opacity}"{klass}>{esc(s)}</text>'
    )


def header(name: str) -> str:
    h = t.HEADER_H
    title = name.upper()
    sub = "TARNISHED // FULL STACK DEVELOPER"
    tag = "// SAAS | APIS | INTEGRACOES | AUTOMACAO"
    prompt = "$ whoami"
    faces = t.embedded_faces(
        (t.FONT_TITLE, 700, title),
        (t.FONT_MONO, 400, sub + tag + prompt),
    )
    body = [background(h), top_bar(), erdtree(CXC, 70, 250)]
    # titulo (brilho atras + texto nítido)
    body.append(txt(CXC, 336, title, family=t.FONT_TITLE, weight=700, size=76, fill=t.GOLD, anchor="middle", spacing=8, opacity=0.5))
    body.append(txt(CXC, 336, title, family=t.FONT_TITLE, weight=700, size=76, fill=t.GOLD_BRIGHT, anchor="middle", spacing=8, cls="glowpulse"))
    body.append(divider(392))
    body.append(txt(CXC, 440, sub, family=t.FONT_MONO, size=17, fill=t.TEXT, anchor="middle", spacing=4))
    body.append(txt(CXC, 468, tag, family=t.FONT_MONO, size=13, fill=t.TEXT_DIM, anchor="middle", spacing=2))
    # linha de terminal
    ty = 524
    prompt_x = CXC - 96
    body.append(txt(prompt_x, ty, prompt, family=t.FONT_MONO, weight=700, size=18, fill=t.STAMINA_GREEN))
    body.append(f'<rect class="cursor" x="{prompt_x + 118}" y="{ty - 16}" width="11" height="20" fill="{t.GRACE}"/>')
    body.append(rails(h))
    return svg(h, "".join(body), faces=faces)


def body_slice() -> str:
    h = t.FILLER_H
    parts = [background(h)]
    # névoa diagonal sutil
    parts.append(
        f'<path d="M {CX0} {h * 0.7:.0f} Q {CXC} {h * 0.4:.0f} {CX1} {h * 0.75:.0f}" '
        f'fill="none" stroke="{t.MIST}" stroke-width="2" opacity="0.5"/>'
    )
    parts.append(
        f'<path d="M {CX0} {h * 0.95:.0f} Q {CXC} {h * 0.65:.0f} {CX1} {h}" '
        f'fill="none" stroke="{t.MIST}" stroke-width="1.4" opacity="0.35"/>'
    )
    parts.append(rails(h))
    return svg(h, "".join(parts))


def footer() -> str:
    h = t.FOOTER_H
    x0, x1 = t.RAIL_W, t.VIEW_W - t.RAIL_W
    bh = 44
    parts = [background(h)]
    # raizes irradiando da base
    base = h - bh
    parts.append(f'<g opacity="0.75">')
    for s in (1, -1):
        for k, dx in enumerate((70, 130, 190, 250)):
            cxp = CXC + s * dx
            parts.append(
                f'<path d="M {CXC} {base} Q {CXC + s * dx * 0.4:.0f} {base - 40 - k * 6} {cxp} {base - 8}" '
                f'fill="none" stroke="{t.GOLD_DIM}" stroke-width="{2.4 - k * 0.3:.1f}" stroke-linecap="round"/>'
            )
            parts.append(f'<circle cx="{cxp}" cy="{base - 8}" r="{3.4 - k * 0.4:.1f}" fill="{t.GRACE}" filter="url(#glow)"/>')
    parts.append('</g>')
    # sigilo de graça central
    parts.append(f'<circle cx="{CXC}" cy="{base - 20}" r="16" fill="none" stroke="{t.GRACE}" stroke-width="1.6" filter="url(#glow)"/>')
    parts.append(f'<circle cx="{CXC}" cy="{base - 20}" r="7" fill="{t.GRACE}" filter="url(#glow)"/>')
    # barra inferior
    parts.append(f'<rect x="{x0}" y="{h - bh}" width="{x1 - x0}" height="{bh}" fill="{t.mix(t.BG, t.GOLD_DIM, 0.16)}"/>')
    parts.append(f'<line x1="{x0}" y1="{h - bh}" x2="{x1}" y2="{h - bh}" stroke="{t.GOLD}" stroke-width="2"/>')
    parts.append(f'<line x1="{x0 + 90}" y1="{h - bh}" x2="{x1 - 90}" y2="{h - bh}" stroke="{t.GOLD_BRIGHT}" stroke-width="1" filter="url(#soft)"/>')
    parts.append(f'<path d="M {CXC} {h - bh + 28} L {CXC + 9} {h - bh + 20} L {CXC} {h - bh + 12} L {CXC - 9} {h - bh + 20} Z" fill="{t.GRACE}" filter="url(#glow)"/>')
    parts.append(rails(h))
    return svg(h, "".join(parts))


def main() -> int:
    stats = json.loads((t.DATA / "stats.json").read_text())
    name = stats.get("name") or stats.get("login", "TARNISHED")

    slices = {
        "header.svg": header(name),
        "body.svg": body_slice(),
        "footer.svg": footer(),
    }
    for fname, content in slices.items():
        (t.ASSETS / fname).write_text(content, encoding="utf-8")
        print(f"  {fname}: {len(content):,} bytes")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "slices": ["header.svg", "body.svg", "footer.svg"],
    }
    (t.ASSETS / "_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"ok: {len(slices)} fatias renderizadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
