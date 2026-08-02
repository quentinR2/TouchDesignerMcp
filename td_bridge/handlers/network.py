from fnmatch import fnmatch


def handle_create_network(params):
    parent_path = params.get("parent_path", "/project1")
    nodes_spec = params.get("nodes", [])
    connections_spec = params.get("connections", [])

    if not nodes_spec:
        raise ValueError("nodes list is required and cannot be empty")

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Parent container not found: {parent_path}")

    created_nodes = []
    node_map = {}

    # Phase 1: Create nodes
    for i, spec in enumerate(nodes_spec):
        node_type = spec.get("type")
        node_name = spec.get("name")
        if not node_type or not node_name:
            raise ValueError(f"Node at index {i} requires 'type' and 'name'. Got: {spec}")

        try:
            new_node = parent.create(node_type, node_name)
        except Exception as e:
            return {"success": False, "error": f"Failed to create '{node_name}' (type={node_type}): {e}", "created_so_far": created_nodes}

        if "x" in spec:
            new_node.nodeX = spec["x"]
        if "y" in spec:
            new_node.nodeY = spec["y"]

        for pname, pvalue in spec.get("params", {}).items():
            par = getattr(new_node.par, pname, None)
            if par is not None:
                par.val = pvalue

        node_map[node_name] = new_node
        created_nodes.append({"name": new_node.name, "type": new_node.type, "path": new_node.path})

    # Phase 2: Wire connections
    created_connections = []
    for i, conn in enumerate(connections_spec):
        src_name = conn.get("source")
        tgt_name = conn.get("target")
        out_idx = conn.get("output_index", 0)
        in_idx = conn.get("input_index", 0)

        if not (isinstance(src_name, str) and src_name and isinstance(tgt_name, str) and tgt_name):
            return {"success": False, "error": f"Connection at index {i} requires non-empty string 'source' and 'target'. Got: {conn}", "created_nodes": created_nodes, "created_connections": created_connections}

        src_node = node_map.get(src_name) or (op(f"{parent_path}/{src_name}") if not src_name.startswith("/") else op(src_name))
        tgt_node = node_map.get(tgt_name) or (op(f"{parent_path}/{tgt_name}") if not tgt_name.startswith("/") else op(tgt_name))

        if src_node is None:
            return {"success": False, "error": f"Connection source '{src_name}' not found", "created_nodes": created_nodes, "created_connections": created_connections}
        if tgt_node is None:
            return {"success": False, "error": f"Connection target '{tgt_name}' not found", "created_nodes": created_nodes, "created_connections": created_connections}

        try:
            tgt_node.inputConnectors[in_idx].connect(src_node.outputConnectors[out_idx])
            created_connections.append({"source": src_node.path, "target": tgt_node.path, "output_index": out_idx, "input_index": in_idx})
        except Exception as e:
            return {"success": False, "error": f"Failed to connect {src_name} → {tgt_name}: {e}", "created_nodes": created_nodes, "created_connections": created_connections}

    return {
        "success": True,
        "created_nodes": created_nodes,
        "created_connections": created_connections,
        "message": f"Created {len(created_nodes)} nodes and {len(created_connections)} connections",
    }


def handle_export_network(params):
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

            node_params = {}
            for p in child.pars():
                try:
                    val = p.eval()
                    if str(val) != str(p.default):
                        node_params[p.name] = str(val)
                except Exception:
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

            for i, conn in enumerate(child.inputConnectors):
                for c in conn.connections:
                    source = c.owner
                    source_idx = next(
                        (j for j, oc in enumerate(source.outputConnectors) if any(cc.owner == child for cc in oc.connections)),
                        0
                    )
                    connections.append({"source": source.name, "target": child.name, "output_index": source_idx, "input_index": i})

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


def handle_search_nodes(params):
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
                results.append({"name": child.name, "type": child.type, "path": child.path, "family": child.family})
            if recursive and hasattr(child, 'children'):
                search(child)

    search(parent)
    return {"success": True, "pattern": pattern, "parent": parent_path, "count": len(results), "nodes": results}


def handle_set_node_position(params):
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
