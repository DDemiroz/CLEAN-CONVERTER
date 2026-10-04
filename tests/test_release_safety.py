from pathlib import Path
from types import SimpleNamespace
import queue
import subprocess

import pytest
import app


def test_bug_report_opens_only_public_website(monkeypatch):
    calls = []
    monkeypatch.setattr(app.webbrowser, "open", lambda url: calls.append(url) or True)
    app.open_bug_report()
    assert calls == ["https://demirdemiroz.com/iletisim/"]


@pytest.mark.parametrize("raises", [False, True])
def test_bug_report_browser_failure_has_manual_fallback(monkeypatch, raises):
    def fail(url):
        if raises:
            raise OSError("No browser")
        return False
    messages = []
    monkeypatch.setattr(app.webbrowser, "open", fail)
    monkeypatch.setattr(app.messagebox, "showinfo", lambda *args: messages.append(args))
    app.open_bug_report()
    assert app.BUG_REPORT_URL in messages[0][1]


def test_error_keeps_details_and_shows_reporting_hint(monkeypatch):
    def unexpected_browser(*args):
        pytest.fail("Errors must not open the browser automatically")
    monkeypatch.setattr(app.webbrowser, "open", unexpected_browser)
    instance = SimpleNamespace(_ui_events=queue.Queue())
    app.CleanConverter.ui_error(instance, "Error", "Conversion failed")
    kind, (title, text) = instance._ui_events.get_nowait()
    assert kind == "error" and title == "Error"
    assert text.startswith("Conversion failed")
    assert "Questions or report any bugs" in text and "demirdemiroz.com" in text
    assert "private" in text


@pytest.mark.parametrize("field,value", [("output_dir", 42), ("output_dir", []), ("default_format", []), ("mp3_bitrate", {}), ("video_quality", {})])
def test_config_wrong_types_recover(field, value):
    cfg = app.normalize_config({field: value})
    assert isinstance(cfg[field], str)


def test_config_false_string():
    assert app.normalize_config({"organize_by_format": "false"})["organize_by_format"] is False


@pytest.mark.parametrize("name", ["CON", "nul.mp4", "LPT1", "AUX", "COM1.txt"])
def test_reserved_names(name):
    assert app.safe_filename(name).startswith("_")


def test_owned_temp_isolated_between_instances(tmp_path):
    one = SimpleNamespace(cfg={"output_dir": str(tmp_path)}, _temp_workspace=None)
    two = SimpleNamespace(cfg={"output_dir": str(tmp_path)}, _temp_workspace=None)
    first = Path(app.CleanConverter.temp_dir(one))
    second = Path(app.CleanConverter.temp_dir(two))
    assert first != second
    app.CleanConverter.cleanup_temp(one)
    assert not first.exists() and second.exists()
    app.CleanConverter.cleanup_temp(two)


@pytest.mark.parametrize("selector", app.build_video_format_chain("360p"))
def test_all_download_fallbacks_obey_height(selector):
    assert all("height<=360" in branch for branch in selector.split("/"))


