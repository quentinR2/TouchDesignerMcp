import json
from mcp_server import mcp
from mcp_server.client import send_to_td


@mcp.tool()
async def save_project(file_path: str = "") -> str:
    """Save the current TouchDesigner project.

    Args:
        file_path: Optional file path for 'Save As'. If empty, saves to the current file.
    """
    result = await send_to_td("save_project", {"file_path": file_path})
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_project_info() -> str:
    """Get information about the current TouchDesigner project including
    name, file path, FPS, and cook rate."""
    result = await send_to_td("get_project_info", {})
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_errors(
    parent_path: str = "/",
    recursive: bool = True,
    include_warnings: bool = True,
) -> str:
    """List all nodes with cooking errors and/or warnings. Useful for debugging
    after building or modifying networks.

    Args:
        parent_path: Container to check (default: / for entire project).
        recursive: Whether to check recursively (default: True).
        include_warnings: Whether to include warnings in addition to errors (default: True).
    """
    result = await send_to_td("get_errors", {
        "parent_path": parent_path,
        "recursive": recursive,
        "include_warnings": include_warnings,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def execute_script(script: str, parent_path: str = "/project1") -> str:
    """Execute arbitrary Python code inside TouchDesigner. The script runs in
    TD's Python environment with access to all TD APIs (op(), me, etc.).
    Use print() to return output.

    Args:
        script: Python code to execute inside TouchDesigner.
        parent_path: Context path for the script execution (default: /project1).
    """
    result = await send_to_td("execute_script", {
        "script": script,
        "parent_path": parent_path,
    })
    return json.dumps(result, indent=2)
