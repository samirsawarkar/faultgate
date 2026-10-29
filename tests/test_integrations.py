"""Check every integrations/*/expected.json against faultgate's real output.

Reads only the saved trace files. Needs no internet, API key or framework.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CASES = [
    (path.parent, trace)
    for path in sorted((ROOT / "integrations").glob("*/expected.json"))
    for trace in json.loads(path.read_text())
]


@pytest.mark.parametrize(
    "recipe,trace", CASES, ids=[f"{r.name}/{t}" for r, t in CASES]
)
def test_recipe_trace(recipe, trace, tmp_path):
    expected = json.loads((recipe / "expected.json").read_text())[trace]
    report = tmp_path / "report.json"
    run = subprocess.run(
        [shutil.which("faultgate"), "check", str(recipe / "traces" / trace),
         "--policy", str(recipe / "policy.json"), "--json", str(report)],
        capture_output=True, text=True,
    )
    assert run.returncode == expected["exit_code"], run.stdout + run.stderr
    data = json.loads(report.read_text())
    fired = sorted(name for name, count in data["fired"].items() if count)
    assert fired == sorted(expected["fired"])