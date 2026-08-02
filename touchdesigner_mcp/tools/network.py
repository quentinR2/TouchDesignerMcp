import json
from touchdesigner_mcp import mcp
from touchdesigner_mcp.client import send_to_td


@mcp.tool()
async def create_network(
    nodes: list[dict],
    connections: list[dict] | None = None,
    parent_path: str = "/project1",
) -> str:
    """Create multiple nodes and connections in one call. The most efficient way
    to build node chains and networks.

    Args:
        nodes: List of node definitions. Each is a dict with:
            - type (str, required): Operator type, e.g. 'noiseTOP', 'levelTOP'
            - name (str, required): Node name
            - params (dict, optional): Parameter name→value pairs to set
            - x (float, optional): Network X position
            - y (float, optional): Network Y position
        connections: List of connections. Each is a dict with:
            - source (str, required): Name of the source node
            - target (str, required): Name of the target node
            - output_index (int, optional, default 0)
            - input_index (int, optional, default 0)
        parent_path: Container to create nodes in (default: /project1).
    """
    result = await send_to_td("create_network", {
        "nodes": nodes,
        "connections": connections or [],
        "parent_path": parent_path,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def export_network(parent_path: str = "/project1", recursive: bool = False) -> str:
    """Export a subnetwork as JSON including all nodes, parameters, positions, and
    connections. The output is compatible with create_network for round-tripping.

    Args:
        parent_path: Container to export (default: /project1).
        recursive: Whether to include nodes in sub-containers (default: False).
    """
    result = await send_to_td("export_network", {
        "parent_path": parent_path,
        "recursive": recursive,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def search_nodes(
    pattern: str,
    parent_path: str = "/project1",
    family: str = "",
    recursive: bool = True,
) -> str:
    """Search for nodes by name or type pattern in the TouchDesigner project.

    Args:
        pattern: Glob pattern to match node names, e.g. 'noise*', '*TOP', '*'.
        parent_path: Container to search in (default: /project1).
        family: Optional filter by family: 'TOP', 'CHOP', 'SOP', 'DAT', 'COMP', or '' for all.
        recursive: Whether to search recursively into sub-containers (default: True).
    """
    result = await send_to_td("search_nodes", {
        "pattern": pattern,
        "parent_path": parent_path,
        "family": family,
        "recursive": recursive,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def set_node_position(node_path: str, x: float, y: float) -> str:
    """Set the visual position of a node in the TouchDesigner network editor.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
        x: Horizontal position in network units.
        y: Vertical position in network units.
    """
    result = await send_to_td("set_node_position", {
        "node_path": node_path,
        "x": x,
        "y": y,
    })
    return json.dumps(result, indent=2)
