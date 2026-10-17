"""Importa dumps TextAsset brutos para catálogos editáveis sem alterar os dumps."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from suikoden_tool.text_extractor import _loads_textasset_json
from suikoden_tool.unity_text_extractor import _dump_textasset_fields


def _load_textasset_payload(script: str) -> Any:
    """Carrega JSON e tenta apenas reparos estruturais conservadores."""
    try:
        return _loads_textasset_json(script)
    except json.JSONDecodeError as original_error:
        # Alguns TextAssets têm objetos adjacentes sem vírgula entre eles.
        # Só inserimos vírgula entre tokens estruturais fora de strings; nunca
        # alteramos pontuação dentro de diálogos.
        repaired: list[str] = []
        in_string = False
        escaped = False
        index = 0
        changed = False
        while index < len(script):
            char = script[index]
            repaired.append(char)
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                index += 1
                continue
            if char == '"':
                in_string = True
                index += 1
                continue
            if char in "}]":
                lookahead = index + 1
                while lookahead < len(script) and script[lookahead].isspace():
                    lookahead += 1
                if lookahead < len(script) and script[lookahead] in '{["' and script[lookahead] != ',':
                    # Adjacência de valores só é válida se separada por vírgula.
                    repaired.append(",")
                    changed = True
            index += 1
        if changed:
            try:
                return _loads_textasset_json("".join(repaired))
            except json.JSONDecodeError:
                pass
        raise original_error


def import_dump_to_catalog(\n    dump_path: Path, output_path: Path | None = None, *, overwrite: bool = False\n) -> dict[str, Any]:
    """Lê um dump UnityDataTool/UABEA e cria um catálogo JSON editável.

    O dump fonte permanece intacto. Cada arquivo gera seu próprio catálogo, evitando
    colisões entre IDs iguais encontrados em TextAssets diferentes.
    """
    dump_path = Path(dump_path).expanduser().resolve()
    if not dump_path.is_file():
        raise FileNotFoundError(f"Dump não encontrado: {dump_path}")
    dump = dump_path.read_text(encoding="utf-8-sig")
    asset_name, script = _dump_textasset_fields(dump)
    try:
        payload = _load_textasset_payload(script)
    except json.JSONDecodeError as exc:
        start = max(0, exc.pos - 100)
        end = min(len(script), exc.pos + 100)
        context = script[start:end].replace("\\r", "\\\\r").replace("\\n", "\\\\n").replace("\\t", "\\\\t")
        raise ValueError(
            f"{dump_path.name}: o m_Script do TextAsset {asset_name!r} não é JSON válido "
            f"(linha {exc.lineno}, coluna {exc.colno}; {exc.msg}). "
            f"Trecho próximo ao erro: {context!r}. O dump original foi preservado."
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("textList"), list):
        raise ValueError(
            f"{dump_path.name}: TextAsset {asset_name!r} não contém uma lista JSON 'textList'. "
            "O dump foi preservado; este recurso precisa de um adaptador específico."
        )

    entries: list[dict[str, Any]] = []
    seen: set[tuple[type, object]] = set()
    for index, item in enumerate(payload["textList"]):
        if not isinstance(item, dict) or "id" not in item or not isinstance(item.get("text"), str):
            raise ValueError(
                f"{dump_path.name}: item textList[{index}] não contém id e text string válidos."
            )
        entry_id = item["id"]
        if isinstance(entry_id, bool) or not isinstance(entry_id, (str, int)):
            raise ValueError(f"{dump_path.name}: ID inválido em textList[{index}].")
        key = (type(entry_id), entry_id)
        if key in seen:
            raise ValueError(f"{dump_path.name}: ID duplicado {entry_id!r} em textList.")
        seen.add(key)
        entries.append({
            "id": entry_id,
            "original": item["text"],
            "translation": "",
            "status": "pending",
        })

    resource = dump_path.stem
    catalog = {
        "schema_version": 1,
        "resource": resource,
        "source_language": "en",
        "target_language": "pt-BR",
        "source_dump": dump_path.name,
        "asset_name": asset_name,
        "entries": entries,
    }
    destination = Path(output_path).expanduser().resolve() if output_path else dump_path.with_suffix(".catalog.json")
    if destination == dump_path:
        raise ValueError("O catálogo não pode sobrescrever o dump original.")
    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"O catálogo já existe e não será sobrescrito: {destination}. "
            "Escolha outro destino ou habilite a substituição."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "dump": str(dump_path),
        "catalog_path": str(destination),
        "asset_name": asset_name,
        "entries": len(entries),
    }


def import_dump_batch(paths: list[Path]) -> list[dict[str, Any]]:
    """Importa vários dumps; cada catálogo é gravado separadamente."""
    results = []
    for path in paths:
        results.append(import_dump_to_catalog(Path(path)))
    return results
