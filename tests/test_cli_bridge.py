"""`touchdesigner-mcp bridge` output encoding (issue #13). No TouchDesigner needed."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRIDGE_FILE = ROOT / "touchdesigner_mcp" / "bridge_script.py"


def run_bridge_cli(console_encoding: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("PYTHONUTF8", None)
    env["PYTHONIOENCODING"] = console_encoding  # emulate a non-UTF-8 console (e.g. French Windows cp1252)
    return subprocess.run(
        [sys.executable, "-m", "touchdesigner_mcp", "bridge"],
        capture_output=True,
        env=env,
        cwd=ROOT,
    )


def test_bridge_subcommand_survives_cp1252_console():
    proc = run_bridge_cli("cp1252")

    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    out = proc.stdout.decode("utf-8")
    assert 'BRIDGE_VERSION = "' in out


def test_bridge_subcommand_output_matches_shipped_file_bytes():
    proc = run_bridge_cli("cp1252")

    assert proc.stdout.replace(b"\r\n", b"\n") == BRIDGE_FILE.read_bytes()


def test_checked_in_bridge_is_pure_ascii():
    # The script is pasted through arbitrary consoles/clipboards; non-ASCII
    # characters are what broke the CLI on cp1252 consoles.
    BRIDGE_FILE.read_bytes().decode("ascii")
