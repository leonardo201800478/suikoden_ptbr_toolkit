"""Extração conservadora de TextAssets via UnityDataTool."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def resolve_unity_data_tool(executable: Path | None = None) -> Path:
    """Resolve o executável sem depender de um caminho absoluto fixo."""
    if executable is not None:
        candidate = Path(executable).expanduser()
        if candidate.is_file():
            return candidate.resolve()
        raise ValueError(f"UnityDataTool não encontrado no caminho informado: {candidate}")

    configured = os.environ.get("UNITY_DATA_TOOL", "").strip()
    if configured:
        return resolve_unity_data_tool(Path(configured))

    on_path = shutil.which("UnityDataTool.exe") or shutil.which("UnityDataTool")
    if on_path:
        return Path(on_path).resolve()

    local_candidate = Path("tools") / "UnityDataTools" / "UnityDataTool.exe"
    if local_candidate.is_file():
        return local_candidate.resolve()

    raise ValueError(
        "UnityDataTool não encontrado. Use --tool, configure UNITY_DATA_TOOL ou coloque "
        "UnityDataTool.exe em tools/UnityDataTools."
    )


def _run_tool(
    executable: Path,
    arguments: list[str],
    timeout: int,
) -> str:
    try:
        result = subprocess.run(
            [str(executable), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"UnityDataTool excedeu o tempo limite de {timeout} segundos.") from exc
    except OSError as exc:
        raise ValueError(f"Não foi possível executar UnityDataTool: {exc}") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "sem detalhes"
        raise ValueError(
            f"UnityDataTool falhou (código {result.returncode}): {detail[-1500:]}"
        )
    return result.stdout


def _dump_textasset_fields(dump: str) -> tuple[str, str]:
    """Extrai nome e m_Script do dump de um único objeto TextAsset."""
    name_match = re.search(r"(?m)^\s*m_Name \(string\) (.*)$", dump)
    script_match = re.search(r"(?m)^\s*m_Script \(string\) ", dump)
    if name_match is None or script_match is None:
        raise ValueError("O dump não contém os campos m_Name e m_Script esperados.")

    # Não aplicar strip/rstrip ao conteúdo: espaços, CR/LF e caracteres de controle
    # podem fazer parte do TextAsset. O dump bruto deve ser preservado; parsers como
    # json.loads aceitam whitespace externo quando o conteúdo é JSON.
    name = name_match.group(1)
    script_start = script_match.end()
    script = dump[script_start:]
    if not script:
        raise ValueError(f"TextAsset {name!r} tem m_Script vazio.")
    return name, script


def extract_textasset_json(
    bundle: Path,
    output: Path,
    *,
    executable: Path | None = None,
    entry: str | None = None,
    asset_name: str | None = None,
    timeout: int = 120,
    force: bool = False,
) -> dict[str, Any]:
    """Extrai o JSON textList de um TextAsset sem modificar o bundle original.

    Quando há vários TextAssets JSON compatíveis, exige --asset-name para evitar
    escolher um recurso arbitrário. Um arquivo de saída existente só é substituído
    mediante force=True.
    """
    bundle = Path(bundle).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if not bundle.is_file():
        raise FileNotFoundError(f"Bundle não encontrado: {bundle}")
    if bundle == output:
        raise ValueError("A saída não pode sobrescrever o bundle original.")
    if output.exists() and not force:
        raise ValueError(f"O arquivo de saída já existe; use --force para substituir: {output}")
    if timeout < 1:
        raise ValueError("O tempo limite precisa ser maior que zero.")

    tool = resolve_unity_data_tool(executable)
    objectlist_args = ["serialized-file", "objectlist", str(bundle), "--format", "json"]
    if entry:
        objectlist_args.extend(["--entry", entry])
    objectlist_output = _run_tool(tool, objectlist_args, timeout)
    try:
        objects = json.loads(objectlist_output)
    except json.JSONDecodeError as exc:
        raise ValueError("UnityDataTool não retornou JSON válido para objectlist.") from exc
    if not isinstance(objects, list):
        raise TypeError("O objectlist retornado pelo UnityDataTool não é uma lista.")

    textassets = [
        obj for obj in objects
        if isinstance(obj, dict)
        and str(obj.get("typeName", "")).casefold() == "textasset"
        and isinstance(obj.get("id"), (int, str))
        and not isinstance(obj.get("id"), bool)
    ]
    if not textassets:
        raise ValueError("Nenhum objeto TextAsset foi encontrado nesse bundle/entrada.")

    candidates: list[tuple[str, dict[str, Any]]] = []
    failures: list[str] = []
    for obj in textassets:
        object_id = str(obj["id"])
        dump_args = ["dump", str(bundle), "--objectid", object_id, "--stdout"]
        if entry:
            dump_args.extend(["--entry", entry])
        try:
            dump = _run_tool(tool, dump_args, timeout)
            name, script = _dump_textasset_fields(dump)
            payload = json.loads(script)
        except ValueError as exc:
            failures.append(f"ID {object_id}: {exc}")
            continue
        if isinstance(payload, dict) and isinstance(payload.get("textList"), list):
            candidates.append((name, payload))

    if asset_name is not None:
        matches = [(name, payload) for name, payload in candidates if name == asset_name]
        if len(matches) != 1:
            available = ", ".join(name for name, _ in candidates) or "nenhum TextAsset JSON compatível"
            raise ValueError(
                f"TextAsset {asset_name!r} não encontrado de forma única. Disponíveis: {available}"
            )
        selected_name, payload = matches[0]
    elif len(candidates) == 1:
        selected_name, payload = candidates[0]
    elif len(candidates) > 1:
        available = ", ".join(name for name, _ in candidates)
        raise ValueError(
            f"Foram encontrados vários TextAssets com textList ({available}); "
            "informe --asset-name para selecionar um."
        )
    else:
        detail = "; ".join(failures[:4]) or "nenhum objeto continha um JSON com lista textList"
        raise ValueError(f"Não foi possível extrair um TextAsset com textList: {detail}")

    for index, item in enumerate(payload["textList"]):
        if not isinstance(item, dict) or "id" not in item or not isinstance(item.get("text"), str):
            raise ValueError(
                f"TextAsset {selected_name!r}: entrada {index} não contém id e text string válidos."
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.extract.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "asset_name": selected_name,
        "entry": entry,
        "object_count": len(objects),
        "textasset_count": len(textassets),
        "text_count": len(payload["textList"]),
        "output": str(output),
        "tool": str(tool),
    }
