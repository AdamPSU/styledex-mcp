# Capture guidelines

Use Playwright as the source of truth because it sees the rendered page. Raw HTML and extracted text are not enough for Copycat capture.

Use the MCP-returned `paths` as the source of truth for where artifacts live. Depending on environment and legacy fallback, captures may be under `~/.copycat/designs` or `~/.style-mirror/designs`; do not assume either root.

Capture both values and evidence:

- desktop fold screenshot
- desktop full-page screenshot
- mobile fold screenshot
- mobile full-page screenshot
- visible DOM computed styles
- CSS variables from `:root`
- typography values
- color values and roles
- spacing, radii, borders, and shadows
- component samples for buttons, cards, and inputs
- transition and animation hints

Prefer public, design-rich pages. Homepages, pricing pages, docs landing pages, and product overview pages usually capture more style signal than legal pages, changelogs, or blog posts.

## Autonomous page sampling

When the user provides one URL, treat it as a seed and autonomously discover supporting pages. Choose representative pages that reveal stable design system choices across the site. Capture enough evidence to understand the system: usually the seed page plus a few high-signal supporting pages, fewer when patterns are already clear, and more only when pages expose genuinely different reusable patterns.

Prefer pages linked from:

- primary navigation
- footer navigation
- hero CTAs
- product or feature cards
- major homepage sections

Prefer page types that expose reusable design decisions:

- pricing
- product/features
- docs or resources landing
- customers/showcase
- public demos or app-like flows
- forms and interaction-heavy pages

Usually deprioritize pages that add noise rather than style signal, unless a public page reveals a missing reusable pattern:

- login or signup-only flows
- privacy, terms, status, careers, and press pages
- isolated blog or support articles
- cookie walls, bot challenges, and modal-dominated pages
- one-off launch campaigns or microsites

Stay on the same origin by default. Include subdomains only when visible page evidence strongly suggests the subdomain shares the same product design system. Do not crawl the full site. If discovery yields too many candidates, pick the pages with the strongest design-system signal and document the selection rationale in @metadata.json or @notes.md. If discovery is sparse, inspect visible navigation interactions, mobile menus, hero CTAs, footer links, sitemap-like pages, and route cards before asking the user for more URLs.

Avoid overfitting to:

- cookie banners
- popups
- temporary launch campaigns
- third-party widgets
- isolated hero illustrations
- ad units
- one-off embedded content

If the capture looks noisy, enrich with another URL rather than guessing.

When multiple pages disagree, separate stable system-wide choices from page-specific decoration. Use repeated patterns across pages as higher-confidence evidence. Treat single-page flourishes as caveats unless they are central to the source site's visual identity.

## MCP extraction caveats

The MCP capture tools are non-interactive. They cannot dismiss cookie banners, open dropdown menus, click tabs, fill forms, or capture hover/focus states. If those states matter, record the gap as a caveat or ask whether to extend the MCP capture API.

`links` extraction can include empty-text anchors, large card anchors, and menu candidates. Choose supporting pages by combining `href`, `sameOrigin`, `inHeader`, `inFooter`, link boxes, screenshots, and design judgment.

`computedStyles` and snapshots sample DOM order and may include hidden, zero-size, or offscreen utility elements. Filter extracted values against screenshots before treating them as design tokens.

Capture responses may show `missing_design` and `missing_tokens` in validation until the final profile is saved. Treat final `copycat_save` validation as the completion check.

Default viewports:

- desktop: `1440x1000`
- mobile: `390x844`

Do not treat screenshots as assets to copy. Use them as evidence for rhythm, hierarchy, density, and responsive behavior.
