class PasswordBook:
    def __init__(self):
        self.local_entries: list[str] = []
        self.dest_entries: list[str] = []
        self._has_changes: bool = False  # Track if there are unsaved changes

        # load passwords from local file
        self.load_passwords("passwords.txt", True)

    def load_passwords(self, path: str, is_local: bool = False) -> None:
        """Load passwords from a file 从文件加载密码"""
        # Try multiple encodings to handle files containing Chinese characters or BOM
        encodings = [
            "utf-8-sig",  # handles BOM if present
            "utf-8",
            "gbk",
            "gb2312",
            "big5",
            "utf-16",
            "utf-16-le",
            "utf-16-be",
        ]
        content_lines: list[str] = []
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc, errors="strict") as f:
                    content_lines = f.readlines()
                break
            except (OSError, UnicodeError):
                # Try next encoding
                content_lines = []
                continue

        if not content_lines:
            # Best-effort fallback that ignores decode errors
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content_lines = f.readlines()
            except OSError:
                # File not found or unreadable; nothing to load
                content_lines = []

        if content_lines:
            cleaned: list[str] = []
            for line in content_lines:
                token = line.strip().strip("\ufeff")  # remove BOM if any and trim
                if not token:
                    continue  # skip empty lines
                cleaned.append(token)

            if cleaned:
                if is_local:
                    self.local_entries.extend(cleaned)
                else:
                    self.dest_entries.extend(cleaned)

        # make sure passwords are unique
        self.local_entries = list(set(self.local_entries))
        self.dest_entries = list(set(self.dest_entries))

    def save_passwords(self, force: bool = False) -> None:
        """Save passwords to local 将密码保存到本地"""
        if not self._has_changes and not force:
            return  # No changes to save

        with open("passwords.txt", "w", encoding="utf-8") as f:
            for entry in self.local_entries:
                f.write(f"{entry}\n")

        self._has_changes = False  # Reset change tracking after save

    def get_passwords(self) -> list[str]:
        """Get all passwords 获取所有密码"""
        return list(set(self.local_entries + self.dest_entries))

    def add_password(self, password: str) -> None:
        """Add a single password 添加单个密码"""
        if password:
            original_length = len(self.local_entries)
            self.local_entries.append(password)
            self.local_entries = list(set(self.local_entries))

            # Mark as changed only if a new password was actually added
            if len(self.local_entries) > original_length:
                self._has_changes = True

    def add_passwords(self, passwords: list[str]) -> None:
        """Add multiple passwords 添加多个密码"""
        if passwords:
            original_length = len(self.local_entries)
            self.local_entries.extend(passwords)
            self.local_entries = list(set(self.local_entries))

            # Mark as changed only if new passwords were actually added
            if len(self.local_entries) > original_length:
                self._has_changes = True

    def remove_password(self, password: str) -> None:
        """Remove a password 删除密码"""
        if password in self.local_entries:
            self.local_entries.remove(password)
            self._has_changes = True
        else:
            raise ValueError(f"Password '{password}' not found in local entries.")

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes 检查是否有未保存的更改"""
        return self._has_changes
