"""Esquema inicial de entradas de tradução JSON."""

from typing import Any


def make_translation_entry(entry_id: str, source_text: str = "") -> dict[str, Any]:
    """Cria uma entrada com campos de tradução, contexto e metadados técnicos."""
    return {
        "id": entry_id,
        "game": None,
        "asset_name": None,
        "asset_path": None,
        "object_path_id": None,
        "text_id": None,
        "source_text": source_text,
        "translation_pt_br": "",
        "context": "",
        "text_type": "unknown",
        "max_characters": None,
        "max_lines": None,
        "max_width_px": None,
        "control_tokens": [],
        "pointer_metadata": None,
        "status": "untranslated",
        "notes": "",
    }
