"""Extração de textos de bundles Unity usando UnityDataTool.

A ferramenta externa é responsável por ler o formato serializado Unity. Este módulo
orquestra os comandos, identifica TextAssets e constrói um catálogo sem alterar os
bundles originais. Marcadores '?' são mantidos exatamente como aparecem no texto.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from suikoden_tool.unity_text_extractor import _dump_textasset_fields

def _loads_textasset_json(script: str) -> Any:
    """Carrega JSON de TextAsset escapando controles crus dentro de strings.

    UnityDataTool pode emitir caracteres U+0000..U+001F literalmente dentro dos
    valores. Escapá-los para o parser JSON preserva o caractere no texto resultante.
    Não altera '?' nem outros caracteres imprimíveis.
    """
    try:
        return json.loads(script)
    except json.JSONDecodeError as original_error:
        repaired: list[str] = []
        in_string = False
        escaped = False
        changed = False
        for char in script:
            code = ord(char)
            if in_string and code < 0x20:
                repaired.append(f"\\u{code:04x}")
                changed = True
                escaped = False
                continue
            repaired.append(char)
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
        if changed:
            try:
                return json.loads("".join(repaired))
            except json.JSONDecodeError:
                pass
        raise original_error


DEFAULT_BUNDLE_NAMES = (
    "03cf0288ba3ecaca0776d7fadf1f0bb6.bundle",
    "0573e2f60d0cda7892d60f38dfd7282c.bundle",
    "49d65af6f8fea7a9e8008c6b2c688fc3.bundle",
    "700bf7ec8ded4a20613b92988e3f8142.bundle",
)

@dataclass(frozen=True)
class ExtractedText:
    game: str
    bundle: str
    asset_path: str
    object_path_id: int | str
    text_id: int | str
    source_text: str
    control_tokens: tuple[str, ...]

    def as_json(self) -> dict[str, Any]:
        return {
            "id": f"{self.game}:{self.bundle}:{self.object_path_id}:{self.text_id}",
            "game": self.game,
            "bundle": self.bundle,
            "asset_path": self.asset_path,
            "object_path_id": self.object_path_id,
            "text_id": self.text_id,
            "source_text": self.source_text,
            "translation_pt_br": "",
            "control_tokens": list(self.control_tokens),
            "status": "untranslated",
        }


def _run_json(command: list[str]) -> Any:
    """Executa UnityDataTool e interpreta a saída JSON sem despejá-la no terminal."""
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"UnityDataTool falhou ({completed.returncode}): {detail[:1200]}")
    try:
        return json.loads(completed.stdout.lstrip("\ufeff"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"A saída de UnityDataTool não é JSON válido para: {' '.join(command)}") from exc


def _records(value: Any) -> Iterable[dict[str, Any]]:
    """Percorre estruturas JSON e devolve todos os objetos encontrados."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _records(child)
    elif isinstance(value, list):
        for child in value:
            yield from _records(child)


def extract_id_text_pairs(value: Any) -> list[tuple[int | str, str]]:
    """Extrai pares {id, text} de JSON aninhado, mantendo texto e marcadores intactos."""
    found: list[tuple[int | str, str]] = []
    seen: set[tuple[str, str]] = set()
    for record in _records(value):
        if "id" not in record or not isinstance(record.get("text"), str):
            continue
        entry_id = record["id"]
        if not isinstance(entry_id, (str, int)) or isinstance(entry_id, bool):
            continue
        key = (str(entry_id), record["text"])
        if key not in seen:
            found.append((entry_id, record["text"]))
            seen.add(key)
    return found


def find_control_tokens(text: str) -> tuple[str, ...]:
    """Registra marcadores observados sem assumir que '?' seja uma quebra de linha.

    O dump observado usa '?' em posições que podem representar controles. O token é
    anotado para revisão, mas o texto original nunca é normalizado nem substituído.
    """
    tokens: list[str] = []
    if "?" in text:
        tokens.append("?")
    # Registra padrões comuns de tags de localização, caso existam em outros assets.
    for token in re.findall(r"\{[^{}]+\}|<[^<>]+>", text):
        if token not in tokens:
            tokens.append(token)
    return tuple(tokens)


