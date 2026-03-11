def handle_create_node(params):
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


def handle_delete_node(params):
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    node_name, node_type = node.name, node.type
    node.destroy()
    return {
        "success": True,
        "message": f"Deleted {node_type} '{node_name}' at {node_path}",
    }


def handle_rename_node(params):
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


def handle_copy_node(params):
    node_path = params.get("node_path")
    destination_path = params.get("destination_path", "")
    new_name = params.get("new_name", "")

    if not node_path:
        raise ValueError("node_path is required")

    source = op(node_path)
    if source is None:
        raise ValueError(f"Node not found: {node_path}")

    dest = op(destination_path) if destination_path else source.parent()
    if dest is None:
        raise ValueError(f"Destination container not found: {destination_path}")

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


def handle_get_node_info(params):
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = op(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    inputs = []
    for i, conn in enumerate(node.inputConnectors):
        connected = [{"name": c.owner.name, "path": c.owner.path} for c in conn.connections]
        inputs.append({"index": i, "connections": connected})

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


def handle_list_nodes(params):
    parent_path = params.get("parent_path", "/project1")

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Container not found: {parent_path}")

    nodes = [
        {"name": child.name, "type": child.type, "path": child.path, "family": child.family}
        for child in parent.children
    ]
    return {
        "success": True,
        "parent": parent_path,
        "count": len(nodes),
        "nodes": nodes,
    }
