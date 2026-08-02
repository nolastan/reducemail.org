#!/usr/bin/env python3
"""Render blog/*.md into <slug>/index.html pages matching the site's design.

This is the one-time importer used to move the Ghost export into static pages;
it is not part of serving the site. The generated HTML is committed and is the
source of truth — rerunning this overwrites any hand edits to those pages.

    python3 tools/import-blog.py
"""

import html
import importlib.util
import json
import os
import re
import subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "optimize_images", os.path.join(TOOLS, "optimize-images.py")
)
_optimize = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_optimize)
BLOG = os.path.join(ROOT, "blog")
SITE = "https://www.reducemail.org"

EXTERNAL_MAP = json.load(
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "imported-images.json"))
)

# ---------------------------------------------------------------- helpers ---

_dim_cache = {}


def dimensions(local_path):
    """Pixel size of a committed image, for width/height attributes."""
    if local_path in _dim_cache:
        return _dim_cache[local_path]
    abs_path = os.path.join(ROOT, local_path.lstrip("/"))
    dims = None
    if os.path.exists(abs_path):
        out = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", abs_path],
            capture_output=True, text=True,
        ).stdout
        w = re.search(r"pixelWidth:\s*(\d+)", out)
        h = re.search(r"pixelHeight:\s*(\d+)", out)
        if w and h:
            dims = (int(w.group(1)), int(h.group(1)))
    _dim_cache[local_path] = dims
    return dims


# Images with no copy left anywhere. talktomel.com redirects every path to the
# reducemail.org homepage now, and login.truste.com 404s. Most of the
# talktomel images were recovered from the Wayback Machine's capture of
# blog.talktomel.com (the blog's earlier home) — see imported-images.json — but
# these two were never crawled at any size. They render as broken boxes on the
# live Ghost site today; here they're dropped and their captions are kept.
DEAD_IMAGES = {
    "https://login.truste.com/services/resources/storage/images/"
    "IMG-cbb6595701294430975d8f20c31848f2.jpg",
    "https://talktomel.com/blog_images/van-driving-away.jpg",
    "https://talktomel.com/blog_images/person-sorting-mail.jpg",
}


def localize(url):
    """Rewrite an image URL to the copy committed in this repo."""
    local = None
    if url.startswith("https://reducemail.org/content/"):
        local = url[len("https://reducemail.org"):]
    elif url.startswith("https://www.reducemail.org/content/"):
        local = url[len("https://www.reducemail.org"):]
    else:
        local = EXTERNAL_MAP.get(url)
    if local is None:
        return url
    if os.path.exists(os.path.join(ROOT, local.lstrip("/"))):
        return local
    # tools/optimize-images.py re-encodes some PNGs as JPEGs; follow the rename.
    stem = os.path.splitext(local)[0]
    for ext in (".jpg", ".jpeg", ".png"):
        if os.path.exists(os.path.join(ROOT, (stem + ext).lstrip("/"))):
            return stem + ext
    return local


def internal_link(url):
    """Keep cross-article links relative so they work on any host."""
    for prefix in ("https://reducemail.org", "https://www.reducemail.org"):
        if url == prefix:
            return "/"
        if url.startswith(prefix + "/"):
            path = url[len(prefix):]
            return path if path.endswith("/") else path + "/"
    return url


def esc(s):
    return html.escape(s, quote=True)


# ------------------------------------------------------------ inline pass ---

PLACEHOLDER = "\x00%d\x00"

# A link target may itself contain balanced parentheses — Wikipedia
# disambiguators like Gail_Anderson_(graphic_designer) are the common case.
URL = r"(?:[^()\s]|\([^()\s]*\))*"

YT_RE = re.compile(r"^https?://(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]+)")
TIKTOK_RE = re.compile(
    r"^https?://(?:www\.)?tiktok\.com/(?:embed/v2/|@[^/]+/video/)(\d+)"
)


