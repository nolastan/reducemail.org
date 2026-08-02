# ReduceMail.org — Agent Instructions

## What This Is
ReduceMail.org is a **free public-resource website** that helps people opt out of unwanted physical junk mail. It provides guides, templates, letter generators, contact directories, and educational content.

## What It Is NOT
- Not a SaaS product
- No user accounts, subscriptions, paywalls, or upsells
- No gated content or lead capture funnels
- No marketing campaigns or conversion tracking

## Key Resources
- **Design System:** See [`docs/design-system.md`](docs/design-system.md) for complete visual language, color tokens, typography, spacing, components, and content tone.
- **Main entry point:** [`index.html`](index.html) at the repo root.
- **Content types:** Guides, templates, letter generators, directory tables, FAQs, blog posts.

## Structure
Plain static HTML served by GitHub Pages. There is **no build step** — edit the HTML and
CSS directly. Each page is a directory with an `index.html` so the URL keeps its trailing
slash (`/start-here/`), matching the URLs the site used on Ghost.

| Path | Page |
|------|------|
| `index.html` | Homepage |
| `start-here/index.html` | The five big opt-out lists |
| `opt-out-forms/index.html` | Brand opt-out form directory |
| `privacy-portals/index.html` | Data-deletion portal directory |
| `about/index.html` | About |
| `<slug>/index.html` | One article each, 27 of them, at the root so the Ghost URLs still resolve |
| `404.html` | Not-found page GitHub Pages serves for any unmatched path |
| `styles.css` | Hand-authored design system (tokens → base → components) |
| `directory-filter.js` | Client-side filter shared by both directory pages |
| `assets/` | Envelope illustrations and the hero pattern |
| `content/images/` | Article images, at the paths Ghost served them from |
| `blog/` | The Ghost markdown export the articles were generated from |
| `tools/import-blog.py` | The one-time importer that generated those pages |
| `tools/optimize-images.py` | Downscales and re-encodes `content/images/` (run before the importer) |
| `tools/build-sitemap.py` | Regenerates `sitemap.xml` from the pages' canonical tags |

Header and footer markup is duplicated per page — when you change one, change them all
(the five section pages, every article, and `404.html`). Adding a brand means adding one
`<li data-name="…">` to the relevant directory; the filter and the count pick it up
automatically. Keep the homepage tile counts in sync.

### Articles

The generated HTML is the source of truth. `tools/import-blog.py` exists to document how
the pages were produced and to rebuild them wholesale if the design changes — rerunning it
overwrites hand edits, so for a one-off correction edit the article's `index.html` (and the
matching `blog/*.md`, so the two don't drift).

Images live at the paths Ghost served them from, so the old image URLs still resolve.
`tools/optimize-images.py` caps them at 1600px and re-encodes; some PNGs of photographs
become JPEGs, and `localize()` in the importer follows the changed extension. Run the
optimizer first, then the importer, so `width`/`height` match the files on disk.

`tools/imported-images.json` maps each externally hosted image URL to its local copy. When
regenerating it, match on the filename *stem* — the optimizer changes extensions, so an
exact-path check silently drops those entries and the pages fall back to hotlinking.

Two images can't be imported: `login.truste.com` 404s, and two `talktomel.com` files
(`van-driving-away`, `person-sorting-mail`) were never crawled by the Wayback Machine —
talktomel.com itself now redirects every path to the homepage. They are listed in
`DEAD_IMAGES` in the importer and dropped from the output, keeping their captions. If the
originals turn up, drop them into `content/images/imported/talktomel/`, remove the entries,
and rebuild. Everything else from talktomel was recovered from the archive's capture of
`blog.talktomel.com`, the blog's earlier home.

The homepage `#resources` section lists all 27 articles as three themed shelves of nine. It
is deliberately sized to that count — no pagination, no "view all". Adding an article means
placing it on a shelf by hand and rebalancing.

### Hosting

GitHub Pages serves the repository root of `main` directly — pushing to `main` publishes.

`CNAME` pins the custom domain to **`www.reducemail.org`**, and that is the canonical
host: every page's `<link rel="canonical">` and `og:url` uses it, and GitHub redirects the
apex `reducemail.org` to it. Keep new pages on `www` too — a canonical pointing at the
apex would fight the redirect and split the page's search signals.

`.nojekyll` turns off Jekyll processing. Without it Jekyll would try to build the site and
`blog/*.md` would be rendered as pages rather than left as the source files they are.

`sitemap.xml` is committed, not generated at deploy time — regenerate and commit it after
adding or removing a page:

    python3 tools/build-sitemap.py

It reads each page's canonical tag, so a page missing one is skipped and reported. `404.html`
is skipped by design: it carries `noindex` and no canonical. `robots.txt` points crawlers at
the sitemap and keeps them out of `blog/` and `tools/`.

## Core Design Principles
1. **Free-first framing** — every page reinforces this is free, public, and community-driven
2. **Trust over urgency** — calm, reassuring tone; avoid pushy CTAs or artificial deadlines
3. **Accessibility** — high contrast, readable typography, simple navigation
4. **Privacy-respecting** — no tracking scripts, no analytics by default, minimal external dependencies

## When Creating Content
- Follow the design system in [`docs/design-system.md`](docs/design-system.md) for colors, typography, spacing, and components
- Use primary accent color (`#FF6B8A`) sparingly for main actions only
- Keep copy conversational, benefit-forward, and sourced where applicable (FTC, DMA, USPS)
- Prefer flat/semi-flat illustrations over photography
- Never introduce monetization language, pricing tiers, or subscription framing

## Common Page Types
| Type | Location Pattern | Key Components |
|------|------------------|----------------|
| Homepage | `pages/index.html` or root | Hero intro, featured resources, value prop, donation banner |
| Guide / Article | `pages/guides/*.html` or `/guides/` | Reading column, TOC, callouts, inline downloads |
| Template Generator | `pages/generator/*.html` | Form inputs, live preview, download actions |
| Directory | `pages/directory/*.html` or `/directory/` | Searchable table, filters, expandable rows |
| FAQ | `pages/faq/*.html` | Collapsible Q&A sections, related links |

## Tone Checklist
✅ Conversational but not silly  
✅ Leads with action/benefit  
✅ Acknowledges frustration without dwelling on it  
✅ Sources claims (FTC, DMA, USPS, etc.)  

❌ Upselling or subscription language  
❌ Gated content or "sign up to continue"  
❌ Artificial urgency ("act now! limited time!")  
❌ Corporate or salesy phrasing  
