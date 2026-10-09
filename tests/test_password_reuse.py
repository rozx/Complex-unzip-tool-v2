import importlib
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

import complex_unzip_tool_v2.main as main


@pytest.fixture
def password_directories(monkeypatch, tmp_path):
    tool = tmp_path / "tool"
    source = tmp_path / "archives"
    tool.mkdir()
    source.mkdir()
    book_path = tool / "passwords.txt"
    book_module = importlib.import_module("complex_unzip_tool_v2.classes.PasswordBook")
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(
        book_module,
        "__file__",
        str(tool / "complex_unzip_tool_v2/classes/PasswordBook.py"),
    )
    monkeypatch.setattr(main.archive_utils, "resolve_seven_zip_path", lambda: "7z")
    monkeypatch.setattr(main.file_utils, "send2trash", lambda path: Path(path).unlink())
    return source, book_path


@pytest.mark.parametrize("multipart", [(False, False), (True, True), (False, True)])
@pytest.mark.parametrize("existing_password", [False, True])
def test_cli_reuses_entered_password_for_later_archives(
    monkeypatch, password_directories, multipart, existing_password
):
    """Issue #24: one password entry unlocks later groups and nested archives."""
    source, book_path = password_directories
    if existing_password:
        book_path.write_text("# keep this comment\nwrong\n", encoding="utf-8")

    monkeypatch.setattr(
        main.archive_utils,
        "is_valid_archive",
        lambda path, **kwargs: Path(path).name.endswith((".7z", ".7z.001")),
    )
    for index, is_multipart in enumerate(multipart):
        names = (
            [f"archive{index}.7z.001", f"archive{index}.7z.002"]
            if is_multipart
            else [f"archive{index}.7z"]
        )
        for name in names:
            (source / name).write_bytes(b"encrypted fixture")

    entered = []

    def prompt(text):
        if text.startswith("Enter password"):
            entered.append("learned-password")
            return "learned-password"
        return "1"

    monkeypatch.setattr("builtins.input", prompt)
    extracted = []

    def extract(archive_path, output_path, password="", **kwargs):
        if password != "learned-password":
            raise main.archive_utils.ArchivePasswordError("Incorrect password")
        name = Path(archive_path).name
        extracted.append(name)
        output = Path(output_path)
        output.mkdir(parents=True, exist_ok=True)
        if name.startswith("archive"):
            (output / f"nested-{name}.7z").write_bytes(b"encrypted nested fixture")
        else:
            (output / f"{name}.txt").write_text("extracted", encoding="utf-8")
        return True

    monkeypatch.setattr(main.archive_utils, "extractArchiveWith7z", extract)

    result = CliRunner().invoke(main.app, [str(source)])

    assert result.exit_code == 0, result.output
    assert entered == ["learned-password"]
    assert len(extracted) == 4
    assert len(list((source / "unzipped").rglob("*.txt"))) == 2
    saved = book_path.read_text(encoding="utf-8")
    assert saved.splitlines().count("learned-password") == 1
    if existing_password:
        assert saved.startswith("# keep this comment\nwrong\n")
    assert not (source / "passwords.txt").exists()


@pytest.mark.parametrize("multipart", [False, True])
@pytest.mark.parametrize("nested_password_failure", [False, True])
def test_cli_reuses_password_learned_on_alternative_archive_retry(
    monkeypatch, password_directories, multipart, nested_password_failure
):
    """Retry-learned passwords reach later groups even with skipped nested files."""
    source, book_path = password_directories
    for index in range(2):
        for side in ("primary", "alternative"):
            directory = source / side / "batch"
            directory.mkdir(parents=True, exist_ok=True)
            extensions = ["7z.001", "7z.002"] if multipart else ["7z"]
            for extension in extensions:
                (directory / f"archive{index}.{extension}").write_bytes(
                    b"source archive"
                )

    attempts = []
    kept_sources = []

    def extract(archive_path, output_path, password_list, **kwargs):
        attempts.append(list(password_list))
        if len(attempts) == 1:
            raise OSError("Try an alternative archive")
        if len(attempts) == 2:
            kept_sources.extend(Path(archive_path).parent.glob("archive*"))
        output = Path(output_path) / f"{Path(archive_path).name}.txt"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("extracted", encoding="utf-8")
        return {
            "success": True,
            "final_files": [str(output)],
            "extracted_archives": [archive_path],
            "errors": [],
            "password_failed_archives": ["nested.7z"]
            if nested_password_failure
            else [],
            "user_provided_passwords": ["retry-password"] if len(attempts) == 2 else [],
        }

    monkeypatch.setattr(main.archive_utils, "extract_nested_archives", extract)

    result = CliRunner().invoke(main.app, [str(source)])

    assert result.exit_code == 0, result.output
    assert len(attempts) == 3
    assert "retry-password" in attempts[2]
    assert len(list((source / "unzipped").rglob("*.txt"))) == 2
    assert book_path.read_text(encoding="utf-8").splitlines() == ["retry-password"]
    if nested_password_failure:
        assert all(path.exists() for path in kept_sources)
