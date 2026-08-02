import json
from touchdesigner_mcp import mcp
from touchdesigner_mcp.client import send_to_td


@mcp.tool()
async def create_node(
    node_type: str,
    node_name: str,
    parent_path: str = "/project1",
) -> str:
    """Create a new operator node in TouchDesigner.

    Args:
        node_type: The operator type, e.g. 'noiseTOP', 'constantCHOP', 'textDAT', 'waveCHOP'.
        node_name: Name for the new node.
        parent_path: Path to the parent container (default: /project1).
    """
    result = await send_to_td("create_node", {
        "node_type": node_type,
        "node_name": node_name,
        "parent_path": parent_path,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def delete_node(node_path: str) -> str:
    """Delete an operator node from TouchDesigner.

    Args:
        node_path: Full path to the node to delete, e.g. '/project1/noise1'.
    """
    result = await send_to_td("delete_node", {"node_path": node_path})
    return json.dumps(result, indent=2)


@mcp.tool()
async def rename_node(node_path: str, new_name: str) -> str:
    """Rename a TouchDesigner node.

    Args:
        node_path: Full path to the node to rename, e.g. '/project1/noise1'.
        new_name: New name for the node.
    """
    result = await send_to_td("rename_node", {
        "node_path": node_path,
        "new_name": new_name,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def copy_node(
    node_path: str,
    destination_path: str = "",
    new_name: str = "",
) -> str:
    """Duplicate a node. Optionally copy to a different container and/or rename.

    Args:
        node_path: Full path to the node to copy.
        destination_path: Container to copy into (default: same parent as source).
        new_name: New name for the copy (default: TD auto-names it).
    """
    result = await send_to_td("copy_node", {
        "node_path": node_path,
        "destination_path": destination_path,
        "new_name": new_name,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_node_info(node_path: str) -> str:
    """Get detailed information about a TouchDesigner node, including type,
    family, inputs, outputs, and position.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
    """
    result = await send_to_td("get_node_info", {"node_path": node_path})
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_nodes(parent_path: str = "/project1") -> str:
    """List all operator nodes inside a TouchDesigner container.

    Args:
        parent_path: Path to the container to list (default: /project1).
    """
    result = await send_to_td("list_nodes", {"parent_path": parent_path})
    return json.dumps(result, indent=2)
