"""Persistência local das configurações da interface gráfica."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def settings_file_path() -> Path:
    """Retorna o caminho de configurações por usuário, fora do repositório."""
    app_data = os.environ.get("APPDATA", "").strip()
    if app_data:
        return Path(app_data) / "SuikodenPTBRToolkit" / "settings.json"
    return Path.home() / ".config" / "suikoden-ptbr-toolkit" / "settings.json"


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """Carrega as preferências; configurações ausentes ou inválidas usam padrões seguros."""
    settings_path = path or settings_file_path()
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def save_settings(settings: dict[str, Any], path: Path | None = None) -> None:
    """Grava preferências atomicamente, sem depender do diretório atual do processo."""
    settings_path = path or settings_file_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = settings_path.with_name(f".{settings_path.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(settings_path)
    finally:
        if temporary.exists():
            temporary.unlink()


def validate_game_directory(value: str | Path) -> Path:
    """Valida a pasta de instalação que contém diretamente o executável do jogo."""
    raw = str(value).strip()
    if not raw:
        raise ValueError("Selecione a pasta de instalação do jogo.")
    directory = Path(raw).expanduser()
    if not directory.is_dir():
        raise ValueError(f"A pasta do jogo não existe ou não é um diretório: {directory}")
    executables = [
        item for item in directory.iterdir() if item.is_file() and item.suffix.lower() == ".exe"
    ]
    if not executables:
        raise ValueError(
            "A pasta selecionada não contém um executável .exe. "
            "Selecione a pasta raiz da instalação do jogo."
        )
    return directory.resolve()


def find_game_assets_directory(game_directory: Path) -> Path:
    """Resolve a pasta Addressables do jogo a partir da instalação selecionada."""
    expected = (
        game_directory
        / "Suikoden I and II HD Remaster_Data"
        / "StreamingAssets"
        / "aa"
        / "StandaloneWindows64"
    )
    if expected.is_dir():
        return expected
    for candidate in game_directory.glob("*_Data/StreamingAssets/aa/StandaloneWindows64"):
        if candidate.is_dir():
            return candidate
    return expected
