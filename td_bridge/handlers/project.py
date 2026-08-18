import io
import sys


def handle_save_project(params):
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

    return {"success": True, "saved_to": saved_to, "message": f"Project saved to {saved_to}"}


def handle_get_project_info(params):
    return {
        "success": True,
        "bridge_version": globals().get("BRIDGE_VERSION"),
        "project": {
            "name": project.name,
            "folder": project.folder,
            "saveVersion": str(project.saveVersion) if hasattr(project, 'saveVersion') else "unknown",
            "cookRate": project.cookRate,
            "realTime": project.realTime,
        },
    }


def handle_get_errors(params):
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
                entry = {"name": child.name, "type": child.type, "path": child.path}
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


def handle_execute_script(params):
    script = params.get("script")
    parent_path = params.get("parent_path", "/project1")

    if not script:
        raise ValueError("script is required")

    parent = op(parent_path)
    if parent is None:
        raise ValueError(f"Parent container not found: {parent_path}")

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        exec(script, {"op": op, "me": parent, "parent": parent, "project": project, "ui": ui})
        output = buffer.getvalue()
    except Exception as e:
        output = buffer.getvalue()
        return {"success": False, "error": str(e), "stdout": output}
    finally:
        sys.stdout = old_stdout

    return {"success": True, "stdout": output, "message": "Script executed successfully"}
