from pathlib import Path

import pytest

from suikoden_tool.uabea_textasset_workflow import (
    compare_uabea_textassets,
    prepare_uabea_import,
    sha256_file,
)


def test_prepare_import_copies_same_name_and_exact_bytes(tmp_path: Path):
    raw = b"\xef\xbb\xbfName\r\nA\x18\x19\x1a\x1b\xff\x00"
    source = tmp_path / "text_gsd1_en.txt"
    source.write_bytes(raw)

    result = prepare_uabea_import(source, tmp_path / "import")

    destination = tmp_path / "import" / source.name
    assert destination.is_file()
    assert destination.read_bytes() == raw
    assert result["file_name"] == source.name
    assert result["byte_identical"] is True
    assert result["sha256"] == sha256_file(source)


def test_prepare_import_does_not_overwrite_without_explicit_permission(tmp_path: Path):
    source = tmp_path / "text_gsd1_en.txt"
    source.write_bytes(b"original")
    destination_dir = tmp_path / "import"
    destination_dir.mkdir()
    (destination_dir / source.name).write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        prepare_uabea_import(source, destination_dir)

    assert (destination_dir / source.name).read_bytes() == b"existing"


def test_prepare_import_overwrite_is_explicit_and_exact(tmp_path: Path):
    source = tmp_path / "text_gsd1_en.txt"
    source.write_bytes(b"translated\r\ncontent")
    destination_dir = tmp_path / "import"
    destination_dir.mkdir()
    (destination_dir / source.name).write_bytes(b"old")

    prepare_uabea_import(source, destination_dir, overwrite=True)

    assert (destination_dir / source.name).read_bytes() == source.read_bytes()


def test_compare_reports_exact_round_trip_and_differences(tmp_path: Path):
    exported = tmp_path / "exported.txt"
    round_trip = tmp_path / "roundtrip.txt"
    edited = tmp_path / "edited.txt"
    exported.write_bytes(b"A\r\nB\x18")
    round_trip.write_bytes(b"A\r\nB\x18")
    edited.write_bytes(b"A\nB\x18")

    assert compare_uabea_textassets(exported, round_trip)["byte_identical"] is True
    result = compare_uabea_textassets(exported, edited)
    assert result["byte_identical"] is False
    assert result["first_sha256"] != result["second_sha256"]


def test_rejects_non_txt_file(tmp_path: Path):
    source = tmp_path / "asset.json"
    source.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="exige o arquivo .txt"):
        prepare_uabea_import(source, tmp_path / "import")


def test_rejects_missing_source(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        prepare_uabea_import(tmp_path / "missing.txt", tmp_path / "import")
