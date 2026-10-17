import csv
import json

import pytest

from suikoden_tool.text_batch import export_translation_batch, import_translation_batch


def write_catalog(path, entries):
    catalog = {
        "schema_version": 1,
        "resource": "text_add_en",
        "source_language": "en",
        "target_language": "pt-BR",
        "entries": entries,
    }
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return catalog


def read_catalog(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_batch_export_is_excel_compatible_and_preserves_unicode_and_newlines(tmp_path):
    catalog_path = tmp_path / "catalog.json"
    csv_path = tmp_path / "lote.csv"
    write_catalog(
        catalog_path,
        [
            {"id": 1, "original": "Hello∠world\nnext", "translation": "", "status": "pending"},
            {"id": "menu_start", "original": "Start", "translation": "", "status": "pending"},
            {"id": 3, "original": "Done", "translation": "Pronto", "status": "translated"},
        ],
    )

    result = export_translation_batch(catalog_path, csv_path, limit=1)

    assert result == {"exported": 1, "available": 2}
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [
        {
            "id": "1",
            "id_type": "int",
            "original": "Hello∠world\nnext",
            "translation": "",
            "status": "pending",
        }
    ]


def test_batch_import_updates_translation_and_keeps_original_intact(tmp_path):
    catalog_path = tmp_path / "catalog.json"
    csv_path = tmp_path / "lote.csv"
    original = "Line 1∠Line 2\ncontinued"
    write_catalog(
        catalog_path,
        [
            {"id": 1, "original": original, "translation": "", "status": "pending"},
            {"id": 2, "original": "Already translated", "translation": "Já traduzido", "status": "translated"},
        ],
    )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["id", "id_type", "original", "translation", "status"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "id": "1",
                "id_type": "int",
                "original": original,
                "translation": "Linha 1∠Linha 2\ncontinuação",
                "status": "pending",
            }
        )

    result = import_translation_batch(catalog_path, csv_path)
    catalog = read_catalog(catalog_path)

    assert result == {"updated": 1, "skipped_empty": 0, "rows": 1}
    assert catalog["entries"][0]["original"] == original
    assert catalog["entries"][0]["translation"] == "Linha 1∠Linha 2\ncontinuação"
    assert catalog["entries"][0]["status"] == "translated"
    assert catalog["entries"][1]["translation"] == "Já traduzido"


def test_batch_import_skips_empty_translation_without_erasing_existing_translation(tmp_path):
    catalog_path = tmp_path / "catalog.json"
    csv_path = tmp_path / "lote.csv"
    write_catalog(
        catalog_path,
        [{"id": 1, "original": "Hello", "translation": "Olá", "status": "translated"}],
    )
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "id_type", "original", "translation"])
        writer.writeheader()
        writer.writerow({"id": "1", "id_type": "int", "original": "Hello", "translation": ""})
    before = catalog_path.read_bytes()

    result = import_translation_batch(catalog_path, csv_path)

    assert result == {"updated": 0, "skipped_empty": 1, "rows": 1}
    assert catalog_path.read_bytes() == before


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (
            [
                {"id": "1", "id_type": "int", "original": "Hello", "translation": "Oi"},
                {"id": "1", "id_type": "int", "original": "Hello", "translation": "Olá"},
            ],
            "ID duplicado",
        ),
        (
            [{"id": "1", "id_type": "int", "original": "Changed", "translation": "Oi"}],
            "Texto original divergente",
        ),
        (
            [{"id": "99", "id_type": "int", "original": "Missing", "translation": "Oi"}],
            "não existe no catálogo",
        ),
    ],
)
def test_batch_import_rejects_invalid_rows_without_changing_catalog(tmp_path, rows, message):
    catalog_path = tmp_path / "catalog.json"
    csv_path = tmp_path / "lote.csv"
    write_catalog(
        catalog_path,
        [{"id": 1, "original": "Hello", "translation": "", "status": "pending"}],
    )
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "id_type", "original", "translation"])
        writer.writeheader()
        writer.writerows(rows)
    before = catalog_path.read_bytes()

    with pytest.raises(ValueError, match=message):
        import_translation_batch(catalog_path, csv_path)

    assert catalog_path.read_bytes() == before


def test_batch_import_keeps_needs_review_status(tmp_path):
    catalog_path = tmp_path / "catalog.json"
    csv_path = tmp_path / "lote.csv"
    write_catalog(
        catalog_path,
        [
            {
                "id": 7,
                "original": "Changed source",
                "translation": "Tradução anterior",
                "status": "needs_review",
                "source_changed": True,
                "previous_original": "Old source",
            }
        ],
    )
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "id_type", "original", "translation"])
        writer.writeheader()
        writer.writerow(
            {
                "id": "7",
                "id_type": "int",
                "original": "Changed source",
                "translation": "Nova tradução",
            }
        )

    import_translation_batch(catalog_path, csv_path)
    entry = read_catalog(catalog_path)["entries"][0]

    assert entry["translation"] == "Nova tradução"
    assert entry["status"] == "needs_review"
