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
- **Main entry point:** Look for `index.html` or `/pages/home` for the homepage structure.
- **Content types:** Guides, templates, letter generators, directory tables, FAQs, blog posts.

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
