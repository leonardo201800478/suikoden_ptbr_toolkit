"""Leitura inicial e não destrutiva do cabeçalho de bundles UnityFS."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Any


def _read_cstring(data: bytes, offset: int) -> tuple[str, int]:
    """Lê uma string terminada em NUL e retorna (texto, próximo_offset)."""
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError("String C não terminada no cabeçalho UnityFS")
    return data[offset:end].decode("utf-8", errors="replace"), end + 1


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calcula SHA-256 em blocos, evitando carregar o arquivo inteiro na memória."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_bundle(path: Path) -> dict[str, Any]:
    """Lê metadados básicos UnityFS sem alterar nem descompactar o arquivo."""
    path = Path(path)
    with path.open("rb") as stream:
        header = stream.read(256)
    if not header.startswith(b"UnityFS\0"):
        return {"path": str(path), "name": path.name, "format": "unknown", "size_bytes": path.stat().st_size, "error": "Assinatura UnityFS não encontrada."}
    offset = len(b"UnityFS\0")
    if len(header) < offset + 4:
        raise ValueError(f"Cabeçalho truncado: {path}")
    version = struct.unpack_from(">I", header, offset)[0]
    offset += 4
    unity_version, offset = _read_cstring(header, offset)
    unity_revision, offset = _read_cstring(header, offset)
    result: dict[str, Any] = {"path": str(path), "name": path.name, "format": "UnityFS", "format_version": version, "unity_version": unity_version, "unity_revision": unity_revision, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if len(header) >= offset + 16:
        result["declared_size_bytes"] = struct.unpack_from(">Q", header, offset)[0]
        result["compressed_blocks_info_size"] = struct.unpack_from(">I", header, offset + 8)[0]
        result["uncompressed_blocks_info_size"] = struct.unpack_from(">I", header, offset + 12)[0]
    if len(header) >= offset + 20:
        result["flags"] = struct.unpack_from(">I", header, offset + 16)[0]
    return result


def inventory_bundles(root: Path) -> list[dict[str, Any]]:
    """Inspeciona recursivamente arquivos .bundle e retorna inventário ordenado."""
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {root}")
    return [inspect_bundle(p) for p in sorted(root.rglob("*.bundle")) if p.is_file()]
