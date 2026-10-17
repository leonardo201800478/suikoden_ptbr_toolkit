import json

import pytest

from suikoden_tool.text_catalog import catalog_stats, export_text_catalog, validate_catalog


def write_source(path, entries):
    path.write_text(json.dumps({"textList": entries}, ensure_ascii=False), encoding="utf-8")
    return path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_export_creates_catalog_and_preserves_original_text(tmp_path):
    source = write_source(
        tmp_path / "text_add_en.json",
        [
            {"id": 1, "text": "Power?"},
            {"id": 2, "text": "Linha 1∠Linha 2\ncontinuação"},
            {"id": 3, "text": ""},
        ],
    )
    output = tmp_path / "catalogo_pt_br.json"

    result = export_text_catalog(source, output, "pt-BR")
    catalog = result["catalog"]

    assert result["created"] == 3
    assert catalog["resource"] == "text_add_en"
    assert catalog["target_language"] == "pt-BR"
    assert catalog["entries"][0] == {
        "id": 1, "original": "Power?", "translation": "", "status": "pending"
    }
    assert catalog["entries"][1]["original"] == "Linha 1∠Linha 2\ncontinuação"
    assert catalog["entries"][2]["original"] == ""


def test_export_rejects_duplicate_source_ids(tmp_path):
    source = write_source(
        tmp_path / "duplicate.json",
        [{"id": 1, "text": "A"}, {"id": 1, "text": "B"}],
    )
    with pytest.raises(ValueError, match="ID duplicado"):
        export_text_catalog(source, tmp_path / "out.json")


