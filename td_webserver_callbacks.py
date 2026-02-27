# =============================================================================
# TouchDesigner MCP Bridge — Web Server DAT Callbacks
# =============================================================================
#
# SETUP INSTRUCTIONS:
# 1. In TouchDesigner, create a "Web Server DAT" (right-click → Add Operator → DAT → Web Server)
# 2. In the Web Server DAT parameters:
#    - Set "Port" to 9980
#    - Make sure "Active" is ON
# 3. Click the small arrow icon on the Web Server DAT to open its callbacks DAT
# 4. Replace ALL contents of the callbacks DAT with this entire script
# 5. The bridge is now running — the MCP server can send commands to TD
#
# =============================================================================

import json


def onHTTPRequest(webServerDAT, request, response):
    """Handle incoming HTTP requests from the MCP server."""

    # Only accept POST requests
    if request['method'] != 'POST':
        response['statusCode'] = 405
        response['statusReason'] = 'Method Not Allowed'
        response['data'] = json.dumps({"error": "Only POST requests are supported"})
        return response

    # Parse JSON body
    try:
        body = json.loads(request['data'])
    except (json.JSONDecodeError, TypeError):
        response['statusCode'] = 400
        response['statusReason'] = 'Bad Request'
        response['data'] = json.dumps({"error": "Invalid JSON body"})
        return response

    action = body.get("action", "")
    params = body.get("params", {})

    # Route to handler
    handlers = {
        "create_node": handle_create_node,
        "list_nodes": handle_list_nodes,
        "set_parameter": handle_set_parameter,
    }

    handler = handlers.get(action)
    if not handler:
        response['statusCode'] = 400
        response['statusReason'] = 'Bad Request'
        response['data'] = json.dumps({"error": f"Unknown action: {action}. Available: {list(handlers.keys())}"})
        return response

    try:
        result = handler(params)
        response['statusCode'] = 200
        response['statusReason'] = 'OK'
        response['data'] = json.dumps(result)
    except Exception as e:
        response['statusCode'] = 500
        response['statusReason'] = 'Internal Server Error'
        response['data'] = json.dumps({"error": str(e)})

    return response


# ---------------------------------------------------------------------------
# Action handlers
# ---------------------------------------------------------------------------

def handle_create_node(params):
    """Create a new operator node."""
    node_type = params.get("node_type")
    node_name = params.get("node_name")
    parent_path = params.get("parent_path", "/project1")

    if not node_type:
        raise ValueError("node_type is required")
    if not node_name:
        raise ValueError("node_name is required")

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Parent container not found: {parent_path}")

    new_node = parent.create(node_type, node_name)

    return {
        "success": True,
        "node": {
            "name": new_node.name,
            "type": new_node.type,
            "path": new_node.path,
            "family": new_node.family,
        },
        "message": f"Created {new_node.type} '{new_node.name}' at {new_node.path}",
    }


def handle_list_nodes(params):
    """List all children of a container."""
    parent_path = params.get("parent_path", "/project1")

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Container not found: {parent_path}")

    nodes = []
    for child in parent.children:
        nodes.append({
            "name": child.name,
            "type": child.type,
            "path": child.path,
            "family": child.family,
        })

    return {
        "success": True,
        "parent": parent_path,
        "count": len(nodes),
        "nodes": nodes,
    }


def handle_set_parameter(params):
    """Set a parameter on a node."""
    node_path = params.get("node_path")
    param_name = params.get("param_name")
    value = params.get("value")

    if not node_path:
        raise ValueError("node_path is required")
    if not param_name:
        raise ValueError("param_name is required")
    if value is None:
        raise ValueError("value is required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    par = getattr(node.par, param_name, None)
    if par is None:
        # List available parameters to help the user
        available = [p.name for p in node.pars()]
        raise ValueError(f"Parameter '{param_name}' not found on {node_path}. Available: {available}")

    old_value = par.eval()
    par.val = value

    return {
        "success": True,
        "node": node_path,
        "parameter": param_name,
        "old_value": str(old_value),
        "new_value": str(par.eval()),
        "message": f"Set {node_path}.par.{param_name} = {value}",
    }


# ---------------------------------------------------------------------------
# Other DAT callbacks (unused but required by TD)
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
