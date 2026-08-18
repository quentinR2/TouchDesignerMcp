"""Bridge/server version mismatch detection (issue #4). No TouchDesigner needed —
the TD side is simulated with httpx.MockTransport."""

import json

import anyio
import httpx
import pytest

from touchdesigner_mcp import client


@pytest.fixture(autouse=True)
def _fresh_state(monkeypatch):
    monkeypatch.setattr(client, "_bridge_check", None)
    monkeypatch.setattr(client, "SERVER_VERSION", "0.3.0")


def test_matching_versions_no_warning():
    assert client.version_mismatch_warning("0.3.0") is None


def test_mismatch_mentions_both_versions():
    warning = client.version_mismatch_warning("0.1.0")
    assert "v0.1.0" in warning and "v0.3.0" in warning


def test_unknown_bridge_version_warns_gently():
    warning = client.version_mismatch_warning(None)
    assert "unknown" in warning and "v0.3.0" in warning


def test_unknown_server_version_never_warns(monkeypatch):
    monkeypatch.setattr(client, "SERVER_VERSION", None)
    assert client.version_mismatch_warning("0.1.0") is None
    assert client.version_mismatch_warning(None) is None


def _send_with_fake_bridge(monkeypatch, project_info_response, action="list_nodes"):
    """Run send_to_td against a fake bridge whose get_project_info returns the given JSON."""

    def handler(request):
        body = json.loads(request.content)
        if body["action"] == "get_project_info":
            return httpx.Response(200, json=project_info_response)
        return httpx.Response(200, json={"success": True, "nodes": []})

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    def patched(**kwargs):
        kwargs["transport"] = transport
        return real_async_client(**kwargs)

    monkeypatch.setattr(client.httpx, "AsyncClient", patched)
    return anyio.run(client.send_to_td, action, {})


def test_send_to_td_appends_warning_on_stale_bridge(monkeypatch):
    result = _send_with_fake_bridge(monkeypatch, {"success": True, "bridge_version": "0.1.0"})
    assert "v0.1.0" in result["warning"] and "v0.3.0" in result["warning"]


def test_send_to_td_no_warning_on_matching_bridge(monkeypatch):
    result = _send_with_fake_bridge(monkeypatch, {"success": True, "bridge_version": "0.3.0"})
    assert "warning" not in result


def test_send_to_td_warns_on_pre_stamp_bridge(monkeypatch):
    # A bridge older than v0.1.0 answers get_project_info without bridge_version.
    result = _send_with_fake_bridge(monkeypatch, {"success": True})
    assert "unknown" in result["warning"]


def test_get_project_info_itself_gets_the_warning(monkeypatch):
    result = _send_with_fake_bridge(
        monkeypatch, {"success": True, "bridge_version": "0.1.0"}, action="get_project_info"
    )
    assert result["bridge_version"] == "0.1.0"
    assert "v0.1.0" in result["warning"]
