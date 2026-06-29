# Contributing

## Local Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m playwright install chromium
```

## Validation

Run the full local checks before submitting changes:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m mypy
```

For package smoke testing, install the current checkout as a persistent uv tool:

```bash
uv tool install .
```

The installed command is `copycat-mcp`. It is a stdio MCP server, so it waits for an MCP client on stdin when run directly.

## Safety Expectations

Do not write to stdout from server code. stdio MCP uses stdout for protocol messages.

## Release Checklist

1. Run tests and mypy.
2. Build the package with `uv build`.
3. Install the built package in a clean environment.
4. Verify `copycat-mcp` is available as an executable.
5. Verify an MCP client can list the Copycat tools.
6. Publish the package.
