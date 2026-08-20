"""Generate touchdesigner_mcp/bridge_script.py — the single-file Web Server DAT callbacks script.

Merges td_bridge/handlers/*.py and td_bridge/router.py into one self-contained
file that users paste into a Web Server DAT's callbacks DAT. Run from anywhere:

    python scripts/build_bridge.py

The generated file is checked into git and shipped inside the touchdesigner-mcp
wheel (exposed via the `touchdesigner-mcp bridge` CLI subcommand). CI fails if
it is stale.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HANDLER_MODULES = ["nodes", "parameters", "connections", "network", "project"]
OUTPUT = ROOT / "touchdesigner_mcp" / "bridge_script.py"

# Stamp for the checked-in copy. Real versions come from git tags: the release
# workflow regenerates the script with --version <tag> before building, so only
# release artifacts carry a concrete version. Keeps the repo copy deterministic
# (CI diffs it) with no version to bump anywhere.
DEV_VERSION = "0.0.0.dev0"

HEADER = '''\
# =============================================================================
# TouchDesigner MCP Bridge — Web Server DAT callbacks (self-contained)
# =============================================================================
#
# Bridge version: {version}
# Release downloads are stamped to match the touchdesigner-mcp package version;
# 0.0.0.dev0 is the in-repo placeholder (grab a stamped copy from a GitHub
# release, or `touchdesigner-mcp bridge` from an installed package).
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
    parser = argparse.ArgumentParser(description="Generate the single-file TD bridge script.")
    parser.add_argument(
        "--version",
        default=DEV_VERSION,
        help=f"Version to stamp into the script (release builds pass the tag; default: {DEV_VERSION})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Where to write the generated script (default: touchdesigner_mcp/bridge_script.py)",
    )
    args = parser.parse_args()

    version = args.version
    all_imports: list[str] = []
    sections: list[str] = []
    seen_names: set[str] = {"BRIDGE_VERSION"}

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
    args.output.write_text("".join(parts), encoding="utf-8", newline="\n")
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes, {len(seen_names)} top-level names, version {version})")


if __name__ == "__main__":
    main()
