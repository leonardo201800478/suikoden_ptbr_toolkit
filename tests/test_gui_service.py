import json

import pytest

from suikoden_tool.gui_service import load_catalog, save_entry, suggest_translation


def make_catalog(path, entries):
    catalog = {
        "schema_version": 1,
        "resource": "text_add_en",
        "source_language": "en",
        "target_language": "pt-BR",
        "entries": entries,
    }
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return catalog


def test_save_entry_changes_only_translation_and_status(tmp_path):
    path = tmp_path / "catalog.json"
    original = "Hello∠world\nNext"
    make_catalog(
        path,
        [{"id": 7, "original": original, "translation": "", "status": "pending", "extra": "keep"}],
    )

    saved = save_entry(path, 7, "Olá∠mundo\nPróximo")

    result = load_catalog(path)
    entry = result["entries"][0]
    assert saved["translation"] == "Olá∠mundo\nPróximo"
    assert entry["original"] == original
    assert entry["extra"] == "keep"
    assert entry["status"] == "translated"


def test_save_entry_requires_explicit_review_when_source_changed(tmp_path):
    path = tmp_path / "catalog.json"
    make_catalog(
        path,
        [{
            "id": 7, "original": "New source", "previous_original": "Old source",
            "source_changed": True, "translation": "Anterior", "status": "needs_review",
        }],
    )

    with pytest.raises(ValueError, match="precisa ser salva como revisada"):
        save_entry(path, 7, "Nova tradução", "translated")

    save_entry(path, 7, "Nova tradução", "reviewed")
    assert load_catalog(path)["entries"][0]["status"] == "reviewed"


def test_save_entry_does_not_allow_empty_translation_or_orphaned_entry(tmp_path):
    path = tmp_path / "catalog.json"
    make_catalog(
        path,
        [
            {"id": 1, "original": "Hello", "translation": "", "status": "pending"},
            {"id": 2, "original": "Removed", "translation": "", "status": "orphaned"},
        ],
    )

    with pytest.raises(ValueError, match="não pode ficar vazia"):
        save_entry(path, 1, "  ")
    with pytest.raises(ValueError, match="órfãs"):
        save_entry(path, 2, "Texto")


def test_ai_suggestion_requires_key_without_making_request(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        suggest_translation("Hello")
