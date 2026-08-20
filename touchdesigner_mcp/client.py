import importlib.metadata

import httpx

from touchdesigner_mcp import config

try:
    SERVER_VERSION = importlib.metadata.version("touchdesigner-mcp")
except importlib.metadata.PackageNotFoundError:  # running from a checkout without install
    SERVER_VERSION = None

# One-time bridge version handshake result: None = not yet determined (retry on
# next call), otherwise {"bridge_version": str | None} — None meaning the bridge
# predates version stamping.
_bridge_check: dict | None = None

_UPDATE_HINT = (
    "Re-paste the output of `uvx touchdesigner-mcp bridge` into the Web Server DAT "
    "callbacks, or update the .tox."
)


def version_mismatch_warning(bridge_version: str | None) -> str | None:
    """Warning string if the TD-side bridge doesn't match this server's version, else None."""
    if SERVER_VERSION is None or bridge_version == SERVER_VERSION:
        return None
    # Dev builds (editable installs, repo-copied bridge scripts) carry
    # setuptools-scm/placeholder versions like 0.2.1.dev3+g1234abc or 0.0.0.dev0
    # — comparing those is meaningless, so stay quiet.
    if ".dev" in SERVER_VERSION or (bridge_version is not None and ".dev" in bridge_version):
        return None
    if bridge_version is None:
        return (
            f"TouchDesigner bridge version is unknown — it likely predates this server (v{SERVER_VERSION}). "
            + _UPDATE_HINT
        )
    return f"TouchDesigner bridge is v{bridge_version} but this server is v{SERVER_VERSION}. " + _UPDATE_HINT


async def _fetch_bridge_version(client: httpx.AsyncClient) -> dict | None:
    """Ask the bridge for its version via get_project_info. None = couldn't tell (retry later)."""
    try:
        resp = await client.post(config.TD_URL, json={"action": "get_project_info", "params": {}})
        resp.raise_for_status()
        info = resp.json()
    except Exception:
        return None
    if not isinstance(info, dict) or not info.get("success"):
        return None
    return {"bridge_version": info.get("bridge_version")}


async def send_to_td(action: str, params: dict) -> dict:
    """Send a JSON command to TouchDesigner's Web Server DAT and return the response."""
    global _bridge_check
    payload = {"action": action, "params": params}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(config.TD_URL, json=payload)
            resp.raise_for_status()
            result = resp.json()
            if action == "get_project_info" and isinstance(result, dict) and result.get("success"):
                _bridge_check = {"bridge_version": result.get("bridge_version")}
            elif _bridge_check is None:
                _bridge_check = await _fetch_bridge_version(client)
    except httpx.ConnectError:
        return {
            "error": f"Cannot connect to TouchDesigner at {config.TD_URL}. "
            "Is TouchDesigner running with the Web Server DAT active on that port? "
            "(Endpoint is configurable via TD_URL / TD_HOST / TD_PORT env vars or --url/--host/--port flags.)"
        }
    except httpx.HTTPStatusError as e:
        return {"error": f"TouchDesigner returned HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

    if _bridge_check and isinstance(result, dict):
        warning = version_mismatch_warning(_bridge_check["bridge_version"])
        if warning:
            result.setdefault("warning", warning)
    return result
