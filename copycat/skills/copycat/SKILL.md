---
name: copycat
description: Captures website design style with Playwright evidence, MCP-managed aliases, and agent-authored DESIGN.md files. Saves, enriches, lists, renames, deletes, and applies saved Copycat profiles to original UI work. Use when the user asks to capture, collect, reuse, or apply a website's visual style.
license: MIT
---

# Copycat

Use this skill to capture the visual language of a website and reuse it as design context for original UI work. The goal is to collect style choices, not clone a website.

The MCP chooses the saved design library root at runtime: `COPYCAT_ROOT` if set, otherwise `~/.copycat/designs`, except legacy installs fall back to `STYLE_MIRROR_ROOT` or `~/.style-mirror/designs` when `~/.copycat/designs` does not exist and the legacy root does. Do not hard-code either root. Use MCP-returned `paths` as the source of truth for reading files and summarizing locations. When the `copycat` MCP is available, use it for alias/library operations instead of mutating this directory by hand.

This skill expects the `copycat` MCP capture tools to be available for browser capture and inspection. They run Python Playwright inside the MCP server so agents do not need Playwright MCP. Do not use Playwright MCP, Playwright CLI, `playwright-cli`, `npx playwright`, shell screenshots, or browser-automation fallbacks for normal Copycat capture.

The agent owns the design judgment. The `copycat_capture_*` tools are only the camera and browser. Do not outsource DESIGN.md authorship to a deterministic script. Use screenshots and page evidence, then write or revise @DESIGN.md yourself.

## Core rule

Mirror the aesthetic system. Do not copy identity.

Extract and reuse typography, color relationships, spacing rhythm, density, surface treatment, component vocabulary, motion feel, and responsive hierarchy. Do not copy logos, brand marks, proprietary assets, exact page structure, exact copy, unique illustrations, or full component replicas.

## MCP/library rule

Use the `copycat` MCP for saved-style library operations when the tools are available:

- `copycat_create` creates alias directories and returns absolute alias paths plus alias-relative suggested screenshot paths.
- `copycat_capture_screenshot` captures one screenshot and registers it under the alias.
- `copycat_capture_snapshot` captures a lightweight DOM snapshot and registers it as evidence.
- `copycat_capture_extract` captures curated structured evidence and registers it as evidence. Supported kinds are `links`, `cssVariables`, and `computedStyles`.
- `copycat_save` writes agent-authored `DESIGN.md`, `tokens.json`, `notes.md`, explicit metadata fields, and screenshot/evidence references after Playwright capture.
- `copycat_get` reads saved aliases for applying or enriching a style.
- `copycat_list`, `copycat_rename`, and `copycat_delete` manage saved aliases.

The Copycat MCP is the archivist and curated camera. The agent is the design judge and must author `DESIGN.md` itself.

Current MCP behavior to account for:

- Aliases must be lowercase slugs matching `^[a-z0-9]+(-[a-z0-9]+)*$`.
- `copycat_create` with `mode: "create"` errors if the alias exists; `mode: "overwrite"` replaces the alias directory.
- Capture tool `path` values must be alias-relative and under `screenshots/` or `evidence/`; absolute paths and reserved root files are rejected.
- Each capture tool immediately registers the artifact and returns a `profile.validation`. Until final `DESIGN.md` and `tokens.json` are saved, `missing_design` and `missing_tokens` are expected and are not capture failures.
- `copycat_save` validates that referenced screenshot/evidence files already exist, merges file lists, and returns the final validation summary.
- `copycat_create` stores `sourceUrl` exactly as passed. If the user-provided URL includes tracking parameters, either intentionally pass a clean same-page canonical URL or record the original/tracking noise in `notes` or `observedNoise`.

## When the user wants to grab a website's design

Capture the site with the Copycat MCP capture tools, autonomously discover a small set of supporting pages, inspect the resulting screenshots, then write the saved design profile under an alias. Read @references/playwright.md and @references/capture-guidelines.md before running capture actions. If the `copycat_capture_*` tools are unavailable, stop and report that Copycat capture is not available in this session.