class Inline:
    """Converts inline markdown, stashing generated HTML behind placeholders so
    later passes (emphasis) can't chew through URLs or attributes."""

    def __init__(self):
        self.parts = []

    def stash(self, fragment):
        self.parts.append(fragment)
        return PLACEHOLDER % (len(self.parts) - 1)

    def restore(self, text):
        return re.sub(r"\x00(\d+)\x00", lambda m: self.parts[int(m.group(1))], text)

    def render(self, text):
        text = self._escapes(text)
        text = self._code(text)
        text = self._images(text)
        text = self._links(text)
        text = esc(text)
        text = self._emphasis(text)
        return self.restore(text)

    def _escapes(self, text):
        r"""Stash backslash-escaped punctuation (\[ \* …) so the passes below
        neither act on it nor leave the backslash visible."""
        return re.sub(
            r"\\([\\`*_{}\[\]()#+\-.!>~|])",
            lambda m: self.stash(esc(m.group(1))),
            text,
        )

    def _code(self, text):
        return re.sub(
            r"`([^`]+)`",
            lambda m: self.stash("<code>%s</code>" % esc(m.group(1))),
            text,
        )

    def _images(self, text):
        def repl(m):
            alt, url = m.group(1), m.group(2).strip()
            return self.stash(img_tag(url, alt))

        return re.sub(r"!\[([^\]]*)\]\((%s)\)" % URL, repl, text)

    def _links(self, text):
        # Innermost first, so the doubled `[[a](url)](url)` links Ghost exported
        # collapse to a single anchor instead of nesting.
        pattern = re.compile(r"\[([^\[\]]*)\]\((%s)\)" % URL)
        for _ in range(3):
            new = pattern.sub(self._link_repl, text)
            if new == text:
                break
            text = new
        return text

    def _link_repl(self, m):
        label, url = m.group(1), m.group(2).strip()
        # Emphasis runs here rather than in the later pass: by then this anchor
        # is already stashed, so `[**Ridwell**](…)` would keep its asterisks.
        rendered = self.restore(self._emphasis(esc(label)))
        if "<a " in rendered:
            # Ghost exported some cards as a link wrapping other links. Nested
            # anchors aren't valid HTML — keep the inner ones and drop the wrapper.
            return label
        href = internal_link(url)
        target = ""
        if href.startswith("http"):
            target = ' target="_blank" rel="noopener"'
        return self.stash('<a href="%s"%s>%s</a>' % (esc(href), target, rendered))

    def _emphasis(self, text):
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
        # Underscore emphasis, but never intraword — plenty of body text names
        # files like IMG_3614.
        text = re.sub(r"(?<!\w)__([^_\n]+)__(?!\w)", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", text)
        return text


_bare_cache = {}


def is_bare(local_path):
    """True for images that carry their own edge — a screenshot with a drop
    shadow, or a cutout on transparent background. Framing those in a border
    draws a box around the shadow."""
    if local_path not in _bare_cache:
        abs_path = os.path.join(ROOT, local_path.lstrip("/"))
        _bare_cache[local_path] = (
            local_path.lower().endswith(".png")
            and os.path.exists(abs_path)
            and _optimize.png_has_transparency(abs_path)
        )
    return _bare_cache[local_path]


def img_tag(url, alt, cls=None):
    src = localize(url)
    dims = dimensions(src) if src.startswith("/") else None
    attrs = ['src="%s"' % esc(src), 'alt="%s"' % esc(alt)]
    if src.startswith("/") and is_bare(src):
        cls = (cls + " bare") if cls else "bare"
    if cls:
        attrs.insert(0, 'class="%s"' % cls)
    if dims:
        attrs += ['width="%d"' % dims[0], 'height="%d"' % dims[1]]
    attrs.append('loading="lazy"')
    attrs.append('decoding="async"')
    return "<img %s />" % " ".join(attrs)


def inline(text):
    return Inline().render(text)


# ------------------------------------------------------------- block pass ---

IMAGE_ONLY = re.compile(r"^!\[([^\]]*)\]\((%s)\)$" % URL)
CAPTION_ONLY = re.compile(r"^\*([^*]+)\*$")
LINK_ONLY = re.compile(r"^\[([^\]]*)\]\((%s)\)$" % URL)
# Ghost's video cards flattened into one link whose label may itself contain
# links, so the label has to be matched greedily.
EMBED_LINE = re.compile(r"^\[(.*)\]\((https?://%s)\)$" % URL)


def embed_html(url, label):
    m = YT_RE.match(url)
    if m:
        return (
            '<figure class="embed">\n'
            '  <div class="embed__frame">\n'
            '    <iframe src="https://www.youtube-nocookie.com/embed/%s" '
            'title="%s" loading="lazy" allowfullscreen '
            'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; '
            'picture-in-picture" referrerpolicy="strict-origin-when-cross-origin">'
            "</iframe>\n"
            "  </div>\n"
            "</figure>" % (esc(m.group(1)), esc(label or "YouTube video"))
        )
    m = TIKTOK_RE.match(url)
    if m:
        return (
            '<figure class="embed">\n'
            '  <div class="embed__frame embed__frame--tall">\n'
            '    <iframe src="https://www.tiktok.com/embed/v2/%s" title="%s" '
            'loading="lazy" allowfullscreen></iframe>\n'
            "  </div>\n"
            "</figure>" % (esc(m.group(1)), esc(label or "TikTok video"))
        )
    return None


def gallery_attrs(imgs):
    """Pick how a run of images should tile.

    Matching proportions need no help — they line up at natural size. A mixed
    run needs a fixed tile, and the tile's shape decides how much of it the
    images waste. Ordinary photos (portrait and landscape snapshots together)
    fill a square tile edge to edge; anything with an unusual shape is a
    document or a screenshot, where cropping would cut off content, so those
    get letterboxed into a tile the shape of the group's median instead.
    """
    ratios = []
    for url, _ in imgs:
        dims = dimensions(localize(url))
        if dims:
            ratios.append(dims[0] / dims[1])
    attrs = ' data-count="%d"' % len(imgs)
    if len(ratios) != len(imgs) or not ratios:
        return attrs + ' data-fit="tile"'
    if max(ratios) / min(ratios) < 1.15:
        return attrs + ' data-fit="natural"'
    if all(0.6 <= r <= 1.8 for r in ratios):
        return attrs + ' data-fit="cover"'
    median = sorted(ratios)[len(ratios) // 2]
    return attrs + ' data-fit="tile" style="--tile-aspect: %.2f"' % median


def render_blockquote(lines):
    """Ghost bookmark cards export as a blockquote whose first line is nothing
    but a link. Those become link cards; everything else stays a quote."""
    body = [re.sub(r"^>\s?", "", ln) for ln in lines]
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    if not body:
        return ""

    m = LINK_ONLY.match(body[0].strip())
    if m:
        title, url = m.group(1), m.group(2)
        rest = [ln.strip() for ln in body[1:] if ln.strip()]
        # Ghost repeats the page title as the first description line.
        if rest and rest[0] == title:
            rest = rest[1:]
        desc = " ".join(rest)
        href = internal_link(url)
        target = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        out = ['<a class="bookmark" href="%s"%s>' % (esc(href), target)]
        out.append('  <span class="bookmark__title">%s</span>' % inline(title))
        if desc:
            out.append('  <span class="bookmark__desc">%s</span>' % inline(desc))
        host = re.sub(r"^www\.", "", href.split("/")[2]) if href.startswith("http") else "reducemail.org"
        out.append('  <span class="bookmark__host">%s</span>' % esc(host))
        out.append("</a>")
        return "\n".join(out)

    paras = []
    buf = []
    for ln in body:
        if ln.strip():
            buf.append(ln.strip())
        elif buf:
            paras.append(" ".join(buf))
            buf = []
    if buf:
        paras.append(" ".join(buf))
    inner = "\n".join("  <p>%s</p>" % inline(p) for p in paras)
    return "<blockquote>\n%s\n</blockquote>" % inner


def render_body(md):
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Fenced code
        if stripped.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % esc("\n".join(code)))
            continue

        # Horizontal rule
        if re.fullmatch(r"-{3,}|\*{3,}", stripped):
            out.append("<hr />")
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{2,6})\s+(.*)$", stripped)
        if m:
            level = min(len(m.group(1)), 4)
            text = m.group(2).strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            out.append('<h%d id="%s">%s</h%d>' % (level, esc(anchor), inline(text), level))
            i += 1
            continue
        if stripped.startswith("# "):
            # The exported H1 duplicates the page title, which the hero renders.
            i += 1
            continue

        # Blockquote. A blank line ends it — Ghost writes a bare ">" for blank
        # lines inside one quote, so a real blank line separates two of them
        # (two consecutive bookmark cards, most often).
        if stripped.startswith(">"):
            block = []
            while i < n and lines[i].strip().startswith(">"):
                block.append(lines[i])
                i += 1
            out.append(render_blockquote(block))
            continue

        # Lists
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            ordered = bool(re.match(r"^\d+\.\s+", stripped))
            marker = r"^\d+\.\s+" if ordered else r"^[-*]\s+"
            items = []
            while i < n and re.match(marker, lines[i].strip()):
                item = re.sub(r"^(?:[-*]|\d+\.)\s+", "", lines[i].strip())
                items.append("  <li>%s</li>" % inline(item))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>\n%s\n</%s>" % (tag, "\n".join(items), tag))
            continue

        # Standalone image (or a run of them — Ghost's gallery card), optionally
        # followed by an italic caption that belongs to the whole group.
        m = IMAGE_ONLY.match(stripped)
        if m:
            imgs = []
            while i < n:
                if not lines[i].strip():
                    i += 1
                    continue
                gm = IMAGE_ONLY.match(lines[i].strip())
                if not gm:
                    break
                if gm.group(2) not in DEAD_IMAGES:
                    imgs.append((gm.group(2), gm.group(1)))
                i += 1

            caption = None
            j = i
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                cm = CAPTION_ONLY.match(lines[j].strip())
                if cm:
                    caption = cm.group(1)
                    i = j + 1

            if not imgs:
                # Every image in the run was dead. The caption still carries
                # information, so it stays — as body text, not a centred
                # caption floating under nothing.
                if caption:
                    out.append("<p><em>%s</em></p>" % inline(caption))
                continue
            if len(imgs) == 1:
                fig = ["<figure>", "  " + img_tag(imgs[0][0], imgs[0][1])]
            else:
                fig = ['<figure class="gallery"%s>' % gallery_attrs(imgs)]
                fig += ["  " + img_tag(u, a) for u, a in imgs]
            if caption:
                fig.append("  <figcaption>%s</figcaption>" % inline(caption))
            fig.append("</figure>")
            out.append("\n".join(fig))
            continue

        # Standalone embed link (Ghost video card)
        m = EMBED_LINE.match(stripped)
        if m:
            label, url = m.group(1), m.group(2)
            plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", label).strip()
            emb = embed_html(url, plain[:120])
            if emb:
                # A label carrying its own links is the video's caption, not a title.
                caption = inline(label) if "](" in label else None
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if caption is None and j < n:
                    cm = CAPTION_ONLY.match(lines[j].strip())
                    if cm:
                        caption = inline(cm.group(1))
                        i = j
                if caption:
                    emb = emb.replace(
                        "</figure>",
                        "  <figcaption>%s</figcaption>\n</figure>" % caption,
                    )
                out.append(emb)
                i += 1
                continue

        # A short link on its own line is a Ghost button card ("Open Form").
        m = LINK_ONLY.match(stripped)
        if m and len(m.group(1)) <= 40 and m.group(1).strip():
            href = internal_link(m.group(2))
            target = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
            out.append(
                '<p class="btn-row"><a class="btn btn--primary" href="%s"%s>%s</a></p>'
                % (esc(href), target, inline(m.group(1)))
            )
            i += 1
            continue

        # Paragraph
        para = []
        while i < n and lines[i].strip() and not re.match(
            r"^\s*(#{1,6}\s|>|```|[-*]\s|\d+\.\s|-{3,}$)", lines[i]
        ):
            para.append(lines[i].strip())
            i += 1
        text = " ".join(para)
        cm = CAPTION_ONLY.match(text)
        if cm:
            out.append('<p class="figure-note">%s</p>' % inline(cm.group(1)))
        else:
            out.append("<p>%s</p>" % inline(text))

    return "\n\n".join(b for b in out if b)


