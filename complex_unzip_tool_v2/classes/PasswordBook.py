class PasswordBook:
    def __init__(self):
        self.local_entries: list[str] = []
        self.dest_entries: list[str] = []

        # load passwords from local file
        self.loadPasswords("passwords.txt", True)

    def loadPasswords(self, path: str, is_local: bool = False) -> None:
        """Load passwords from a file 从文件加载密码"""
        try:
            with open(path, "r") as f:
                for line in f:
                    if is_local:
                        self.local_entries.append(line.strip())
                    else:
                        self.dest_entries.append(line.strip())
        except Exception as e:
            # doesnt matter if this fails
            pass

        # make sure passwords are unique
        self.local_entries = list(set(self.local_entries))
        self.dest_entries = list(set(self.dest_entries))

    def savePasswords(self) -> None:
        """Save passwords to local 将密码保存到本地"""
        with open("passwords.txt", "w") as f:
            for entry in self.local_entries:
                f.write(f"{entry}\n")

    def getPasswords(self) -> list[str]:
        """Get all passwords 获取所有密码"""
        return list(set(self.local_entries + self.dest_entries))
    
    def addPassword(self, password: str) -> None:
        """Add a single password 添加单个密码"""
        if password:
            self.local_entries.append(password)
            self.local_entries = list(set(self.local_entries))

    def addPasswords(self, passwords: list[str]) -> None:
        """Add multiple passwords 添加多个密码"""
        if passwords:
            self.local_entries.extend(passwords)
            self.local_entries = list(set(self.local_entries))

    def removePassword(self, password: str) -> None:
        """Remove a password 删除密码"""
        self.local_entries.remove(password)
