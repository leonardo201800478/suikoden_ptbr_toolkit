import json
from pathlib import Path

import pytest

from suikoden_tool.dump_catalog_import import import_dump_to_catalog


def make_dump(path: Path, script: str) -> Path:
    path.write_text(
        "ID: 9 (ClassID: 49) TextAsset\n"
        "  m_Name (string) text_gsd1_en\n"
        f"  m_Script (string) {script}\n",
        encoding="utf-8",
    )
    return path


def test_import_dump_creates_catalog_without_modifying_original(tmp_path):
    script = json.dumps(
        {"textList": [{"id": 12, "text": "Hello?"}, {"id": "n2", "text": "World"}]},
        ensure_ascii=False,
    )
    dump_path = make_dump(tmp_path / "text_gsd1_en-CAB-123-9.txt", script)
    original = dump_path.read_bytes()

    result = import_dump_to_catalog(dump_path)
    catalog_path = Path(result["catalog_path"])
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert result["entries"] == 2
    assert catalog["source_dump"] == dump_path.name
    assert catalog["asset_name"] == "text_gsd1_en"
    assert catalog["entries"][0] == {
        "id": 12, "original": "Hello?", "translation": "", "status": "pending"
    }
    assert catalog["entries"][1]["id"] == "n2"
    assert dump_path.read_bytes() == original


def test_import_dump_rejects_non_textlist_without_changing_dump(tmp_path):
    dump_path = make_dump(tmp_path / "text_add_en-CAB-123-9.txt", '{"menu": "not textList"}')
    original = dump_path.read_bytes()

    with pytest.raises(ValueError, match="textList"):
        import_dump_to_catalog(dump_path)

    assert dump_path.read_bytes() == original
    assert not dump_path.with_suffix(".catalog.json").exists()


def test_import_dump_never_overwrites_existing_catalog(tmp_path):
    dump_path = make_dump(
        tmp_path / "text_gsd2_en-CAB-123-9.txt",
        '{"textList": [{"id": 1, "text": "Hello"}]}',
    )
    catalog_path = dump_path.with_suffix(".catalog.json")
    catalog_path.write_text('{"keep": true}', encoding="utf-8")

    with pytest.raises(FileExistsError, match="não será sobrescrito"):
        import_dump_to_catalog(dump_path)

    assert catalog_path.read_text(encoding="utf-8") == '{"keep": true}'



def test_import_dump_repairs_missing_comma_between_textlist_objects(tmp_path):
    script = '{"textList": [{"id": 1, "text": "First"} {"id": 2, "text": "Second"}]}'
    dump_path = make_dump(tmp_path / "text_add_en-CAB-123-9.txt", script)

    result = import_dump_to_catalog(dump_path)
    catalog = json.loads(Path(result["catalog_path"]).read_text(encoding="utf-8"))

    assert result["entries"] == 2
    assert [entry["original"] for entry in catalog["entries"]] == ["First", "Second"]


def test_import_dump_preserves_control_characters_inside_json_strings(tmp_path):
    script = '{"textList": [{"id": 1, "text": "Line one\\nLine two"}]}'
    dump_path = make_dump(tmp_path / "text_gsd1_en-CAB-123-9.txt", script)

    result = import_dump_to_catalog(dump_path)
    catalog = json.loads(Path(result["catalog_path"]).read_text(encoding="utf-8"))

    assert result["entries"] == 1
    assert catalog["entries"][0]["original"] == "Line one\\nLine two"
