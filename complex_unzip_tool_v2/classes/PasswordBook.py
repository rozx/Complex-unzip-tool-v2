class PasswordBook:
    def __init__(self):
        self.entries: list[str] = [""]  # default empty password

    def loadPasswords(self, path: str) -> None:
        """Load passwords from a file."""
        try:
            with open(path, "r") as f:
                for line in f:
                    self.entries.append(line.strip())
        except Exception as e:
            # doesnt matter if this fails
            pass

        # make sure passwords are unique
        self.entries = list(set(self.entries))

    def savePasswords(self) -> None:
        """Save passwords to local"""
        with open("passwords.txt", "w") as f:
            for entry in self.entries:
                f.write(f"{entry}\n")
        