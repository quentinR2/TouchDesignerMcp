import argparse
import importlib.resources
import sys

from touchdesigner_mcp import config, mcp
import touchdesigner_mcp.tools  # noqa: F401 — imports all tool modules, registering @mcp.tool() decorators


def main():
    parser = argparse.ArgumentParser(
        prog="touchdesigner-mcp",
        description="MCP server for TouchDesigner (relays tool calls to a Web Server DAT).",
    )
    parser.add_argument("--url", help="Full TouchDesigner endpoint URL (overrides --host/--port and env vars)")
    parser.add_argument("--host", help=f"TouchDesigner host (default: {config.DEFAULT_HOST})")
    parser.add_argument("--port", type=int, help=f"Web Server DAT port (default: {config.DEFAULT_PORT})")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser(
        "bridge",
        help="Print the TouchDesigner Web Server DAT callbacks script to stdout",
    )
    args = parser.parse_args()

    if args.command == "bridge":
        script = importlib.resources.files("touchdesigner_mcp").joinpath("bridge_script.py").read_text(encoding="utf-8")
        # The script is pasted into a DAT or redirected to a file: always emit UTF-8
        # bytes instead of re-encoding with the console codec (cp1252 consoles crash on
        # anything non-ASCII — issue #13).
        sys.stdout.flush()
        sys.stdout.buffer.write(script.encode("utf-8"))
        sys.stdout.buffer.flush()
        return

    # Precedence: --url > --host/--port > TD_URL > TD_HOST/TD_PORT > defaults
    config.TD_URL = config.resolve_url(url=args.url, host=args.host, port=args.port)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
