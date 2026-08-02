import httpx
from touchdesigner_mcp import config


async def send_to_td(action: str, params: dict) -> dict:
    """Send a JSON command to TouchDesigner's Web Server DAT and return the response."""
    payload = {"action": action, "params": params}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(config.TD_URL, json=payload)
            resp.raise_for_status()
            return resp.json()
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
