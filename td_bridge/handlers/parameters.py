def handle_get_parameter(params):
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


def handle_set_parameter(params):
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


def handle_list_parameters(params):
    from fnmatch import fnmatch

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