def test_cover_command_maps_cover_and_audio():
    cmd = app.build_audio_to_video_cmd("source.mp4", "cover.jpg", "out.mp4", "mp4_video", True, 360)
    assert cmd[cmd.index("-map") + 1] == "0:v:0"
    assert "1:a:0" in cmd and "-vf" in cmd


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    if not Path(app.FFMPEG).is_file():
        pytest.skip("Bundled FFmpeg required for integration checks")
    root = tmp_path_factory.mktemp("media")
    video, audio, cover = [root / n for n in ["örnek video.mp4", "audio.wav", "cover.jpg"]]
    commands = [
        ["-f", "lavfi", "-i", "color=c=red:s=1920x1080:r=24", "-f", "lavfi", "-i", "sine=frequency=440", "-t", "0.5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(video)],
        ["-f", "lavfi", "-i", "sine=frequency=440", "-t", "0.5", str(audio)],
        ["-f", "lavfi", "-i", "color=c=blue:s=1080x1080", "-frames:v", "1", "-update", "1", str(cover)],
    ]
    for cmd in commands:
        subprocess.run([app.FFMPEG, "-nostdin", *cmd], check=True, capture_output=True, timeout=30)
    return video, audio, cover


@pytest.mark.parametrize("fmt", app.AUDIO_FORMAT_LABELS)
def test_real_audio_formats(media, tmp_path, fmt):
    out = tmp_path / ("out." + fmt.lower())
    ok, error = app.run_cmd_live(app.build_audio_convert_cmd(str(media[1]), str(out), fmt.lower(), "192k"))
    assert ok, error
    assert app.probe_stream_codecs(str(out))[1]


@pytest.mark.parametrize("fmt", ["mp4", "webm", "mkv", "mov", "avi"])
def test_real_video_formats(media, tmp_path, fmt):
    out = tmp_path / ("out." + fmt)
    if fmt == "mp4":
        cmd = app.build_video_to_mp4_compatible_cmd(str(media[0]), str(out), 360)
    elif fmt == "webm":
        cmd = app.build_webm_convert_cmd(str(media[0]), str(out), True, 360)
    else:
        cmd = app.build_video_container_cmd(str(media[0]), str(out), True, fmt == "mov", 360)
    ok, error = app.run_cmd_live(cmd)
    assert ok, error
    assert app.probe_video_resolution(str(out)) == "640x360"
    assert app.probe_stream_codecs(str(out))[1]


@pytest.mark.parametrize("source", [0, 1])
def test_real_cover_uses_blue_cover_at_requested_height(media, tmp_path, source):
    out = tmp_path / "cover.mp4"
    ok, error = app.run_cmd_live(app.build_audio_to_video_cmd(str(media[source]), str(media[2]), str(out), "mp4_video", True, 360))
    assert ok, error
    assert app.probe_video_resolution(str(out)) == "360x360"
    pixel = subprocess.run([app.FFMPEG, "-i", str(out), "-vf", "scale=1:1", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=15, check=True).stdout
    assert pixel[2] > pixel[0] + 100  # Blue cover, not the red source video.


def test_failed_conversion_preserves_cause_and_removes_partial(tmp_path, media):
    out = tmp_path / "bad.mp4"
    ok, error = app.run_cmd_live([app.FFMPEG, "-i", str(tmp_path / "missing.mp4"), str(out)])
    assert not ok and "missing.mp4" in error
    assert not out.exists() and not list(tmp_path.glob(".clean-converter-*"))


def test_existing_output_never_overwritten(tmp_path, media):
    out = tmp_path / "existing.mp4"
    out.write_bytes(b"keep")
    ok, _ = app.run_cmd_live(app.build_video_to_mp4_compatible_cmd(str(media[0]), str(out), 360))
    assert not ok and out.read_bytes() == b"keep"


def test_close_while_running_preserves_window(monkeypatch):
    events = []
    monkeypatch.setattr(app.messagebox, "showinfo", lambda *args: events.append("notice"))
    harness = SimpleNamespace(_busy=True, destroy=lambda: events.append("destroy"))
    app.CleanConverter.on_close(harness)
    assert events == ["notice"]


def test_output_folder_failure_restores_previous_setting(monkeypatch):
    errors = []
    monkeypatch.setattr(app.messagebox, "showerror", lambda *args: errors.append(args))
    def fail():
        raise OSError("denied")
    harness = SimpleNamespace(_busy=False, cfg={"output_dir": "previous"},
                              ask_output_dir=lambda: "next", ensure_output_dir_ready=fail)
    app.CleanConverter.change_output_dir(harness)
    assert harness.cfg["output_dir"] == "previous" and errors


def test_missing_tools_stops_startup(monkeypatch):
    closed = []
    monkeypatch.setattr(app.os.path, "exists", lambda _: False)
    monkeypatch.setattr(app.messagebox, "showerror", lambda *args: None)
    with pytest.raises(SystemExit):
        app.ensure_tools_or_exit(SimpleNamespace(destroy=lambda: closed.append(True)))
    assert closed


@pytest.mark.parametrize("fmt", ["mp4", "webm", "mkv", "mov", "avi"])
def test_real_audio_black_video_formats(media, tmp_path, fmt):
    out = tmp_path / ("black." + fmt)
    ok, error = app.run_cmd_live(app.build_audio_to_video_cmd(str(media[1]), None, str(out), fmt + "_video", fmt in {"mp4", "mov"}, 360))
    assert ok, error
    assert app.probe_video_resolution(str(out)) == "640x360"
    assert app.probe_stream_codecs(str(out))[1]
