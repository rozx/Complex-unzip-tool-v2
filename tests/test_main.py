import complex_unzip_tool_v2.main as main


def test_should_delete_original_archives_false_when_password_failed_archives_present():
    assert (
        main._should_delete_original_archives(
            {"success": True, "password_failed_archives": ["a.7z"]}
        )
        is False
    )


def test_should_delete_original_archives_true_when_no_password_failed_archives():
    assert main._should_delete_original_archives({"success": True}) is True

