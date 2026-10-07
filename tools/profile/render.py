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
import math
import random
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
<linearGradient id="fadeTop" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{t.BG}" stop-opacity="0.92"/>
  <stop offset="1" stop-color="{t.BG}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="fadeBottom" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{t.BG}" stop-opacity="0"/>
  <stop offset="1" stop-color="{t.BG}" stop-opacity="1"/>
</linearGradient>
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


def txt(x, y, s, *, family=t.FONT_MONO, weight=400, size=16, fill=t.TEXT, anchor="start", spacing=0, cls="", opacity=1.0, filter=None, style=None):
    klass = f' class="{cls}"' if cls else ""
    filt = f' filter="{filter}"' if filter else ""
    sty = f' style="{style}"' if style else ""
    return (
        f'<text x="{x}" y="{y}" font-family="\'{family}\', monospace" font-weight="{weight}" '
        f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}" '
        f'opacity="{opacity}"{klass}{filt}{sty}>{esc(s)}</text>'
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


def stat_bar(x, y, w, frac, color, label, value, sub) -> str:
    h = 14
    frac = max(0.02, min(1.0, frac))
    out = [
        txt(x, y - 10, label, family=t.FONT_TITLE, weight=600, size=15, fill=t.GOLD, spacing=2),
        txt(x + w, y - 10, value, family=t.FONT_MONO, weight=700, size=15, fill=t.TEXT, anchor="end"),
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{t.BG_PANEL}" stroke="{t.GOLD_DIM}" stroke-width="1"/>',
        f'<rect x="{x}" y="{y}" width="{w * frac:.0f}" height="{h}" fill="{color}" opacity="0.85" filter="url(#soft)"/>',
        f'<rect x="{x}" y="{y}" width="{w * frac:.0f}" height="{h}" fill="{color}"/>',
    ]
    step = w / 10
    for i in range(1, 10):
        out.append(
            f'<line x1="{x + step * i:.0f}" y1="{y}" x2="{x + step * i:.0f}" y2="{y + h}" '
            f'stroke="{t.BG}" stroke-width="1" opacity="0.45"/>'
        )
    out.append(f'<path d="M {x - 12} {y + h / 2} L {x - 6} {y} L {x} {y + h / 2} L {x - 6} {y + h} Z" fill="{t.GRACE}"/>')
    out.append(txt(x, y + h + 18, sub, family=t.FONT_MONO, size=11, fill=t.TEXT_DIM))
    return "".join(out)


def compass(cx, cy, r, progress) -> str:
    out = [
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t.BG_PANEL}" stroke="{t.GOLD_DIM}" stroke-width="1.5"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r - 7}" fill="none" stroke="{t.GOLD_DIM}" stroke-width="0.7" opacity="0.6"/>',
    ]
    for letter, ax, ay in [("N", 0, -1), ("E", 1, 0), ("S", 0, 1), ("W", -1, 0)]:
        lx = cx + ax * (r - 17)
        ly = cy + ay * (r - 17) + 5
        out.append(txt(lx, ly, letter, family=t.FONT_TITLE, weight=600, size=13, fill=t.GOLD, anchor="middle"))
    angle = -90 + max(0.0, min(1.0, progress)) * 360
    out.append(
        f'<g transform="rotate({angle:.1f} {cx} {cy})">'
        f'<path d="M {cx} {cy - r + 9} L {cx - 5} {cy} L {cx + 5} {cy} Z" fill="{t.GRACE}" filter="url(#glow)"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy + r - 9}" stroke="{t.GOLD_DIM}" stroke-width="2"/></g>'
    )
    out.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{t.GOLD_BRIGHT}"/>')
    return "".join(out)


def runes_block(x, y, count) -> str:
    gx = x - 200
    return "".join([
        f'<circle cx="{gx}" cy="{y}" r="18" fill="none" stroke="{t.GRACE}" stroke-width="1.8" filter="url(#glow)"/>',
        f'<line x1="{gx}" y1="{y - 26}" x2="{gx}" y2="{y + 26}" stroke="{t.GOLD_DIM}" stroke-width="1.4"/>',
        f'<line x1="{gx - 13}" y1="{y - 20}" x2="{gx + 13}" y2="{y + 20}" stroke="{t.GOLD_DIM}" stroke-width="1.4"/>',
        f'<line x1="{gx + 13}" y1="{y - 20}" x2="{gx - 13}" y2="{y + 20}" stroke="{t.GOLD_DIM}" stroke-width="1.4"/>',
        f'<circle cx="{gx}" cy="{y}" r="3" fill="{t.GRACE}"/>',
        txt(x, y + 4, t.fmt_int(count), family=t.FONT_TITLE, weight=600, size=40, fill=t.GOLD_BRIGHT, anchor="end"),
        txt(x, y + 30, "RUNES", family=t.FONT_MONO, size=12, fill=t.TEXT_DIM, anchor="end", spacing=3),
    ])


