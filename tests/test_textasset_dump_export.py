import json
from pathlib import Path
from types import SimpleNamespace

from suikoden_tool.textasset_dump_export import export_textasset_dumps


def test_export_textasset_dumps_preserves_non_json_script_and_full_dump(tmp_path, monkeypatch):
    bundle = tmp_path / "sample.bundle"
    bundle.write_bytes(b"placeholder")
    tool = tmp_path / "UnityDataTool.exe"
    tool.write_bytes(b"placeholder")
    output = tmp_path / "dumps"
    raw_dump = (
        "ID: 7 (ClassID: 49) TextAsset\n"
        "  m_Name (string) text_menu_en\n"
        "  m_Script (string) not-json\x00with-control\n"
    )

    def fake_run(command, **kwargs):
        if "archive" in command:
            stdout = json.dumps([{"path": "CAB-123", "flags": "SerializedFile"}])
        elif "objectlist" in command:
            stdout = json.dumps([{"id": 7, "typeName": "TextAsset"}])
        elif "dump" in command:
            return SimpleNamespace(returncode=0, stdout=raw_dump, stderr="")
        else:
            raise AssertionError(command)
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr("suikoden_tool.textasset_dump_export.subprocess.run", fake_run)

    result = export_textasset_dumps([bundle], tool, output)
    saved = Path(result["exported"][0]["path"]).read_text(encoding="utf-8")

    assert result["exported_count"] == 1
    assert result["exported"][0]["asset_name"] == "text_menu_en"
    assert Path(result["exported"][0]["path"]).name == "text_menu_en-CAB-123-7.txt"
    assert saved == raw_dump
    assert "not-json\x00with-control" in saved


def test_export_textasset_dumps_does_not_overwrite_existing_dump(tmp_path, monkeypatch):
    bundle = tmp_path / "sample.bundle"
    bundle.write_bytes(b"placeholder")
    tool = tmp_path / "UnityDataTool.exe"
    tool.write_bytes(b"placeholder")
    output = tmp_path / "dumps"
    output.mkdir()
    existing = output / "text_menu_en-CAB-123-7.txt"
    existing.write_text("keep me", encoding="utf-8")

    def fake_run(command, **kwargs):
        if "archive" in command:
            stdout = json.dumps([{"path": "CAB-123", "flags": "SerializedFile"}])
        elif "objectlist" in command:
            stdout = json.dumps([{"id": 7, "typeName": "TextAsset"}])
        elif "dump" in command:
            return SimpleNamespace(
                returncode=0,
                stdout="ID: 7 (ClassID: 49) TextAsset\n  m_Name (string) text_menu_en\n  m_Script (string) text",
                stderr="",
            )
        else:
            raise AssertionError(command)
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr("suikoden_tool.textasset_dump_export.subprocess.run", fake_run)
    result = export_textasset_dumps([bundle], tool, output)

    assert result["exported_count"] == 0
    assert "já existe" in result["errors"][0]
    assert existing.read_text(encoding="utf-8") == "keep me"
