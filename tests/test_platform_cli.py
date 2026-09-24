import builtins
import platform
import sys

import pytest
from rich.text import Text
from typer.testing import CliRunner

import complex_unzip_tool_v2.main as main


def test_cli_rejects_unsupported_platform_before_extraction(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "riscv64")
    archive = tmp_path / "archive.zip删除"
    archive.write_bytes(b"unchanged")
    monkeypatch.setattr(
        main, "extract_files", lambda *a, **k: pytest.fail("Extraction started")
    )
    result = CliRunner().invoke(main.app, [str(archive)])
    assert result.exit_code == 1
    assert "Unsupported 7-Zip platform" in Text.from_ansi(result.output).plain
    assert list(tmp_path.iterdir()) == [archive]
    assert archive.read_bytes() == b"unchanged"


@pytest.mark.parametrize("option", ["--help", "--version"])
def test_cli_information_does_not_require_engine(monkeypatch, option):
    monkeypatch.setattr(platform, "system", lambda: "FreeBSD")
    assert CliRunner().invoke(main.app, [option]).exit_code == 0


def test_cli_missing_engine_preserves_input(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "missing"), raising=False)
    archive = tmp_path / "archive.zip删除"
    archive.write_bytes(b"unchanged")
    result = CliRunner().invoke(main.app, [str(archive)])
    assert result.exit_code == 1
    assert "7-Zip executable not found" in Text.from_ansi(result.output).plain
    assert list(tmp_path.iterdir()) == [archive]
    assert archive.read_bytes() == b"unchanged"


@pytest.mark.parametrize(
    "system,terminal,expected_prompts",
    [
        ("Darwin", True, 0),
        ("Linux", True, 0),
        ("Windows", False, 0),
        ("Windows", True, 1),
    ],
)
def test_standalone_exit_only_pauses_in_windows_terminal(
    monkeypatch, system, terminal, expected_prompts
):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(platform, "system", lambda: system)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: terminal)
    prompts = []
    monkeypatch.setattr(builtins, "input", lambda prompt: prompts.append(prompt))
    with pytest.raises(SystemExit) as exc:
        main._ask_for_user_input_and_exit()
    assert exc.value.code == 0
    assert len(prompts) == expected_prompts
