# =============================================================================
# TouchDesigner MCP Bridge — Web Server DAT Callbacks (thin stub)
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
# NOTE: The actual handler logic lives in td_bridge/ (Python package).
# TouchDesigner imports it via project.folder added to sys.path below.
# If you edit td_bridge/ files, re-paste this script to force a module reload.
# =============================================================================

import sys
import importlib

# Add the project folder to sys.path so TD can import the td_bridge package.
# project.folder is a TouchDesigner global — it's the directory of the .toe file.
_project_folder = "C:\\Users\\UF434QRO\\Documents\\TouchDesigner"
if _project_folder not in sys.path:
    sys.path.insert(0, _project_folder)

# Reload to pick up any code changes since last paste.
import td_bridge.handlers.nodes
import td_bridge.handlers.parameters
import td_bridge.handlers.connections
import td_bridge.handlers.network
import td_bridge.handlers.project
import td_bridge.router

for _mod in [
    td_bridge.handlers.nodes,
    td_bridge.handlers.parameters,
    td_bridge.handlers.connections,
    td_bridge.handlers.network,
    td_bridge.handlers.project,
    td_bridge.router,
]:
    importlib.reload(_mod)

# Inject TouchDesigner globals into handler modules
for _mod in [
    td_bridge.handlers.nodes,
    td_bridge.handlers.parameters,
    td_bridge.handlers.connections,
    td_bridge.handlers.network,
    td_bridge.handlers.project,
]:
    _mod.op = op
    _mod.project = project
    _mod.ui = ui

from td_bridge.router import handle_request


def onHTTPRequest(webServerDAT, request, response):
    return handle_request(request, response)


# ---------------------------------------------------------------------------
# Unused WebSocket callbacks (required by TD)
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

