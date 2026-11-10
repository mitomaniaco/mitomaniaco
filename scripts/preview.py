"""Rasterises assets/card-*.svg to PNG for local preview (not used in CI)."""
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ROOT / "preview"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def size_of(svg: str) -> tuple[int, int]:
    m = re.search(r'width="(\d+)" height="([\d.]+)"', svg)
    return int(m.group(1)), int(float(m.group(2)))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name in ("dark", "light"):
        src = ASSETS / f"card-{name}.svg"
        svg = src.read_text(encoding="utf-8")
        w, h = size_of(svg)
        html = f'<!doctype html><html><body style="margin:0;background:transparent">{svg}</body></html>'
        tmp = Path(tempfile.mkdtemp()) / "card.html"
        tmp.write_text(html, encoding="utf-8")
        png = OUT / f"card-{name}.png"
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", f"--window-size={w},{h}",
                        f"--screenshot={png}", tmp.as_uri()], check=True,
                       capture_output=True)
        print(png, png.stat().st_size)


if __name__ == "__main__":
    main()