def _iso(px_col: int, px_row: int, offx: float, offy: float) -> tuple[float, float]:
    """Projeta (coluna, linha) da grade no plano isometrico 2:1."""
    x = (px_col - px_row) * t.ISO_TW / 2 + offx
    y = (px_col + px_row) * t.ISO_TH / 2 + offy
    return x, y


def _tile_polys(px: float, py: float, elev: float, inset: float):
    """Vertices (topo, lado esq, lado dir) de um tile com relevo `elev`."""
    hw = t.ISO_TW / 2 * (1 - inset)
    hh = t.ISO_TH / 2 * (1 - inset)
    rt = t.ISO_TH / 2 * (1 - inset)
    cx = px
    top = (cx, py - elev)
    right = (cx + hw, py + rt - elev)
    bottom = (cx, py + 2 * hh - elev)
    left = (cx - hw, py + rt - elev)
    top_face = [top, right, bottom, left]
    left_base = (cx - hw, py + rt)
    bottom_base = (cx, py + 2 * hh)
    right_base = (cx + hw, py + rt)
    left_face = [left, bottom, bottom_base, left_base]
    right_face = [bottom, right, right_base, bottom_base]
    return top_face, left_face, right_face


def _poly(points, fill, *, stroke="none", sw=0, opacity=1.0, dash=None) -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
        f'opacity="{opacity}"{dash_attr}/>'
    )


def _grace(cx: float, cy: float, heat: float) -> str:
    """Site of grace: facho vertical dourado sobre a face de um tile revelado."""
    beam = 5 + 10 * heat
    r = 1.6 + 2.4 * heat
    top = cy - beam
    return "".join([
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{top:.1f}" '
        f'stroke="{t.GRACE}" stroke-width="1.2" opacity="{0.35 + 0.45 * heat:.2f}"/>',
        f'<circle cx="{cx:.1f}" cy="{top:.1f}" r="{r:.1f}" fill="{t.GRACE}" opacity="{0.55 + 0.4 * heat:.2f}" filter="url(#soft)"/>',
        f'<circle cx="{cx:.1f}" cy="{top:.1f}" r="{r * 0.5:.1f}" fill="{t.GOLD_BRIGHT}"/>',
    ])


