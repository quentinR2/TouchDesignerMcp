"""Smoke test: spawn the MCP server over stdio and verify all tools register.

Does not require TouchDesigner — only exercises the MCP layer.
"""

import subprocess
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {
    "create_node",
    "delete_node",
    "rename_node",
    "copy_node",
    "get_node_info",
    "list_nodes",
    "get_parameter",
    "set_parameter",
    "list_parameters",
    "connect_nodes",
    "disconnect_nodes",
    "create_network",
    "export_network",
    "search_nodes",
    "set_node_position",
    "save_project",
    "get_project_info",
    "get_errors",
    "execute_script",
}


def test_server_lists_all_tools():
    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "touchdesigner_mcp"])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return {t.name for t in result.tools}

    tool_names = anyio.run(run)
    assert tool_names == EXPECTED_TOOLS


def test_bridge_script_importable():
    import touchdesigner_mcp.bridge_script as bridge

    assert set(bridge.HANDLERS) == EXPECTED_TOOLS
    assert callable(bridge.handle_request)
    assert callable(bridge.onHTTPRequest)


def test_checked_in_bridge_has_dev_placeholder():
    # Real versions are stamped by the release workflow from the git tag; the
    # repo copy must stay on the deterministic placeholder or CI's staleness
    # check would churn.
    import touchdesigner_mcp.bridge_script as bridge

    assert bridge.BRIDGE_VERSION == "0.0.0.dev0"


def test_build_bridge_stamps_explicit_version(tmp_path):
    out = tmp_path / "bridge.py"
    root = Path(__file__).parent.parent
    subprocess.run(
        [sys.executable, str(root / "scripts" / "build_bridge.py"), "--version", "9.9.9", "--output", str(out)],
        check=True,
    )
    text = out.read_text(encoding="utf-8")
    assert 'BRIDGE_VERSION = "9.9.9"' in text
    assert "# Bridge version: 9.9.9" in text
