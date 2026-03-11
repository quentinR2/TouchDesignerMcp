def handle_connect_nodes(params):
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
        raise ValueError(f"Source {source_path} has no output index {output_index} (has {len(source.outputConnectors)})")
    if input_index >= len(target.inputConnectors):
        raise ValueError(f"Target {target_path} has no input index {input_index} (has {len(target.inputConnectors)})")

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
    target_path = params.get("target_path")
    input_index = params.get("input_index", 0)

    if not target_path:
        raise ValueError("target_path is required")

    target = op(target_path)
    if target is None:
        raise ValueError(f"Node not found: {target_path}")

    if input_index >= len(target.inputConnectors):
        raise ValueError(f"Node {target_path} has no input index {input_index} (has {len(target.inputConnectors)})")

    connector = target.inputConnectors[input_index]
    if not connector.connections:
        return {"success": True, "message": f"Input {input_index} on {target_path} was already disconnected"}

    connector.disconnect()
    return {
        "success": True,
        "target": target_path,
        "input_index": input_index,
        "message": f"Disconnected input {input_index} on {target_path}",
    }
