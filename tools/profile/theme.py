"""Elden Console - fonte unica de verdade visual.

Paleta, grade e fontes compartilhadas por fetch/render. Tudo arte original
inspirada no clima de Elden Ring - nenhum asset oficial e usado.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
DATA = Path(__file__).resolve().parent / "data"
FONTS = Path(__file__).resolve().parent / "fonts"

# --- Paleta ---------------------------------------------------------------
BG = "#0a0a0c"
BG_PANEL = "#121216"
GRID = "#1c1c24"

GOLD = "#c8a15a"
GOLD_BRIGHT = "#f2d06b"
GOLD_DIM = "#7a6234"
GRACE = "#f2d06b"

BLOOD = "#7a1e1e"
BLOOD_BRIGHT = "#b3261e"

FP_BLUE = "#3a6ea5"
STAMINA_GREEN = "#4e7a3a"

MIST = "#3a3a45"
TEXT = "#d8d2c4"
TEXT_DIM = "#8a8578"

# --- Geometria ------------------------------------------------------------
# Toda fatia tem altura multipla de GRID_UNIT para a grade de fundo
# continuar atravessando as emendas sem saltos.
GRID_UNIT = 40
VIEW_W = 1200
RAIL_W = 56
PAD = 40

# alturas nomeadas (multiplos de GRID_UNIT)
HEADER_H = 14 * GRID_UNIT
HUD_H = 8 * GRID_UNIT
FILLER_H = 4 * GRID_UNIT
FOOTER_H = 6 * GRID_UNIT

# --- Fontes ---------------------------------------------------------------
FONT_TITLE = "Cinzel"
FONT_MONO = "JetBrains Mono"


def font_face(name: str, path: Path, weight: int = 400) -> str:
    """Bloco @font-face com a fonte embutida em base64 (SVG modo imagem nao
    carrega recurso externo)."""
    import base64

    data = base64.b64encode(path.read_bytes()).decode("ascii")
    fmt = "woff2" if path.suffix == ".woff2" else "truetype"
    mime = "font/woff2" if path.suffix == ".woff2" else "font/ttf"
    return (
        f"@font-face{{font-family:'{name}';font-style:normal;font-weight:{weight};"
        f"src:url(data:{mime};base64,{data}) format('{fmt}');}}"
    )


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def mix(a: str, b: str, t: float) -> str:
    """Interpola linearmente duas cores hex (t em 0..1)."""
    ra, ga, ba = hex_to_rgb(a)
    rb, gb, bb = hex_to_rgb(b)
    r = round(ra + (rb - ra) * t)
    g = round(ga + (gb - ga) * t)
    bl = round(ba + (bb - ba) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")
