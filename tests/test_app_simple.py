from app import clean_error_text, safe_filename, status_path


def test_safe_filename_strips_windows_invalid_characters():
    assert safe_filename('bad<>:"/\\\\|?*name') == "bad__________name"


def test_clean_error_text_removes_error_prefix():
    assert clean_error_text("ERROR: something broke") == "something broke"
    assert clean_error_text("plain text") == "plain text"


def test_status_path_returns_folder_and_filename():
    assert status_path(r"C:\Output\MP4_VIDEO\clip.mp4") == r"MP4_VIDEO\clip.mp4"