def map_slice(calendar: dict) -> str:
    """M3 - Mapa Lands Between: grade isometrica com fog-of-war e gracas."""
    h = t.MAP_H
    weeks = calendar.get("grid") or []
    if not weeks:
        return svg(h, background(h) + rails(h))
    cols, rows = len(weeks), 7
    cells = [(c, r, weeks[c][r]) for c in range(cols) for r in range(rows)]
    maxc = max((d.get("count", 0) for *_, d in cells), default=1) or 1

    # centralizacao da grade iso na moldura
    min_x = _iso(0, rows - 1, 0, 0)[0]
    max_x = _iso(cols - 1, 0, 0, 0)[0]
    offx = CXC - (min_x + max_x) / 2
    field_h = (cols - 1 + rows - 1) * t.ISO_TH / 2 + t.ISO_TH
    top_pad, bot_pad = 122, 34
    offy = top_pad + max(0.0, (h - top_pad - bot_pad - field_h) / 2)

    past = [d for *_, d in cells if not d.get("future")]
    revealed = sum(1 for d in past if d.get("count", 0) > 0)
    total_days = len(past)
    recent = sum(d.get("count", 0) for *_, d in cells[-2 * 7:] if not d.get("future"))
    pulse = max(2.6, min(6.0, 6.0 - recent / 40.0))

    fog_top = t.mix(t.BG, t.MIST, 0.24)
    parts = [background(h)]
    # halo da Erdtree atras do campo, pulsando com a atividade recente
    fy = offy + field_h / 2
    parts.append(
        f'<ellipse class="glowpulse" style="animation-duration:{pulse:.1f}s" '
        f'cx="{CXC}" cy="{fy:.0f}" rx="330" ry="150" fill="url(#halo)" opacity="0.55"/>'
    )

    rng = random.Random(t.MAP_SEED)
    n_decor = 130
    decor: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for _ in range(n_decor):
        c, r, d = cells[rng.randrange(len(cells))]
        if d.get("future") or d.get("count", 0) == 0:
            continue
        fx = rng.uniform(-0.32, 0.32)
        fy2 = rng.uniform(0.18, 0.82)
        decor.setdefault((c, r), []).append((fx, fy2))

    # painter's algorithm: fundo (col+row pequeno) primeiro
    for c, r, d in sorted(cells, key=lambda t3: (t3[0] + t3[1], t3[0])):
        px, py = _iso(c, r, offx, offy)
        future = bool(d.get("future"))
        count = d.get("count", 0)
        heat = 0.0 if future else count / maxc
        elev = 0.0 if future else round(t.ISO_ELEV_MAX * heat ** 0.62)
        if future:
            top_col = t.mix(t.BG, t.MIST, 0.07)
            frame, b1, b2 = _tile_polys(px, py, 0, t.ISO_INSET)
            parts.append(_poly(frame, top_col, stroke=t.MIST, sw=0.6, opacity=0.5, dash="3 4"))
            continue
        if count == 0:
            top_col = fog_top
        else:
            ramp = t.mix(t.mix(t.BG, t.STAMINA_GREEN, 0.5), t.GOLD_BRIGHT, min(1.0, 0.22 + 0.85 * math.sqrt(heat)))
            top_col = ramp
        top_face, left_face, right_face = _tile_polys(px, py, elev, t.ISO_INSET)
        edge = t.shade(top_col, 0.5)
        if elev > 0:
            parts.append(_poly(left_face, t.shade(top_col, 0.42), stroke=edge, sw=0.6))
            parts.append(_poly(right_face, t.shade(top_col, 0.62), stroke=edge, sw=0.6))
        parts.append(_poly(top_face, top_col, stroke=t.MIST if count == 0 else edge, sw=0.7, opacity=0.96, dash="3 3" if count == 0 else None))

        if count > 0:
            cx = px
            cy = py + t.ISO_TH / 2 - elev - t.ISO_TH * 0.10
            parts.append(_grace(cx, cy, min(1.0, heat * 1.6)))
            for fx, fy2 in decor.get((c, r), []):
                dx = cx + fx * t.ISO_TW * 0.5
                dy = cy + (fy2 - 0.5) * t.ISO_TH * 0.6
                parts.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="0.9" fill="{t.GOLD_BRIGHT}" opacity="0.7"/>')

    # legenda / cabecalho do mapa
    parts.append(txt(t.RAIL_W + 28, 38, "THE LANDS BETWEEN", family=t.FONT_TITLE, weight=600, size=24, fill=t.GOLD_BRIGHT, spacing=3))
    parts.append(txt(t.RAIL_W + 30, 58, "// 53 WEEKS CHARTED - ONE TILE PER DAY", family=t.FONT_MONO, size=12, fill=t.TEXT_DIM, spacing=1))
    parts.append(txt(t.VIEW_W - t.RAIL_W - 28, 34, f"{revealed} / {total_days}", family=t.FONT_MONO, weight=700, size=22, fill=t.GOLD_BRIGHT, anchor="end"))
    parts.append(txt(t.VIEW_W - t.RAIL_W - 28, 54, "DAYS REVEALED", family=t.FONT_MONO, size=11, fill=t.TEXT_DIM, anchor="end", spacing=2))
    parts.append(f'<line x1="{t.RAIL_W + 24}" y1="72" x2="{t.VIEW_W - t.RAIL_W - 24}" y2="72" stroke="{t.GOLD_DIM}" stroke-width="1"/>')

    legend = [
        ("revealed", "REVEALED"),
        ("fog", "FOG OF WAR"),
        ("grace", "SITE OF GRACE"),
    ]
    ly = 98
    lx = CXC - sum(18 + len(lbl) * 6.8 + 34 for _, lbl in legend) / 2
    for kind, label in legend:
        if kind == "grace":
            parts.append(f'<circle cx="{lx:.1f}" cy="{ly}" r="4" fill="{t.GRACE}" filter="url(#glow)"/>')
        elif kind == "fog":
            parts.append(_poly([(lx, ly - 8), (lx + 8, ly), (lx, ly + 8), (lx - 8, ly)], fog_top, stroke=t.MIST, sw=0.8, dash="3 3"))
        else:
            parts.append(_poly(
                [(lx, ly - 8), (lx + 8, ly), (lx, ly + 8), (lx - 8, ly)],
                t.mix(t.mix(t.BG, t.STAMINA_GREEN, 0.5), t.GOLD_BRIGHT, 0.72),
                stroke=t.GOLD_DIM, sw=0.8,
            ))
        parts.append(txt(lx + 16, ly + 4, label, family=t.FONT_MONO, size=11, fill=t.TEXT_DIM, spacing=1))
        lx += 18 + len(label) * 6.8 + 34
    parts.append(rails(h))

    faces = t.embedded_faces(
        (t.FONT_TITLE, 600, "THE LANDS BETWEEN"),
        (t.FONT_MONO, 400, "WEEKS CHARTED ONE TILE PER DAY DAYS REVEALED REVEALED FOG OF WAR SITE OF GRACE /"),
        (t.FONT_MONO, 700, str(revealed) + str(total_days)),
    )
    return svg(h, "".join(parts), faces=faces)


