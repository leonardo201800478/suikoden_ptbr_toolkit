import struct
from pathlib import Path
from suikoden_tool.bundle_inspector import inspect_bundle

def test_inspect_unityfs_header(tmp_path: Path) -> None:
    header = b"UnityFS\0" + struct.pack(">I", 8) + b"2022.3.0f1\0" + b"2022.3.0f1\0" + struct.pack(">QIII", 40, 10, 20, 0)
    path = tmp_path / "sample.bundle"; path.write_bytes(header + b"payload")
    result = inspect_bundle(path)
    assert result["format"] == "UnityFS" and result["format_version"] == 8
    assert result["unity_version"] == "2022.3.0f1" and result["size_bytes"] == len(header) + 7
