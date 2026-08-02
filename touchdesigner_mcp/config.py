import os

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9980


def resolve_url(url: str | None = None, host: str | None = None, port: int | None = None) -> str:
    """Resolve the TD endpoint. Precedence: url arg > host/port args > TD_URL env > TD_HOST/TD_PORT env > defaults."""
    if url:
        return url.rstrip("/")
    env_url = os.environ.get("TD_URL")
    if env_url and not (host or port):
        return env_url.rstrip("/")
    final_host = host or os.environ.get("TD_HOST", DEFAULT_HOST)
    final_port = port or os.environ.get("TD_PORT", str(DEFAULT_PORT))
    return f"http://{final_host}:{final_port}"


# May be overridden by CLI flags in __main__.main() — always read via
# `config.TD_URL` at call time, never `from touchdesigner_mcp.config import TD_URL`.
TD_URL = resolve_url()
