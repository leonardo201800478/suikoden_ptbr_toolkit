from pathlib import Path

import pytest

from suikoden_tool.app_settings import (
    find_game_assets_directory,
    load_settings,
    save_settings,
    validate_game_directory,
)


def test_settings_round_trip_uses_explicit_path(tmp_path):
    path = tmp_path / "settings.json"
    settings = {"game_directory": str(tmp_path / "game")}

    save_settings(settings, path)

    assert load_settings(path) == settings


def test_missing_or_invalid_settings_return_empty_mapping(tmp_path):
    path = tmp_path / "settings.json"
    assert load_settings(path) == {}
    path.write_text("[not an object]", encoding="utf-8")
    assert load_settings(path) == {}
    path.write_text("{invalid", encoding="utf-8")
    assert load_settings(path) == {}


def test_validate_game_directory_requires_existing_folder_with_executable(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    with pytest.raises(ValueError, match="não contém um executável"):
        validate_game_directory(game)

    (game / "Suikoden I and II HD Remaster.exe").write_bytes(b"")
    assert validate_game_directory(str(game)) == game.resolve()


def test_validate_game_directory_rejects_missing_directory(tmp_path):
    with pytest.raises(ValueError, match="não existe"):
        validate_game_directory(tmp_path / "missing")


def test_find_game_assets_directory_resolves_addressables_folder(tmp_path):
    game = tmp_path / "game"
    assets = (
        game
        / "Suikoden I and II HD Remaster_Data"
        / "StreamingAssets"
        / "aa"
        / "StandaloneWindows64"
    )
    assets.mkdir(parents=True)

    assert find_game_assets_directory(game) == assets
