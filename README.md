# StyleDex MCP

StyleDex gives your coding agent a place to keep design references.

Point an MCP client at a site, give it an alias, and StyleDex saves the screenshots and evidence an agent needs to describe the style: DOM snapshots, CSS variables, computed styles, notes, design guidance, and tokens. Later, the agent can pull that profile back by name and use it as direction for new UI.

This avoids your agent reinventing the wheel on every new project. The agent can inspect a saved profile instead of relying on a one-time page description from an old session.

## How it works

A typical capture can start with one sentence:

1. You say: `Save https://linear.app as linear`.
2. Your MCP client routes the request to StyleDex, and the agent calls `styledex_create` to create `~/.styledex/designs/linear/`.
3. The agent captures Linear with Playwright: screenshots, a DOM snapshot, CSS variables, computed styles, and any page evidence it needs.
4. The agent calls `styledex_save` to write `DESIGN.md`, `tokens.json`, `notes.md`, metadata, screenshots, and evidence paths into the `linear` profile.
5. Later, you can say `Use linear as visual direction for this settings page`, and the agent can read the saved profile with `styledex_get` instead of starting over.

Each alias is isolated on disk. A profile for `linear` lives at `~/.styledex/designs/linear/`, and its screenshots stay inside that folder.

## Install

Install the MCP server & Playwright Browser:

```bash
uv tool install styledex-mcp
uvx --from playwright playwright install chromium
```

## Connect an MCP client

Use the installed `styledex-mcp` executable in your MCP client config.

```json
{
  "mcpServers": {
    "styledex": {
      "command": "styledex-mcp"
    }
  }
}
```

For opencode:

```json
{
  "mcp": {
    "styledex": {
      "type": "local",
      "command": ["styledex-mcp"],
      "enabled": true
    }
  }
}
```

Restart your MCP client after changing MCP config.

## Try it

Ask your MCP-aware coding agent for the result you want. You usually do not need to call the tools by hand.

```text
Capture https://vercel.com as a StyleDex profile named vercel.
Save desktop and mobile screenshots, extract CSS variables and computed styles,
then write a concise DESIGN.md with colors, typography, spacing, layout patterns,
component notes, confidence, and caveats.
```

```text
List my saved StyleDex profiles and tell me which one fits a clean B2B SaaS
settings page.
```

```text
Use the vercel StyleDex profile as visual direction for a billing settings page
in this app. Do not copy assets or text. Reuse the spacing, type scale, color
behavior, and component rhythm.
```

```text
Open the vercel StyleDex profile and summarize the design tokens I should use
for a pricing page.
```

If your client exposes raw tools, the usual capture flow is:

```text
styledex_create
styledex_capture_screenshot
styledex_capture_snapshot
styledex_capture_extract
styledex_save
```

## What gets saved

StyleDex writes each profile under:

```text
~/.styledex/designs/<alias>/
```

The important files are:

```text
DESIGN.md       Human-readable design guidance
tokens.json     Structured colors, type, spacing, radii, shadows, and other tokens
notes.md        Additional observations or agent notes
metadata.json   Source URL, status, confidence, pages, caveats, and file index
screenshots/    Captured desktop and mobile screenshots
evidence/       DOM snapshots, links, CSS variables, and computed styles
```

## Storage location

By default, StyleDex stores profiles in:

```text
~/.styledex/designs
```

Set `STYLEDEX_ROOT` to use a different design library root.

For older Style Mirror installs, StyleDex has a legacy fallback. When `STYLEDEX_ROOT` is unset, `~/.styledex/designs` does not exist, and the old root exists, StyleDex reads `STYLE_MIRROR_ROOT` or `~/.style-mirror/designs` so existing captures remain available after the rename.

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m playwright install chromium
```

Run validation:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m mypy
```

Verify the package installs as a persistent tool:

```bash
uv tool install .
uv tool list
```
