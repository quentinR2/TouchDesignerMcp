"""Bridge handler logic (issue #5). No TouchDesigner needed — the TD builtin
`op` is monkeypatched onto the generated bridge module with a fake node tree."""

import json

import pytest

import touchdesigner_mcp.bridge_script as bridge


class FakeOP:
    """Mimics the TD OP API: errors()/warnings() are METHODS returning str."""

    def __init__(self, name, errors="", warnings="", children=(), type="nullCHOP"):
        self.name = name
        self.type = type
        self.path = f"/project1/{name}"
        self._errors = errors
        self._warnings = warnings
        self.children = list(children)

    def errors(self):
        return self._errors

    def warnings(self):
        return self._warnings


@pytest.fixture
def root(monkeypatch):
    nested = FakeOP("deep", errors="deep failure")
    tree = FakeOP(
        "project1",
        children=[
            FakeOP("clean"),
            FakeOP("broken", errors="Missing input"),
            FakeOP("noisy", warnings="Deprecated parameter"),
            FakeOP("container", children=[nested], type="baseCOMP"),
        ],
    )
    monkeypatch.setattr(bridge, "op", lambda path: tree if path == "/project1" else None, raising=False)
    return tree


def test_get_errors_only_reports_nodes_with_errors(root):
    result = bridge.handle_get_errors({"parent_path": "/project1", "include_warnings": False})

    json.dumps(result)  # must be serializable — was the HTTP 500
    assert result["count"] == 2
    assert {n["name"] for n in result["nodes"]} == {"broken", "deep"}
    broken = next(n for n in result["nodes"] if n["name"] == "broken")
    assert broken["errors"] == "Missing input"
    assert "warnings" not in broken


def test_get_errors_include_warnings_false_skips_warning_only_nodes(root):
    with_w = bridge.handle_get_errors({"parent_path": "/project1", "include_warnings": True})
    without_w = bridge.handle_get_errors({"parent_path": "/project1", "include_warnings": False})

    assert "noisy" in {n["name"] for n in with_w["nodes"]}
    assert "noisy" not in {n["name"] for n in without_w["nodes"]}
    noisy = next(n for n in with_w["nodes"] if n["name"] == "noisy")
    assert noisy["warnings"] == "Deprecated parameter"
    assert "errors" not in noisy


def test_get_errors_recursive_false_stays_at_top_level(root):
    result = bridge.handle_get_errors({"parent_path": "/project1", "recursive": False, "include_warnings": False})

    assert {n["name"] for n in result["nodes"]} == {"broken"}


def test_get_errors_clean_tree_reports_none(monkeypatch):
    tree = FakeOP("project1", children=[FakeOP("a"), FakeOP("b")])
    monkeypatch.setattr(bridge, "op", lambda path: tree, raising=False)

    result = bridge.handle_get_errors({"parent_path": "/project1"})

    assert result["count"] == 0
    assert result["nodes"] == []
    assert result["message"] == "No errors or warnings found"


def test_get_errors_unknown_parent_raises(root):
    with pytest.raises(ValueError, match="Container not found: /nope"):
        bridge.handle_get_errors({"parent_path": "/nope"})
