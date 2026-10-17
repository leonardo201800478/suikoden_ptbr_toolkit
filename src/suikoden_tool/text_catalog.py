"""Operações seguras para catálogos de tradução exportados de TextAssets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
VALID_STATUSES = {"pending", "translated", "reviewed", "needs_review", "orphaned"}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em '{path}': {exc}") from exc


def _write_json(data: object, path: Path) -> None:
    """Grava primeiro em arquivo temporário e depois substitui o destino."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _source_entries(source: Path) -> tuple[list[dict[str, Any]], str]:
    data = _read_json(source)
    if not isinstance(data, dict) or not isinstance(data.get("textList"), list):
        raise ValueError("Formato inválido: esperado um objeto JSON com uma lista 'textList'.")  # noqa: TRY004

    entries: list[dict[str, Any]] = []
    seen_ids: set[tuple[type, object]] = set()
    for index, item in enumerate(data["textList"]):
        if not isinstance(item, dict):
            raise ValueError(f"Entrada {index} não é um objeto JSON.")  # noqa: TRY004
        if "id" not in item or "text" not in item:
            raise ValueError(f"Entrada {index} precisa conter 'id' e 'text'.")
        entry_id = item["id"]
        if isinstance(entry_id, bool) or not isinstance(entry_id, (str, int)):
            raise ValueError(f"ID da entrada {index} precisa ser string ou inteiro.")  # noqa: TRY004
        if not isinstance(item["text"], str):
            raise ValueError(f"O texto da entrada {index} precisa ser uma string.")  # noqa: TRY004
        key = (type(entry_id), entry_id)
        if key in seen_ids:
            raise ValueError(f"ID duplicado no catálogo de origem: {entry_id!r}.")
        seen_ids.add(key)
        entries.append({"id": entry_id, "original": item["text"]})
    return entries, source.stem


def _catalog_index(catalog: dict[str, Any]) -> dict[tuple[type, object], dict[str, Any]]:
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Catálogo inválido: 'entries' precisa ser uma lista.")  # noqa: TRY004
    indexed: dict[tuple[type, object], dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Entrada {index} do catálogo não é um objeto.")  # noqa: TRY004
        if "id" not in entry:
            raise ValueError(f"Entrada {index} do catálogo não contém 'id'.")
        entry_id = entry["id"]
        if isinstance(entry_id, bool) or not isinstance(entry_id, (str, int)):
            raise ValueError(f"ID da entrada {index} do catálogo precisa ser string ou inteiro.")  # noqa: TRY004
        key = (type(entry_id), entry_id)
        if key in indexed:
            raise ValueError(f"ID duplicado no catálogo existente: {entry_id!r}.")
        indexed[key] = entry
    return indexed


def export_text_catalog(
    source: Path,
    output: Path,
    target_language: str = "pt-BR",
) -> dict[str, Any]:
    """Cria ou mescla um catálogo sem descartar silenciosamente trabalho existente.

    Entradas compatíveis mantêm tradução/status. Texto de origem alterado gera
    needs_review e preserva a versão anterior. Entradas ausentes na nova fonte
    são mantidas como orphaned. O destino nunca pode ser o arquivo de origem.
    """
    if source.resolve() == output.resolve():
        raise ValueError("A entrada e a saída não podem ser o mesmo arquivo.")
    if not target_language.strip():
        raise ValueError("O idioma de destino não pode ser vazio.")

    source_entries, resource = _source_entries(source)
    if not output.exists():
        catalog = {
            "schema_version": SCHEMA_VERSION,
            "resource": resource,
            "source_language": "en",
            "target_language": target_language,
            "entries": [
                {**entry, "translation": "", "status": "pending"} for entry in source_entries
            ],
        }
        _write_json(catalog, output)
        return {
            "catalog": catalog,
            "created": len(source_entries),
            "preserved": 0,
            "changed": 0,
            "orphaned": 0,
            "new": len(source_entries),
        }

    existing = _read_json(output)
    if not isinstance(existing, dict) or existing.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            "O arquivo de saída existe, mas não é um catálogo compatível (schema_version 1)."
        )
    if existing.get("target_language") != target_language:
        raise ValueError(
            f"O catálogo existente usa {existing.get('target_language')!r}; "
            f"o destino solicitado é {target_language!r}. Não foi alterado."
        )
    if existing.get("resource") != resource:
        raise ValueError(
            f"O catálogo existente é do recurso {existing.get('resource')!r}, "
            f"mas a fonte é {resource!r}. Não foi alterado."
        )

    existing_report = validate_catalog(existing)
    if existing_report["errors"]:
        raise ValueError(
            "Catálogo existente inválido; não foi alterado: " + "; ".join(existing_report["errors"])
        )
    old_by_id = _catalog_index(existing)
    merged: list[dict[str, Any]] = []
    current_ids: set[tuple[type, object]] = set()
    preserved = changed = new = 0

    for fresh in source_entries:
        key = (type(fresh["id"]), fresh["id"])
        current_ids.add(key)
        old = old_by_id.get(key)
        if old is None:
            merged.append({**fresh, "translation": "", "status": "pending"})
            new += 1
            continue

        merged_entry = dict(old)
        merged_entry["id"] = fresh["id"]
        if old.get("original") != fresh["original"]:
            previous_original = old.get("original")
            merged_entry["previous_original"] = previous_original
            merged_entry["original"] = fresh["original"]
            merged_entry["source_changed"] = True
            merged_entry["status"] = "needs_review"
            changed += 1
        else:
            merged_entry["original"] = fresh["original"]
            if merged_entry.get("status") == "orphaned":
                merged_entry["status"] = (
                    "needs_review"
                    if merged_entry.get("source_changed")
                    else ("translated" if merged_entry.get("translation") else "pending")
                )
            preserved += 1
        merged.append(merged_entry)

    orphaned = 0
    for key, old in old_by_id.items():
        if key not in current_ids:
            orphan = dict(old)
            orphan["status"] = "orphaned"
            merged.append(orphan)
            orphaned += 1

    result = dict(existing)
    result.update(
        {
            "schema_version": SCHEMA_VERSION,
            "resource": resource,
            "source_language": existing.get("source_language", "en"),
            "target_language": target_language,
            "entries": merged,
        }
    )
    _write_json(result, output)
    return {
        "catalog": result,
        "created": 0,
        "preserved": preserved,
        "changed": changed,
        "orphaned": orphaned,
        "new": new,
    }


