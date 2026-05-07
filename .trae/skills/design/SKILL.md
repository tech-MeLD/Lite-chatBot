---
name: "design"
description: "Comprehensive design skill: brand identity, design tokens, UI styling, logo, CIP, slides, banners, icons, and social photos. Invoke for any design task involving brand assets, visual systems, or creative content generation."
---

# Design

Unified design skill: brand, tokens, UI, logo, CIP, slides, banners, social photos, icons.

## When to Use

- Brand identity, voice, assets
- Design system tokens and specs
- UI styling with shadcn/ui + Tailwind
- Logo design and AI generation
- Corporate identity program (CIP) deliverables
- Presentations and pitch decks
- Banner design for social media, ads, web, print
- Social photos for Instagram, Facebook, LinkedIn, Twitter, Pinterest, TikTok

## Sub-skill Routing

| Task | Sub-skill | Details |
|------|-----------|---------|
| Brand identity, voice, assets | `brand` | External skill |
| Tokens, specs, CSS vars | `design-system` | External skill |
| shadcn/ui, Tailwind, code | `ui-styling` | External skill |
| Logo creation, AI generation | Logo | `references/logo-design.md` |
| CIP mockups, deliverables | CIP | `references/cip-design.md` |
| Presentations, pitch decks | Slides | `references/slides.md` |
| Banners, covers, headers | Banner | `references/banner-sizes-and-styles.md` |
| Social media images/photos | Social Photos | `references/social-photos-design.md` |
| SVG icons, icon sets | Icon | `references/icon-design.md` |

## Logo Design

55+ styles, 30 color palettes, 25 industry guides.

```bash
python3 scripts/logo/search.py "tech startup modern" --design-brief -p "BrandName"
python3 scripts/logo/generate.py --brand "BrandName" --style minimalist --industry tech
```

## CIP Design

50+ deliverables, 20 styles, 20 industries.

```bash
python3 scripts/cip/search.py "tech startup" --cip-brief -b "BrandName"
python3 scripts/cip/generate.py --brand "BrandName" --logo /path/to/logo.png --deliverable "business card"
```

## Slides

Strategic HTML presentations with Chart.js, design tokens, copywriting formulas.

Load `references/slides-create.md` for the creation workflow.

## Banner Design

22 art direction styles across social, ads, web, print.

Load `references/banner-sizes-and-styles.md` for complete sizes and styles reference.

## Icon Design

15 styles, 12 categories. SVG output.

```bash
python3 scripts/icon/generate.py --prompt "settings gear" --style outlined
```

## References

| Topic | File |
|-------|------|
| Design Routing | `references/design-routing.md` |
| Logo Design Guide | `references/logo-design.md` |
| CIP Design Guide | `references/cip-design.md` |
| Slides Create | `references/slides-create.md` |
| Banner Sizes | `references/banner-sizes-and-styles.md` |
| Social Photos | `references/social-photos-design.md` |
| Icon Design | `references/icon-design.md` |