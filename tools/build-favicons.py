#!/usr/bin/env python3
"""Self-host each brand's favicon on the Opt-Out Forms page and tint its card.

    python3 tools/build-favicons.py            # fetch missing icons, then update the page
    python3 tools/build-favicons.py --offline  # only update the page from icons on disk
    python3 tools/build-favicons.py --refetch  # fetch every icon again

For each `<li data-name="…">` in opt-out-forms/index.html it works out the brand's
domain, downloads the favicon once into assets/favicons/<domain>.png (64×64), finds the
icon's main colour, and rewrites the card so it shows the icon and carries that colour
as `--tint`. Visitors only ever load the copies on our own domain, so no third party
learns who is browsing the directory.

Icons are fetched from the brand's own site first. When a site blocks scripts or has no
usable icon, Google's and DuckDuckGo's favicon services are tried, but only here, at
build time. A brand with no icon at all gets a monogram, and an icon with no real colour
(black, white or grey) gets no tint.

Needs Pillow (`pip install pillow`). Run it after adding a brand to the list and commit
the new file in assets/favicons/ along with the page.
"""

from __future__ import annotations

import argparse
import colorsys
import html
import io
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "opt-out-forms" / "index.html"
ICON_DIR = ROOT / "assets" / "favicons"
ICON_URL = "/assets/favicons/"
SIZE = 64

# Brands whose opt-out link lives on someone else's host (a form builder, a privacy
# vendor) or on one of our own guides. Keyed by data-name.
DOMAINS = {
    "Chevrolet GM": "chevrolet.com",
    "Cosabella": "cosabella.com",
    "GE Appliances": "geappliances.com",
    "Harry &amp; David 1-800-Flowers": "harryanddavid.com",
    "Intuit QuickBooks": "quickbooks.intuit.com",
    "Osprey": "osprey.com",
    "Rails": "railsclothing.com",
    "Royal Caribbean Cruises": "royalcaribbean.com",
    "T-Mobile": "t-mobile.com",
    "Walmart": "walmart.com",
    "Walt Disney": "disney.com",
    "Woman Within": "womanwithin.com",
    "Xfinity Comcast": "xfinity.com",
    "ACLU": "aclu.org",
}

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)

ENTRY_RE = re.compile(
    r'(?P<indent>[ \t]*)<li data-name="(?P<name>[^"]*)"[^>]*>\s*'
    r'<a class="entry"(?P<attrs>[^>]*?)>(?P<body>.*?)</a>\s*</li>',
    re.S,
)


# --- Domains -----------------------------------------------------------------


def domain_for(name: str, href: str) -> str | None:
    if name in DOMAINS:
        return DOMAINS[name]
    host = urllib.parse.urlparse(html.unescape(href)).hostname
    if not host:
        return None
    return host[4:] if host.startswith("www.") else host


# --- Fetching ----------------------------------------------------------------


def get(url: str, limit: int = 2_000_000) -> tuple[bytes, str] | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.status != 200:
                return None
            return res.read(limit), res.geturl()
    except Exception:
        return None


class IconLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[int, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        a = dict(attrs)
        rel = (a.get("rel") or "").lower().split()
        href = a.get("href")
        if not href or not ({"icon", "apple-touch-icon", "apple-touch-icon-precomposed"} & set(rel)):
            return
        if href.lower().split("?")[0].endswith(".svg") or "svg" in (a.get("type") or ""):
            return  # Pillow can't rasterise SVG; the fallbacks cover these sites.
        sizes = re.findall(r"(\d+)x\d+", a.get("sizes") or "")
        size = max(map(int, sizes)) if sizes else (180 if "apple-touch-icon" in rel[0] else 16)
        self.links.append((size, href))


def decode(data: bytes, min_size: int = 16) -> Image.Image | None:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()  # Pillow opens an ICO at its largest size.
    except Exception:
        return None
    if min(img.size) < min_size:
        return None
    return img.convert("RGBA")


def from_site(domain: str) -> Image.Image | None:
    page = get(f"https://{domain}/") or get(f"https://www.{domain}/")
    candidates: list[tuple[int, str]] = []
    base = f"https://{domain}/"
    if page:
        body, base = page
        parser = IconLinks()
        try:
            parser.feed(body.decode("utf-8", "replace"))
        except Exception:
            pass
        candidates = sorted(parser.links, reverse=True)
    candidates.append((16, "/favicon.ico"))
    for _, href in candidates:
        res = get(urllib.parse.urljoin(base, href))
        img = res and decode(res[0], min_size=32)
        if img:
            return img
    return None


def from_service(domain: str) -> Image.Image | None:
    for url in (
        f"https://www.google.com/s2/favicons?domain={domain}&sz={SIZE}",
        f"https://icons.duckduckgo.com/ip3/{domain}.ico",
    ):
        res = get(url)  # Google answers 404 with a generic globe when it has nothing.
        img = res and decode(res[0], min_size=16)
        if img:
            return img
    return None


def fetch(domain: str) -> Image.Image | None:
    return from_site(domain) or from_service(domain)


def save(img: Image.Image, path: Path) -> None:
    bbox = img.getchannel("A").getbbox()
    if bbox:
        img = img.crop(bbox)
    img.thumbnail((SIZE, SIZE), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, optimize=True)


# --- Colour ------------------------------------------------------------------


def main_color(path: Path) -> str | None:
    """The most common saturated colour in the icon, or None if it is monochrome."""
    img = Image.open(path).convert("RGBA")
    pixels = img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()
    opaque = [p[:3] for p in pixels if p[3] >= 160]
    if not opaque:
        return None
    colourful = []
    for r, g, b in opaque:
        _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s >= 0.3 and v >= 0.25:
            colourful.append((r, g, b))
    if len(colourful) < 0.08 * len(opaque):
        return None
    buckets = Counter((r >> 4, g >> 4, b >> 4) for r, g, b in colourful)
    top = buckets.most_common(1)[0][0]
    members = [p for p in colourful if (p[0] >> 4, p[1] >> 4, p[2] >> 4) == top]
    r, g, b = (round(sum(c) / len(members)) for c in zip(*members))
    return f"#{r:02x}{g:02x}{b:02x}"


# --- Page --------------------------------------------------------------------


def render(m: re.Match, domain: str | None) -> str:
    name, indent = m["name"], m["indent"]
    attrs = re.sub(r'\s*style="[^"]*"', "", m["attrs"])
    body = m["body"]
    # Strip anything a previous run added, leaving "<label><arrow>".
    body = re.sub(r'<(?:img|span) class="entry__icon[^>]*>(?:[^<]*</span>)?', "", body)
    body = re.sub(r'<span class="entry__name">(.*?)</span>', r"\1", body, flags=re.S)
    label, _, arrow = body.partition('<span class="entry__arrow"')
    arrow = '<span class="entry__arrow"' + arrow if arrow else ""

    icon_path = ICON_DIR / f"{domain}.png" if domain else None
    if icon_path and icon_path.exists():
        icon = (
            f'<img class="entry__icon" src="{ICON_URL}{domain}.png" alt="" '
            f'width="{SIZE // 2}" height="{SIZE // 2}" loading="lazy" decoding="async" />'
        )
        color = main_color(icon_path)
    else:
        letter = html.unescape(re.sub(r"^The ", "", html.unescape(label).strip()))[:1].upper()
        icon = f'<span class="entry__icon entry__icon--letter" aria-hidden="true">{html.escape(letter)}</span>'
        color = None

    style = f' style="--tint: {color}"' if color else ""
    domain_attr = f' data-domain="{domain}"' if domain else ""
    return (
        f'{indent}<li data-name="{name}"{domain_attr}>\n'
        f'{indent}  <a class="entry"{attrs}{style}>{icon}'
        f'<span class="entry__name">{label.strip()}</span>{arrow}</a>\n'
        f"{indent}</li>"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--offline", action="store_true", help="don't fetch, just update the page")
    ap.add_argument("--refetch", action="store_true", help="fetch every icon again")
    args = ap.parse_args()

    page = PAGE.read_text()
    entries = list(ENTRY_RE.finditer(page))
    domains = {}
    for m in entries:
        href = re.search(r'href="([^"]*)"', m["attrs"])
        domains[m.start()] = domain_for(m["name"], href[1] if href else "")

    missing = []
    if not args.offline:
        for domain in sorted({d for d in domains.values() if d}):
            path = ICON_DIR / f"{domain}.png"
            if path.exists() and not args.refetch:
                continue
            img = fetch(domain)
            if img:
                save(img, path)
                print(f"fetched  {domain}")
            else:
                missing.append(domain)
                print(f"missing  {domain}", file=sys.stderr)

    out, last = [], 0
    for m in entries:
        out.append(page[last : m.start()])
        out.append(render(m, domains[m.start()]))
        last = m.end()
    out.append(page[last:])
    PAGE.write_text("".join(out))

    with_icon = sum(1 for d in domains.values() if d and (ICON_DIR / f"{d}.png").exists())
    print(f"{with_icon} of {len(entries)} brands have an icon")
    if missing:
        print("no icon found for: " + ", ".join(missing), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
