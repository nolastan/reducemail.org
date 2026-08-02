---
name: postal-unsubscribe-design-system
description: Design system for ReduceMail.org — a free resource site helping people stop unwanted physical junk mail. Defines the visual language, tokens, component patterns, and layout principles for any page or screen on this site.
---

# ReduceMail.org — Design System

A design system for **ReduceMail.org**, a free public resource that helps people opt out of physical junk mail. Use this skill whenever creating or editing screens, pages, or components for this site.

## Brand Personality

Friendly, trustworthy, calm, and community-minded. The site reassures visitors that a frustrating problem (unwanted mail) has straightforward solutions they can act on themselves — for free. Visuals should feel helpful and light — never aggressive, corporate, cluttered, or sales-driven.

## Site Context

- **Not a SaaS product.** There are no accounts, subscriptions, paywalls, or upsells.
- The site is a **free public-resource hub**: guides, templates, opt-out letter generators, mailer contact directories, and educational content.
- Tone is that of a knowledgeable friend or librarian — empowering the visitor to take action themselves.
- Environmental impact and privacy are secondary motivators woven into content, not primary marketing hooks.

## Color Tokens

### Backgrounds
- **Page base:** Off-white (#F8F9FB or similar very light cool gray)
- **Surface:** White (cards, modals, elevated containers)
- **Tinted surface – pink:** Soft blush (#FFF0F3)
- **Tinted surface – blue:** Pale sky (#EAF4FB)
- **Tinted surface – mint:** Light green (#E8FDF5)
- **Tinted surface – lavender:** Soft purple (#F3EEFF)
- **Footer/warm zone:** Soft coral wash (#FFF5F5)

### Foreground
- **Text primary:** Dark navy/charcoal (#1A1A2E)
- **Text secondary:** Medium gray (#5C5C6E)
- **Text muted:** Light gray (#9CA3AF)

### Accent
- **Primary action:** Coral/pink (#FF6B8A) — main buttons, active states, key highlights
- **Secondary action:** Sky blue (#4DA8DA) — links, informational emphasis
- **Success/impact:** Mint (#34D399) — environmental stats, positive outcomes
- **Warning/urgency:** Soft amber (#FBBF24) — deadlines, time-sensitive notices (e.g. "respond within 30 days")

### Borders & Dividers
- **Default border:** Very light gray (#E5E7EB)
- **Accent border:** Primary action at reduced opacity for highlighted cards

## Typography

| Role | Weight | Size | Use |
|------|--------|------|-----|
| Display | Bold | 48–56px | Hero headlines |
| Heading 1 | Bold | 36–40px | Section titles |
| Heading 2 | Semi-bold | 24–28px | Card titles, subsections |
| Heading 3 | Semi-bold | 18–20px | Labels, resource names |
| Body | Regular | 16–18px | Paragraphs, guide content |
| Caption | Medium | 13–14px | Metadata, helper text, sources |
| Kicker | Semi-bold uppercase | 12–13px | Section intros, category labels |

- **Font family:** Geometric or rounded sans-serif (e.g. Inter, Plus Jakarta Sans, or similar)
- **Line height:** 1.5–1.6 for body, 1.2–1.3 for headings
- **Max paragraph width:** ~640px for readability

## Spacing Scale

- **4px** — tight inner gaps (icon-to-label)
- **8px** — compact padding (badges, pills)
- **16px** — default inner spacing
- **24px** — card internal padding
- **32px** — between grouped elements
- **48px** — between sub-sections
- **80–120px** — between major page sections

## Radius Scale

- **4px** — small inputs, tags
- **8px** — buttons, small cards
- **12–16px** — standard cards, containers
- **24px** — large feature cards, hero panels
- **Full (pill)** — pill buttons, badges

## Elevation

- **Level 0:** Flat (tinted backgrounds define boundary)
- **Level 1:** Subtle shadow — `0 1px 3px rgba(0,0,0,0.06)` (cards at rest)
- **Level 2:** Lifted — `0 4px 12px rgba(0,0,0,0.08)` (hover, modals)

## Component Patterns

### Buttons
- **Primary:** Pill-shaped, coral/pink fill, white text, medium padding (12px 24px) — used for actions like "Generate Letter," "Download Template," "Copy to Clipboard"
- **Secondary:** Pill-shaped, white fill with subtle border or ghost, dark text — used for "Learn More," "View Guide"
- **Tertiary / Text link:** Sky-blue underlined text for inline links within body content
- **Hover:** Slight darken + shadow lift
- **Disabled:** 40% opacity, no pointer

### Resource Cards
- White or pastel-tinted fill, rounded corners (12–16px), optional subtle shadow
- Internal structure: optional icon top → title → short description → meta (type: "Guide" / "Template" / "Directory" / "FAQ") → optional action link
- Highlighted card: accent border-left or accent background tint + "Featured" or "New" badge
- Cards link to individual resource pages, guide pages, or download views

### Guide / Article Layout
- Left-aligned reading column (~720px max width) for step-by-step opt-out instructions
- Sticky table of contents on desktop (right sidebar) for multi-step guides
- Inline callout boxes for tips, warnings, and deadlines (see Callouts below)
- Downloadable/template assets embedded inline where relevant

### Callouts
- **Tip (mint tint):** Helpful aside or shortcut
- **Warning (amber tint):** Deadline reminder or common pitfall
- **Info (blue tint):** Additional context or statutory reference
- Compact, rounded (8px), icon + short text, indented from body

### Badges & Pills
- Small rounded containers (full radius), pastel fill + darker matching text
- Used for resource types ("Guide," "Template," "Directory," "FAQ"), difficulty levels, and status indicators

### Step Indicators
- Numbered circles (coral/pink fill, white number) or icon circles
- Connected by dotted/dashed lines or subtle flow arrows
- Horizontal on desktop, vertical stack on narrow layouts
- Used within guides to show opt-out process steps (e.g. "Fill out form → Mail to address → Confirm")

### Letter / Template Generator
- Form-style interface: inputs for sender name/address, mailer name/address, date, opt-out reason
- Live preview pane showing formatted letter in real time
- Primary action: "Download as PDF" or "Copy text"
- Clean, focused layout — minimal surrounding distraction

### Contact Directory Table
- Searchable/filterable table of known junk-mail senders with opt-out methods
- Columns: Company name, Opt-out method (online/phone/mail/email), Link/Address, Notes
- Row hover highlight; expandable detail on click
- Mobile: stacked card layout per entry

### Donation / Support Banner (optional, footer-only)
- Discreet, non-intrusive banner near footer — "ReduceMail.org is a free project. You can support it here."
- Small, muted styling — never prominent or pushy
- Links to external donation page (Ko-fi, OpenCollective, etc.)

### Section Pattern
- Optional kicker (uppercase, muted or accent-colored)
- Heading (H1 or H2)
- Optional subtitle/body paragraph
- Content block (resource cards, guide steps, directory table, generator, illustration)
- Generous vertical padding above and below

## Layout Principles

- **Max content width:** 1200px centered, with comfortable horizontal padding (40–80px)
- **Reading width:** ~720px for guides and articles; full-width for directory and generator
- **Grid:** 12-column on desktop, collapsing to single-column on mobile
- **Alignment:** Center-aligned for hero/intro sections; left-aligned for informational and guide content
- **Whitespace:** Err on the side of more — breathing room builds trust
- **Visual hierarchy:** One focal point per section; use size, color, and spacing to guide the eye top-to-bottom
- **Section rhythm:** Alternate between white and tinted backgrounds to create visual separation without hard dividers

## Imagery & Illustration

- Light, flat or semi-flat illustrations preferred over photography
- Pastel palette consistent with brand colors
- Small decorative elements (mail icons, envelopes, recycling/leaves for eco context) as texture — never dominant
- Data visualizations: simple bar/donut charts with brand accent colors (e.g. "X tons of mail diverted")

## Content Tone

- Conversational but not silly
- Lead with the action or benefit, not the background explanation
- Short sentences, active voice
- Acknowledge the user's frustration without dwelling on it
- Environmental/privacy angles as supporting context, not the primary pitch
- No upselling, no artificial urgency, no gated content
- Attribute sources (FTC, DMA, USPS) where applicable
