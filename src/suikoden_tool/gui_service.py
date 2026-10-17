"""Serviços seguros usados pela interface gráfica de tradução."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

from suikoden_tool.text_catalog import catalog_stats, validate_catalog


def load_catalog(path: Path) -> dict[str, Any]:
    """Carrega e valida um catálogo sem modificá-lo."""
    try:
        catalog = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em '{path}': {exc}") from exc
    report = validate_catalog(catalog)
    if not report["valid"]:
        raise ValueError("Catálogo inválido: " + "; ".join(report["errors"]))
    return catalog


def save_entry(
    path: Path,
    entry_id: str | int,
    translation: str,
    status: str = "translated",
) -> dict[str, Any]:
    """Atualiza somente tradução/status da entrada identificada e grava atomicamente."""
    if status not in {"translated", "reviewed"}:
        raise ValueError("O status de gravação precisa ser 'translated' ou 'reviewed'.")
    if not translation.strip():
        raise ValueError("A tradução não pode ficar vazia.")
    catalog = load_catalog(path)
    matches = [
        entry
        for entry in catalog["entries"]
        if type(entry.get("id")) is type(entry_id) and entry.get("id") == entry_id
    ]
    if len(matches) != 1:
        raise ValueError(f"ID não encontrado ou ambíguo no catálogo: {entry_id!r}.")
    entry = matches[0]
    if entry.get("status") == "orphaned":
        raise ValueError("Entradas órfãs não podem ser editadas pela interface.")
    if entry.get("status") == "needs_review" and status == "translated":
        # Exige ação explícita de revisão para não ocultar uma mudança na fonte.
        raise ValueError("Esta entrada precisa ser salva como revisada.")
    entry["translation"] = translation
    entry["status"] = status
    _atomic_write(path, catalog)
    return entry


def _atomic_write(path: Path, catalog: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.gui.tmp")
    try:
        temporary.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def suggest_translation(original: str, context: str = "") -> str:
    """Pede uma sugestão a uma API compatível com OpenAI, sem gravar no catálogo.

    Configure OPENAI_API_KEY no ambiente. OPENAI_MODEL é opcional.
    O texto enviado é somente a entrada atual e o contexto fornecido.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY não configurada. Defina a variável de ambiente e reabra a ferramenta."
        )
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    prompt = (
        "Traduza o texto abaixo do inglês para português brasileiro para um jogo de RPG. "
        "Preserve exatamente marcadores de controle, placeholders, tags, símbolos, quebras "
        "de linha e nomes próprios quando apropriado. Não explique; retorne somente a tradução.\n\n"
        f"Texto original:\n{original}"
    )
    if context.strip():
        prompt += f"\n\nContexto adicional fornecido pelo tradutor:\n{context.strip()}"
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um tradutor/localizador experiente de RPGs japoneses. "
                        "Priorize naturalidade em PT-BR e consistência terminológica."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
    ).encode("utf-8")
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ValueError(f"Falha na API de tradução (HTTP {exc.code}): {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError(f"Não foi possível acessar a API de tradução: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("A API retornou uma resposta JSON inválida.") from exc

    try:
        suggestion = result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ValueError("A resposta da API não contém uma sugestão de tradução válida.") from exc
    if not suggestion:
        raise ValueError("A API retornou uma sugestão vazia.")
    return suggestion


def get_catalog_stats(catalog: dict[str, Any]) -> dict[str, Any]:
    """Expose estatísticas validadas para a GUI."""
    return catalog_stats(catalog)
