import os
from turtle import st
from ..classes.PasswordBook import PasswordBook


def loadAllPasswords(paths: list[str]) -> PasswordBook:
    """Load all passwords from a directory."""
    password_book = PasswordBook()

    # load password from paths
    for path in paths:
        if os.path.isdir(path):
            # load from directory
            password_book.loadPasswords(os.path.join(path, "passwords.txt"))
        else:
            dir = os.path.dirname(path)
            password_book.loadPasswords(os.path.join(dir, "passwords.txt"))

    return password_book

def saveAllPasswords(password_book: PasswordBook) -> None:
    """Save all passwords to all loaded files."""
    password_book.savePasswords()
