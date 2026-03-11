from mcp_server import mcp
import mcp_server.tools  # noqa: F401 — imports all tool modules, registering @mcp.tool() decorators


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
