import json
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_cli_roundtrip(tmp_path):
    out = tmp_path / "out.json"
    subprocess.run([sys.executable, "-m", "eorplan", "predict", str(ROOT / "configs/sat2.json"),
                    "-o", str(out)], cwd=ROOT, check=True)
    data = json.loads(out.read_text())
    assert [c["day"] for c in data["checkpoints"]] == [5.0, 10.0, 20.0]
