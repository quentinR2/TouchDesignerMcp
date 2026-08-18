# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`touchdesigner-mcp` — a published PyPI package providing an MCP server that lets AI clients control TouchDesigner. Two halves connected over HTTP:

```
MCP client ←— stdio/MCP —→ touchdesigner_mcp (this package) ←— HTTP :9980 —→ TouchDesigner (Web Server DAT running the bridge script)
```

## Commands

```bash
uv venv && uv pip install -e .[dev]    # setup (or pip install -e .[dev])
pytest                                  # run tests — no TouchDesigner needed
pytest tests/test_smoke.py::test_server_lists_all_tools   # single test
python scripts/build_bridge.py          # regenerate the bridge script (REQUIRED after editing td_bridge/)
```

There is no linter configured. CI (`.github/workflows/ci.yml`) runs `build_bridge.py` + `git diff --exit-code` to fail if the generated bridge is stale, then pytest on Python 3.10 and 3.12.

## Architecture

**Two mirrored halves, one action namespace.** Every tool exists in both places, matched by action name (e.g. `create_node`):

- `touchdesigner_mcp/tools/*.py` — MCP-server side. Each module registers tools with `@mcp.tool()` (FastMCP instance defined in `touchdesigner_mcp/__init__.py`); each tool just calls `send_to_td(action, params)` (`client.py`), which POSTs `{"action": ..., "params": ...}` to the Web Server DAT.
- `td_bridge/handlers/*.py` — TouchDesigner side. `td_bridge/router.py` maps action names to `handle_<action>` functions in its `HANDLERS` dict. These run *inside* TD and use TD builtins (`op`, `project`, `ui`) that TD injects — they are not importable-clean Python.

Module names mirror each other: `tools/nodes.py` ↔ `handlers/nodes.py`, and likewise for `parameters`, `connections`, `network`, `project`.

**Generated file — never edit directly:** `touchdesigner_mcp/bridge_script.py` is produced by `scripts/build_bridge.py`, which concatenates `td_bridge/handlers/*` + `router.py` into one self-contained file users paste into a Web Server DAT callbacks DAT. It's checked into git and shipped in the wheel (`touchdesigner-mcp bridge` CLI subcommand prints it). Because all modules merge into one namespace, top-level names must be unique across all `td_bridge` files — the build script errors on collisions.

**Adding a tool** touches four places: a handler in `td_bridge/handlers/`, an entry in `HANDLERS` in `td_bridge/router.py`, an `@mcp.tool()` function in `touchdesigner_mcp/tools/`, `EXPECTED_TOOLS` in `tests/test_smoke.py` — then regenerate the bridge and update the tool table in README.md.

**Config:** endpoint resolution in `config.py`, precedence `--url` > `--host`/`--port` > `TD_URL` > `TD_HOST`/`TD_PORT` > `http://127.0.0.1:9980`. CLI flags mutate `config.TD_URL` at startup, so always read it as `config.TD_URL` at call time — never `from touchdesigner_mcp.config import TD_URL`.

**Tests** (`tests/test_smoke.py`) exercise only the MCP layer: spawn the server over stdio and assert the tool set, and import the generated bridge to assert `HANDLERS` matches. Bridge handler logic can only be truly tested inside TouchDesigner (re-paste the regenerated script into the callbacks DAT).

## Releasing

Bump `version` in `pyproject.toml`, tag `vX.Y.Z`, push the tag. GitHub Actions publishes to PyPI (Trusted Publishing) and creates a GitHub release with the bridge script attached. The `.tox` asset is built in TouchDesigner and uploaded manually when the bridge changed.

## TouchDesigner gotchas (when writing bridge/handler code)

- Geometry component create-type is `geometryCOMP`, not `geoCOMP`; it spawns with a default torus SOP inside.
- A CHOP-to-TOP takes its source via its `chop` parameter, not an input wire.
- A Feedback TOP errors until an input is wired.
- On Windows, ports can silently fall into reserved ranges (`netsh interface ipv4 show excludedportrange protocol=tcp`) — a known cause of "Failed to start server" on the Web Server DAT.
