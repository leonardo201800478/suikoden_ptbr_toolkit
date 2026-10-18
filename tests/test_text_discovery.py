import json
from types import SimpleNamespace

from suikoden_tool.text_discovery import discover_text_assets


def _fake_process(stdout):
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def test_discover_text_assets_reports_names_counts_and_samples(tmp_path, monkeypatch):
    bundle = tmp_path / "sample.bundle"
    bundle.write_bytes(b"bundle bytes")
    tool = tmp_path / "UnityDataTool.exe"
    tool.write_bytes(b"fake executable")

    def fake_run(command, **kwargs):
        if "objectlist" in command:
            return _fake_process(
                json.dumps([{"id": 101, "typeName": "TextAsset"}])
            )
        return _fake_process(
            'ID: 101 (ClassID: 49) TextAsset\n'
            '  m_Name (string) text_menu_en\n'
            '  m_Script (string) '
            '{"textList":[{"id":1,"text":"New Game"},{"id":2,"text":"Load Game"}]}\n'
        )

    monkeypatch.setattr("suikoden_tool.unity_text_extractor.subprocess.run", fake_run)
    report = discover_text_assets(tmp_path, executable=tool)

    assert report["bundle_count"] == 1
    asset = report["bundles"][0]["textassets"][0]
    assert asset["name"] == "text_menu_en"
    assert asset["textlist_count"] == 2
    assert asset["sample_texts"][0] == {"id": 1, "text": "New Game"}
    assert asset["json_textlist"] is True


def test_discover_text_assets_reports_bundle_errors_without_stopping(tmp_path, monkeypatch):
    bundle = tmp_path / "broken.bundle"
    bundle.write_bytes(b"bundle bytes")
    tool = tmp_path / "UnityDataTool.exe"
    tool.write_bytes(b"fake executable")

    def fake_run(command, **kwargs):
        return SimpleNamespace(returncode=2, stdout="", stderr="bad bundle")

    monkeypatch.setattr("suikoden_tool.unity_text_extractor.subprocess.run", fake_run)
    report = discover_text_assets(tmp_path, executable=tool)

    assert report["bundle_count"] == 1
    assert "bad bundle" in report["bundles"][0]["error"]
