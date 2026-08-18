"""Generate touchdesigner_mcp/bridge_script.py — the single-file Web Server DAT callbacks script.

Merges td_bridge/handlers/*.py and td_bridge/router.py into one self-contained
file that users paste into a Web Server DAT's callbacks DAT. Run from anywhere:

    python scripts/build_bridge.py

The generated file is checked into git and shipped inside the touchdesigner-mcp
wheel (exposed via the `touchdesigner-mcp bridge` CLI subcommand). CI fails if
it is stale.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HANDLER_MODULES = ["nodes", "parameters", "connections", "network", "project"]
OUTPUT = ROOT / "touchdesigner_mcp" / "bridge_script.py"

HEADER = '''\
# =============================================================================
# TouchDesigner MCP Bridge — Web Server DAT callbacks (self-contained)
# =============================================================================
#
# Bridge version: {version} — matches the touchdesigner-mcp package version.
#
# SETUP:
# 1. In TouchDesigner, create a Web Server DAT
#    (right-click network → Add Operator → DAT → Web Server)
# 2. In its parameters: set "Port" to 9980 (or your TD_PORT), turn "Active" ON
# 3. Open its callbacks DAT (the small arrow icon on the Web Server DAT)
# 4. Replace ALL contents of the callbacks DAT with this entire file
#
# That's it — the MCP server (`uvx touchdesigner-mcp`) can now control this
# project. Your .toe file can be saved anywhere; no disk dependencies.
#
# GENERATED FILE — DO NOT EDIT.
# Source of truth: td_bridge/ in https://github.com/quentinR2/TouchDesignerMcp
# Regenerate with: python scripts/build_bridge.py
# =============================================================================

'''

VERSION_CONSTANT = 'BRIDGE_VERSION = "{version}"  # touchdesigner-mcp release this bridge was generated from\n\n'

# TouchDesigner injects its builtins (op, project, ui, ...) into every DAT's
# execution namespace, so no import is needed inside TD. The guard below only
# keeps this file importable outside TD (linting, packaging, tests).
TD_GUARD = '''\
try:
    import td  # noqa: F401 — only exists inside TouchDesigner
    op, project, ui = td.op, td.project, td.ui
except ImportError:
    pass

'''

CALLBACKS = '''\
def onHTTPRequest(webServerDAT, request, response):
    return handle_request(request, response)


# ---------------------------------------------------------------------------
# Unused WebSocket/server callbacks (required by the Web Server DAT)
# ---------------------------------------------------------------------------

def onWebSocketOpen(webServerDAT, client, uri):
    return

def onWebSocketClose(webServerDAT, client):
    return

def onWebSocketReceiveText(webServerDAT, client, data):
    return

def onWebSocketReceiveBinary(webServerDAT, client, data):
    return

def onWebSocketReceivePing(webServerDAT, client, data):
    return

def onWebSocketReceivePong(webServerDAT, client, data):
    return

def onServerStart(webServerDAT):
    return

def onServerStop(webServerDAT):
    return
'''


def read_version() -> str:
    """Package version from pyproject.toml (regex keeps this runnable on 3.10, no tomllib)."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        sys.exit("ERROR: could not find version in pyproject.toml")
    return match.group(1)


def split_source(text: str) -> tuple[list[str], str]:
    """Separate top-level import lines from the rest of a module's source."""
    imports, body = [], []
    for line in text.splitlines():
        if re.match(r"^(import|from)\s", line):
            imports.append(line.strip())
        else:
            body.append(line)
    return imports, "\n".join(body).strip("\n")


def top_level_names(body: str) -> set[str]:
    """Names defined at module top level (defs, classes, assignments)."""
    names = set(re.findall(r"^(?:def|class)\s+(\w+)", body, re.MULTILINE))
    names |= set(re.findall(r"^(\w+)\s*=", body, re.MULTILINE))
    return names


def main() -> None:
    version = read_version()
    all_imports: list[str] = []
    sections: list[str] = []
    seen_names: set[str] = set()

    sources = [ROOT / "td_bridge" / "handlers" / f"{m}.py" for m in HANDLER_MODULES]
    sources.append(ROOT / "td_bridge" / "router.py")

    for path in sources:
        imports, body = split_source(path.read_text(encoding="utf-8"))
        for imp in imports:
            if "td_bridge" in imp:
                continue  # inter-module imports disappear in the merged file
            if imp not in all_imports:
                all_imports.append(imp)

        if path.name == "router.py":
            # Handlers become same-module functions: nodes.handle_x → handle_x
            body = re.sub(
                r"\b(?:%s)\.(handle_\w+)" % "|".join(HANDLER_MODULES),
                r"\1",
                body,
            )

        names = top_level_names(body)
        clash = names & seen_names
        if clash:
            sys.exit(f"ERROR: top-level name collision merging {path.name}: {sorted(clash)}")
        seen_names |= names

        sections.append(f"# --- from td_bridge/{path.relative_to(ROOT / 'td_bridge').as_posix()} ---\n\n{body}")

    parts = [
        HEADER.format(version=version),
        VERSION_CONSTANT.format(version=version),
        "\n".join(all_imports) + "\n\n",
        TD_GUARD,
        "\n\n\n".join(sections) + "\n\n\n",
        CALLBACKS,
    ]
    OUTPUT.write_text("".join(parts), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size} bytes, {len(seen_names)} top-level names)")


if __name__ == "__main__":
    main()
