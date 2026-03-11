import json
from td_bridge.handlers import nodes, parameters, connections, network, project

HANDLERS = {
    "create_node": nodes.handle_create_node,
    "delete_node": nodes.handle_delete_node,
    "rename_node": nodes.handle_rename_node,
    "copy_node": nodes.handle_copy_node,
    "get_node_info": nodes.handle_get_node_info,
    "list_nodes": nodes.handle_list_nodes,
    "get_parameter": parameters.handle_get_parameter,
    "set_parameter": parameters.handle_set_parameter,
    "list_parameters": parameters.handle_list_parameters,
    "connect_nodes": connections.handle_connect_nodes,
    "disconnect_nodes": connections.handle_disconnect_nodes,
    "create_network": network.handle_create_network,
    "export_network": network.handle_export_network,
    "search_nodes": network.handle_search_nodes,
    "set_node_position": network.handle_set_node_position,
    "save_project": project.handle_save_project,
    "get_project_info": project.handle_get_project_info,
    "get_errors": project.handle_get_errors,
    "execute_script": project.handle_execute_script,
}


def handle_request(request, response):
    """Main entry point called from td_webserver_callbacks.py."""
    if request['method'] != 'POST':
        response['statusCode'] = 405
        response['statusReason'] = 'Method Not Allowed'
        response['data'] = json.dumps({"error": "Only POST requests are supported"})
        return response

    try:
        body = json.loads(request['data'])
    except (json.JSONDecodeError, TypeError):
        response['statusCode'] = 400
        response['statusReason'] = 'Bad Request'
        response['data'] = json.dumps({"error": "Invalid JSON body"})
        return response

    action = body.get("action", "")
    params = body.get("params", {})

    handler = HANDLERS.get(action)
    if not handler:
        response['statusCode'] = 400
        response['statusReason'] = 'Bad Request'
        response['data'] = json.dumps({"error": f"Unknown action: '{action}'. Available: {sorted(HANDLERS)}"})
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
