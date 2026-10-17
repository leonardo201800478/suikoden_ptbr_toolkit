"""Exportação e importação segura de lotes CSV para tradução."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from suikoden_tool.text_catalog import validate_catalog

CSV_FIELDS = ("id", "id_type", "original", "translation", "status")


def _read_catalog(path: Path) -> dict[str, Any]:
    try:
        catalog = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em '{path}': {exc}") from exc
    report = validate_catalog(catalog)
    if not report["valid"]:
        raise ValueError("Catálogo inválido: " + "; ".join(report["errors"]))
    return catalog


def _write_catalog(path: Path, catalog: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def export_translation_batch(
    catalog_path: Path,
    output_path: Path,
    limit: int | None = 100,
    include_needs_review: bool = True,
) -> dict[str, int]:
    """Exporta entradas pendentes para CSV UTF-8 com BOM, compatível com Excel."""
    if limit is not None and limit < 1:
        raise ValueError("O limite do lote precisa ser maior que zero.")
    if catalog_path.resolve() == output_path.resolve():
        raise ValueError("O CSV de saída não pode sobrescrever o catálogo.")

    catalog = _read_catalog(catalog_path)
    allowed_statuses = {"pending"}
    if include_needs_review:
        allowed_statuses.add("needs_review")
    selected = [
        entry for entry in catalog["entries"] if entry["status"] in allowed_statuses
    ]
    if limit is not None:
        selected = selected[:limit]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for entry in selected:
            entry_id = entry["id"]
            writer.writerow(
                {
                    "id": str(entry_id),
                    "id_type": (
                        "int"
                        if isinstance(entry_id, int) and not isinstance(entry_id, bool)
                        else "str"
                    ),
                    "original": entry["original"],
                    "translation": entry["translation"],
                    "status": entry["status"],
                }
            )
    return {"exported": len(selected), "available": len([
        entry for entry in catalog["entries"] if entry["status"] in allowed_statuses
    ])}


def import_translation_batch(catalog_path: Path, input_path: Path) -> dict[str, int]:
    """Importa traduções sem editar originais ou limpar traduções com células vazias.

    A importação é validada integralmente antes de gravar o catálogo. Entradas
    com status needs_review continuam nesse status para exigir revisão humana.
    """
    if catalog_path.resolve() == input_path.resolve():
        raise ValueError("O CSV de entrada não pode ser o arquivo do catálogo.")
    catalog = _read_catalog(catalog_path)

    with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"id", "id_type", "original", "translation"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(
                "CSV inválido: colunas obrigatórias: id, id_type, original, translation."
            )
        rows = list(reader)

    by_id: dict[tuple[type, object], dict[str, Any]] = {}
    for entry in catalog["entries"]:
        entry_id = entry["id"]
        by_id[(type(entry_id), entry_id)] = entry

    parsed_rows: list[tuple[dict[str, Any], str]] = []
    seen: set[tuple[type, object]] = set()
    for line_number, row in enumerate(rows, start=2):
        id_text = row.get("id")
        id_type = row.get("id_type")
        original = row.get("original")
        translation = row.get("translation")
        if (
            not isinstance(id_text, str)
            or not isinstance(id_type, str)
            or not isinstance(original, str)
            or not isinstance(translation, str)
        ):
            raise TypeError(f"Linha {line_number}: contém coluna ou valor ausente ou de tipo inválido.")
        if id_type == "int":
            if not re.fullmatch(r"-?\d+", id_text):
                raise ValueError(f"Linha {line_number}: ID inteiro inválido: {id_text!r}.")
            key = (int, int(id_text))
        elif id_type == "str":
            key = (str, id_text)
        else:
            raise ValueError(f"Linha {line_number}: id_type precisa ser 'int' ou 'str'.")

        if key in seen:
            raise ValueError(f"ID duplicado no CSV na linha {line_number}: {id_text!r}.")
        seen.add(key)
        entry = by_id.get(key)
        if entry is None:
            raise ValueError(
                f"ID do CSV não existe no catálogo (linha {line_number}): {id_text!r}."
            )
        if original != entry["original"]:
            raise ValueError(
                f"Texto original divergente para ID {id_text!r} na linha {line_number}; "
                "catálogo não foi alterado."
            )
        parsed_rows.append((entry, translation))

    updated = skipped_empty = 0
    for entry, translation in parsed_rows:
        if not translation.strip():
            skipped_empty += 1
            continue
        entry["translation"] = translation
        if entry["status"] != "needs_review":
            entry["status"] = "translated"
        updated += 1

    if updated:
        _write_catalog(catalog_path, catalog)
    return {"updated": updated, "skipped_empty": skipped_empty, "rows": len(rows)}
