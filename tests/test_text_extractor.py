import json
from pathlib import Path
from unittest.mock import patch

import pytest

from suikoden_tool.text_extractor import (
    DEFAULT_BUNDLE_NAMES,
    _parse_archive_entries,
    extract_id_text_pairs,
    find_control_tokens,
    export_catalog_csv,
)


def test_extract_id_text_pairs_nested_and_deduplicates() -> None:
    payload = {"textList": [{"id": 1128000022, "text": "Ted!?Hurry up"},
                            {"id": 1128000022, "text": "Ted!?Hurry up"},
                            {"id": 1128000023, "text": "Thanks!"}]}
    assert extract_id_text_pairs(payload) == [(1128000022, "Ted!?Hurry up"), (1128000023, "Thanks!")]


def test_control_markers_are_recorded_without_modifying_source() -> None:
    original = "Good...?What's the point??"
    assert find_control_tokens(original) == ("?",)
    assert original == "Good...?What's the point??"


def test_archive_parser_filters_serializedfile_at_call_site() -> None:
    data = [{"path": "CAB-abc", "flags": "SerializedFile"},
            {"path": "CAB-abc.resS", "flags": "None"}]
    records = _parse_archive_entries(data)
    assert [r["path"] for r in records if "SerializedFile" in r["flags"]] == ["CAB-abc"]


def test_export_catalog_csv_preserves_question_mark(tmp_path: Path) -> None:
    source = tmp_path / "catalog.json"
    source.write_text(json.dumps({"entries": [{"id": "x", "game": "unknown", "bundle": "a.bundle",
        "text_id": 5, "source_text": "Hello?There", "translation_pt_br": "", "control_tokens": ["?"],
        "status": "untranslated"}]}, ensure_ascii=False), encoding="utf-8")
    target = tmp_path / "catalog.csv"
    assert export_catalog_csv(source, target) == 1
    content = target.read_text(encoding="utf-8-sig")
    assert "Hello?There" in content and "?" in content


def test_four_expected_bundles_are_configured() -> None:
    assert len(DEFAULT_BUNDLE_NAMES) == 4
    assert all(name.endswith(".bundle") for name in DEFAULT_BUNDLE_NAMES)


def test_extract_id_text_pairs_ignores_invalid_records() -> None:
    assert extract_id_text_pairs({"id": True, "text": "invalid", "other": {"id": 1, "text": "valid"}}) == [(1, "valid")]
