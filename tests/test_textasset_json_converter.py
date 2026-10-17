import json
from pathlib import Path

import pytest

from suikoden_tool.textasset_json_converter import convert_textasset_batch, convert_textasset_dump


def test_converts_textlist_json_to_separate_output_and_preserves_source(tmp_path):
    source = tmp_path / "text_gsd1_en-CAB-abc-1.txt"
    raw = '{"textList":[{"id":1,"text":"Hello\\nworld"},{"id":2,"text":"It\'s fine"}]}'
    source.write_text(raw, encoding="utf-8")
    result = convert_textasset_dump(source, tmp_path / "converted" / "text_gsd1_en.json")
    output = Path(result["output"])
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert result["kind"] == "textList"
    assert result["entries"] == 2
    assert payload["textList"][0]["text"] == "Hello\\nworld"
    assert source.read_text(encoding="utf-8") == raw
    assert output != source


def test_wraps_license_plain_text_in_valid_json(tmp_path):
    source = tmp_path / "License_steam-CAB-abc-1.txt"
    source.write_text("<b>License</b>\nCopyright text", encoding="utf-8")
    result = convert_textasset_dump(source, tmp_path / "licenses" / "License_steam.json")
    payload = json.loads(Path(result["output"]).read_text(encoding="utf-8"))

    assert result["kind"] == "license"
    assert payload["content"] == "<b>License</b>\nCopyright text"


def test_rejects_unknown_invalid_json_without_creating_output(tmp_path):
    source = tmp_path / "text_add_en.txt"
    source.write_text('{"textList": [broken]}', encoding="utf-8")
    destination = tmp_path / "out" / "text_add_en.json"

    with pytest.raises(ValueError, match="não é JSON válido"):
        convert_textasset_dump(source, destination)

    assert not destination.exists()
    assert source.exists()


def test_batch_uses_catalog_and_license_subfolders_and_overwrites(tmp_path):
    source_catalog = tmp_path / "text_gsd2_en.txt"
    source_catalog.write_text('{"textList":[{"id":7,"text":"A"}]}', encoding="utf-8")
    source_license = tmp_path / "License_xb.txt"
    source_license.write_text("legal", encoding="utf-8")
    output = tmp_path / "json"
    (output / "catalogos").mkdir(parents=True)
    (output / "catalogos" / "text_gsd2_en.json").write_text('{"old":true}', encoding="utf-8")

    results = convert_textasset_batch([source_catalog, source_license], output)

    assert len(results) == 2
    assert json.loads((output / "catalogos" / "text_gsd2_en.json").read_text())["textList"][0]["id"] == 7
    assert (output / "licencas" / "License_xb.json").is_file()



def test_preserves_confirmed_suikoden_glyphs_and_replacement_character(tmp_path):
    source = tmp_path / "text_add_en-CAB-abc-1.txt"
    original = {
        "textList": [
            {"id": 1, "text": "Line∠next∨page ♂㈱■☆★▲▼"},
            {"id": 2, "text": "Replacement � is original content"},
        ]
    }
    source.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
    result = convert_textasset_dump(source, tmp_path / "out" / "text_add_en.json")
    payload = json.loads(Path(result["output"]).read_text(encoding="utf-8"))
    assert payload["textList"][0]["text"] == original["textList"][0]["text"]
    assert payload["textList"][1]["text"] == original["textList"][1]["text"]


def test_converts_confirmed_control_codes_to_visible_markers(tmp_path):
    source = tmp_path / "text_add_en-CAB-abc-1.txt"
    # Raw U+0018..U+001B are escaped in JSON source, then represented visibly
    # in the translation catalog to avoid invisible controls in translation UI.
    raw = json.dumps({"textList": [{"id": 1, "text": "A\\u0018B\\u0019C\\u001aD\\u001bE"}]})
    source.write_text(raw, encoding="utf-8")
    result = convert_textasset_dump(source, tmp_path / "out" / "text_add_en.json")
    payload = json.loads(Path(result["output"]).read_text(encoding="utf-8"))
    assert payload["textList"][0]["text"] == (
        "A⟦CTRL-U+0018⟧B⟦CTRL-U+0019⟧C⟦CTRL-U+001A⟧D⟦CTRL-U+001B⟧E"
    )
