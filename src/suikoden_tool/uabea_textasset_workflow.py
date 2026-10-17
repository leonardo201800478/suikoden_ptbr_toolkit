"""Operações sem perda para arquivos TextAsset exportados pelo UABEA.

O arquivo .txt é tratado como bytes opacos para preservar codificação, BOM,
quebras de linha, caracteres de controle e qualquer outro byte.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any


def _require_txt(path: Path) -> Path:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo .txt não encontrado: {path}")
    if path.suffix.casefold() != ".txt":
        raise ValueError(f"O fluxo UABEA exige o arquivo .txt exportado: {path.name}")
    return path


def sha256_file(path: Path) -> str:
    """Calcula SHA-256 lendo os bytes originais, sem decodificação."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_uabea_import(source_txt: Path, import_dir: Path, *, overwrite: bool = False) -> dict[str, Any]:
    """Copia o .txt para a pasta de importação com o mesmo nome e bytes."""
    source = _require_txt(source_txt)
    destination_dir = Path(import_dir).expanduser().resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    if source == destination:
        raise ValueError("O arquivo fonte já está na pasta de destino.")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"O arquivo de importação já existe: {destination}")

    source_hash = sha256_file(source)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{source.name}.", suffix=".tmp", dir=destination_dir
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with source.open("rb") as src, temporary.open("wb") as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        if sha256_file(temporary) != source_hash:
            raise OSError("A cópia temporária difere do arquivo fonte; destino não substituído.")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "source": str(source),
        "destination": str(destination),
        "file_name": source.name,
        "bytes": destination.stat().st_size,
        "sha256": source_hash,
        "byte_identical": True,
    }


def compare_uabea_textassets(first_txt: Path, second_txt: Path) -> dict[str, Any]:
    """Compara dois .txt byte a byte; útil para testar um round-trip sem edição."""
    first = _require_txt(first_txt)
    second = _require_txt(second_txt)
    first_hash = sha256_file(first)
    second_hash = sha256_file(second)
    identical = first_hash == second_hash and first.read_bytes() == second.read_bytes()
    return {
        "first": str(first),
        "second": str(second),
        "first_sha256": first_hash,
        "second_sha256": second_hash,
        "byte_identical": identical,
        "first_bytes": first.stat().st_size,
        "second_bytes": second.stat().st_size,
    }