def hud_slice(stats: dict) -> str:
    h = t.HUD_H
    year = datetime.now(timezone.utc).year
    prs = stats.get("pull_requests", 0)
    year_contrib = stats.get("contributions_year", 0)
    all_time = stats.get("contributions_all_time", 0)
    cur = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0) or 1

    faces = t.embedded_faces(
        (t.FONT_TITLE, 600, "HP FP STAMINA N E S W RUNES"),
        (t.FONT_MONO, 700, t.fmt_int(all_time) + str(prs) + t.fmt_int(year_contrib)),
        (t.FONT_MONO, 400, f"{cur}d streak record {longest}d contributions pull requests {year}"),
    )
    parts = [background(h)]
    bx, bw = 120, 300
    parts.append(stat_bar(bx, 78, bw, year_contrib / 1000, t.BLOOD_BRIGHT, "HP", t.fmt_int(year_contrib), f"contributions {year}"))
    parts.append(stat_bar(bx, 150, bw, prs / 250, t.FP_BLUE, "FP", str(prs), "pull requests"))
    parts.append(stat_bar(bx, 222, bw, cur / longest, t.STAMINA_GREEN, "STAMINA", f"{cur}d", f"streak (record {longest}d)"))
    doy = datetime.now(timezone.utc).timetuple().tm_yday
    parts.append(compass(600, 150, 52, doy / 365))
    parts.append(runes_block(1096, 150, all_time))
    parts.append(rails(h))
    return svg(h, "".join(parts), faces=faces)


def banner() -> str:
    """M4 - tela de titulo: Vale Gotico (fundo) + cavaleiro (frente, parallax)."""
    h = t.BANNER_H
    year = datetime.now(timezone.utc).year
    parts = [
        background(h),
        f'<image href="{t.image_data_uri("banner_valley.png")}" x="0" y="0" '
        f'width="{t.VIEW_W}" height="{h}" preserveAspectRatio="none"/>',
        f'<rect width="{t.VIEW_W}" height="{h}" fill="{t.BG}" opacity="0.12"/>',
        f'<image href="{t.image_data_uri("banner_knight.png")}" x="0" y="0" '
        f'width="{t.VIEW_W}" height="{h}" preserveAspectRatio="none"/>',
        f'<rect x="0" y="{h - 200}" width="{t.VIEW_W}" height="200" fill="url(#fadeBottom)"/>',
        f'<rect x="0" y="{h - 6}" width="{t.VIEW_W}" height="6" fill="{t.BG}"/>',
        f'<rect width="{t.VIEW_W}" height="96" fill="url(#fadeTop)"/>',
        f'<rect width="{t.VIEW_W}" height="6" fill="{t.BG}"/>',
    ]
    y_prompt = h - 78
    parts.append(txt(t.RAIL_W + 22, 34, "// ELDEN CONSOLE", family=t.FONT_MONO, size=12, fill=t.TEXT_DIM, spacing=1))
    parts.append(txt(t.VIEW_W - t.RAIL_W - 22, 34, f"LANDS BETWEEN // {year}", family=t.FONT_MONO, size=12, fill=t.TEXT_DIM, anchor="end", spacing=1))
    parts.append(txt(CXC, y_prompt, "PRESS ANY BUTTON", family=t.FONT_TITLE, weight=600, size=24, fill=t.GOLD_BRIGHT, anchor="middle", spacing=7, cls="blink-slow"))
    parts.append(txt(CXC, y_prompt + 30, "// NEW GAME     CONTINUE     SETTINGS", family=t.FONT_MONO, size=12, fill=t.TEXT_DIM, anchor="middle", spacing=2))
    parts.append(rails(h))
    faces = t.embedded_faces(
        (t.FONT_TITLE, 600, "PRESS ANY BUTTON"),
        (t.FONT_MONO, 400, f"// ELDEN CONSOLE LANDS BETWEEN {year} // NEW GAME CONTINUE SETTINGS"),
    )
    css = "@keyframes blinkslow{0%,100%{opacity:.4}50%{opacity:1}}.blink-slow{animation:blinkslow 2.4s ease-in-out infinite}"
    return svg(h, "".join(parts), faces=faces, css=css)