# ----------------------------------------------------------------- pages ----

def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    meta_raw, body = m.group(1), m.group(2)
    meta = {}
    for line in meta_raw.split("\n"):
        km = re.match(r'^(\w+):\s*"?(.*?)"?\s*$', line)
        if km:
            meta[km.group(1)] = km.group(2)
    # This image 404s at the source, so there is nothing to import and nothing
    # worth rendering a broken box for.
    body = re.sub(
        r"!\[\]\(https://login\.truste\.com/[^)]*\)\s*\n", "", body
    )
    # Trailing Ghost artifacts: a rule plus an invitation to comment. This site
    # has no comment system, so both go.
    body = re.sub(r"\n-{3,}\s*\n+💬[^\n]*\s*$", "\n", body)
    body = re.sub(r"\n-{3,}\s*$", "\n", body).strip()
    meta["body"] = body
    return meta


HEADER = """    <header class="site-header">
      <div class="wrap site-header__inner">
        <a class="brand-mark" href="/">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--accent)"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h9" />
            <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
            <path d="m17 17 4 4" />
            <path d="m21 17-4 4" />
          </svg>
          ReduceMail.org
        </a>
        <nav class="site-nav" aria-label="Main">
          <a href="/start-here/">Start Here</a>
          <a href="/opt-out-forms/">Opt-Out Forms</a>
          <a href="/privacy-portals/">Privacy Portals</a>
          <a href="/#resources">Resources</a>
          <a href="/about/">About</a>
        </nav>
      </div>
    </header>"""

