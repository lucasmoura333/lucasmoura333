#!/usr/bin/env python3
"""Elden Console - preparo dos assets raster (M4).

Le as artes-fonte (fora do repo, em `SRC_DIR`), reduz a paleta e grava PNGs
pequenos em `img/`. O `render.py` embute esses PNGs em base64 nos SVGs.

Nenhum asset oficial e usado: as artes sao originais/tematicas.

Uso:
    python tools/profile/prep_assets.py [SRC_DIR]   # padrao: /mnt/d/hub
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
IMG = HERE / "img"
SRC_DEFAULT = Path("/mnt/d/hub")

VALLEY = "*Sobre o Vale*"
KNIGHT = "Cavaleiro*Penhasco*"
FOREST = "Floresta*Pixel Art*"


def _find(src_dir: Path, pattern: str) -> Path:
    hits = sorted(src_dir.glob(pattern))
    if not hits:
        raise FileNotFoundError(f"nenhum arquivo casa com {pattern!r} em {src_dir}")
    return hits[0]


def _quantize(img: Image.Image, colors: int) -> Image.Image:
    method = Image.FASTOCTREE if img.mode in ("RGBA", "LA") else Image.MEDIANCUT
    return img.quantize(colors=colors, method=method, dither=Image.Dither.NONE)


def pixelate(src: Image.Image, out_w: int, out_h: int, step_w: int, colors: int) -> Image.Image:
    """Reduz a `step_w` px, quantiza e amplia de volta com NEAREST (pixel-art)."""
    step_h = max(1, round(step_w * out_h / out_w))
    small = src.resize((step_w, step_h), Image.LANCZOS)
    small = _quantize(small, colors)
    return small.resize((out_w, out_h), Image.NEAREST)


def primary(src: Image.Image, out_w: int, out_h: int, colors: int) -> Image.Image:
    """Reamostra direto no tamanho final e quantiza (mantem alpha se houver)."""
    rgba = src.convert("RGBA")
    resized = rgba.resize((out_w, out_h), Image.LANCZOS)
    return _quantize(resized, colors)


def key_light_alpha(src: Image.Image, blur: int = 5, threshold: int = 150, gain: float = 3.0) -> Image.Image:
    """Transparencia = quao mais escuro o pixel e que um limiar, sobre a
    luminancia suavizada.

    Robusto a fundos claros texturizados (ex.: xadrez de transparencia
    "assado" nos pixels): o blur uniformiza o padrao antes do limiar,
    preservando as silhuetas escuras.
    """
    rgb = src.convert("RGB")
    lum = rgb.convert("L").filter(ImageFilter.GaussianBlur(blur))
    alpha = lum.point(lambda v: max(0, min(255, int((threshold - v) * gain))))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def save(img: Image.Image, name: str, *, colors: int | None = None) -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    if colors is not None:
        img = _quantize(img, colors)
    path = IMG / name
    img.save(path, "PNG", optimize=True)
    print(f"  {name}: {path.stat().st_size:,} bytes  ({img.size[0]}x{img.size[1]}, {img.mode})")


def main(argv: list[str]) -> int:
    src_dir = Path(argv[1]) if len(argv) > 1 else SRC_DEFAULT
    print(f"src: {src_dir}")

    valley = Image.open(_find(src_dir, VALLEY))
    save(pixelate(valley, 1200, 480, step_w=360, colors=24), "banner_valley.png")

    knight = Image.open(_find(src_dir, KNIGHT))
    save(primary(knight, 1200, 480, colors=48), "banner_knight.png")

    forest = Image.open(_find(src_dir, FOREST))
    keyed = key_light_alpha(forest).resize((1200, 480), Image.LANCZOS)
    band = keyed.crop((0, 140, 1200, 380))
    save(band, "trial_forest.png", colors=32)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
