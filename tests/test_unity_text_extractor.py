import json
from types import SimpleNamespace

import pytest

from suikoden_tool.unity_text_extractor import _dump_textasset_fields, extract_textasset_json


def _fake_process(stdout):
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def test_extract_textasset_json_uses_unitydatatool_and_preserves_unicode(tmp_path, monkeypatch):
    bundle = tmp_path / "sample.bundle"
    bundle.write_bytes(b"UnityFS placeholder")
    tool = tmp_path / "UnityDataTool.exe"
    tool.write_bytes(b"fake executable")
    output = tmp_path / "out" / "text_add_en.json"
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if "objectlist" in command:
            return _fake_process(json.dumps([{"id": 42, "typeName": "TextAsset"}]))
        if "dump" in command:
            return _fake_process(
                'ID: 42 (ClassID: 49) TextAsset\n'
                '  m_Name (string) text_add_en\n'
                '  m_Script (string) {"textList":[{"id":1,"text":"♂㈱ ♂① ♂② ♂⑩∠Linha∨Próxima☆ＬＶ２ ★☆ ◎1  espaços  ?"}]}\n'
            )
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr("suikoden_tool.unity_text_extractor.subprocess.run", fake_run)

    result = extract_textasset_json(bundle, output, executable=tool)

    assert result["asset_name"] == "text_add_en"
    assert result["text_count"] == 1
    assert json.loads(output.read_text(encoding="utf-8"))["textList"][0]["text"] == "♂㈱ ♂① ♂② ♂⑩∠Linha∨Próxima☆ＬＶ２ ★☆ ◎1  espaços  ?"
    assert len(calls) == 2
    assert calls[0][1:3] == ["serialized-file", "objectlist"]
    assert "--stdout" in calls[1]


def test_extract_refuses_to_overwrite_existing_output_without_force(tmp_path):
    bundle = tmp_path / "sample.bundle"
    bundle.write_bytes(b"bundle")
    output = tmp_path / "existing.json"
    output.write_text('{"keep": true}', encoding="utf-8")

    with pytest.raises(ValueError, match="já existe"):
        extract_textasset_json(bundle, output, executable=tmp_path / "missing.exe")

    assert output.read_text(encoding="utf-8") == '{"keep": true}'


def test_extract_requires_asset_name_when_multiple_json_textassets_exist(tmp_path, monkeypatch):
    bundle = tmp_path / "sample.bundle"
    bundle.write_bytes(b"UnityFS placeholder")
    tool = tmp_path / "UnityDataTool.exe"
    tool.write_bytes(b"fake executable")

    def fake_run(command, **kwargs):
        if "objectlist" in command:
            return _fake_process(
                json.dumps(
                    [
                        {"id": 10, "typeName": "TextAsset"},
                        {"id": 20, "typeName": "TextAsset"},
                    ]
                )
            )
        object_id = command[command.index("--objectid") + 1]
        name = "text_one" if object_id == "10" else "text_two"
        payload = {"textList": [{"id": int(object_id), "text": name}]}
        return _fake_process(
            f"ID: {object_id} (ClassID: 49) TextAsset\n"
            f"  m_Name (string) {name}\n"
            f"  m_Script (string) {json.dumps(payload)}\n"
        )

    monkeypatch.setattr("suikoden_tool.unity_text_extractor.subprocess.run", fake_run)

    with pytest.raises(ValueError, match="informe --asset-name"):
        extract_textasset_json(bundle, tmp_path / "out.json", executable=tool)

    result = extract_textasset_json(
        bundle,
        tmp_path / "selected.json",
        executable=tool,
        asset_name="text_two",
    )
    assert result["asset_name"] == "text_two"


def test_dump_textasset_fields_preserves_trailing_whitespace_and_newlines():
    dump = (
        "ID: 42 (ClassID: 49) TextAsset\r\n"
        "  m_Name (string) text_asset  \r\n"
        "  m_Script (string) {\"textList\":[{\"id\":1,\"text\":\"A∠B\"}]}\r\n\r\n"
    )

    name, script = _dump_textasset_fields(dump)

    assert name == "text_asset  "
    assert script.endswith("\r\n\r\n")
    assert "∠" in script
