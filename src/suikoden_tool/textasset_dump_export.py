"""Exportação integral de dumps TextAsset compatíveis com o fluxo do UABEA.

Não interpreta o conteúdo de m_Script como JSON: assim, dumps de menus,
licenças e recursos com caracteres de controle não são descartados.
Os bundles originais nunca são modificados.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


def _run_json(executable: Path, args: list[str], timeout: int) -> Any:
    try:
        result = subprocess.run(
            [str(executable), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"UnityDataTool excedeu {timeout} segundos.") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise ValueError(f"UnityDataTool falhou ({result.returncode}): {detail[-1200:]}")
    try:
        return json.loads(result.stdout.lstrip("\ufeff"))
    except json.JSONDecodeError as exc:
        raise ValueError("UnityDataTool retornou JSON inválido ao listar arquivos/objetos.") from exc


def _archive_entries(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for child in value.values():
            try:
                found = _archive_entries(child)
            except ValueError:
                continue
            if found and all("path" in item for item in found):
                return found
    raise ValueError("Formato inesperado na listagem do bundle.")


def _object_entries(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for child in value.values():
            if isinstance(child, list):
                matches = [item for item in child if isinstance(item, dict) and "typeName" in item and "id" in item]
                if matches:
                    return matches
    return []


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "TextAsset"


def export_textasset_dumps(
    bundles: list[Path] | tuple[Path, ...],
    executable: Path,
    output_dir: Path,
    *,
    timeout: int = 180,
    force: bool = False,
) -> dict[str, Any]:
    """Exporta cada TextAsset como dump bruto, sem exigir JSON válido em m_Script."""
    executable = Path(executable).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if not executable.is_file():
        raise FileNotFoundError(f"UnityDataTool não encontrado: {executable}")
    if not bundles:
        raise ValueError("Nenhum bundle foi informado.")
    exported: list[dict[str, Any]] = []
    errors: list[str] = []

    for bundle_value in bundles:
        bundle = Path(bundle_value).expanduser().resolve()
        if not bundle.is_file():
            errors.append(f"{bundle.name}: arquivo não encontrado")
            continue
        try:
            archive = _archive_entries(_run_json(
                executable, ["archive", "list", str(bundle), "-f", "Json"], timeout
            ))
        except (OSError, ValueError) as exc:
            errors.append(f"{bundle.name}: {exc}")
            continue
        serialized = [
            item for item in archive
            if "SerializedFile" in str(item.get("flags", ""))
            and isinstance(item.get("path"), str)
        ]
        if not serialized:
            errors.append(f"{bundle.name}: nenhum SerializedFile encontrado")
            continue

        for archive_item in serialized:
            entry = str(archive_item["path"])
            try:
                objects = _object_entries(_run_json(
                    executable,
                    ["serialized-file", "objectlist", str(bundle), "-e", entry, "-f", "Json"],
                    timeout,
                ))
            except (OSError, ValueError) as exc:
                errors.append(f"{bundle.name} [{entry}]: {exc}")
                continue
            for obj in objects:
                if str(obj.get("typeName", "")).casefold() != "textasset":
                    continue
                object_id = obj.get("id")
                if not isinstance(object_id, (str, int)) or isinstance(object_id, bool):
                    continue
                command = [
                    str(executable), "dump", str(bundle), "--objectid", str(object_id),
                    "--stdout", "-e", entry,
                ]
                try:
                    result = subprocess.run(
                        command, capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=timeout, check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    errors.append(f"{bundle.name} [{entry}] ID {object_id}: {exc}")
                    continue
                if result.returncode:
                    errors.append(
                        f"{bundle.name} [{entry}] ID {object_id}: "
                        f"{(result.stderr or result.stdout).strip()[-500:]}"
                    )
                    continue
                dump = result.stdout
                name_match = re.search(r"(?m)^\s*m_Name \(string\) (.*)$", dump)
                asset_name = name_match.group(1).strip() if name_match else f"TextAsset_{object_id}"
                # UABEA Import Dump expects the original TextAsset name and CAB entry/ID
                # identity in the filename; do not prepend the source bundle filename.
                filename = f"{_safe_name(asset_name)}-{_safe_name(Path(entry).stem)}-{object_id}.txt"
                destination = output_dir / filename
                if destination.exists() and not force:
                    errors.append(f"{filename}: já existe; exportação interrompida para preservar o arquivo")
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = destination.with_name("." + destination.name + ".tmp")
                try:
                    temporary.write_text(dump, encoding="utf-8", newline="")
                    temporary.replace(destination)
                finally:
                    if temporary.exists():
                        temporary.unlink()
                exported.append({
                    "bundle": bundle.name, "entry": entry, "asset_name": asset_name,
                    "object_id": object_id, "path": str(destination),
                    "bytes": destination.stat().st_size,
                })

    return {
        "exported_count": len(exported),
        "exported": exported,
        "errors": errors,
        "output_dir": str(output_dir),
    }
