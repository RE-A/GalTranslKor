import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

from ollama_mock import mock_ollama
from test_ollama_ko_integration import project


ROOT = Path(__file__).resolve().parents[1]


def test_noninteractive_cli_with_unicode_project_path(tmp_path):
    with mock_ollama() as (url, calls):
        folder = tmp_path / "한국어 테스트 프로젝트"
        project(folder, url, 5)
        result = subprocess.run([sys.executable, str(ROOT / "run_ollama_ko.py"), str(folder)],
                                cwd=tmp_path, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(calls) == 2
        assert (folder / "gt_output" / "scene.json").exists()


def test_cli_failure_has_nonzero_exit_and_no_prompt(tmp_path):
    project(tmp_path, "http://127.0.0.1:1")
    data = yaml.safe_load((tmp_path / "config.yaml").read_text())
    data["backendSpecific"]["Ollama"]["model"] = ""
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(data))
    result = subprocess.run([sys.executable, str(ROOT / "run_ollama_ko.py"), str(tmp_path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert "model" in result.stdout + result.stderr
    assert not (tmp_path / "gt_output" / "scene.json").exists()


def test_committed_sample_runs_with_only_model_and_mock_endpoint_changed(tmp_path):
    sample = ROOT / "examples" / "ollama_ko"
    assert (sample / "config.yaml").exists()
    shutil.copytree(sample, tmp_path, dirs_exist_ok=True)
    with mock_ollama() as (url, calls):
        cfg = yaml.safe_load((tmp_path / "config.yaml").read_text())
        cfg["backendSpecific"]["Ollama"].update(model="mock-ko", endpoint=url)
        (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "run_ollama_ko.py"), str(tmp_path)],
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        original = json.loads((tmp_path / "gt_input" / "rainy_station.json").read_text())
        output = json.loads((tmp_path / "gt_output" / "rainy_station.json").read_text())
        assert len(output) == len(original) >= 20
        assert len(calls) > 1
        assert any(r.get("name") for r in original) and any(not r.get("name") for r in original)
