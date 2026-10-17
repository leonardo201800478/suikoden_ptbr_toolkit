import json
from types import SimpleNamespace

from suikoden_tool.text_extractor import extract_from_bundles


def _process(stdout):
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def test_extract_from_bundles_parses_m_script_not_entire_dump(tmp_path, monkeypatch):
    bundle_name = "03cf0288ba3ecaca0776d7fadf1f0bb6.bundle"
    bundle = tmp_path / bundle_name
    bundle.write_bytes(b"fake bundle")
    tool = tmp_path / "UnityDataTool.exe"
    tool.write_bytes(b"fake executable")
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if "archive" in command:
            return _process(json.dumps([{"path": "CAB-test", "flags": "SerializedFile"}]))
        if "objectlist" in command:
            return _process(json.dumps([{"id": 42, "typeName": "TextAsset"}]))
        if "dump" in command:
            script = json.dumps({
                "textList": [
                    {"id": 1629000095, "text": "Friend? Wait! Did you say leader of the Liberation Army?!"},
                    {"id": 1031027251, "text": "Yes.?No."},
                ]
            }, ensure_ascii=False)
            return _process(
                "ID: 42 (ClassID: 49) TextAsset\n"
                "  m_Name (string) text_dialogue_en\n"
                f"  m_Script (string) {script}\n"
            )
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr("suikoden_tool.text_extractor.subprocess.run", fake_run)
    output = tmp_path / "catalog.json"

    catalog = extract_from_bundles(
        tmp_path,
        tool,
        output,
        bundle_names=(bundle_name,),
    )

    assert catalog["entry_count"] == 2
    assert [entry["source_text"] for entry in catalog["entries"]] == [
        "Friend? Wait! Did you say leader of the Liberation Army?!",
        "Yes.?No.",
    ]
    assert catalog["entries"][1]["control_tokens"] == ["?"]
    assert json.loads(output.read_text(encoding="utf-8"))["entry_count"] == 2


def test_extract_from_bundles_rejects_raw_control_characters_without_repair(tmp_path, monkeypatch):
    bundle_name = "03cf0288ba3ecaca0776d7fadf1f0bb6.bundle"
    (tmp_path / bundle_name).write_bytes(b"fake bundle")
    tool = tmp_path / "UnityDataTool.exe"
    tool.write_bytes(b"fake executable")

    def fake_run(command, **kwargs):
        if "archive" in command:
            return _process(json.dumps([{"path": "CAB-test", "flags": "SerializedFile"}]))
        if "objectlist" in command:
            return _process(json.dumps([{"id": 42, "typeName": "TextAsset"}]))
        if "dump" in command:
            # Simula JSON inválido emitido pelo dump: a extração não deve repará-lo.
            script = '{"textList":[{"id":7,"text":"line one\\x0bline two ?"}]}'
            return _process(
                "ID: 42 (ClassID: 49) TextAsset\n"
                "  m_Name (string) text_gsd2_en\n"
                f"  m_Script (string) {script}\\n"
            )
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr("suikoden_tool.text_extractor.subprocess.run", fake_run)
    catalog = extract_from_bundles(
        tmp_path, tool, tmp_path / "catalog.json", bundle_names=(bundle_name,)
    )
    assert catalog["entry_count"] == 0
    failures = [item for item in catalog["diagnostics"] if item.get("integrity_action")]
    assert len(failures) == 1
    assert failures[0]["integrity_action"] == "rejected_without_repair"
