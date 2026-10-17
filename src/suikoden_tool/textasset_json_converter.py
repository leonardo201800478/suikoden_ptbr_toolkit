"""Converte dumps TextAsset em JSON válido numa pasta separada."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def convert_textasset_dump(source: Path, destination: Path, *, overwrite: bool = True) -> dict[str, Any]:
    """Converte um TextAsset exportado em JSON e preserva o arquivo de origem.

    Dumps de textList são lidos como JSON diretamente. Recursos de licença, que
    são texto/HTML e não JSON, são encapsulados num objeto JSON com o conteúdo
    original integral no campo `content`.
    """
    source = Path(source).expanduser().resolve()
    destination = Path(destination).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Arquivo fonte não encontrado: {source}")
    if source == destination:
        raise ValueError("A saída JSON não pode sobrescrever o dump original.")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"O JSON já existe: {destination}")

    raw = source.read_text(encoding="utf-8-sig")
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError:
        if not source.stem.casefold().startswith("license_"):
            raise ValueError(
                f"{source.name}: conteúdo não é JSON válido nem um dump de licença conhecido. "
                "O arquivo original foi preservado."
            )
        payload = {
            "schema_version": 1,
            "resource_type": "license_textasset",
            "source_file": source.name,
            "asset_name": source.name.split("-CAB-", 1)[0],
            "content": raw,
        }

    if isinstance(payload, dict) and "textList" in payload:
        text_list = payload["textList"]
        if not isinstance(text_list, list):
            raise ValueError(f"{source.name}: textList não é uma lista.")
        for index, item in enumerate(text_list):
            if not isinstance(item, dict) or "id" not in item or not isinstance(item.get("text"), str):
                raise ValueError(f"{source.name}: entrada textList[{index}] inválida.")
    elif not (isinstance(payload, dict) and payload.get("resource_type") == "license_textasset"):
        raise ValueError(f"{source.name}: JSON válido, mas não contém uma estrutura textList reconhecida.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Reabrir o arquivo antes de substituir o destino é uma validação final.
        json.loads(temporary.read_text(encoding="utf-8"))
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "source": str(source),
        "output": str(destination),
        "kind": "textList" if isinstance(payload, dict) and "textList" in payload else "license",
        "entries": len(payload["textList"]) if isinstance(payload, dict) and isinstance(payload.get("textList"), list) else 0,
        "bytes": destination.stat().st_size,
    }


def convert_textasset_batch(sources: list[Path], output_dir: Path, *, overwrite: bool = True) -> list[dict[str, Any]]:
    """Converte vários dumps em subpastas organizadas, mantendo os nomes-base."""
    output_dir = Path(output_dir).expanduser().resolve()
    results = []
    for source in sources:
        source = Path(source)
        category = "licencas" if source.stem.casefold().startswith("license_") else "catalogos"
        destination = output_dir / category / f"{source.stem}.json"
        results.append(convert_textasset_dump(source, destination, overwrite=overwrite))
    return results