def trial() -> str:
    """M4 - tela de morte/vitoria: YOU DIED ~ ENEMY FELLED (crossfade)."""
    h = t.TRIAL_H
    cy = h / 2 + 10
    bar = 30
    parts = [background(h)]
    parts.append(f'<image href="{t.image_data_uri("trial_forest.png")}" x="0" y="0" '
                 f'width="{t.VIEW_W}" height="{h}" preserveAspectRatio="none" opacity="0.55"/>')
    parts.append(f'<rect width="{t.VIEW_W}" height="{h}" fill="{t.BG}" opacity="0.5"/>')
    parts.append(f'<rect width="{t.VIEW_W}" height="{bar}" fill="{t.BG}" opacity="0.85"/>')
    parts.append(f'<rect x="0" y="{h - bar}" width="{t.VIEW_W}" height="{bar}" fill="{t.BG}" opacity="0.85"/>')
    for cls, label, col in (("trialA", "YOU DIED", t.BLOOD_BRIGHT), ("trialB", "ENEMY FELLED", t.GOLD_BRIGHT)):
        parts.append(
            f'<g class="{cls}">'
            + txt(CXC, cy, label, family=t.FONT_TITLE, weight=700, size=54, fill=col, anchor="middle", spacing=12, filter="url(#glow)", opacity=0.7)
            + txt(CXC, cy, label, family=t.FONT_TITLE, weight=700, size=54, fill=col, anchor="middle", spacing=12)
            + "</g>"
        )
    parts.append(txt(CXC, h - 9, "// DEATH IS NOT THE END", family=t.FONT_MONO, size=11, fill=t.TEXT_DIM, anchor="middle", spacing=2))
    parts.append(rails(h))
    faces = t.embedded_faces(
        (t.FONT_TITLE, 700, "YOU DIED ENEMY FELLED"),
        (t.FONT_MONO, 400, "// DEATH IS NOT THE END"),
    )
    css = ("@keyframes trialA{0%,38%{opacity:1}48%,100%{opacity:0}}"
           "@keyframes trialB{0%,48%{opacity:0}58%,90%{opacity:1}100%{opacity:0}}"
           ".trialA{animation:trialA 9s ease-in-out infinite}"
           ".trialB{animation:trialB 9s ease-in-out infinite}")
    return svg(h, "".join(parts), faces=faces, css=css)


def main() -> int:
    stats = json.loads((t.DATA / "stats.json").read_text())
    calendar = json.loads((t.DATA / "calendar.json").read_text())
    name = stats.get("name") or stats.get("login", "TARNISHED")

    slices = {
        "banner.svg": banner(),
        "header.svg": header(name),
        "hud.svg": hud_slice(stats),
        "map.svg": map_slice(calendar),
        "body.svg": body_slice(),
        "trial.svg": trial(),
        "footer.svg": footer(),
    }
    for fname, content in slices.items():
        (t.ASSETS / fname).write_text(content, encoding="utf-8")
        print(f"  {fname}: {len(content):,} bytes")

    manifest = {
        "slices": ["banner.svg", "header.svg", "hud.svg", "map.svg", "body.svg", "trial.svg", "footer.svg"],
    }
    (t.ASSETS / "_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"ok: {len(slices)} fatias renderizadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
