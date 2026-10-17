"""Converte dumps TextAsset do Unity em JSONs organizados e validados."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from suikoden_tool.text_extractor import _loads_textasset_json
from suikoden_tool.unity_text_extractor import _dump_textasset_fields


def _read_payload(source: Path) -> tuple[Any, str, str]:
    raw = source.read_text(encoding="utf-8-sig")
    asset_name = source.name.split("-CAB-", 1)[0]
    script = raw

    # Os .txt exportados pelo UnityDataTool/UABEA são dumps de objeto, não
    # necessariamente JSON puro. Converter o m_Script, não o envelope do dump.
    if "m_Script (string)" in raw:
        asset_name, script = _dump_textasset_fields(raw)

    try:
        payload: Any = _loads_textasset_json(script)
    except json.JSONDecodeError as exc:
        if asset_name.casefold().startswith("license_") or source.name.casefold().startswith("license_"):
            return {
                "schema_version": 1,
                "resource_type": "license_textasset",
                "source_file": source.name,
                "asset_name": asset_name,
                "content": script,
            }, asset_name, script
        position = exc.pos
        start = max(0, position - 100)
        end = min(len(script), position + 100)
        context = script[start:end]
        codepoints = " ".join(
            f"U+{ord(char):04X}" for char in script[max(0, position - 8):min(len(script), position + 8)]
        )
        raise ValueError(
            f"{source.name}: m_Script de {asset_name!r} não pode ser convertido em JSON "
            f"(linha {exc.lineno}, coluna {exc.colno}, posição {position}: {exc.msg}). "
            f"Contexto escapado: {context!r}. Caracteres próximos: {codepoints}. "
            "Nenhum JSON de saída foi gravado; o dump original foi preservado."
        ) from exc

    if isinstance(payload, dict) and "textList" in payload:
        text_list = payload["textList"]
        if not isinstance(text_list, list):
            raise ValueError(f"{source.name}: textList não é uma lista.")
        for index, item in enumerate(text_list):
            if not isinstance(item, dict) or "id" not in item or not isinstance(item.get("text"), str):
                raise ValueError(f"{source.name}: entrada textList[{index}] inválida.")
        return payload, asset_name, script

    if asset_name.casefold().startswith("license_") or source.name.casefold().startswith("license_"):
        return {
            "schema_version": 1,
            "resource_type": "license_textasset",
            "source_file": source.name,
            "asset_name": asset_name,
            "content": script,
        }, asset_name, script

    raise ValueError(
        f"{source.name}: JSON válido, mas não contém textList. "
        "O dump original foi preservado e nenhum arquivo foi gravado."
    )


def convert_textasset_dump(source: Path, destination: Path, *, overwrite: bool = True) -> dict[str, Any]:
    """Converte um dump TextAsset para JSON sem modificar a origem."""
    source = Path(source).expanduser().resolve()
    destination = Path(destination).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Arquivo fonte não encontrado: {source}")
    if source == destination:
        raise ValueError("A saída JSON não pode sobrescrever o dump original.")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"O JSON já existe: {destination}")

    payload, asset_name, _ = _read_payload(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        # Confirma que a saída é JSON válido antes de substituir a versão anterior.
        json.loads(temporary.read_text(encoding="utf-8"))
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    is_textlist = isinstance(payload, dict) and isinstance(payload.get("textList"), list)
    return {
        "source": str(source),
        "output": str(destination),
        "asset_name": asset_name,
        "kind": "textList" if is_textlist else "license",
        "entries": len(payload["textList"]) if is_textlist else 0,
        "bytes": destination.stat().st_size,
    }


def convert_textasset_batch(
    sources: list[Path], output_dir: Path, *, overwrite: bool = True
) -> list[dict[str, Any]]:
    """Converte cada arquivo independentemente; erros não cancelam os demais."""
    output_dir = Path(output_dir).expanduser().resolve()
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source in sources:
        source = Path(source)
        category = "licencas" if source.name.casefold().startswith("license_") else "catalogos"
        destination = output_dir / category / f"{source.stem}.json"
        try:
            results.append(convert_textasset_dump(source, destination, overwrite=overwrite))
        except (OSError, ValueError) as exc:
            errors.append({"source": str(source), "error": str(exc)})
    # Log persistente para diagnóstico; o contexto já vem escapado e não altera a origem.
    log_path = output_dir / "logs" / "conversao_textasset.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", newline="\n") as log_file:
        for item in results:
            if "batch_errors" not in item:
                log_file.write(json.dumps({"status": "ok", **item}, ensure_ascii=False) + "\n")
        for error in errors:
            log_file.write(json.dumps({"status": "error", **error}, ensure_ascii=False) + "\n")
    # Mantém retorno dos sucessos e erros estruturados para a GUI/CLI.
    if errors:
        results.append({"batch_errors": errors, "log_path": str(log_path)})
    else:
        results.append({"log_path": str(log_path)})
    return results