FOOTER = """    <footer class="site-footer">
      <div class="wrap">
        <div class="site-footer__grid">
          <div class="stack">
            <a class="brand-mark" href="/">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--accent)"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h9" />
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                <path d="m17 17 4 4" />
                <path d="m21 17-4 4" />
              </svg>
              ReduceMail.org
            </a>
            <p class="support-note">
              A free project by
              <a href="https://www.stanfordrosenthal.com/">Stanford Rosenthal</a>. Say
              hello at <a href="mailto:stan@talktomel.com">stan@talktomel.com</a>.
            </p>
          </div>
          <nav aria-label="Footer">
            <a href="/start-here/">Start Here</a>
            <a href="/opt-out-forms/">Opt-Out Forms</a>
            <a href="/privacy-portals/">Privacy Portals</a>
            <a href="/#resources">Resources</a>
            <a href="/about/">About</a>
          </nav>
        </div>
        <p class="site-footer__note">
          Created with care in Yelamu, also known as San Francisco, on the unceded,
          traditional Tribal lands of the Ramaytush &amp; Muwekma Ohlone people.
        </p>
      </div>
    </footer>"""


PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title_esc} — ReduceMail.org</title>
    <meta name="description" content="{excerpt}" />
    <meta name="author" content="Stanford Rosenthal" />
    <link rel="canonical" href="{url}" />
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="stylesheet" href="/styles.css" />
    <meta property="og:type" content="article" />
    <meta property="og:title" content="{title_esc}" />
    <meta property="og:description" content="{excerpt}" />
    <meta property="og:url" content="{url}" />
{og_image}    <meta property="article:published_time" content="{published}" />
    <meta property="article:modified_time" content="{modified}" />
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to content</a>

