import json
from touchdesigner_mcp import mcp
from touchdesigner_mcp.client import send_to_td


@mcp.tool()
async def connect_nodes(
    source_path: str,
    target_path: str,
    input_index: int = 0,
    output_index: int = 0,
) -> str:
    """Connect the output of one node to the input of another node.

    Args:
        source_path: Full path to the source node (output side).
        target_path: Full path to the target node (input side).
        input_index: Input connector index on the target node (default: 0).
        output_index: Output connector index on the source node (default: 0).
    """
    result = await send_to_td("connect_nodes", {
        "source_path": source_path,
        "target_path": target_path,
        "input_index": input_index,
        "output_index": output_index,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def disconnect_nodes(target_path: str, input_index: int = 0) -> str:
    """Disconnect a specific input on a node.

    Args:
        target_path: Full path to the node whose input to disconnect.
        input_index: Input connector index to disconnect (default: 0).
    """
    result = await send_to_td("disconnect_nodes", {
        "target_path": target_path,
        "input_index": input_index,
    })
    return json.dumps(result, indent=2)
