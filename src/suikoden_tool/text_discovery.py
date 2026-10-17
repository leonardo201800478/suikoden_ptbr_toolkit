"""Descoberta de TextAssets em lotes de bundles Unity via UnityDataTool."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from suikoden_tool.unity_text_extractor import (
    _dump_textasset_fields,
    _run_tool,
    resolve_unity_data_tool,
)


def discover_text_assets(
    directory: Path,
    *,
    executable: Path | None = None,
    recursive: bool = True,
    timeout: int = 120,
) -> dict[str, Any]:
    """Inventaria TextAssets em bundles e amostra JSON textList sem modificar entradas."""
    root = Path(directory).expanduser().resolve()
    if not root.exists() or not (root.is_dir() or root.is_file()):
        raise ValueError(f"Arquivo ou diretório de bundles não encontrado: {root}")
    if timeout < 1:
        raise ValueError("O tempo limite precisa ser maior que zero.")

    tool = resolve_unity_data_tool(executable)
    if root.is_file():
        if root.suffix.casefold() != ".bundle":
            raise ValueError(f"O arquivo selecionado não tem extensão .bundle: {root}")
        bundles = [root]
    else:
        bundles = sorted(root.rglob("*.bundle") if recursive else root.glob("*.bundle"))
    report: list[dict[str, Any]] = []

    for bundle in bundles:
        data = bundle.read_bytes()
        record: dict[str, Any] = {
            "bundle": bundle.name,
            "path": str(bundle),
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "object_count": 0,
            "textasset_count": 0,
            "textassets": [],
            "error": None,
        }
        try:
            # AssetBundles can contain a SerializedFile named CAB-<hash>.
            # Enumerate archive entries first, then inspect each SerializedFile.
            entries: list[str | None] = []
            try:
                archive_output = _run_tool(
                    tool, ["archive", "list", str(bundle), "--format", "json"], timeout
                )
                archive_items = json.loads(archive_output)
                if isinstance(archive_items, list):
                    for item in archive_items:
                        if not isinstance(item, dict):
                            continue
                        entry_name = next(
                            (
                                item[key] for key in ("path", "name", "fileName", "filename")
                                if isinstance(item.get(key), str) and item[key].strip()
                            ),
                            None,
                        )
                        if entry_name and entry_name not in entries:
                            entries.append(entry_name)
            except (OSError, ValueError, json.JSONDecodeError):
                # Some UnityDataTool versions/bundles can be inspected without --entry.
                entries = []
            if not entries:
                entries = [None]

            for entry_name in entries:
                objectlist_args = [
                    "serialized-file", "objectlist", str(bundle), "--format", "json"
                ]
                if entry_name:
                    objectlist_args.extend(["--entry", entry_name])
                stdout = _run_tool(tool, objectlist_args, timeout)
                objects = json.loads(stdout)
                if not isinstance(objects, list):
                    raise TypeError("objectlist não retornou uma lista JSON.")
                record["object_count"] += len(objects)
                textassets = [
                    obj for obj in objects
                    if isinstance(obj, dict)
                    and str(obj.get("typeName", "")).casefold() == "textasset"
                    and isinstance(obj.get("id"), (int, str))
                    and not isinstance(obj.get("id"), bool)
                ]
                record["textasset_count"] += len(textassets)
                for obj in textassets:
                    object_id = str(obj["id"])
                    asset: dict[str, Any] = {
                        "object_id": object_id,
                        "entry": entry_name,
                        "name": None,
                        "textlist_count": None,
                        "sample_texts": [],
                        "json_textlist": False,
                        "error": None,
                    }
                    try:
                        dump_args = [
                            "dump", str(bundle), "--objectid", object_id, "--stdout"
                        ]
                        if entry_name:
                            dump_args.extend(["--entry", entry_name])
                        dump = _run_tool(tool, dump_args, timeout)
                        name, script = _dump_textasset_fields(dump)
                        asset["name"] = name
                        try:
                            payload = json.loads(script)
                        except json.JSONDecodeError:
                            payload = None
                        if isinstance(payload, dict) and isinstance(payload.get("textList"), list):
                            items = payload["textList"]
                            asset["json_textlist"] = True
                            asset["textlist_count"] = len(items)
                            asset["sample_texts"] = [
                                {"id": item.get("id"), "text": item.get("text")}
                                for item in items[:8] if isinstance(item, dict)
                            ]
                    except (OSError, ValueError, json.JSONDecodeError) as exc:
                        asset["error"] = str(exc)
                    record["textassets"].append(asset)
        except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
            record["error"] = str(exc)
        report.append(record)

    return {
        "schema_version": 1,
        "directory": str(root.parent if root.is_file() else root),
        "bundle_count": len(bundles),
        "bundles": report,
        "tool": str(tool),
    }
