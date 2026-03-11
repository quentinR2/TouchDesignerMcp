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
import io
import sys
from fnmatch import fnmatch


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
        "delete_node": handle_delete_node,
        "connect_nodes": handle_connect_nodes,
        "disconnect_nodes": handle_disconnect_nodes,
        "get_node_info": handle_get_node_info,
        "get_parameter": handle_get_parameter,
        "rename_node": handle_rename_node,
        "execute_script": handle_execute_script,
        "list_parameters": handle_list_parameters,
        "search_nodes": handle_search_nodes,
        "set_node_position": handle_set_node_position,
        "get_project_info": handle_get_project_info,
        "create_network": handle_create_network,
        "export_network": handle_export_network,
        "save_comp": handle_save_comp,
        "save_project": handle_save_project,
        "get_errors": handle_get_errors,
        "copy_node": handle_copy_node,
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


def handle_delete_node(params):
    """Delete a node."""
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    node_name = node.name
    node_type = node.type
    node.destroy()

    return {
        "success": True,
        "message": f"Deleted {node_type} '{node_name}' at {node_path}",
    }


def handle_connect_nodes(params):
    """Connect output of one node to input of another."""
    source_path = params.get("source_path")
    target_path = params.get("target_path")
    input_index = params.get("input_index", 0)
    output_index = params.get("output_index", 0)

    if not source_path:
        raise ValueError("source_path is required")
    if not target_path:
        raise ValueError("target_path is required")

    source = op(source_path)
    target = op(target_path)
    if source is None:
        raise ValueError(f"Source node not found: {source_path}")
    if target is None:
        raise ValueError(f"Target node not found: {target_path}")

    if output_index >= len(source.outputConnectors):
        raise ValueError(f"Source {source_path} has no output index {output_index} (has {len(source.outputConnectors)} outputs)")
    if input_index >= len(target.inputConnectors):
        raise ValueError(f"Target {target_path} has no input index {input_index} (has {len(target.inputConnectors)} inputs)")

    target.inputConnectors[input_index].connect(source.outputConnectors[output_index])

    return {
        "success": True,
        "source": source_path,
        "target": target_path,
        "output_index": output_index,
        "input_index": input_index,
        "message": f"Connected {source_path}[out:{output_index}] → {target_path}[in:{input_index}]",
    }


def handle_disconnect_nodes(params):
    """Disconnect a specific input on a node."""
    target_path = params.get("target_path")
    input_index = params.get("input_index", 0)

    if not target_path:
        raise ValueError("target_path is required")

    target = op(target_path)
    if target is None:
        raise ValueError(f"Node not found: {target_path}")

    if input_index >= len(target.inputConnectors):
        raise ValueError(f"Node {target_path} has no input index {input_index} (has {len(target.inputConnectors)} inputs)")

    connector = target.inputConnectors[input_index]
    connections = connector.connections
    if not connections:
        return {
            "success": True,
            "message": f"Input {input_index} on {target_path} was already disconnected",
        }

    connector.disconnect()

    return {
        "success": True,
        "target": target_path,
        "input_index": input_index,
        "message": f"Disconnected input {input_index} on {target_path}",
    }


def handle_get_node_info(params):
    """Get detailed info about a node."""
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    # Collect input connections
    inputs = []
    for i, conn in enumerate(node.inputConnectors):
        connected = [{"name": c.owner.name, "path": c.owner.path} for c in conn.connections]
        inputs.append({"index": i, "connections": connected})

    # Collect output connections
    outputs = []
    for i, conn in enumerate(node.outputConnectors):
        connected = [{"name": c.owner.name, "path": c.owner.path} for c in conn.connections]
        outputs.append({"index": i, "connections": connected})

    return {
        "success": True,
        "node": {
            "name": node.name,
            "type": node.type,
            "path": node.path,
            "family": node.family,
            "x": node.nodeX,
            "y": node.nodeY,
            "inputs": inputs,
            "outputs": outputs,
        },
    }


