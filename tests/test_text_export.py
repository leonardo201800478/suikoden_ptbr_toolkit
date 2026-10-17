import json

import pytest

from suikoden_tool.cli import _export_text_catalog


def test_export_text_catalog_preserves_original_text(tmp_path):
    source = tmp_path / "text_add_en.json"
    output = tmp_path / "catalogo_pt_br.json"
    original = {
        "textList": [
            {"id": 1, "text": "Power?"},
            {"id": 2, "text": "Linha 1∠Linha 2\ncontinuação"},
            {"id": 3, "text": ""},
        ]
    }
    source.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")

    catalog = _export_text_catalog(source, output, "pt-BR")

    assert catalog["resource"] == "text_add_en"
    assert catalog["target_language"] == "pt-BR"
    assert len(catalog["entries"]) == 3
    assert catalog["entries"][0] == {
        "id": 1,
        "original": "Power?",
        "translation": "",
        "status": "pending",
    }
    assert catalog["entries"][1]["original"] == "Linha 1∠Linha 2\ncontinuação"
    assert catalog["entries"][2]["original"] == ""


def test_export_text_catalog_rejects_duplicate_ids(tmp_path):
    source = tmp_path / "duplicate.json"
    source.write_text(
        json.dumps({"textList": [{"id": 1, "text": "A"}, {"id": 1, "text": "B"}]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ID duplicado"):
        _export_text_catalog(source, tmp_path / "out.json", "pt-BR")


def test_export_text_catalog_rejects_invalid_shape(tmp_path):
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps({"items": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="textList"):
        _export_text_catalog(source, tmp_path / "out.json", "pt-BR")
