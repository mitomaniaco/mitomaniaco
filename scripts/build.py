#!/usr/bin/env python3
"""Renders assets/profile.svg: ASCII name, a rule, and four lines of facts.

Everything here is a fact about the account. No positioning copy, no project
grid, no live numbers - so nothing needs a scheduled workflow.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
PORTRAIT = (ASSETS / "portrait.txt").read_text(encoding="utf-8").rstrip("\n")

MONO = "ui-monospace, 'Cascadia Mono', Consolas, monospace"

BANNER = """\
██████╗ ███████╗ ██████╗ ██╗   ██╗██╗███████╗███╗   ███╗
██╔══██╗██╔════╝██╔═══██╗██║   ██║██║██╔════╝████╗ ████║
██████╔╝█████╗  ██║   ██║██║   ██║██║█████╗  ██╔████╔██║
██╔══██╗██╔══╝  ██║▄▄ ██║██║   ██║██║██╔══╝  ██║╚██╔╝██║
██║  ██║███████╗╚██████╔╝╚██████╔╝██║███████╗██║ ╚═╝ ██║
╚═╝  ╚═╝╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝╚══════╝╚═╝     ╚═╝"""

FACTS = [
    ("stack", "TypeScript · Kotlin · Python · C#"),
    ("repos", "harvey · cobblemon-companion · VeinMining"),
    ("site", "caioaugusto.vercel.app"),
    ("where", "Brasil · UTC-3"),
]

W, H = 880, 312


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def grid(x: float, y: float, width: float, lines: list[str], scale: float,
         fill: str, opacity: float) -> str:
    """Locks a block of monospace art to an exact box, whatever font loads."""
    cols = max(len(l) for l in lines)
    cell = width / cols
    lh, size = cell * 2, cell * 1.75
    return (
        f'<g transform="translate({x:.1f},{y:.1f})" opacity="{opacity}" '
        f'font-family="{MONO}">'
        + "".join(
            f'<text x="0" y="{i * lh * scale:.1f}" font-size="{size * scale:.2f}px" '
            f'fill="{fill}" textLength="{width:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{esc(l)}</text>'
            for i, l in enumerate(lines))
        + "</g>")


def banner(x: float, y: float, width: float, fill: str) -> str:
    lines = BANNER.split("\n")
    cell = width / max(len(l) for l in lines)
    lh, size = cell * 1.08, cell * 1.36
    return (
        f'<g transform="translate({x:.1f},{y:.1f})" font-family="{MONO}">'
        + "".join(
            f'<text x="0" y="{i * lh:.1f}" font-size="{size:.2f}px" fill="{fill}" '
            f'textLength="{width:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{esc(l)}</text>'
            for i, l in enumerate(lines))
        + "</g>")


def build() -> str:
    rows = "".join(
        f'<text x="96" y="{184 + i * 27}" font-size="12.5px" font-family="{MONO}" '
        f'fill="#646c78">{esc(k)}</text>'
        f'<text x="170" y="{184 + i * 27}" font-size="12.5px" font-family="{MONO}" '
        f'fill="#d9dfe8">{esc(v)}</text>'
        for i, (k, v) in enumerate(FACTS))
    body = (
        grid(566, 30, 288, PORTRAIT.split("\n"), 1.0, "#e8eef6", 0.22)
        + banner(96, 40, 440, "#e8eef6")
        + '<rect x="96" y="142" width="452" height="1" fill="#232932"/>'
        + rows)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Requiem - TypeScript, Kotlin, Python, C#">'
        f'<rect width="{W}" height="{H}" rx="14" fill="#0c0f14"/>{body}</svg>\n')


if __name__ == "__main__":
    out = ASSETS / "profile.svg"
    out.write_text(build(), encoding="utf-8")
    print(out, out.stat().st_size)
