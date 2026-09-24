import platform
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import build


@pytest.mark.parametrize(
    "system,machine,files",
    [
        (
            "Windows",
            "AMD64",
            ["7z/windows-x64/7z.exe", "7z/windows-x64/7z.dll"],
        ),
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
def test_missing_assets_keep_previous_build(monkeypatch, tmp_path, capsys, missing):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(build, "__file__", str(tmp_path / "scripts" / "build.py"))
    (tmp_path / "scripts").mkdir()
    assets = {"engine": "7z.exe", "library": "7z.dll", "license": "License.txt"}
    engine_dir = tmp_path / "7z" / "windows-x64"
    engine_dir.mkdir(parents=True)
    for kind, name in assets.items():
        if kind != missing:
            (engine_dir / name).touch(mode=0o755)
    previous = tmp_path / "dist" / "previous.exe"
    previous.parent.mkdir()
    previous.write_bytes(b"previous build")
    assert build.main() == 1
    assert str(engine_dir / assets[missing]) in capsys.readouterr().out
    assert previous.read_bytes() == b"previous build"


def test_build_does_not_embed_personal_passwords(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    engine_dir = tmp_path / "7z" / "macos"
    engine_dir.mkdir(parents=True)
    (engine_dir / "7zz").touch(mode=0o755)
    (engine_dir / "License.txt").touch()
    (tmp_path / "passwords.txt").write_text("private-password", encoding="utf-8")
    spec = build.generate_spec_content(tmp_path, tmp_path / "scripts")
    assert "passwords.txt" not in spec