def _parse_archive_entries(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    for record in _records(data):
        if isinstance(record.get("path"), str) and "flags" in record:
            return [item for item in _records(data) if isinstance(item.get("path"), str) and "flags" in item]
    raise ValueError("Formato inesperado na resposta de 'archive list'.")


def _parse_object_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return [item for item in _records(data) if "typeName" in item and "id" in item]


def extract_from_bundles(
    bundles_dir: Path,
    unity_data_tool: Path,
    output_json: Path,
    bundle_names: Iterable[str] = DEFAULT_BUNDLE_NAMES,
) -> dict[str, Any]:
    """Extrai TextAssets dos bundles definidos e grava catálogo JSON.

    Apenas entradas `SerializedFile` são processadas; recursos `.resS` são ignorados.
    O programa não modifica nenhum bundle original.
    """
    bundles_dir, unity_data_tool, output_json = Path(bundles_dir), Path(unity_data_tool), Path(output_json)
    if not unity_data_tool.is_file():
        raise FileNotFoundError(f"UnityDataTool não encontrado: {unity_data_tool}")
    missing = [name for name in bundle_names if not (bundles_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("Bundles não encontrados: " + ", ".join(missing))

    entries: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for bundle_name in bundle_names:
        bundle = bundles_dir / bundle_name
        archive = _parse_archive_entries(_run_json([str(unity_data_tool), "archive", "list", str(bundle), "-f", "Json"]))
        serialized = [item for item in archive if "SerializedFile" in str(item.get("flags", ""))]
        bundle_text_count = 0
        for archive_entry in serialized:
            asset_path = str(archive_entry["path"])
            object_list = _parse_object_list(_run_json([
                str(unity_data_tool), "serialized-file", "objectlist", str(bundle), "-e", asset_path, "-f", "Json"
            ]))
            text_assets = [obj for obj in object_list if str(obj.get("typeName", "")).casefold() == "textasset"]
            for obj in text_assets:
                object_id = obj.get("id")
                dumped = subprocess.run(
                    [str(unity_data_tool), "dump", str(bundle), "--objectid", str(object_id), "--stdout", "-e", asset_path],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                )
                if dumped.returncode:
                    diagnostics.append({"bundle": bundle_name, "asset_path": asset_path, "object_path_id": object_id,
                                        "error": (dumped.stderr or dumped.stdout).strip()[:1200]})
                    continue
                # UnityDataTool dump inclui cabeçalho e campos serializados antes de m_Script.
                # Interpretar stdout inteiro como JSON faz a extração ignorar todos os TextAssets.
                try:
                    asset_name, script = _dump_textasset_fields(dumped.stdout.lstrip("\ufeff"))
                except ValueError as exc:
                    diagnostics.append({
                        "bundle": bundle_name,
                        "asset_path": asset_path,
                        "object_path_id": object_id,
                        "warning": f"Não foi possível localizar m_Script: {exc}",
                    })
                    continue

                try:
                    payload = _loads_textasset_json(script)
                    if not isinstance(payload, dict) or not isinstance(payload.get("textList"), list):
                        diagnostics.append({
                            "bundle": bundle_name,
                            "asset_path": asset_path,
                            "object_path_id": object_id,
                            "asset_name": asset_name,
                            "info": "TextAsset ignorado: não contém objeto JSON com lista textList.",
                        })
                        continue
                    pairs = extract_id_text_pairs(payload)
                except json.JSONDecodeError as exc:
                    # Alguns dumps podem conter JSON parcial/serialização com escapes inválidos.
                    # Mantemos diagnóstico detalhado em vez de descartar silenciosamente o objeto.
                    diagnostics.append({
                        "bundle": bundle_name,
                        "asset_path": asset_path,
                        "object_path_id": object_id,
                        "asset_name": asset_name,
                        "warning": "m_Script não contém JSON válido.",
                        "json_error": str(exc),
                        "script_preview": script[:1000],
                    })
                    continue
                for text_id, text in pairs:
                    entry = ExtractedText(
                        game="unknown", bundle=bundle_name, asset_path=asset_path,
                        object_path_id=object_id, text_id=text_id, source_text=text,
                        control_tokens=find_control_tokens(text),
                    ).as_json()
                    entries.append(entry)
                bundle_text_count += len(pairs)
        diagnostics.append({"bundle": bundle_name, "serialized_files": len(serialized), "text_entries": bundle_text_count})

    # Evita duplicação idêntica quando o mesmo ID/texto aparece em assets repetidos.
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        key = (str(entry["text_id"]), entry["source_text"], entry["bundle"])
        if key not in seen:
            unique.append(entry)
            seen.add(key)
    catalog = {
        "schema_version": 1,
        "project": "Suikoden I & II HD Remaster PT-BR",
        "source": "UnityDataTool TextAsset extraction",
        "entry_count": len(unique),
        "entries": unique,
        "diagnostics": diagnostics,
        "notes": ["Marcadores '?' foram preservados literalmente; não foram convertidos em quebras de linha.",
                  "Bundles originais não foram modificados."]
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return catalog


def export_catalog_csv(catalog_json: Path, output_csv: Path) -> int:
    """Exporta catálogo JSON para CSV com colunas simples para tradução manual."""
    payload = json.loads(Path(catalog_json).read_text(encoding="utf-8-sig"))
    entries = payload.get("entries", [])
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "game", "bundle", "text_id", "source_text", "translation_pt_br", "control_tokens", "status"]
    with output_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for entry in entries:
            row = dict(entry)
            row["control_tokens"] = " | ".join(row.get("control_tokens", []))
            writer.writerow(row)
    return len(entries)