{header}

    <main id="main">
      <article class="article">
        <div class="wrap">
          <div class="article__head">
            <a class="article__back" href="/#resources">All resources</a>
            <h1>{title_html}</h1>
{lede}            <p class="article__meta">
              <time datetime="{published}">{date_h}</time>
            </p>
          </div>
{feature}
          <div class="prose">
{body}
          </div>

          <div class="article__foot">
            <p class="sub">
              ReduceMail.org is a free, ad-free guide to stopping junk mail.
            </p>
            <div class="btn-row">
              <a class="btn btn--primary" href="/start-here/">Start here</a>
              <a class="btn btn--secondary" href="/#resources">More resources</a>
            </div>
          </div>
        </div>
      </article>
    </main>

{footer}

    <script src="https://cdn.usefathom.com/script.js" data-site="KEOJWEPM" defer></script>
  </body>
</html>
"""


def indent(block, spaces):
    """Indent for readability, but leave <pre> contents byte-for-byte alone."""
    pad = " " * spaces
    out = []
    in_pre = False
    for ln in block.split("\n"):
        if in_pre:
            out.append(ln)
        else:
            out.append(pad + ln if ln.strip() else ln)
        if "<pre>" in ln:
            in_pre = True
        if "</code></pre>" in ln:
            in_pre = False
    return "\n".join(out)


def build(meta):
    slug = meta["slug"]
    url = "%s/%s/" % (SITE, slug)
    title = meta["title"]
    excerpt = meta.get("excerpt", "").strip()
    published = meta["date"]
    modified = meta.get("updated", published)
    date_h = datetime.strptime(published[:10], "%Y-%m-%d").strftime("%B %-d, %Y")

    feature_url = meta.get("feature_image", "").strip()
    feature = ""
    og_image = ""
    if feature_url:
        local = localize(feature_url)
        og_src = SITE + local if local.startswith("/") else local
        og_image = '    <meta property="og:image" content="%s" />\n' % esc(og_src)
        feature = (
            '          <figure class="article__feature">\n'
            "            %s\n"
            "          </figure>\n" % img_tag(feature_url, "").replace(
                'loading="lazy"', 'loading="eager" fetchpriority="high"'
            )
        )

    lede = ""
    if excerpt:
        lede = '            <p class="lede">%s</p>\n' % inline(excerpt)

    body = indent(render_body(meta["body"]), 12)

    return PAGE.format(
        title_esc=esc(title),
        title_html=inline(title),
        excerpt=esc(excerpt),
        url=esc(url),
        og_image=og_image,
        published=esc(published),
        modified=esc(modified),
        date_h=date_h,
        lede=lede,
        feature=feature,
        body=body,
        header=HEADER,
        footer=FOOTER,
    )


def main():
    posts = []
    for fn in sorted(os.listdir(BLOG)):
        if not fn.endswith(".md"):
            continue
        meta = parse(os.path.join(BLOG, fn))
        posts.append(meta)
        outdir = os.path.join(ROOT, meta["slug"])
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
            f.write(build(meta))
    print("wrote %d pages" % len(posts))


if __name__ == "__main__":
    main()
