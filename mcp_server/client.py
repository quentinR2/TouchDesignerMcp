import httpx
from mcp_server.config import TD_URL


async def send_to_td(action: str, params: dict) -> dict:
    """Send a JSON command to TouchDesigner's Web Server DAT and return the response."""
    payload = {"action": action, "params": params}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(TD_URL, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        return {"error": "Cannot connect to TouchDesigner. Is it running with the Web Server DAT active on port 9980?"}
    except httpx.HTTPStatusError as e:
        return {"error": f"TouchDesigner returned HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