def _line_break_count(text: str) -> int:
    """Conta quebras CRLF, LF e CR como uma quebra lógica cada."""
    return text.count("\n") + text.count("\r") - text.count("\r\n")


def validate_catalog(catalog: Any, source: Path | None = None) -> dict[str, Any]:
    """Valida estrutura e conteúdo; source opcional compara com nova extração."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(catalog, dict):
        errors = ["A raiz do catálogo precisa ser um objeto."]
        return {
            "valid": False,
            "entry_count": 0,
            "error_count": len(errors),
            "warning_count": 0,
            "errors": errors,
            "warnings": [],
        }

    if catalog.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version precisa ser {SCHEMA_VERSION}.")
    for field in ("resource", "source_language", "target_language"):
        if not isinstance(catalog.get(field), str) or not catalog[field].strip():
            errors.append(f"Campo obrigatório inválido: {field}.")

    entries = catalog.get("entries")
    if not isinstance(entries, list):
        errors.append("Campo 'entries' precisa ser uma lista.")
        entries = []

    seen: set[tuple[type, object]] = set()
    valid_by_id: dict[tuple[type, object], dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"Entrada {index}: precisa ser um objeto.")
            continue
        entry_id = entry.get("id")
        if isinstance(entry_id, bool) or not isinstance(entry_id, (str, int)):
            errors.append(f"Entrada {index}: 'id' precisa ser string ou inteiro.")
            continue
        key = (type(entry_id), entry_id)
        if key in seen:
            errors.append(f"ID duplicado no catálogo: {entry_id!r}.")
        seen.add(key)
        valid_by_id[key] = entry

        if not isinstance(entry.get("original"), str):
            errors.append(f"Entrada {entry_id!r}: 'original' precisa ser string.")
        if not isinstance(entry.get("translation"), str):
            errors.append(f"Entrada {entry_id!r}: 'translation' precisa ser string.")
        status = entry.get("status")
        if not isinstance(status, str) or status not in VALID_STATUSES:
            errors.append(f"Entrada {entry_id!r}: status inválido {status!r}.")
        original = entry.get("original")
        translation = entry.get("translation")
        if isinstance(translation, str) and not translation.strip():
            warnings.append(f"Entrada {entry_id!r}: tradução pendente.")
        elif isinstance(original, str) and isinstance(translation, str):
            original_marker_count = original.count("∠")
            translation_marker_count = translation.count("∠")
            if original_marker_count != translation_marker_count:
                warnings.append(
                    f"Entrada {entry_id!r}: quantidade do marcador ∠ difere "
                    f"da origem ({original_marker_count} vs. {translation_marker_count}); "
                    "verifique antes de aprovar."
                )
            original_breaks = _line_break_count(original)
            translation_breaks = _line_break_count(translation)
            if original_breaks != translation_breaks:
                warnings.append(
                    f"Entrada {entry_id!r}: quantidade de quebras de linha difere "
                    f"da origem ({original_breaks} vs. {translation_breaks}); "
                    "verifique o layout antes de aprovar."
                )
        if "source_changed" in entry and not isinstance(entry["source_changed"], bool):
            errors.append(f"Entrada {entry_id!r}: 'source_changed' precisa ser booleano.")
        if "previous_original" in entry and not isinstance(entry["previous_original"], str):
            errors.append(f"Entrada {entry_id!r}: 'previous_original' precisa ser string.")
        if entry.get("source_changed") is True:
            warnings.append(f"Entrada {entry_id!r}: texto de origem mudou; revisar tradução.")
        if status == "pending" and isinstance(translation, str) and translation.strip():
            warnings.append(
                f"Entrada {entry_id!r}: tradução preenchida, mas status ainda é pending."
            )
        if status == "translated" and isinstance(translation, str) and not translation.strip():
            errors.append(f"Entrada {entry_id!r}: status translated exige tradução não vazia.")
        if status == "reviewed" and isinstance(translation, str) and not translation.strip():
            errors.append(f"Entrada {entry_id!r}: status reviewed exige tradução não vazia.")

    if source is not None:
        try:
            source_entries, _ = _source_entries(source)
        except (OSError, ValueError) as exc:
            errors.append(f"Não foi possível validar contra a fonte: {exc}")
        else:
            source_by_id = {
                (type(entry["id"]), entry["id"]): entry["original"] for entry in source_entries
            }
            for key, source_text in source_by_id.items():
                catalog_entry = valid_by_id.get(key)
                if catalog_entry is None:
                    warnings.append(f"ID novo na fonte, ausente do catálogo: {key[1]!r}.")
                elif catalog_entry.get("original") != source_text:
                    warnings.append(f"Texto de origem alterado para ID {key[1]!r}.")
            for key in valid_by_id:
                if key not in source_by_id:
                    warnings.append(f"ID do catálogo ausente na fonte: {key[1]!r}.")

    return {
        "valid": not errors,
        "entry_count": len(entries),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def catalog_stats(catalog: Any) -> dict[str, Any]:
    """Conta entradas pendentes, traduzidas e revisadas sem modificar o catálogo."""
    if not isinstance(catalog, dict) or not isinstance(catalog.get("entries"), list):
        raise ValueError("Catálogo inválido: esperado objeto JSON com lista 'entries'.")  # noqa: TRY004
    counts = {"pending": 0, "translated": 0, "reviewed": 0, "needs_review": 0, "orphaned": 0}
    for index, entry in enumerate(catalog["entries"]):
        if not isinstance(entry, dict):
            raise ValueError(f"Entrada {index} do catálogo não é um objeto.")  # noqa: TRY004
        status = entry.get("status")
        if not isinstance(status, str) or status not in VALID_STATUSES:
            raise ValueError(f"Entrada {index} tem status inválido: {status!r}.")
        counts[status] += 1
    total = len(catalog["entries"])
    return {
        "total": total,
        **counts,
        "completion_percent": round(
            100 * (total - counts["pending"] - counts["needs_review"] - counts["orphaned"]) / total,
            1,
        )
        if total
        else 0.0,
    }