Prefer this phrasing:

```text
Capture https://linear.app as linear.
```

If the user provides a URL without an alias, suggest a short lowercase domain-based slug before saving. Validate the alias by using `copycat_create`. If the alias already exists, ask whether to enrich the existing style, overwrite it, or choose another alias.

Treat the provided URL as the seed page. After capturing it, discover candidate links from the rendered page and choose enough high-signal same-site pages to understand stable design system choices. Usually this means the seed page plus a few supporting pages; use fewer when the system is clear and more only when pages expose genuinely different reusable patterns. Do not ask the user to provide more links unless bounded discovery fails, all useful pages are blocked, or the site is too ambiguous to sample safely.

Prefer supporting pages linked from primary navigation, footer navigation, hero CTAs, product cards, or major homepage sections. Good targets include pricing, product/features, docs or resources landing pages, customers/showcase pages, forms, and public app-like demos. Usually deprioritize login, signup-only flows, privacy, terms, careers, status, press, isolated blog posts, support articles, cookie walls, bot challenges, and one-off campaign pages unless they are public and reveal a missing reusable pattern.

Keep discovery bounded. This is representative sampling, not a crawler. Stay on the same origin by default. Include a subdomain only when visible page evidence strongly indicates it belongs to the same product design system, such as a docs or app demo subdomain.

Create the alias with `copycat_create`. Use `suggestedScreenshotPaths` as the `path` argument for seed screenshots; these values are alias-relative, such as `screenshots/desktop-fold.png`. Do not pass absolute filesystem paths to `copycat_capture_*`. Use returned `paths.root`, not a guessed `~/.copycat` or `~/.style-mirror` path, when reading saved files after capture or explaining where the alias lives. Do not manually create alias roots unless the MCP is unavailable.

Take the required seed screenshots with `copycat_capture_screenshot`: desktop fold, desktop full page, mobile fold, and mobile full page. Use `copycat_capture_snapshot` for desktop and mobile snapshots. Use `copycat_capture_extract` for `links`, `cssVariables`, and `computedStyles` evidence.

Read the screenshots. Use the captured snapshots, link discovery, CSS variables, and computed styles to guide your reasoning. Keep screenshots under the alias-level `screenshots/` directory. For supporting pages, use `suggestedPageScreenshotPaths` when present, or stable alias-relative names such as `screenshots/pricing-desktop-full.png` and `screenshots/pricing-mobile-full.png`. Store page-specific JSON evidence under `evidence/pages/<short-page-name>/` inside the returned `paths.root`:

```text
<paths.root>/evidence/pages/<short-page-name>/
  computed-styles.json      # optional when the page adds new style signal
  css-variables.json        # optional when variables help explain tokens
```

After capture, use the seed and supporting evidence to author the files below in the returned `paths.root`:

```text
<paths.root>/
  DESIGN.md
  tokens.json
  metadata.json
  notes.md
  screenshots/
    desktop-fold.png
    desktop-full.png
    mobile-fold.png
    mobile-full.png
    pricing-desktop-full.png
    pricing-mobile-full.png
```

Write @DESIGN.md yourself after reviewing the evidence. Use `copycat_save` once to save the design guide, structured tokens, notes, metadata updates, and relative screenshot/evidence paths that were actually created. Ignore expected intermediate `missing_design` or `missing_tokens` validation issues from capture responses; check the validation summary returned by final `copycat_save` before declaring the capture complete. Summarize the important style cues for the user: mood, typography, fonts, primary colors, spacing rhythm, component treatment, and any caveats.

If the capture tools report missing browser binaries, report the MCP environment issue and stop. Do not install CLI tools, switch to Playwright MCP, or use shell-based capture unless the user explicitly changes the workflow.

## When the user wants to apply a saved website's design

Resolve the alias with `copycat_get`. Read @DESIGN.md first. Read @tokens.json when concrete values are needed. Use the screenshots when visual judgment matters, such as density, hero composition, section rhythm, or mobile hierarchy.

