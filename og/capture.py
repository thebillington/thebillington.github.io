#!/usr/bin/env python3
"""Capture the nine project tiles that og/card.html shows.

Each tile is a real screenshot of the project, driven into a state worth
photographing rather than the page as it loads: the emulator is stepped past its
studio splash, the terminal is zoomed and given a command, the cipher has real
words typed into it.

Two tiles are the other projects' own cards — tphysics and pydle — and are copied
from their repositories rather than captured twice. Point the script at a
checkout of each with --tphysics and --pydle (they default to siblings of this
repository).

    python3 og/capture.py

Requires Playwright with a Chromium (`playwright install chromium`), or pass
`--browser /path/to/chrome`, and network access to the published demos.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
ASSETS = REPO / "og" / "assets"
TILE_W, TILE_H = 201, 180          # the card's tile box, in CSS pixels
SCALE = 2
ASPECT = TILE_W / TILE_H

DEMOS = "https://thebillington.github.io"


def crop_to_aspect(image: Image.Image, anchor: str = "center") -> Image.Image:
    w, h = image.size
    if w / h > ASPECT:
        new_w = round(h * ASPECT)
        x = {"left": 0, "right": w - new_w}.get(anchor, (w - new_w) // 2)
        return image.crop((x, 0, x + new_w, h))
    new_h = round(w / ASPECT)
    y = 0 if anchor == "top" else h - new_h if anchor == "bottom" else (h - new_h) // 2
    return image.crop((0, y, w, y + new_h))


def live(browser, url: str, *, selector: str = "#mainCanvas", start_presses: int = 0,
         zoom: float | None = None, type_text: tuple[str, str] | None = None,
         wait: int = 4000, full_page: bool = False, start_click: bool = False,
         keys: tuple[str, ...] = (), dsf: int = SCALE,
         trim: int = 0) -> Image.Image:
    page = browser.new_page(viewport={"width": 1000, "height": 760},
                            device_scale_factor=dsf)
    # the published demos are on GitHub Pages, which drops connections now and
    # then; a retry is cheaper than a half-captured tile set
    for attempt in range(4):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            break
        except Exception:
            if attempt == 3:
                raise
            page.wait_for_timeout(2000 * (attempt + 1))
    page.wait_for_timeout(wait)

    if type_text:
        field, text = type_text
        page.click(field)
        page.type(field, text, delay=30)
        page.wait_for_timeout(1500)

    if start_presses:
        try:
            page.click(selector)
        except Exception:
            pass
        for _ in range(start_presses):          # step past splash screens
            page.keyboard.down("Enter")
            page.wait_for_timeout(400)
            page.keyboard.up("Enter")
            page.wait_for_timeout(2500)

    if start_click:
        page.mouse.click(640, 400)          # some demos open on a start overlay
        page.wait_for_timeout(1800)
        for key in keys:                    # e.g. Seasons cycles its season on "s"
            page.keyboard.press(key)
            page.wait_for_timeout(1500)

    if zoom:
        page.evaluate(f"document.body.style.zoom='{zoom}'")
        page.wait_for_timeout(800)

    page.evaluate("document.fonts.ready.then(() => true)")
    page.wait_for_timeout(600)

    path = ASSETS / ".capture.png"
    if full_page:
        page.screenshot(path=str(path))
    else:
        page.locator(selector).wait_for(timeout=30_000)
        page.locator(selector).screenshot(path=str(path))
    page.close()
    image = Image.open(path).convert("RGB")
    if trim:                       # the emulator pages put a 1px border round the screen
        image = image.crop((trim, trim, image.width - trim, image.height - trim))
    return image


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser")
    ap.add_argument("--tphysics", default=str(REPO.parent / "tphysics"),
                    help="checkout of the tphysics repository")
    ap.add_argument("--pydle", default=str(REPO.parent / "pydle"),
                    help="checkout of the pydle repository")
    ap.add_argument("--only", type=int, action="append",
                    help="re-capture just this tile index (repeatable)")
    args = ap.parse_args()

    tphysics_flappy = Path(args.tphysics) / "og" / "assets" / "flappy.png"
    pydle_drawing = Path(args.pydle) / "og" / "assets" / "drawing.png"
    for needed in (tphysics_flappy, pydle_drawing):
        if not needed.is_file():
            raise SystemExit(f"og: {needed} is missing — run that repo's og/capture.py first")

    ASSETS.mkdir(parents=True, exist_ok=True)
    launch = {"args": ["--no-sandbox"]}
    with sync_playwright() as p:
        if args.browser:
            launch["executable_path"] = args.browser
        browser = p.chromium.launch(**launch)

        wanted = set(args.only) if args.only else set(range(9))

        def save(index: int, image: Image.Image, *, native: bool = False,
                 anchor: str = "center"):
            if index not in wanted:
                return
            if not native:
                image = crop_to_aspect(image, anchor)
                image = image.resize((TILE_W * SCALE, TILE_H * SCALE), Image.LANCZOS)
            image.save(ASSETS / f"tile-{index}.png")
            print(f"  tile-{index}.png {image.size}")

        def capture(index: int):
            if index == 0:
                save(0, Image.open(tphysics_flappy).convert("RGB"))
            elif index == 1:
                save(1, live(browser, f"{DEMOS}/mushys_adventure/", dsf=1, trim=1), native=True)
            elif index == 2:
                save(2, Image.open(pydle_drawing).convert("RGB"))
            elif index == 3:
                seasons = live(browser, f"{DEMOS}/seasons/", selector="#defaultCanvas0",
                               start_click=True, wait=2500)
                save(3, seasons.crop((0, 0, seasons.width, int(seasons.height * 0.88))))
            elif index == 4:
                save(4, live(browser, f"{DEMOS}/Skazka/", dsf=1, trim=1), native=True)
            elif index == 5:
                save(5, live(browser, f"{DEMOS}/shellJS/", selector="body", full_page=True,
                             zoom=2, wait=20000, start_click=True,
                             keys=("h", "e", "l", "p", "Enter")))
            elif index == 6:
                page = browser.new_page(viewport={"width": 1000, "height": 760},
                                        device_scale_factor=SCALE)
                page.goto(f"{DEMOS}/dnd-cipher/", wait_until="domcontentloaded",
                          timeout=45_000)
                page.wait_for_timeout(2500)
                page.click("#input")
                page.type("#input", "Meet me at the tavern before dawn.", delay=30)
                page.evaluate("document.fonts.ready.then(() => true)")
                page.wait_for_timeout(1500)
                box = page.locator("#output").bounding_box()
                page.screenshot(path=str(ASSETS / ".dnd.png"), clip=box)
                page.close()
                save(6, Image.open(ASSETS / ".dnd.png").convert("RGB"), anchor="top")
                (ASSETS / ".dnd.png").unlink(missing_ok=True)
            elif index == 7:
                save(7, live(browser, f"{DEMOS}/garden-of-eden-GB/", start_presses=1,
                             dsf=1, trim=1), native=True)
            elif index == 8:
                save(8, live(browser, "https://billy.rebecchi.uk/", selector="body",
                             full_page=True))

        for index in sorted(wanted):
            capture(index)

        browser.close()

    (ASSETS / ".capture.png").unlink(missing_ok=True)
    print(f"og: wrote nine tiles into {ASSETS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
