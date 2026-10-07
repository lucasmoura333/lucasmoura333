#!/usr/bin/env python3
"""Elden Console - atualiza o README.

Reescreve apenas o bloco entre <!-- elden:start --> e <!-- elden:end --> com a
pilha de fatias do assets/_manifest.json. O resto do README fica intacto.
HTML comments sao invisiveis no GitHub, entao os marcadores nao custam nada.
"""

from __future__ import annotations

import json
import re
import sys

import theme as t

README = t.ROOT / "README.md"
MANIFEST = t.ASSETS / "_manifest.json"
BLOCK = re.compile(r"<!-- elden:start -->.*?<!-- elden:end -->", re.S)


def writing_block(slices: list[str]) -> str:
    imgs = "\n".join(
        f'<img src="./assets/{name}" width="100%" align="top">' for name in slices
    )
    return f'<!-- elden:start -->\n<p align="center">\n{imgs}\n</p>\n<!-- elden:end -->'


def main() -> int:
    slices = json.loads(MANIFEST.read_text())["slices"]
    src = README.read_text(encoding="utf-8")
    new, n = BLOCK.subn(lambda _: writing_block(slices), src)
    if n != 1:
        sys.exit("error: README precisa de exatamente um bloco <!-- elden:start/end -->")
    if new == src:
        print("ok: README ja atualizado")
        return 0
    README.write_text(new, encoding="utf-8")
    print(f"ok: README atualizado ({len(slices)} fatias)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