Read @references/apply-guidelines.md when applying or reviewing a saved style.

Apply the style to the user's product, not the source website. Keep content, information architecture, components, and naming aligned to the user's project. Use the saved style for typography, spacing, colors, radii, borders, shadows, interaction feel, and visual density.

User overrides are local unless the user explicitly asks to update the saved style. For example, `Use linear, but warmer` should not mutate `linear`; it should only guide the current output.

## When the user wants to enrich an existing design with even more context

Add more evidence to the existing alias rather than creating a new alias. Resolve the alias with `copycat_get`, then try autonomous discovery from the provided URL or the saved primary source. Capture the best missing page types. Useful enrichment targets include pricing pages, docs pages, dashboard screenshots, mobile nav, forms, empty states, and interaction-heavy pages.

Create a page-specific evidence directory for each enrichment pass. Use `copycat_capture_screenshot` for desktop/mobile full-page supporting captures, then use `copycat_capture_extract` for additional `computedStyles` or `cssVariables` only when the page adds new style signal. Use @references/playwright.md for the curated capture workflow.

After enrichment, revise @DESIGN.md, @tokens.json, metadata, and @notes.md yourself, then use `copycat_save` once with the new screenshot/evidence paths. Check the validation summary returned by `copycat_save`. Explain what changed or what new evidence was added. If the new page appears to be a temporary campaign, cookie wall, or off-brand microsite, call that out instead of overfitting the saved design.

## When the user wants to list the saved styles

Use `copycat_list`. Summarize aliases, source URLs, statuses, confidence, and last updated dates. If no styles exist, suggest capturing one.

## When the user wants to rename an alias

Rename only when the user clearly asks for it. Use `copycat_rename`. If the target alias already exists, stop and ask for a different name. Mention the new alias and updated directory.

## When the user wants to delete an alias

Delete only when the user clearly asks for it. Use `copycat_delete`; the MCP does not require an extra confirmation argument. Mention the deleted alias.

## DESIGN.md writing standards

The generated @DESIGN.md should be useful to an agent, not just a token dump. It must include observed values and judgment rules.

Good:

```text
Reserve the indigo accent for primary CTAs and active states. Do not use it decoratively across large surfaces.
```

Weak:

```text
Primary color: #5e6ad2
```

Use these sections when reviewing or improving a saved @DESIGN.md:

- Visual theme and atmosphere
- Color palette and roles
- Typography rules
- Layout and spacing principles
- Component styling
- Depth, surfaces, borders, and shadows
- Motion and interaction feel
- Responsive behavior
- Do's and don'ts
- Agent application guide
- Source evidence and caveats

Read @references/design-md-guidelines.md before manually revising a saved @DESIGN.md.

## Failure handling

If a site blocks automation, requires login, or renders empty content, say so clearly. Do not invent a design profile from a failed capture. Ask the user for a different public URL, a manually exported screenshot, or permission to try a browser-authenticated flow later.

If the capture is noisy, explain the likely cause and recommend enrichment with better pages. Common noisy sources include cookie banners, popups, campaign pages, A/B tests, pages dominated by third-party embeds, and extraction output dominated by hidden/offscreen utility elements. Link extraction may include empty-text anchors from menus or cards; use screenshots, boxes, same-origin fields, and page judgment rather than link text alone.

## Examples

```text
Capture https://linear.app as linear.
```

Capture the site, save `linear`, and summarize the resulting design profile.

```text
Use linear for this dashboard.
```

Read the saved `linear` profile and apply its style to the dashboard while keeping the dashboard original.

```text
Deepen linear with https://linear.app/pricing.
```

Add pricing-page evidence to the existing `linear` profile and summarize what changed.

```text
List saved Copycat profiles.
```

Show saved aliases and source metadata.

```text
Rename linear to linear-2026.
```

Rename the alias and update metadata.

## References

- @references/capture-guidelines.md
- @references/playwright.md
- @references/apply-guidelines.md
- @references/design-md-guidelines.md
- @references/legal-boundaries.md
