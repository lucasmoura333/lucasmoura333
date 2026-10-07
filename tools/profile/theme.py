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

# fontes OFL baixadas em fonts/ (subset acontece no render, por SVG)
FONT_FILES: dict[tuple[str, int], Path] = {
    (FONT_TITLE, 400): FONTS / "cinzel-latin-400-normal.woff2",
    (FONT_TITLE, 600): FONTS / "cinzel-latin-600-normal.woff2",
    (FONT_TITLE, 700): FONTS / "cinzel-latin-700-normal.woff2",
    (FONT_MONO, 400): FONTS / "jetbrains-mono-latin-400-normal.woff2",
    (FONT_MONO, 700): FONTS / "jetbrains-mono-latin-700-normal.woff2",
    (FONT_MONO, 800): FONTS / "jetbrains-mono-latin-800-normal.woff2",
}


def subset_font_b64(path: Path, text: str) -> str:
    """Subseta a fonte para os glifos de `text` e devolve woff2 em base64."""
    import base64
    from io import BytesIO

    from fontTools import subset

    opts = subset.Options()
    opts.flavor = "woff2"
    opts.desubroutinize = True
    opts.notdef_outline = True
    opts.layout_features = ["kern", "liga"]
    font = subset.load_font(str(path), opts)
    sub = subset.Subsetter(options=opts)
    sub.populate(text="".join(dict.fromkeys(text)) + " ")
    sub.subset(font)
    buf = BytesIO()
    font.save(buf)
    font.close()
    return base64.b64encode(buf.getvalue()).decode("ascii")


def font_face(name: str, weight: int = 400, text: str | None = None) -> str:
    """Bloco @font-face com a fonte embutida em base64 (SVG modo imagem nao
    carrega recurso externo). Se `text` for dado, subseta para esses glifos."""
    import base64

    path = FONT_FILES[(name, weight)]
    data = subset_font_b64(path, text) if text is not None else base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f"@font-face{{font-family:'{name}';font-style:normal;font-weight:{weight};"
        f"src:url(data:font/woff2;base64,{data}) format('woff2');}}"
    )


def embedded_faces(*specs: tuple[str, int, str]) -> str:
    """Concatena @font-face de (familia, peso, texto-usado)."""
    return "".join(font_face(name, w, text) for name, w, text in specs)


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
