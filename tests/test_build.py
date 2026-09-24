import platform
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import build


@pytest.mark.parametrize(
    "system,machine,files",
    [
        ("Windows", "AMD64", ["7z/7z.exe", "7z/7z.dll"]),
        ("Darwin", "arm64", ["7z/macos/7zz"]),
        ("Linux", "x86_64", ["7z/linux-x64/7zzs"]),
        ("Linux", "aarch64", ["7z/linux-arm64/7zzs"]),
    ],
)
def test_spec_packages_only_native_engine(monkeypatch, system, machine, files):
    monkeypatch.setattr(platform, "system", lambda: system)
    monkeypatch.setattr(platform, "machine", lambda: machine)
    root = Path(__file__).resolve().parents[1]
    analysis = {}
    executable = {}

    def build_executable(*args, **kwargs):
        executable.update(kwargs)
        assert ("X utf8", None, "OPTION") in args[-1]

    def analyze(*args, **kwargs):
        analysis.update(kwargs)
        return SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])

    exec(
        build.generate_spec_content(root, root / "scripts"),
        {
            "Analysis": analyze,
            "PYZ": lambda x: x,
            "EXE": build_executable,
        },
    )
    assert analysis["binaries"] == [
        (str(root / file), Path(file).parent.as_posix()) for file in files
    ]
    license_path = Path(files[0]).parent / "License.txt"
    assert (str(root / license_path), license_path.parent.as_posix()) in analysis[
        "datas"
    ]
    assert bool(executable["icon"]) == (system == "Windows")


@pytest.mark.parametrize("missing", ["engine", "library", "license"])
def test_missing_assets_keep_previous_build(monkeypatch, tmp_path, missing):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(build, "__file__", str(tmp_path / "scripts" / "build.py"))
    (tmp_path / "scripts").mkdir()
    assets = {"engine": "7z.exe", "library": "7z.dll", "license": "License.txt"}
    (tmp_path / "7z").mkdir()
    for kind, name in assets.items():
        if kind != missing:
            (tmp_path / "7z" / name).touch(mode=0o755)
    previous = tmp_path / "dist" / "previous.exe"
    previous.parent.mkdir()
    previous.write_bytes(b"previous build")
    assert build.main() == 1
    assert previous.read_bytes() == b"previous build"
