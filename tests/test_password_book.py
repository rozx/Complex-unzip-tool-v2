import importlib
import sys
from pathlib import Path

import pytest

from complex_unzip_tool_v2.classes.PasswordBook import PasswordBook
from complex_unzip_tool_v2.modules.password_util import load_all_passwords
from typer.testing import CliRunner

import complex_unzip_tool_v2.main as main


@pytest.mark.parametrize("frozen", [False, True])
def test_password_book_uses_tool_directory_across_working_directories(
    monkeypatch, tmp_path, frozen
):
    tool = tmp_path / "tool"
    target = tmp_path / "archives"
    working = tmp_path / "working"
    for directory in (tool, target, working):
        directory.mkdir()
    global_book = tool / "passwords.txt"
    global_book.write_text("全局密码\n", encoding="utf-8")
    target_book = target / "passwords.txt"
    target_book.write_text("目标密码\n", encoding="utf-8")
    cwd_book = working / "passwords.txt"
    cwd_book.write_text("unrelated\n", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", frozen, raising=False)
    monkeypatch.setattr(sys, "executable", str(tool / "cuz.exe"))
    module = importlib.import_module("complex_unzip_tool_v2.classes.PasswordBook")
    monkeypatch.setattr(
        module, "__file__", str(tool / "complex_unzip_tool_v2/classes/PasswordBook.py")
    )
    monkeypatch.chdir(working)

    book = load_all_passwords([str(target)])
    assert set(book.get_passwords()) == {"全局密码", "目标密码"}
    book.add_password("新密码")
    monkeypatch.chdir(target)
    book.save_passwords()

    assert set(global_book.read_text(encoding="utf-8").splitlines()) == {"全局密码", "新密码"}
    assert target_book.read_text(encoding="utf-8") == "目标密码\n"
    assert cwd_book.read_text(encoding="utf-8") == "unrelated\n"
    assert not book.has_unsaved_changes()


def test_cli_finishes_when_password_book_is_not_writable(monkeypatch, tmp_path):
    book = PasswordBook()
    book.password_file = tmp_path / "read-only" / "passwords.txt"
    book.add_password("synthetic-secret")
    original_open = open

    def deny_password_write(file, mode="r", *args, **kwargs):
        if Path(file) == book.password_file and "w" in mode:
            raise PermissionError("Permission denied")
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", deny_password_write)
    monkeypatch.setattr(main.password_util, "load_all_passwords", lambda paths: book)
    monkeypatch.setattr(main.archive_utils, "resolve_seven_zip_path", lambda: "7z")
    result = CliRunner().invoke(main.app, [str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "Could not save passwords" in result.output
    assert "synthetic-secret" not in result.output
    assert book.has_unsaved_changes()
    assert not (tmp_path / ".unzip-rename-history.tmp.json").exists()
