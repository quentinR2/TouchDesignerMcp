import json
from mcp_server import mcp
from mcp_server.client import send_to_td


@mcp.tool()
async def get_parameter(node_path: str, param_name: str) -> str:
    """Read the current value of a parameter on a TouchDesigner node.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
        param_name: Parameter name, e.g. 'seed', 'roughness', 'text'.
    """
    result = await send_to_td("get_parameter", {
        "node_path": node_path,
        "param_name": param_name,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def set_parameter(node_path: str, param_name: str, value: str) -> str:
    """Set a parameter value on an existing TouchDesigner node.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
        param_name: Parameter name, e.g. 'seed', 'roughness', 'text'.
        value: New value for the parameter (will be converted to the appropriate type).
    """
    result = await send_to_td("set_parameter", {
        "node_path": node_path,
        "param_name": param_name,
        "value": value,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_parameters(node_path: str, filter_pattern: str = "*") -> str:
    """List all parameters of a TouchDesigner node with their current values,
    types, defaults, and ranges.

    Args:
        node_path: Full path to the node, e.g. '/project1/noise1'.
        filter_pattern: Optional glob pattern to filter parameter names (default: '*').
    """
    result = await send_to_td("list_parameters", {
        "node_path": node_path,
        "filter_pattern": filter_pattern,
    })
    return json.dumps(result, indent=2)
