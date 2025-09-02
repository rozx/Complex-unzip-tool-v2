class PasswordBook:
    def __init__(self):
        self.local_entries: list[str] = [""]  # default empty password
        self.dest_entries: list[str] = [""]  # default empty password

        # load passwords from local file
        self.loadPasswords("passwords.txt")

    def loadPasswords(self, path: str) -> None:
        """Load passwords from a file."""
        try:
            with open(path, "r") as f:
                for line in f:
                    self.dest_entries.append(line.strip())
        except Exception as e:
            # doesnt matter if this fails
            pass

        # make sure passwords are unique
        self.dest_entries = list(set(self.dest_entries))

    def savePasswords(self) -> None:
        """Save passwords to local"""
        with open("passwords.txt", "w") as f:
            for entry in self.local_entries:
                f.write(f"{entry}\n")

    def getPasswords(self) -> list[str]:
        """Get all passwords."""
        return list(set(self.local_entries + self.dest_entries))
    
    def addPassword(self, password: str) -> None:
        self.local_entries.append(password)

        self.local_entries = list(set(self.local_entries))

    def removePassword(self, password: str) -> None:
        self.local_entries.remove(password)