def handle_get_parameter(params):
    """Read a parameter value."""
    node_path = params.get("node_path")
    param_name = params.get("param_name")

    if not node_path:
        raise ValueError("node_path is required")
    if not param_name:
        raise ValueError("param_name is required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    par = getattr(node.par, param_name, None)
    if par is None:
        available = [p.name for p in node.pars()]
        raise ValueError(f"Parameter '{param_name}' not found on {node_path}. Available: {available}")

    return {
        "success": True,
        "node": node_path,
        "parameter": param_name,
        "value": str(par.eval()),
        "default": str(par.default),
        "mode": str(par.mode),
    }


def handle_rename_node(params):
    """Rename a node."""
    node_path = params.get("node_path")
    new_name = params.get("new_name")

    if not node_path:
        raise ValueError("node_path is required")
    if not new_name:
        raise ValueError("new_name is required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    old_name = node.name
    node.name = new_name

    return {
        "success": True,
        "old_name": old_name,
        "new_name": node.name,
        "new_path": node.path,
        "message": f"Renamed '{old_name}' → '{node.name}'",
    }


def handle_execute_script(params):
    """Execute arbitrary Python inside TouchDesigner."""
    script = params.get("script")
    parent_path = params.get("parent_path", "/project1")

    if not script:
        raise ValueError("script is required")

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Parent container not found: {parent_path}")

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        exec(script, {"op": op, "me": parent, "parent": parent, "project": project, "ui": ui})
        output = buffer.getvalue()
    except Exception as e:
        output = buffer.getvalue()
        return {
            "success": False,
            "error": str(e),
            "stdout": output,
        }
    finally:
        sys.stdout = old_stdout

    return {
        "success": True,
        "stdout": output,
        "message": "Script executed successfully",
    }


def handle_list_parameters(params):
    """List all parameters of a node with metadata."""
    node_path = params.get("node_path")
    filter_pattern = params.get("filter_pattern", "*")

    if not node_path:
        raise ValueError("node_path is required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    parameters = []
    for p in node.pars():
        if not fnmatch(p.name, filter_pattern):
            continue
        par_info = {
            "name": p.name,
            "label": p.label,
            "value": str(p.eval()),
            "default": str(p.default),
            "mode": str(p.mode),
            "page": p.page.name if p.page else "",
        }
        # Add range info if available
        if hasattr(p, 'min') and p.min is not None:
            par_info["min"] = str(p.min)
        if hasattr(p, 'max') and p.max is not None:
            par_info["max"] = str(p.max)
        parameters.append(par_info)

    return {
        "success": True,
        "node": node_path,
        "count": len(parameters),
        "parameters": parameters,
    }


def handle_search_nodes(params):
    """Search for nodes by name pattern."""
    pattern = params.get("pattern")
    parent_path = params.get("parent_path", "/project1")
    family_filter = params.get("family", "")
    recursive = params.get("recursive", True)

    if not pattern:
        raise ValueError("pattern is required")

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Container not found: {parent_path}")

    results = []

    def search(container):
        for child in container.children:
            name_match = fnmatch(child.name, pattern) or fnmatch(child.type, pattern)
            family_match = (not family_filter) or (child.family == family_filter)
            if name_match and family_match:
                results.append({
                    "name": child.name,
                    "type": child.type,
                    "path": child.path,
                    "family": child.family,
                })
            if recursive and hasattr(child, 'children'):
                search(child)

    search(parent)

    return {
        "success": True,
        "pattern": pattern,
        "parent": parent_path,
        "count": len(results),
        "nodes": results,
    }


def handle_set_node_position(params):
    """Set the visual position of a node in the network."""
    node_path = params.get("node_path")
    x = params.get("x")
    y = params.get("y")

    if not node_path:
        raise ValueError("node_path is required")
    if x is None or y is None:
        raise ValueError("x and y are required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    old_x, old_y = node.nodeX, node.nodeY
    node.nodeX = x
    node.nodeY = y

    return {
        "success": True,
        "node": node_path,
        "old_position": {"x": old_x, "y": old_y},
        "new_position": {"x": node.nodeX, "y": node.nodeY},
        "message": f"Moved {node_path} from ({old_x}, {old_y}) to ({node.nodeX}, {node.nodeY})",
    }


def handle_get_project_info(params):
    """Get project metadata."""
    return {
        "success": True,
        "project": {
            "name": project.name,
            "folder": project.folder,
            "saveVersion": str(project.saveVersion) if hasattr(project, 'saveVersion') else "unknown",
            "cookRate": project.cookRate,
            "realTime": project.realTime,
        },
    }


def handle_create_network(params):
    """Batch create nodes and connections."""
    parent_path = params.get("parent_path", "/project1")
    nodes_spec = params.get("nodes", [])
    connections_spec = params.get("connections", [])

    if not nodes_spec:
        raise ValueError("nodes list is required and cannot be empty")

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Parent container not found: {parent_path}")

    created_nodes = []
    node_map = {}  # name → created node, for wiring connections

    # Phase 1: Create all nodes
    for i, spec in enumerate(nodes_spec):
        node_type = spec.get("type")
        node_name = spec.get("name")
        if not node_type or not node_name:
            raise ValueError(f"Node at index {i} requires 'type' and 'name'. Got: {spec}")

        try:
            new_node = parent.create(node_type, node_name)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create node '{node_name}' (type={node_type}): {e}",
                "created_so_far": created_nodes,
            }

        # Set position if specified
        if "x" in spec:
            new_node.nodeX = spec["x"]
        if "y" in spec:
            new_node.nodeY = spec["y"]

        # Set parameters if specified
        node_params = spec.get("params", {})
        for pname, pvalue in node_params.items():
            par = getattr(new_node.par, pname, None)
            if par is not None:
                par.val = pvalue

        node_map[node_name] = new_node
        created_nodes.append({
            "name": new_node.name,
            "type": new_node.type,
            "path": new_node.path,
        })

    # Phase 2: Create connections
    created_connections = []
    for conn in connections_spec:
        src_name = conn.get("source")
        tgt_name = conn.get("target")
        out_idx = conn.get("output_index", 0)
        in_idx = conn.get("input_index", 0)

        if src_name not in node_map:
            # Try to find as existing node path
            src_node = op(f"{parent_path}/{src_name}") if not src_name.startswith("/") else op(src_name)
            if src_node is None:
                return {
                    "success": False,
                    "error": f"Connection source '{src_name}' not found in created nodes or project",
                    "created_nodes": created_nodes,
                    "created_connections": created_connections,
                }
        else:
            src_node = node_map[src_name]

        if tgt_name not in node_map:
            tgt_node = op(f"{parent_path}/{tgt_name}") if not tgt_name.startswith("/") else op(tgt_name)
            if tgt_node is None:
                return {
                    "success": False,
                    "error": f"Connection target '{tgt_name}' not found in created nodes or project",
                    "created_nodes": created_nodes,
                    "created_connections": created_connections,
                }
        else:
            tgt_node = node_map[tgt_name]

        try:
            tgt_node.inputConnectors[in_idx].connect(src_node.outputConnectors[out_idx])
            created_connections.append({
                "source": src_node.path,
                "target": tgt_node.path,
                "output_index": out_idx,
                "input_index": in_idx,
            })
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to connect {src_name} → {tgt_name}: {e}",
                "created_nodes": created_nodes,
                "created_connections": created_connections,
            }

    return {
        "success": True,
        "created_nodes": created_nodes,
        "created_connections": created_connections,
        "message": f"Created {len(created_nodes)} nodes and {len(created_connections)} connections",
    }


def handle_export_network(params):
    """Serialize a subnetwork to JSON."""
    parent_path = params.get("parent_path", "/project1")
    recursive = params.get("recursive", False)

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Container not found: {parent_path}")

    nodes = []
    connections = []
    seen_paths = set()

    def export_container(container):
        for child in container.children:
            if child.path in seen_paths:
                continue
            seen_paths.add(child.path)

            # Collect non-default parameters
            node_params = {}
            for p in child.pars():
                try:
                    val = p.eval()
                    if str(val) != str(p.default):
                        node_params[p.name] = str(val)
                except:
                    pass

            nodes.append({
                "name": child.name,
                "type": child.type,
                "path": child.path,
                "family": child.family,
                "x": child.nodeX,
                "y": child.nodeY,
                "params": node_params,
            })

            # Collect input connections
            for i, conn in enumerate(child.inputConnectors):
                for c in conn.connections:
                    source = c.owner
                    source_idx = 0
                    for j, oc in enumerate(source.outputConnectors):
                        if any(cc.owner == child for cc in oc.connections):
                            source_idx = j
                            break
                    connections.append({
                        "source": source.name,
                        "target": child.name,
                        "output_index": source_idx,
                        "input_index": i,
                    })

            if recursive and hasattr(child, 'children'):
                export_container(child)

    export_container(parent)

    return {
        "success": True,
        "parent": parent_path,
        "nodes": nodes,
        "connections": connections,
        "node_count": len(nodes),
        "connection_count": len(connections),
    }


def handle_save_comp(params):
    """Save a component as a .tox file."""
    comp_path = params.get("comp_path", "")
    file_path = params.get("file_path", "")

    if not comp_path:
        raise ValueError("comp_path is required")
    if not file_path:
        raise ValueError("file_path is required")

    comp = op(comp_path)
    if comp is None:
        raise ValueError(f"Component not found: {comp_path}")

    try:
        comp.save(file_path)
    except Exception as e:
        raise ValueError(f"Failed to save component: {e}")

    return {
        "success": True,
        "comp": comp_path,
        "saved_to": file_path,
        "message": f"Component '{comp_path}' saved to {file_path}",
    }


def handle_save_project(params):
    """Save the project."""
    file_path = params.get("file_path", "")

    try:
        if file_path:
            project.save(file_path)
            saved_to = file_path
        else:
            project.save()
            saved_to = project.name
    except Exception as e:
        raise ValueError(f"Failed to save project: {e}")

    return {
        "success": True,
        "saved_to": saved_to,
        "message": f"Project saved to {saved_to}",
    }


def handle_get_errors(params):
    """List all nodes with errors/warnings."""
    parent_path = params.get("parent_path", "/")
    recursive = params.get("recursive", True)
    include_warnings = params.get("include_warnings", True)

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Container not found: {parent_path}")

    error_nodes = []

    def check_node(container):
        for child in container.children:
            errors = child.errors if hasattr(child, 'errors') else ""
            warnings = child.warnings if hasattr(child, 'warnings') else ""

            has_errors = bool(errors)
            has_warnings = bool(warnings) and include_warnings

            if has_errors or has_warnings:
                entry = {
                    "name": child.name,
                    "type": child.type,
                    "path": child.path,
                }
                if has_errors:
                    entry["errors"] = errors
                if has_warnings:
                    entry["warnings"] = warnings
                error_nodes.append(entry)

            if recursive and hasattr(child, 'children'):
                check_node(child)

    check_node(parent)

    return {
        "success": True,
        "parent": parent_path,
        "count": len(error_nodes),
        "nodes": error_nodes,
        "message": f"Found {len(error_nodes)} nodes with issues" if error_nodes else "No errors or warnings found",
    }


def handle_copy_node(params):
    """Duplicate a node."""
    node_path = params.get("node_path")
    destination_path = params.get("destination_path", "")
    new_name = params.get("new_name", "")

    if not node_path:
        raise ValueError("node_path is required")

    source = op(node_path)
    if source is None:
        raise ValueError(f"Node not found: {node_path}")

    if destination_path:
        dest = op(destination_path)
        if dest is None:
            raise ValueError(f"Destination container not found: {destination_path}")
    else:
        dest = source.parent()

    copied = dest.copy(source)

    if new_name:
        copied.name = new_name

    return {
        "success": True,
        "source": node_path,
        "copy": {
            "name": copied.name,
            "type": copied.type,
            "path": copied.path,
        },
        "message": f"Copied {node_path} → {copied.path}",
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
