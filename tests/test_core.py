import json
import tempfile
from pathlib import Path

import pytest

import app
from app import (
    DEFAULT_FORMAT_LABEL,
    DEFAULT_VIDEO_QUALITY,
    QuietYtDlpLogger,
    build_audio_format_chain,
    build_video_format_chain,
    build_ytdlp_merge_options,
    explain_yt_error,
    fmt_folder_name,
    format_eta,
    human_bytes,
    is_media_link,
    is_retryable_ytdlp_error,
    media_link_host,
    normalize_config,
    normalize_media_link,
    parse_quality_height,
    unique_path,
)


def test_load_config_starts_at_1080p_even_if_best_was_saved(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"video_quality": "Best"}), encoding="utf-8")
    monkeypatch.setattr(app, "CONFIG_PATH", str(config_path))

    assert app.load_config()["video_quality"] == DEFAULT_VIDEO_QUALITY


def test_normalize_media_link_adds_https_for_common_media_domains():
    assert normalize_media_link("youtu.be/abcdefghijk") == "https://youtu.be/abcdefghijk"
    assert normalize_media_link("www.instagram.com/reels/example/") == "https://www.instagram.com/reels/example/"


def test_is_media_link_requires_http_or_https():
    assert is_media_link("https://www.youtube.com/watch?v=abcdefghijk")
    assert is_media_link("http://example.com/file.mp4")
    assert not is_media_link("not_a_link")
    assert not is_media_link("")


def test_media_link_host_extracts_domain():
    assert media_link_host("https://www.youtube.com/watch?v=test") == "www.youtube.com"
    assert media_link_host("youtu.be/test") == "youtu.be"
    assert media_link_host("") == ""


def test_normalize_config_repairs_invalid_values():
    cfg = normalize_config(
        {
            "default_format": "broken",
            "video_quality": "9999p",
            "mp3_bitrate": "999k",
            "organize_by_format": 0,
            "output_dir": "  C:/Temp  ",
        }
    )
    assert cfg["default_format"] == DEFAULT_FORMAT_LABEL
    assert cfg["video_quality"] == "1080p"
    assert cfg["mp3_bitrate"] == "192k"
    assert cfg["organize_by_format"] is False
    assert cfg["output_dir"] == "C:/Temp"


def test_parse_quality_height_handles_named_best():
    assert parse_quality_height("Best") is None
    assert parse_quality_height("1080p") == 1080
    assert parse_quality_height("2160p (4K)") == 2160


def test_video_download_prefers_hls_before_direct_https():
    formats = build_video_format_chain("1080p")
    assert "protocol^=m3u8" in formats[0]
    assert "height<=1080" in formats[0]
    assert any("protocol=https" in value for value in formats[1:])


def test_audio_download_prefers_hls_before_direct_https():
    formats = build_audio_format_chain()
    assert formats[0] == "bestaudio[protocol^=m3u8]"
    assert any("protocol=https" in value for value in formats[1:])


def test_ytdlp_merge_repairs_missing_hls_timestamps():
    options = build_ytdlp_merge_options()
    assert options["merge_output_format"] == "mp4"
    assert options["postprocessor_args"]["merger+ffmpeg_i"] == ["-fflags", "+genpts"]
    assert options["postprocessor_args"]["merger+ffmpeg_o"] == ["-avoid_negative_ts", "make_zero"]


def test_fmt_folder_name_is_windows_friendly():
    assert fmt_folder_name("MP4 Video (H.264 + AAC)") == "MP4_VIDEO_H.264___AAC"
    assert fmt_folder_name("MP4 Audio + Cover") == "MP4_AUDIO___COVER"


def test_unique_path_adds_numeric_suffix():
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir) / "video.mp4"
        base.write_text("x", encoding="utf-8")
        assert unique_path(str(base)).endswith("video (2).mp4")


def test_human_bytes_and_eta_are_readable():
    assert human_bytes(1024) == "1.0 KB"
    assert human_bytes(None) == ""
    assert format_eta(65) == "1:05"
    assert format_eta(3661) == "1:01:01"


def test_explain_yt_error_requested_format_is_user_friendly():
    text = explain_yt_error("ERROR: Requested format is not available", "https://example.com/video")
    assert "no format compatible" in text.lower()
    assert "technical detail" in text.lower()


def test_explain_yt_error_403_mentions_server_access():
    text = explain_yt_error("ERROR: HTTP Error 403: Forbidden", "https://example.com/video")
    assert "403" in text
    assert "server denied access" in text.lower()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        ("Sign in to confirm you're not a bot", "additional bot verification"),
        ("Private video", "video is private"),
        ("Login required", "requires sign-in"),
        ("Video unavailable", "video is unavailable"),
        ("Unsupported URL", "does not appear to be supported"),
        ("Requested format is not available", "no format compatible"),
        ("HTTP Error 429: Too Many Requests", "too many requests were detected"),
        ("Unexpected extractor failure", "video could not be downloaded"),
    ],
)
def test_explain_yt_error_messages_are_english(error, expected):
    text = explain_yt_error(error, "https://example.com/video")
    assert expected in text.lower()
    assert "technical detail" in text.lower()


def test_quiet_ytdlp_logger_methods_are_noops():
    logger = QuietYtDlpLogger()
    assert logger.debug("x") is None
    assert logger.info("x") is None
    assert logger.warning("x") is None
    assert logger.error("x") is None


def test_is_retryable_ytdlp_error_recognizes_known_transient_cases():
    assert is_retryable_ytdlp_error("ERROR: HTTP Error 403: Forbidden")
    assert is_retryable_ytdlp_error("ERROR: Requested format is not available")
    assert not is_retryable_ytdlp_error("ERROR: Private video")


def test_cleanup_temp_preserves_unowned_temp_folder(tmp_path):
    temp_root = tmp_path / "output"
    temp_dir = temp_root / "_temp"
    temp_dir.mkdir(parents=True)
    (temp_dir / "part.tmp").write_text("x", encoding="utf-8")
    harness = type("Harness", (), {"cfg": {"output_dir": str(temp_root)}})()

    app.CleanConverter.cleanup_temp(harness)

    assert (temp_dir / "part.tmp").read_text() == "x"


def test_ensure_output_dir_ready_raises_for_unwritable_folder(monkeypatch, tmp_path):
    harness = type("Harness", (), {"cfg": {"output_dir": str(tmp_path)}})()

    def raise_oserror(*_args, **_kwargs):
        raise OSError("denied")

    monkeypatch.setattr(app.tempfile, "NamedTemporaryFile", raise_oserror)

    try:
        app.CleanConverter.ensure_output_dir_ready(harness)
    except RuntimeError as ex:
        assert "not writable" in str(ex)
    else:
        raise AssertionError("ensure_output_dir_ready should have raised RuntimeError")