def test_export_rejects_invalid_source_shape(tmp_path):
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps({"items": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="textList"):
        export_text_catalog(source, tmp_path / "out.json")


def test_update_preserves_translation_and_status_when_id_and_original_match(tmp_path):
    source = write_source(tmp_path / "resource.json", [{"id": 1, "text": "Original"}])
    output = tmp_path / "catalog.json"
    export_text_catalog(source, output)
    catalog = read_json(output)
    catalog["entries"][0]["translation"] = "Tradução"
    catalog["entries"][0]["status"] = "reviewed"
    output.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    result = export_text_catalog(source, output)

    entry = result["catalog"]["entries"][0]
    assert entry["translation"] == "Tradução"
    assert entry["status"] == "reviewed"
    assert result["preserved"] == 1
    assert result["changed"] == 0


def test_update_keeps_translation_and_marks_changed_source_for_review(tmp_path):
    source = write_source(tmp_path / "resource.json", [{"id": 1, "text": "Updated source"}])
    output = tmp_path / "catalog.json"
    catalog = {
        "schema_version": 1,
        "resource": "resource",
        "source_language": "en",
        "target_language": "pt-BR",
        "entries": [{
            "id": 1, "original": "Old source", "translation": "Tradução existente",
            "status": "translated",
        }],
    }
    output.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    result = export_text_catalog(source, output)
    entry = result["catalog"]["entries"][0]

    assert entry["translation"] == "Tradução existente"
    assert entry["original"] == "Updated source"
    assert entry["previous_original"] == "Old source"
    assert entry["source_changed"] is True
    assert entry["status"] == "needs_review"
    assert result["changed"] == 1


def test_update_preserves_removed_entries_as_orphaned(tmp_path):
    source = write_source(tmp_path / "resource.json", [{"id": 1, "text": "Keep"}])
    output = tmp_path / "catalog.json"
    catalog = {
        "schema_version": 1, "resource": "resource", "source_language": "en",
        "target_language": "pt-BR",
        "entries": [
            {"id": 1, "original": "Keep", "translation": "Manter", "status": "translated"},
            {"id": 2, "original": "Removed", "translation": "Não apagar", "status": "translated"},
        ],
    }
    output.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    result = export_text_catalog(source, output)
    orphan = next(entry for entry in result["catalog"]["entries"] if entry["id"] == 2)

    assert orphan["translation"] == "Não apagar"
    assert orphan["status"] == "orphaned"
    assert result["orphaned"] == 1


def test_update_adds_new_ids_without_resetting_existing_translation(tmp_path):
    source = write_source(tmp_path / "resource.json", [{"id": 1, "text": "A"}, {"id": 2, "text": "B"}])
    output = tmp_path / "catalog.json"
    catalog = {
        "schema_version": 1, "resource": "resource", "source_language": "en",
        "target_language": "pt-BR",
        "entries": [{"id": 1, "original": "A", "translation": "AA", "status": "translated"}],
    }
    output.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    result = export_text_catalog(source, output)
    entries = {entry["id"]: entry for entry in result["catalog"]["entries"]}

    assert entries[1]["translation"] == "AA"
    assert entries[2]["translation"] == ""
    assert entries[2]["status"] == "pending"
    assert result["new"] == 1


def test_update_refuses_different_target_language_without_modifying_file(tmp_path):
    source = write_source(tmp_path / "resource.json", [{"id": 1, "text": "A"}])
    output = tmp_path / "catalog.json"
    original_bytes = json.dumps({
        "schema_version": 1, "resource": "resource", "source_language": "en",
        "target_language": "en", "entries": [],
    }).encode()
    output.write_bytes(original_bytes)

    with pytest.raises(ValueError, match="Não foi alterado"):
        export_text_catalog(source, output, "pt-BR")
    assert output.read_bytes() == original_bytes


def test_validate_reports_duplicate_ids_invalid_fields_and_pending_translations():
    catalog = {
        "schema_version": 1, "resource": "resource", "source_language": "en",
        "target_language": "pt-BR",
        "entries": [
            {"id": 1, "original": "A", "translation": "", "status": "pending"},
            {"id": 1, "original": "B", "translation": 7, "status": "unknown"},
        ],
    }

    report = validate_catalog(catalog)

    assert report["valid"] is False
    assert any("ID duplicado" in error for error in report["errors"])
    assert any("translation" in error for error in report["errors"])
    assert any("status inválido" in error for error in report["errors"])
    assert any("tradução pendente" in warning for warning in report["warnings"])


def test_validate_detects_source_changes_and_new_or_removed_ids(tmp_path):
    source = write_source(
        tmp_path / "resource.json",
        [{"id": 1, "text": "Changed"}, {"id": 3, "text": "New"}],
    )
    catalog = {
        "schema_version": 1, "resource": "resource", "source_language": "en",
        "target_language": "pt-BR",
        "entries": [
            {"id": 1, "original": "Old", "translation": "Antigo", "status": "translated"},
            {"id": 2, "original": "Removed", "translation": "Removido", "status": "translated"},
        ],
    }

    report = validate_catalog(catalog, source)
    warnings = "\n".join(report["warnings"])

    assert "Texto de origem alterado para ID 1" in warnings
    assert "ID novo na fonte, ausente do catálogo: 3" in warnings
    assert "ID do catálogo ausente na fonte: 2" in warnings


def test_validate_rejects_non_object_catalog():
    report = validate_catalog([])

    assert report["valid"] is False
    assert report["error_count"] == 1


def test_stats_counts_statuses_without_modifying_catalog():
    catalog = {
        "schema_version": 1, "resource": "resource", "source_language": "en",
        "target_language": "pt-BR",
        "entries": [
            {"id": 1, "original": "A", "translation": "", "status": "pending"},
            {"id": 2, "original": "B", "translation": "B traduzido", "status": "translated"},
            {"id": 3, "original": "C", "translation": "C revisado", "status": "reviewed"},
            {"id": 4, "original": "D", "translation": "D", "status": "needs_review"},
            {"id": 5, "original": "E", "translation": "E", "status": "orphaned"},
        ],
    }

    stats = catalog_stats(catalog)

    assert stats == {
        "total": 5, "pending": 1, "translated": 1, "reviewed": 1,
        "needs_review": 1, "orphaned": 1, "completion_percent": 40.0,
    }


def test_stats_rejects_invalid_status():
    with pytest.raises(ValueError, match="status inválido"):
        catalog_stats({"entries": [{"id": 1, "status": "mystery"}]})
