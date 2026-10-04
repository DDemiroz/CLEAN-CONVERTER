# SPDX-License-Identifier: GPL-3.0-only
# Copyright © 2026 Demir Demiröz. See LICENSE.md; provided without warranty.
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import queue
import webbrowser
from collections import deque
from urllib.parse import urlparse

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import yt_dlp
from yt_dlp.utils import DownloadError
from splash_screen import StartupSplash

APP_NAME = "Clean Converter"
BUG_REPORT_URL = "https://demirdemiroz.com/iletisim/"


def open_bug_report():
    """Open support without attaching error text, paths or source URLs."""
    try:
        opened = webbrowser.open(BUG_REPORT_URL)
    except Exception:
        opened = False
    if not opened:
        messagebox.showinfo("Report a bug", f"Open {BUG_REPORT_URL} in your browser to report the issue.\n\nDo not share private paths, links or account details.")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else BASE_DIR
TOOLS_DIR_CANDIDATES = (
    os.path.join(APP_ROOT, "tools"),
    os.path.join(APP_ROOT, "_internal", "tools"),
    os.path.join(APP_ROOT, "_internal"),
    os.path.join(BASE_DIR, "tools"),
)
TOOLS_DIR = next((p for p in TOOLS_DIR_CANDIDATES if os.path.isdir(p)), TOOLS_DIR_CANDIDATES[0])
FFMPEG = os.path.join(TOOLS_DIR, "ffmpeg.exe")
FFPROBE = os.path.join(TOOLS_DIR, "ffprobe.exe")
DENO = os.path.join(TOOLS_DIR, "deno.exe")
CONFIG_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "Clean Converter")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
ASSETS_DIR = "assets"
APP_ICON_PNG = os.path.join(ASSETS_DIR, "icon.png")
APP_ICON_ICO = os.path.join(ASSETS_DIR, "icon.ico")

COVER_MAX_DIM = 1080

VIDEO_FORMAT_LABELS = [
    "MP4 Video (H.264 + AAC)",
    "WEBM Video (VP9 + Opus)",
    "MKV Video (H.264 + AAC)",
    "MOV Video (H.264 + AAC)",
    "AVI Video (H.264 + AAC)",
]
AUDIO_FORMAT_LABELS = ["MP3", "WAV", "FLAC", "OGG", "M4A", "AAC"]
COVER_FORMAT_LABEL = "MP4 Audio + Cover"
DEFAULT_FORMAT_LABEL = "MP4 Video (H.264 + AAC)"
FORMAT_LABELS = [
    *VIDEO_FORMAT_LABELS,
    COVER_FORMAT_LABEL,
    *AUDIO_FORMAT_LABELS,
]
FORMAT_SECTION_VIDEO = "Video Formats"
FORMAT_SECTION_AUDIO = "Sound Formats"

FORMAT_MAP = {
    "MP4 Video (H.264 + AAC)": "mp4_video",
    "WEBM Video (VP9 + Opus)": "webm_video",
    "MKV Video (H.264 + AAC)": "mkv_video",
    "MOV Video (H.264 + AAC)": "mov_video",
    "AVI Video (H.264 + AAC)": "avi_video",
    "MP4 Audio + Cover": "mp4_cover",
    "MP3": "mp3",
    "WAV": "wav",
    "FLAC": "flac",
    "OGG": "ogg",
    "M4A": "m4a",
    "AAC": "aac",
}

VIDEO_QUALITY_OPTIONS = ["Best", "2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "360p"]
DEFAULT_VIDEO_QUALITY = "1080p"
VIDEO_OUTPUT_KEYS = {"mp4_video", "webm_video", "mkv_video", "mov_video", "avi_video"}
VIDEO_INPUT_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v"}
AUDIO_INPUT_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus", ".wma"}
VIDEO_X264_PRESET = "medium"
VIDEO_X264_CRF = "18"
BG_COLOR = "#191b1e"
PANEL_COLOR = "#222529"
SURFACE_COLOR = "#222529"
SURFACE_ALT_COLOR = "#2e3238"
ACCENT_COLOR = "#2466c2"
ACCENT_HOVER = "#327ce2"
TEXT_PRIMARY = "#f0f1f2"
TEXT_MUTED = "#b8bec6"
TEXT_SOFT = "#a7afb9"
RESPONSIVE_BREAKPOINT = 980


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ---------------- Config ----------------
def load_config() -> dict:
    defaults = {
        "output_dir": "",
        "default_format": DEFAULT_FORMAT_LABEL,
        "mp3_bitrate": "192k",
        "video_quality": DEFAULT_VIDEO_QUALITY,
        "organize_by_format": True,
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            defaults.update(data)
        except Exception:
            pass
    config = normalize_config(defaults)
    # Start every session at a predictable size; higher qualities remain opt-in.
    config["video_quality"] = DEFAULT_VIDEO_QUALITY
    return config


def save_config(cfg: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    normalized = normalize_config(cfg)
    fd, temp_path = tempfile.mkstemp(prefix="config-", suffix=".json", dir=CONFIG_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, CONFIG_PATH)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def normalize_config(cfg: dict | None) -> dict:
    normalized = {
        "output_dir": "",
        "default_format": DEFAULT_FORMAT_LABEL,
        "mp3_bitrate": "192k",
        "video_quality": DEFAULT_VIDEO_QUALITY,
        "organize_by_format": True,
    }
    if isinstance(cfg, dict):
        normalized.update(cfg)
    if not isinstance(normalized.get("default_format"), str) or normalized["default_format"] not in FORMAT_MAP:
        normalized["default_format"] = DEFAULT_FORMAT_LABEL
    if normalized.get("video_quality") not in VIDEO_QUALITY_OPTIONS:
        normalized["video_quality"] = DEFAULT_VIDEO_QUALITY
    if not isinstance(normalized.get("mp3_bitrate"), str) or normalized["mp3_bitrate"] not in {"192k", "256k", "320k"}:
        normalized["mp3_bitrate"] = "192k"
    organize = normalized.get("organize_by_format", True)
    if isinstance(organize, str):
        organize = organize.lower().strip() not in {"false", "0", "no"}
    normalized["organize_by_format"] = bool(organize) if isinstance(organize, (bool, int, float)) else True
    output = normalized.get("output_dir")
    normalized["output_dir"] = output.strip() if isinstance(output, str) else ""
    return normalized


# ---------------- Tool checks ----------------
def ensure_tools_or_exit(root):
    missing = []
    if not os.path.exists(FFMPEG):
        missing.append(FFMPEG)
    if not os.path.exists(FFPROBE):
        missing.append(FFPROBE)
    if missing:
        searched = "\n".join(f"- {p}" for p in TOOLS_DIR_CANDIDATES)
        messagebox.showerror(
            "Missing tools",
            "FFmpeg not found. Make sure these files exist in one of these folders:\n\n"
            f"{searched}\n\n"
            "- ffmpeg.exe\n- ffprobe.exe\n\nMissing:\n" + "\n".join(missing),
        )
        root.destroy()
        raise SystemExit(1)


# ---------------- Utilities ----------------
def normalize_drop_data(data: str) -> str:
    s = data.strip()
    parts = re.findall(r"\{([^}]*)\}|(\S+)", s)
    if parts:
        s = parts[0][0] or parts[0][1]
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1]
    return s.strip()


def normalize_media_link(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if re.match(r"^[a-z][a-z0-9+.-]*://", text, flags=re.IGNORECASE):
        return text
    if re.match(r"^(www\.|youtu\.be/|youtube\.com/|m\.youtube\.com/|x\.com/|twitter\.com/|reddit\.com/)", text, flags=re.IGNORECASE):
        return f"https://{text}"
    return text


def is_media_link(value: str) -> bool:
    return normalize_media_link(value).lower().startswith(("http://", "https://"))


def media_link_host(value: str) -> str:
    normalized = normalize_media_link(value)
    if not normalized:
        return ""
    try:
        return (urlparse(normalized).netloc or "").lower().lstrip(".")
    except Exception:
        return ""


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", BASE_DIR)
    return os.path.join(base_path, relative_path)


def safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    name = name.strip().strip(".")
    name = name[:180].rstrip(" .") or "output"
    if re.match(r"^(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", name, re.IGNORECASE):
        name = "_" + name
    return name


def status_path(path: str) -> str:
    folder = os.path.basename(os.path.dirname(path))
    name = os.path.basename(path)
    return os.path.join(folder, name) if folder else name


def has_video_stream(path: str) -> bool:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=nw=1:nk=1",
            path,
        ],
        capture_output=True,
        creationflags=creationflags,
        **subprocess_text_kwargs(),
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def probe_video_resolution(path: str) -> str:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            path,
        ],
        capture_output=True,
        creationflags=creationflags,
        **subprocess_text_kwargs(),
    )
    if result.returncode != 0:
        return "unknown"
    value = result.stdout.strip()
    return value or "unknown"


def resolution_area(value: str) -> int:
    match = re.fullmatch(r"(\d+)x(\d+)", (value or "").strip())
    if not match:
        return 0
    return int(match.group(1)) * int(match.group(2))


def resolution_height(value: str) -> int:
    match = re.fullmatch(r"(\d+)x(\d+)", (value or "").strip())
    return int(match.group(2)) if match else 0


def probe_stream_codecs(path: str) -> tuple[str, str]:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    video_result = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "default=nw=1:nk=1",
            path,
        ],
        capture_output=True,
        creationflags=creationflags,
        **subprocess_text_kwargs(),
    )
    audio_result = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "default=nw=1:nk=1",
            path,
        ],
        capture_output=True,
        creationflags=creationflags,
        **subprocess_text_kwargs(),
    )
    video_codec = video_result.stdout.strip() if video_result.returncode == 0 else ""
    audio_codec = audio_result.stdout.strip() if audio_result.returncode == 0 else ""
    return video_codec, audio_codec


def can_copy_to_mp4(path: str) -> bool:
    video_codec, audio_codec = probe_stream_codecs(path)
    return video_codec in {"h264", "avc1"} and audio_codec.startswith("aac")


def can_copy_to_mp4_at_height(path: str, max_height: int | None = None) -> bool:
    if not can_copy_to_mp4(path):
        return False
    if not max_height:
        return True
    source_height = resolution_height(probe_video_resolution(path))
    return bool(source_height and source_height <= max_height)


def detect_local_media_kind(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in VIDEO_INPUT_EXTENSIONS:
        return "video"
    if ext in AUDIO_INPUT_EXTENSIONS:
        return "audio"
    return "video" if has_video_stream(path) else "audio"


def unique_path(path: str) -> str:
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    i = 2
    while True:
        candidate = f"{root} ({i}){ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1


def fmt_folder_name(label: str) -> str:
    return label.upper().replace(" ", "_").replace("+", "_").replace("(", "").replace(")", "")


def parse_quality_height(label: str) -> int | None:
    match = re.match(r"(\d+)p", (label or "").strip(), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def human_bytes(value: int | float | None) -> str:
    if value is None:
        return ""
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def format_eta(seconds: int | float | None) -> str:
    if seconds is None:
        return ""
    try:
        seconds = max(0, int(seconds))
    except (TypeError, ValueError):
        return ""
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{sec:02d}"
    return f"{minutes}:{sec:02d}"


def subprocess_text_kwargs() -> dict:
    return {
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }


def run_cmd_live(cmd: list[str], on_line=None) -> tuple[bool, str]:
    # Only publish a complete conversion; reserve the destination without overwriting.
    destination = cmd[-1]
    try:
        fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except OSError as ex:
        return False, str(ex)
    temporary = None
    process = None
    completed = False
    try:
        fd, temporary = tempfile.mkstemp(prefix=".clean-converter-", suffix=os.path.splitext(destination)[1], dir=os.path.dirname(os.path.abspath(destination)))
        os.close(fd)
        actual = [cmd[0], "-nostdin", "-y", *cmd[1:-1], temporary]
        process = subprocess.Popen(actual, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                                   **subprocess_text_kwargs())
        tail = deque(maxlen=50)
        for line in process.stderr:
            text = line.strip()
            if text:
                tail.append(text)
            if on_line:
                on_line(text)
        if process.wait() != 0:
            return False, "\n".join(tail)[-4500:] or "Conversion failed."
        if os.path.getsize(temporary) == 0:
            return False, "Conversion produced an empty file."
        os.replace(temporary, destination)
        completed = True
        return True, ""
    except Exception as ex:
        return False, str(ex)
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stderr:
                process.stderr.close()
        for path in ([temporary] + ([] if completed else [destination])):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass


def clean_error_text(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("ERROR:"):
        text = text[6:].strip()
    return text


def is_retryable_ytdlp_error(message: str) -> bool:
    text = clean_error_text(message).lower()
    return (
        "requested format is not available" in text
        or "uygun format bulunamadi" in text
        or "http error 403" in text
        or "403 forbidden" in text
        or "downloaded file is empty" in text
        or "file is empty" in text
    )


def build_video_format_chain(quality_label: str) -> list[str]:
    """Prefer HLS streams, which avoid YouTube GVS 403 failures mid-download."""
    max_height = parse_quality_height(quality_label)
    height_filter = f"[height<={max_height}]" if max_height else ""
    return [
        (
            f"bestvideo*[protocol^=m3u8][vcodec*=avc1]{height_filter}"
            f"+bestaudio[protocol^=m3u8]/best[protocol^=m3u8]{height_filter}"
        ),
        (
            f"bestvideo*[protocol^=m3u8]{height_filter}"
            f"+bestaudio[protocol^=m3u8]/best[protocol^=m3u8]{height_filter}"
        ),
        (
            f"bestvideo*[protocol=https][vcodec*=avc1]{height_filter}"
            f"+bestaudio[protocol=https][ext=m4a]/best[protocol=https][ext=mp4]{height_filter}"
        ),
        f"bestvideo*{height_filter}+bestaudio/best{height_filter}",
        f"bv*{height_filter}+ba/b{height_filter}",
        f"best{height_filter}",
    ]


def build_audio_format_chain() -> list[str]:
    return [
        "bestaudio[protocol^=m3u8]",
        "bestaudio[protocol=https]/bestaudio/best",
        "bestaudio/best",
    ]


def build_ytdlp_merge_options() -> dict:
    """Repair missing HLS timestamps before yt-dlp merges video and audio."""
    return {
        "merge_output_format": "mp4",
        "postprocessor_args": {
            "merger+ffmpeg_i": ["-fflags", "+genpts"],
            "merger+ffmpeg_o": ["-avoid_negative_ts", "make_zero"],
        },
    }


class QuietYtDlpLogger:
    def debug(self, _msg: str) -> None:
        pass

    def info(self, _msg: str) -> None:
        pass

    def warning(self, _msg: str) -> None:
        pass

    def error(self, _msg: str) -> None:
        pass


def explain_yt_error(message: str, url: str) -> str:
    msg = clean_error_text(message)
    lower = msg.lower()

    if "sign in to confirm you're not a bot" in lower or "confirm you're not a bot" in lower:
        return (
            "YouTube requested additional bot verification.\n\n"
            "Why: YouTube requires an extra verification step for this video.\n"
            "What to try: Wait and retry later, or try another network with any VPN disabled.\n\n"
            f"Technical detail:\n{msg}"
        )

    if "private video" in lower:
        return f"This video is private and cannot be downloaded.\n\nTechnical detail:\n{msg}"

    if "login required" in lower or "sign in" in lower:
        return (
            "This video requires sign-in or may have an age, account, or regional restriction.\n\n"
            f"Technical detail:\n{msg}"
        )

    if "video unavailable" in lower or "this video is unavailable" in lower:
        return (
            "The video is unavailable. It may have been removed, hidden, or region-restricted.\n\n"
            f"Link:\n{url}\n\nTechnical detail:\n{msg}"
        )

    if "unsupported url" in lower:
        return f"This link does not appear to be supported.\n\nLink:\n{url}\n\nTechnical detail:\n{msg}"

    if "requested format is not available" in lower or "no video formats found" in lower:
        return (
            "No format compatible with the selected quality was found. The available streams may use "
            "separate audio/video, a quality limit, or a service-side restriction.\n\n"
            f"Technical detail:\n{msg}"
        )

    if "http error 403" in lower or "403 forbidden" in lower:
        return (
            "The server denied access (403). This may be caused by temporary service protection, a regional "
            "restriction, an expired stream URL, or a client/extractor issue.\n\n"
            f"Technical detail:\n{msg}"
        )

    if "http error 429" in lower or "too many requests" in lower:
        return (
            "Too many requests were detected (429). Stop repeated attempts, wait, and try again later.\n\n"
            f"Technical detail:\n{msg}"
        )

    return f"The video could not be downloaded.\n\nLink:\n{url}\n\nTechnical detail:\n{msg or 'Unknown yt-dlp error'}"


# ---------------- FFmpeg commands ----------------
def build_audio_convert_cmd(inp: str, outp: str, fmt: str, mp3_bitrate: str) -> list[str]:
    cmd = [FFMPEG, "-i", inp, "-vn"]
    if fmt == "mp3":
        cmd += ["-b:a", mp3_bitrate]
    elif fmt == "wav":
        cmd += ["-ar", "44100"]
    elif fmt == "flac":
        cmd += ["-c:a", "flac"]
    elif fmt == "ogg":
        cmd += ["-c:a", "libvorbis", "-q:a", "5"]
    elif fmt == "m4a":
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    elif fmt == "aac":
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += [outp]
    return cmd


def build_video_scale_args(max_height: int | None) -> list[str]:
    if not max_height:
        return []
    return [
        "-vf",
        f"scale='min(iw,{max_height}*a)':'min(ih,{max_height})':force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2",
    ]


def video_canvas_size(max_height: int | None) -> str:
    height = max_height or 1080
    width = int(round(height * 16 / 9))
    width -= width % 2
    height -= height % 2
    return f"{width}x{height}"


def build_video_to_mp4_compatible_cmd(inp: str, out_mp4: str, max_height: int | None = None) -> list[str]:
    if can_copy_to_mp4_at_height(inp, max_height):
        return [
            FFMPEG,
            "-i",
            inp,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            out_mp4,
        ]
    return [
        FFMPEG,
        "-i",
        inp,
        *build_video_scale_args(max_height),
        "-c:v",
        "libx264",
        "-preset",
        VIDEO_X264_PRESET,
        "-crf",
        VIDEO_X264_CRF,
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        out_mp4,
    ]


def build_video_container_cmd(inp: str, out_path: str, has_video: bool, movflags: bool, max_height: int | None = None) -> list[str]:
    cmd = [FFMPEG, "-i", inp]
    if has_video:
        cmd += build_video_scale_args(max_height)
        cmd += ["-c:v", "libx264", "-preset", VIDEO_X264_PRESET, "-crf", VIDEO_X264_CRF, "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-vn", "-c:a", "aac", "-b:a", "192k"]
    if movflags:
        cmd += ["-movflags", "+faststart"]
    cmd += [out_path]
    return cmd


def build_webm_convert_cmd(inp: str, out_webm: str, has_video: bool, max_height: int | None = None) -> list[str]:
    cmd = [FFMPEG, "-i", inp]
    if has_video:
        cmd += build_video_scale_args(max_height)
        cmd += ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-c:a", "libopus", "-b:a", "128k"]
    else:
        cmd += ["-vn", "-c:a", "libopus", "-b:a", "128k"]
    cmd += [out_webm]
    return cmd


def build_audio_to_video_cmd(
    audio_path: str,
    cover_img: str | None,
    out_path: str,
    fmt_choice: str,
    movflags: bool,
    max_height: int | None = None,
) -> list[str]:
    if cover_img:
        cmd = [FFMPEG, "-loop", "1", "-i", cover_img, "-i", audio_path]
    else:
        cmd = [
            FFMPEG,
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={video_canvas_size(max_height)}:r=30",
            "-i",
            audio_path,
        ]

    cmd += ["-map", "0:v:0", "-map", "1:a:0", *build_video_scale_args(max_height)]
    if fmt_choice == "webm_video":
        cmd += ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-c:a", "libopus", "-b:a", "128k"]
    else:
        cmd += [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
        ]
        if movflags:
            cmd += ["-movflags", "+faststart"]

    cmd += ["-shortest", out_path]
    return cmd


def build_cover_preprocess_cmd(in_img: str, out_img: str) -> list[str]:
    vf = (
        "crop=min(iw\\,ih):min(iw\\,ih):(iw-min(iw\\,ih))/2:(ih-min(iw\\,ih))/2,"
        f"scale={COVER_MAX_DIM}:{COVER_MAX_DIM}:force_original_aspect_ratio=decrease,"
        "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p"
    )
    return [
        FFMPEG,
        "-y",
        "-i",
        in_img,
        "-vf",
        vf,
        "-q:v",
        "2",
        out_img,
    ]




def build_audio_to_mp4_cover_cmd(audio_path: str, cover_img: str, out_mp4: str) -> list[str]:
    return build_audio_to_video_cmd(audio_path, cover_img, out_mp4, "mp4_video", True, COVER_MAX_DIM)


# ---------------- Main App ----------------
class CleanConverter(TkinterDnD.Tk):
    def __init__(self):
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DemirDemiroz.CleanConverter.1")
        super().__init__()
        self.withdraw()
        self.title(APP_NAME)
        # Prefer a taller window, while leaving room for the taskbar/title bar.
        initial_height = min(860, max(540, self.winfo_screenheight() - 110))
        self.geometry(f"1080x{initial_height}")
        self.minsize(740, 540)
        self.configure(bg=BG_COLOR)
        self._set_app_icon()

        ensure_tools_or_exit(self)

        self.cfg = load_config()
        self._busy = False
        self._ui_events = queue.Queue()
        self._temp_workspace = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.input_file: str | None = None
        self.cover_img: str | None = None
        self.active_popup = None
        self.active_popup_button = None
        self.active_popup_button_style = None
        self._startup_splash: StartupSplash | None = None

        self._build_ui_modern()
        self.after(100, self._drain_ui_events)
        self.after(0, self._start_startup_sequence)

    def _start_startup_sequence(self):
        try:
            self.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        self.deiconify()
        self.update_idletasks()
        self._startup_splash = StartupSplash(
            root=self,
            app_name=APP_NAME,
            studio_name="Made by Demir Demiröz",
            logo_path=resource_path(APP_ICON_PNG),
            bg_color=BG_COLOR,
            panel_color=PANEL_COLOR,
            text_primary=TEXT_PRIMARY,
            text_muted=TEXT_MUTED,
            border_color="#263554",
            accent_color=ACCENT_COLOR,
        )
        self._startup_splash.show(on_complete=self._complete_startup_sequence)
        self.after(10, self._reveal_splash_window)

    def _reveal_splash_window(self):
        if not self.winfo_exists():
            return
        try:
            self.attributes("-alpha", 1.0)
        except tk.TclError:
            pass

    def _complete_startup_sequence(self):
        self._startup_splash = None
        if not self.winfo_exists():
            return
        try:
            self.attributes("-alpha", 1.0)
        except tk.TclError:
            pass
        if not self.cfg.get("output_dir"):
            out = self.ask_output_dir(first_time=True)
            if not out:
                self.destroy()
                return
            self.cfg["output_dir"] = out
            try:
                self.persist_config()
            except OSError as ex:
                messagebox.showwarning(
                    "Config Warning",
                    "Output folder was selected, but settings could not be saved yet.\n\n"
                    f"Technical detail:\n{ex}"
                )
        self.lift()
        try:
            self.focus_force()
        except tk.TclError:
            pass

    # ---------- UI ----------
    def _build_ui_modern(self):
        root = ctk.CTkFrame(self, fg_color=BG_COLOR)
        root.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(root, fg_color=BG_COLOR)
        footer.pack(side="bottom", fill="x", padx=26, pady=(0, 18))
        self.status = ctk.CTkLabel(footer, text="Ready.", text_color=TEXT_MUTED, font=("Segoe UI", 12))
        self.status.pack(fill="x", anchor="w")
        self.status.configure(wraplength=680, justify="left", anchor="w")
        support_row = ctk.CTkFrame(footer, fg_color="transparent")
        self.support_link = ctk.CTkButton(
            support_row, text="demirdemiroz.com", width=112, height=28,
            font=("Segoe UI", 12), anchor="w", border_spacing=0,
            fg_color="transparent", hover_color=SURFACE_ALT_COLOR,
            text_color=TEXT_SOFT, command=open_bug_report)
        self.support_hint = ctk.CTkLabel(
            support_row, text="Questions or report any bugs →",
            font=("Segoe UI", 12), text_color=TEXT_SOFT, anchor="w")
        self.support_hint.pack(side="left", padx=(0, 4))
        self.support_link.pack(side="left")
        self.credit = ctk.CTkLabel(footer, text="Made by Demir Demiröz", text_color=TEXT_SOFT, font=("Segoe UI", 12))
        self.credit.pack(side="right", anchor="e")
        support_row.pack(side="left", padx=(0, 16))
        for label, url in [("GitHub", "https://github.com/DDemiroz")]:
            ctk.CTkButton(footer, text=label, width=65, height=28, fg_color="transparent",
                          hover_color=SURFACE_ALT_COLOR, text_color=TEXT_MUTED,
                          command=lambda address=url: webbrowser.open(address)).pack(side="left", padx=(0, 8))

        action_bar = ctk.CTkFrame(root, fg_color=BG_COLOR)
        action_bar.pack(side="bottom", fill="x", padx=26, pady=(0, 10))
        self.convert_btn = ctk.CTkButton(
            action_bar,
            text="Convert",
            width=240,
            height=46,
            corner_radius=12,
            command=self.convert,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            font=("Segoe UI Semibold", 14),
        )
        self.convert_btn.pack(side="right")
        ctk.CTkButton(action_bar, text="Output folder…", width=150, height=40,
                      fg_color=SURFACE_ALT_COLOR, hover_color=ACCENT_HOVER,
                      command=self.change_output_dir).pack(side="left")

        content = ctk.CTkScrollableFrame(root, fg_color=BG_COLOR, corner_radius=0)
        content.pack(fill="both", expand=True, padx=26, pady=(26, 12))

        hero = ctk.CTkFrame(content, fg_color=BG_COLOR, corner_radius=0)
        hero.pack(fill="x", pady=(0, 18))

        hero_body = ctk.CTkFrame(hero, fg_color="transparent")
        hero_body.pack(fill="x", padx=2, pady=6)
        hero_body.grid_columnconfigure(0, weight=3)
        hero_body.grid_columnconfigure(1, weight=2)

        hero_text = ctk.CTkFrame(hero_body, fg_color="transparent")
        hero_text.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        ctk.CTkLabel(hero_text, text=APP_NAME, font=("Segoe UI Semibold", 25), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            hero_text,
            text="Local files. Supported links. Your preferred format.",
            font=("Segoe UI", 13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))

        toolbar = ctk.CTkFrame(hero_text, fg_color="transparent")
        toolbar.pack(fill="x", pady=(16, 0))
        ctk.CTkButton(
            toolbar,
            text="Choose File",
            command=self.pick_file,
            height=40,
            corner_radius=12,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
        ).pack(side="left")
        ctk.CTkLabel(
            toolbar,
            text="or drop a file",
            font=("Segoe UI", 12),
            text_color=TEXT_SOFT,
        ).pack(side="left", padx=(14, 0), pady=2)

        self.drop = ctk.CTkLabel(
            hero_body,
            text="Drop a file here",
            height=96,
            corner_radius=8,
            fg_color=SURFACE_COLOR,
            text_color=TEXT_PRIMARY,
            font=("Segoe UI Semibold", 18),
        )
        self.drop.grid(row=0, column=1, sticky="nsew")
        self.drop.drop_target_register(DND_FILES)
        self.drop.dnd_bind("<<Drop>>", self.on_drop)

        self.main_grid = ctk.CTkFrame(content, fg_color="transparent")
        self.main_grid.pack(fill="both", expand=True)
        self.main_grid.grid_columnconfigure(0, weight=3)
        self.main_grid.grid_columnconfigure(1, weight=2)
        self.main_grid.grid_rowconfigure(0, weight=1)
        self.main_grid.grid_rowconfigure(1, weight=1)

        self.left_panel = ctk.CTkFrame(
            self.main_grid,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color="#263554",
        )
        self.right_panel = ctk.CTkFrame(
            self.main_grid,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color="#263554",
        )
        self._refresh_modern_layout()

        ctk.CTkLabel(self.left_panel, text="Source", font=("Segoe UI Semibold", 18), text_color=TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(18, 6))
        ctk.CTkLabel(
            self.left_panel,
            text="Paste a link or prepare local media and optional cover art.",
            font=("Segoe UI", 12),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=18)
        self.source_summary = ctk.CTkLabel(
            self.left_panel,
            text="No source selected yet.",
            font=("Segoe UI", 12),
            text_color=TEXT_SOFT,
            wraplength=560,
            justify="left",
        )
        self.source_summary.pack(anchor="w", padx=18, pady=(6, 0))

        link_frame = ctk.CTkFrame(self.left_panel, fg_color=SURFACE_COLOR, corner_radius=14)
        link_frame.pack(fill="x", padx=18, pady=(16, 12))
        ctk.CTkLabel(link_frame, text="Link", text_color=TEXT_MUTED, font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=14, pady=(10, 2))
        self.link_entry = ctk.CTkEntry(
            link_frame,
            placeholder_text="Paste a supported media link here",
            height=42,
            corner_radius=12,
            fg_color=SURFACE_ALT_COLOR,
            border_color="#314264",
            text_color=TEXT_PRIMARY,
        )
        self.link_entry.pack(fill="x", padx=12, pady=(0, 12))
        self.link_entry.bind("<KeyRelease>", lambda _e: (self.close_format_dropdown(), self.update_format_controls()))

        extras = ctk.CTkFrame(self.left_panel, fg_color=SURFACE_COLOR, corner_radius=14)
        extras.pack(fill="x", padx=18, pady=(0, 12))
        ctk.CTkLabel(extras, text="Cover / Extras", text_color=TEXT_MUTED, font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=14, pady=(10, 8))

        self.cover_frame = ctk.CTkFrame(extras, fg_color="transparent")
        self.cover_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.cover_btn = ctk.CTkButton(
            self.cover_frame,
            text="Select Cover Image",
            command=self.pick_cover,
            height=38,
            corner_radius=12,
            fg_color=SURFACE_ALT_COLOR,
            hover_color="#314264",
        )
        self.cover_btn.pack(side="left")
        self.cover_label = ctk.CTkLabel(self.cover_frame, text="No cover selected", text_color=TEXT_MUTED, font=("Segoe UI", 12))
        self.cover_label.pack(side="left", padx=(12, 0))

        self.auto_thumb_var = ctk.BooleanVar(value=True)
        self.auto_thumb = ctk.CTkCheckBox(
            extras,
            text="Use link thumbnail automatically if no cover is selected",
            variable=self.auto_thumb_var,
            command=self.on_auto_thumbnail_toggle,
            text_color=TEXT_PRIMARY,
            fg_color="#147d83",
            hover_color=ACCENT_HOVER,
        )
        self.auto_thumb.pack(anchor="w", padx=14, pady=(0, 12))

        ctk.CTkLabel(self.right_panel, text="Output Settings", font=("Segoe UI Semibold", 18), text_color=TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(18, 6))
        ctk.CTkLabel(
            self.right_panel,
            text="Choose output format, bitrate, and target quality.",
            font=("Segoe UI", 12),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=18)

        opt = ctk.CTkFrame(self.right_panel, fg_color=SURFACE_COLOR, corner_radius=14)
        opt.pack(fill="x", padx=18, pady=(16, 12))
        ctk.CTkLabel(opt, text="Format", text_color=TEXT_MUTED, font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=14, pady=(12, 6))

        self.last_format_label = self.cfg.get("default_format", DEFAULT_FORMAT_LABEL)
        self.format_var = ctk.StringVar(value=self.last_format_label)
        self.format_button = ctk.CTkButton(
            opt,
            text=self.format_var.get(),
            command=self.toggle_format_dropdown,
            height=38,
            corner_radius=12,
            fg_color=SURFACE_ALT_COLOR,
            hover_color="#314264",
            text_color=TEXT_PRIMARY,
            anchor="w",
            font=("Segoe UI", 13),
        )
        self.format_button.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(opt, text="MP3 Bitrate", text_color=TEXT_MUTED, font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=14, pady=(0, 6))
        self.mp3_var = ctk.StringVar(value=self.cfg.get("mp3_bitrate", "192k"))
        self.mp3_button = ctk.CTkButton(
            opt,
            text=self.mp3_var.get(),
            command=lambda: self.toggle_simple_dropdown(self.mp3_button, ["192k", "256k", "320k"], self.select_mp3_bitrate),
            height=38,
            corner_radius=12,
            fg_color=SURFACE_ALT_COLOR,
            hover_color="#314264",
            text_color=TEXT_PRIMARY,
            anchor="w",
            font=("Segoe UI", 13),
        )
        self.mp3_button.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(opt, text="Video Quality", text_color=TEXT_MUTED, font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=14, pady=(0, 6))
        self.video_quality_var = ctk.StringVar(value=self.cfg.get("video_quality", DEFAULT_VIDEO_QUALITY))
        self.video_quality_button = ctk.CTkButton(
            opt,
            text=self.video_quality_var.get(),
            command=lambda: self.toggle_simple_dropdown(
                self.video_quality_button,
                VIDEO_QUALITY_OPTIONS,
                self.select_video_quality,
            ),
            height=38,
            corner_radius=12,
            fg_color=SURFACE_ALT_COLOR,
            hover_color="#314264",
            text_color=TEXT_PRIMARY,
            anchor="w",
            font=("Segoe UI", 13),
        )
        self.video_quality_button.pack(fill="x", padx=12, pady=(0, 14))
        self.format_hint = ctk.CTkLabel(
            opt,
            text="Choose a file or paste a link to tailor the available output formats.",
            text_color=TEXT_SOFT,
            font=("Segoe UI", 12),
            wraplength=280,
            justify="left",
        )
        self.format_hint.pack(anchor="w", padx=14, pady=(0, 14))

        self.bind("<Configure>", self._on_window_resize)
        self.bind_all("<Button-1>", self._on_global_click, add="+")
        self.update_format_controls()

    def _set_app_icon(self) -> None:
        png_path = resource_path(APP_ICON_PNG)
        ico_path = resource_path(APP_ICON_ICO)
        if os.path.exists(png_path):
            try:
                icon_image = tk.PhotoImage(file=png_path)
                self.iconphoto(True, icon_image)
                self._icon_image = icon_image
            except Exception:
                pass
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    def _refresh_modern_layout(self):
        if not hasattr(self, "left_panel") or not hasattr(self, "right_panel"):
            return

        width = self.winfo_width() or self.winfo_reqwidth()
        if width < RESPONSIVE_BREAKPOINT:
            self.main_grid.grid_columnconfigure(0, weight=1)
            self.main_grid.grid_columnconfigure(1, weight=0)
            self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 12))
            self.right_panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        else:
            self.main_grid.grid_columnconfigure(0, weight=3)
            self.main_grid.grid_columnconfigure(1, weight=2)
            self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 9), pady=0)
            self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(9, 0), pady=0)

    def _on_window_resize(self, _event=None):
        if _event is not None and _event.widget is not self:
            return
        previous_size = getattr(self, "_last_window_size", None)
        current_size = (self.winfo_width(), self.winfo_height())
        self._refresh_modern_layout()
        if previous_size is not None and current_size != previous_size:
            self.close_format_dropdown()
        self._last_window_size = current_size

    def get_source_kind(self) -> str:
        link = self.link_entry.get().strip() if hasattr(self, "link_entry") else ""
        if is_media_link(link):
            return "link"
        if self.input_file and os.path.exists(self.input_file):
            return detect_local_media_kind(self.input_file)
        return "empty"

    def allowed_format_labels(self) -> list[str]:
        return FORMAT_LABELS

    def close_active_dropdown(self):
        popup = getattr(self, "active_popup", None)
        if popup is not None:
            try:
                if popup.winfo_exists():
                    popup.destroy()
            except tk.TclError:
                pass
        self.restore_dropdown_button()
        self.active_popup = None
        self.active_popup_button = None

    def close_format_dropdown(self):
        self.close_active_dropdown()

    def mute_dropdown_button(self, button):
        self.active_popup_button_style = {
            "button": button,
            "text": button.cget("text"),
            "fg_color": button.cget("fg_color"),
            "hover_color": button.cget("hover_color"),
            "text_color": button.cget("text_color"),
        }
        button.configure(
            text="",
            fg_color=SURFACE_COLOR,
            hover_color=SURFACE_COLOR,
            text_color=SURFACE_COLOR,
        )

    def restore_dropdown_button(self):
        style = getattr(self, "active_popup_button_style", None)
        if not style:
            return
        button = style.get("button")
        try:
            if button is not None and button.winfo_exists():
                button.configure(
                    text=style["text"],
                    fg_color=style["fg_color"],
                    hover_color=style["hover_color"],
                    text_color=style["text_color"],
                )
        except tk.TclError:
            pass
        self.active_popup_button_style = None

    def _point_inside_widget(self, widget, x_root: int, y_root: int) -> bool:
        if widget is None:
            return False
        try:
            if not widget.winfo_exists():
                return False
            left = widget.winfo_rootx()
            top = widget.winfo_rooty()
            right = left + widget.winfo_width()
            bottom = top + widget.winfo_height()
        except tk.TclError:
            return False
        return left <= x_root <= right and top <= y_root <= bottom

    def _on_global_click(self, event):
        popup = getattr(self, "active_popup", None)
        if popup is None:
            return
        try:
            if not popup.winfo_exists():
                self.close_active_dropdown()
                return
        except tk.TclError:
            self.close_active_dropdown()
            return

        if self._point_inside_widget(popup, event.x_root, event.y_root):
            return
        if self._point_inside_widget(self.active_popup_button, event.x_root, event.y_root):
            return
        self.close_active_dropdown()

    def create_dropdown_popup(self, button, height: int, width: int | None = None, align: str = "left"):
        self.close_active_dropdown()
        self.update_idletasks()
        parent = self
        width = width or max(button.winfo_width(), 180)
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        if align == "right":
            x = button.winfo_rootx() - parent_x + button.winfo_width() - width
        else:
            x = button.winfo_rootx() - parent_x
        y = button.winfo_rooty() - parent_y + button.winfo_height() + 4

        x = max(10, min(x, max(10, parent.winfo_width() - width - 10)))
        if y + height > parent.winfo_height() - 10:
            y = max(10, parent.winfo_height() - height - 10)

        popup = ctk.CTkFrame(
            parent,
            width=width,
            height=height,
            fg_color=SURFACE_ALT_COLOR,
            corner_radius=0,
            border_width=0,
        )
        popup.pack_propagate(False)
        popup.place(x=x, y=y)
        popup.bind("<Escape>", lambda _e: self.close_active_dropdown())
        popup.focus_set()
        self.active_popup = popup
        self.active_popup_button = button
        popup.lift()
        return popup

    def toggle_format_dropdown(self):
        popup = getattr(self, "active_popup", None)
        if popup is not None and self.active_popup_button is self.format_button:
            try:
                if popup.winfo_exists():
                    self.close_active_dropdown()
                    return
            except tk.TclError:
                pass
        self.open_format_dropdown()

    def open_format_dropdown(self):
        video_options = [*VIDEO_FORMAT_LABELS, COVER_FORMAT_LABEL]
        audio_options = AUDIO_FORMAT_LABELS
        popup_height = 20 + 2 * 23 + (len(video_options) + len(audio_options)) * 23 + 1
        frame = self.create_dropdown_popup(self.format_button, popup_height, max(self.format_button.winfo_width(), 270))
        ctk.CTkFrame(frame, height=5, fg_color="transparent").pack(fill="x")
        self.add_dropdown_section(frame, FORMAT_SECTION_VIDEO, video_options, self.select_format)
        ctk.CTkFrame(frame, height=1, fg_color="#3d4f72").pack(fill="x", padx=0, pady=0)
        self.add_dropdown_section(frame, FORMAT_SECTION_AUDIO, audio_options, self.select_format)
        ctk.CTkFrame(frame, height=7, fg_color="transparent").pack(fill="x")
        frame.lift()

    def add_dropdown_section(self, parent, title: str, options: list[str], callback):
        ctk.CTkLabel(
            parent,
            text=f"~ {title} ~",
            height=23,
            text_color=TEXT_PRIMARY,
            font=("Segoe UI Semibold", 12),
        ).pack(fill="x", padx=0, pady=0)
        self.add_dropdown_options(parent, options, callback)

    def add_dropdown_options(self, parent, options: list[str], callback):
        for label in options:
            option = ctk.CTkButton(
                parent,
                text=label,
                height=23,
                corner_radius=0,
                fg_color="transparent",
                hover_color="#314264",
                text_color=TEXT_PRIMARY,
                anchor="w",
                font=("Segoe UI", 12),
                command=lambda value=label: callback(value),
            )
            option.pack(fill="x", padx=0, pady=0)
            option.bind("<Return>", lambda _e, value=label: callback(value))
            option.bind("<Escape>", lambda _e: self.close_active_dropdown())

    def select_format(self, value: str):
        if value not in FORMAT_MAP:
            return
        self.format_var.set(value)
        self.last_format_label = value
        self.close_active_dropdown()
        self.format_button.configure(text=value)
        self.update_format_controls()

    def toggle_simple_dropdown(self, button, values: list[str], callback):
        popup = getattr(self, "active_popup", None)
        if popup is not None and self.active_popup_button is button:
            try:
                if popup.winfo_exists():
                    self.close_active_dropdown()
                    return
            except tk.TclError:
                pass
        self.open_simple_dropdown(button, values, callback)

    def open_simple_dropdown(self, button, values: list[str], callback):
        height = 12 + len(values) * 25
        width = max(130, min(button.winfo_width(), max(len(value) for value in values) * 9 + 58))
        frame = self.create_dropdown_popup(button, height, width)
        ctk.CTkFrame(frame, height=5, fg_color="transparent").pack(fill="x")
        self.add_dropdown_options(frame, values, callback)
        ctk.CTkFrame(frame, height=7, fg_color="transparent").pack(fill="x")
        frame.lift()

    def select_mp3_bitrate(self, value: str):
        self.mp3_var.set(value)
        self.close_active_dropdown()
        self.mp3_button.configure(text=value)

    def select_video_quality(self, value: str):
        self.video_quality_var.set(value)
        self.close_active_dropdown()
        self.video_quality_button.configure(text=value)

    def on_format_change(self, value: str):
        if value not in FORMAT_MAP:
            self.format_var.set(self.last_format_label)
            return
        self.last_format_label = value
        self.update_format_controls()

    def update_source_summary(self):
        source_kind = self.get_source_kind()
        if source_kind == "link":
            host = media_link_host(self.link_entry.get())
            text = "Link mode active. Video, audio, and cover-based exports are available."
            if host:
                text = f"Link mode active for {host}. Video, audio, and cover-based exports are available."
        elif source_kind == "video" and self.input_file:
            text = f"Local video file ready: {os.path.basename(self.input_file)}"
        elif source_kind == "audio" and self.input_file:
            text = f"Local audio file ready: {os.path.basename(self.input_file)}"
        else:
            text = "No source selected yet."
        self.source_summary.configure(text=text)

    def on_auto_thumbnail_toggle(self):
        if self.auto_thumb_var.get():
            self.ui_status("Auto thumbnail enabled. Link thumbnails will be used when no cover is selected.")
        else:
            self.ui_status("Auto thumbnail disabled. A selected cover will still be used.")

    def update_format_controls(self):
        source_kind = self.get_source_kind()
        current_label = self.format_var.get()
        if current_label not in FORMAT_MAP:
            fallback = self.last_format_label if self.last_format_label in FORMAT_MAP else DEFAULT_FORMAT_LABEL
            self.format_var.set(fallback)
            current_label = fallback
        self.last_format_label = current_label
        self.format_button.configure(text=current_label)
        is_cover = FORMAT_MAP.get(current_label) == "mp4_cover"
        is_video = FORMAT_MAP.get(current_label) in VIDEO_OUTPUT_KEYS
        cover_relevant = is_cover or (source_kind == "audio" and is_video)

        self.cover_btn.configure(state="normal")
        self.cover_label.configure(text_color=TEXT_MUTED if cover_relevant else TEXT_SOFT)
        self.auto_thumb.configure(state="normal")

        video_state = "normal" if is_video else "disabled"
        self.video_quality_button.configure(state=video_state)
        if source_kind == "audio":
            hint = "Audio file detected. Video formats create a cover video, or a black-screen video if no cover is selected."
        elif source_kind == "video":
            hint = "Video file detected. You can export video containers or extract audio formats."
        elif source_kind == "link":
            hint = "Link mode supports video, audio, and cover-based exports depending on the source."
        else:
            hint = "Choose a file or paste a link to tailor the available output formats."
        self.format_hint.configure(text=hint)
        self.update_source_summary()

    # ---------- UI helpers (thread-safe) ----------
    def ui_status(self, text: str):
        self._ui_events.put(("status", text))

    def ui_done(self, path: str):
        self.ui_status(f"Done: {status_path(path)}")

    def ui_error(self, title: str, text: str):
        help_text = "\n\nNeed help? Close this dialog and click 'demirdemiroz.com' next to 'Questions or report any bugs' at the bottom of the app.\nDo not share private paths, links or account details."
        self._ui_events.put(("error", (title, text + help_text)))

    def _drain_ui_events(self):
        for _ in range(100):
            try:
                kind, value = self._ui_events.get_nowait()
            except queue.Empty:
                break
            if kind == "status":
                self.status.configure(text=value)
            elif kind == "error":
                self.status.configure(text="Failed. Check the error details.")
                messagebox.showerror(*value)
            elif kind == "finished":
                self._busy = False
                self.convert_btn.configure(state="normal")
                self.auto_thumb.configure(state="normal")
        self.after(100, self._drain_ui_events)

    def on_close(self):
        if self._busy:
            messagebox.showinfo("Conversion running", "Please wait for the current operation to finish before closing.")
            return
        self.cleanup_temp()
        self.destroy()

    def persist_config(self):
        self.cfg = normalize_config(self.cfg)
        save_config(self.cfg)

    def run_background(self, job_fn):
        def runner():
            try:
                job_fn()
            finally:
                try:
                    self.cleanup_temp()
                finally:
                    self._ui_events.put(("finished", None))

        self._busy = True
        self.convert_btn.configure(state="disabled")
        self.auto_thumb.configure(state="disabled")
        threading.Thread(target=runner, daemon=True).start()

    # ---------- Output dir ----------
    def ask_output_dir(self, first_time=False) -> str:
        title = "Select output folder" if first_time else "Select output folder"
        return filedialog.askdirectory(title=title) or ""

    def output_dir_for(self, label: str) -> str:
        base_out = self.cfg.get("output_dir", "")
        if not base_out:
            return ""
        if not self.cfg.get("organize_by_format", True):
            os.makedirs(base_out, exist_ok=True)
            return base_out
        out = os.path.join(base_out, fmt_folder_name(label))
        os.makedirs(out, exist_ok=True)
        return out

    def ensure_output_dir_ready(self) -> str:
        base_out = (self.cfg.get("output_dir") or "").strip()
        if not base_out:
            raise RuntimeError("Output folder is missing. Please choose an output folder first.")
        os.makedirs(base_out, exist_ok=True)
        try:
            probe = tempfile.NamedTemporaryFile(dir=base_out, prefix=".write-test-", delete=False)
            probe.close()
            os.remove(probe.name)
        except OSError as ex:
            raise RuntimeError(
                "Output folder is not writable. Choose another folder or check permissions.\n\n"
                f"Technical detail:\n{ex}"
            ) from ex
        return base_out

    # ---------- TEMP ----------
    def temp_dir(self) -> str:
        if self._temp_workspace is None:
            self._temp_workspace = tempfile.TemporaryDirectory(prefix="clean-converter-", dir=self.cfg["output_dir"])
        return self._temp_workspace.name

    def cleanup_temp(self):
        workspace = getattr(self, "_temp_workspace", None)
        if workspace is not None:
            try:
                workspace.cleanup()
                self._temp_workspace = None
            except OSError:
                # Retain ownership so a later cleanup can retry, never delete a shared path.
                pass

    def change_output_dir(self):
        if self._busy:
            return
        selected = self.ask_output_dir()
        if not selected:
            return
        previous = self.cfg["output_dir"]
        self.cfg["output_dir"] = selected
        try:
            self.ensure_output_dir_ready()
            self.persist_config()
            self.ui_status("Output folder updated.")
        except (OSError, RuntimeError) as ex:
            self.cfg["output_dir"] = previous
            messagebox.showerror("Output folder", str(ex))

    # ---------- Drop / pick ----------
    def on_drop(self, e):
        if self._busy:
            return
        self.close_format_dropdown()
        data = normalize_drop_data(e.data)
        if os.path.exists(data):
            self.input_file = data
            self.link_entry.delete(0, "end")
            self.drop.configure(text=f"Selected: {os.path.basename(data)}")
            self.update_format_controls()
            self.ui_status(f"Input file: {data}")
        else:
            self.input_file = None
            self.link_entry.delete(0, "end")
            self.link_entry.insert(0, data)
            self.drop.configure(text="Drop a file here")
            self.update_format_controls()
            self.ui_status("Link detected. Click Convert.")

    def pick_file(self):
        if self._busy:
            return
        self.close_format_dropdown()
        p = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[
                ("Media", "*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.opus *.wma *.mp4 *.webm *.mkv *.mov *.avi *.m4v"),
                ("All", "*.*"),
            ],
        )
        if p:
            self.input_file = p
            self.link_entry.delete(0, "end")
            self.drop.configure(text=f"Selected: {os.path.basename(p)}")
            self.update_format_controls()
            self.ui_status(f"Input file: {p}")

    def pick_cover(self):
        if self._busy:
            return
        self.close_format_dropdown()
        p = filedialog.askopenfilename(
            title="Select cover image",
            filetypes=[("Images", "*.jpg *.jpeg *.png"), ("All", "*.*")],
        )
        if p:
            self.cover_img = p
            self.cover_label.configure(text=os.path.basename(p))
            if FORMAT_MAP.get(self.format_var.get()) == "mp4_cover":
                self.ui_status("Cover selected.")
            else:
                self.ui_status("Cover selected. It will be used with MP4 Audio + Cover.")

    # ---------- yt-dlp ----------
    def yt_dlp_base_opts(self) -> dict:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "no_color": True,
            "noplaylist": True,
            "retries": 3,
            "fragment_retries": 3,
            "socket_timeout": 20,
            "logger": QuietYtDlpLogger(),
        }
        if os.path.isfile(DENO):
            opts["js_runtimes"] = {"deno": {"path": DENO}}
        return opts

    def run_yt_dlp(self, url: str, extra_opts: dict | None = None, download: bool = False):
        opts = self.yt_dlp_base_opts()
        if extra_opts:
            opts.update(extra_opts)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=download)
        except DownloadError as ex:
            raise RuntimeError(explain_yt_error(str(ex), url)) from ex
        except Exception as ex:
            raise RuntimeError(explain_yt_error(str(ex), url)) from ex

    def ytdlp_info(self, url: str) -> dict:
        return self.run_yt_dlp(url, download=False)

    def make_ytdlp_progress_hook(self, label: str):
        def hook(data: dict):
            status = data.get("status")
            if status == "downloading":
                downloaded = data.get("downloaded_bytes") or data.get("downloaded_bytes_estimate")
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                speed = data.get("speed")
                eta = data.get("eta")

                parts = [label]
                if downloaded and total:
                    percent = min(100.0, (downloaded / total) * 100)
                    parts.append(f"{percent:.1f}%")
                    parts.append(f"{human_bytes(downloaded)} / {human_bytes(total)}")
                elif downloaded:
                    parts.append(human_bytes(downloaded))

                if speed:
                    parts.append(f"{human_bytes(speed)}/s")
                eta_text = format_eta(eta)
                if eta_text:
                    parts.append(f"ETA {eta_text}")

                self.ui_status(" - ".join(part for part in parts if part))
            elif status == "finished":
                self.ui_status(f"{label} finished. Preparing file...")

        return hook

    def ytdlp_title(self, url: str) -> str:
        info = self.ytdlp_info(url)
        return safe_filename(info.get("title", "video"))

    def ytdlp_download_best(self, url: str, quality_label: str) -> str:
        tmp = self.temp_dir()
        format_chain = build_video_format_chain(quality_label)

        last_error = None
        total_attempts = len(format_chain)
        for attempt, format_selector in enumerate(format_chain, start=1):
            for fn in os.listdir(tmp):
                p = os.path.join(tmp, fn)
                if os.path.isfile(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

            ydl_opts = {
                "format": format_selector,
                "outtmpl": os.path.join(tmp, "%(title)s.%(ext)s"),
                "ffmpeg_location": TOOLS_DIR,
                **build_ytdlp_merge_options(),
                "continuedl": False,
                "nopart": True,
                "progress_hooks": [self.make_ytdlp_progress_hook("Downloading video")],
            }
            try:
                self.ui_status(f"Preparing download source {attempt}/{total_attempts} ({quality_label})...")
                self.run_yt_dlp(url, extra_opts=ydl_opts, download=True)
                last_error = None
                break
            except RuntimeError as ex:
                last_error = ex
                retryable = is_retryable_ytdlp_error(str(ex))
                if retryable:
                    if attempt < total_attempts:
                        self.ui_status(f"Download source {attempt}/{total_attempts} failed. Trying another source...")
                    else:
                        self.ui_status("All download sources failed. Showing error...")
                    continue
                raise

        if last_error:
            raise last_error

        candidates = []
        for fn in os.listdir(tmp):
            p = os.path.join(tmp, fn)
            if os.path.isfile(p) and os.path.getsize(p) > 0 and os.path.splitext(fn)[1].lower() in [".webm", ".mkv", ".mp4", ".mov"]:
                candidates.append(p)
        video_candidates = [p for p in candidates if has_video_stream(p)]
        if video_candidates:
            return max(
                video_candidates,
                key=lambda p: (resolution_area(probe_video_resolution(p)), os.path.getsize(p)),
            )
        if candidates:
            return max(candidates, key=lambda p: os.path.getsize(p))
        raise RuntimeError("No downloaded video file was found in temp.")

    def ytdlp_download_audio(self, url: str) -> str:
        tmp = self.temp_dir()
        format_chain = build_audio_format_chain()
        last_error = None
        total_attempts = len(format_chain)
        for attempt, format_selector in enumerate(format_chain, start=1):
            for fn in os.listdir(tmp):
                p = os.path.join(tmp, fn)
                if os.path.isfile(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

            ydl_opts = {
                "format": format_selector,
                "outtmpl": os.path.join(tmp, "%(title)s.%(ext)s"),
                "ffmpeg_location": TOOLS_DIR,
                "continuedl": False,
                "nopart": True,
                "progress_hooks": [self.make_ytdlp_progress_hook("Downloading audio")],
            }
            try:
                self.ui_status(f"Preparing audio source {attempt}/{total_attempts}...")
                info = self.run_yt_dlp(url, extra_opts=ydl_opts, download=True)
                requested = info.get("requested_downloads") or []
                if requested:
                    filepath = requested[0].get("filepath")
                    if filepath and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        return filepath
                ext = info.get("ext") or "media"
                fallback = os.path.join(tmp, f"{info.get('title', 'video')}.{ext}")
                if os.path.exists(fallback) and os.path.getsize(fallback) > 0:
                    return fallback
                candidates = []
                for fn in os.listdir(tmp):
                    p = os.path.join(tmp, fn)
                    if os.path.isfile(p) and os.path.getsize(p) > 0:
                        candidates.append(p)
                if candidates:
                    return max(candidates, key=os.path.getsize)
                raise RuntimeError("No downloaded audio file was found in temp.")
            except RuntimeError as ex:
                last_error = ex
                if is_retryable_ytdlp_error(str(ex)) and attempt < total_attempts:
                    self.ui_status(f"Audio source {attempt}/{total_attempts} failed. Trying another source...")
                    continue
                raise

        if last_error:
            raise last_error
        raise RuntimeError("No downloaded audio file was found in temp.")

    def download_thumbnail(self, url: str) -> str:
        info = self.ytdlp_info(url)
        thumb_url = info.get("thumbnail")
        if not thumb_url:
            raise RuntimeError("No thumbnail URL found for this video.")
        tmp = self.temp_dir()
        out_path = os.path.join(tmp, "_auto_thumb.jpg")
        with urllib.request.urlopen(thumb_url, timeout=20) as response, open(out_path, "wb") as target:
            shutil.copyfileobj(response, target)
        return out_path

    # ---------- Cover preprocess ----------
    def preprocess_cover(self, cover_path: str) -> str:
        tmp = self.temp_dir()
        out_img = os.path.join(tmp, "_cover_spotify.jpg")

        self.ui_status("Processing cover image...")

        ok, err = run_cmd_live(build_cover_preprocess_cmd(cover_path, out_img))
        if not ok:
            self.ui_error("Cover Error", err)
            raise RuntimeError(err)
        return out_img

    def optional_cover_image(self, link: str | None = None, require_auto_thumb: bool = False) -> str | None:
        if self._job_cover and os.path.exists(self._job_cover):
            return self.preprocess_cover(self._job_cover)
        if link and self._job_auto_thumb:
            try:
                self.ui_status("Fetching thumbnail...")
                return self.preprocess_cover(self.download_thumbnail(link))
            except Exception as ex:
                if require_auto_thumb:
                    raise RuntimeError(f"Auto thumbnail could not be used.\n\nTechnical detail:\n{ex}") from ex
                self.ui_status("Auto thumbnail could not be fetched. Using black background.")
                return None
        return None

    # ---------- Convert ----------
    def convert(self):
        if self._busy:
            return
        self.close_format_dropdown()
        link = normalize_media_link(self.link_entry.get())
        fmt_label = self.format_var.get().strip()
        if fmt_label not in FORMAT_MAP:
            fmt_label = self.last_format_label if self.last_format_label in FORMAT_MAP else DEFAULT_FORMAT_LABEL
            self.format_var.set(fmt_label)
        fmt_choice = FORMAT_MAP.get(fmt_label, "mp3")
        mp3_bitrate = self.mp3_var.get()
        video_quality = self.video_quality_var.get().strip()
        input_file = self.input_file
        self._job_cover = self.cover_img
        self._job_auto_thumb = self.auto_thumb_var.get()

        self.cfg["default_format"] = fmt_label
        self.cfg["mp3_bitrate"] = mp3_bitrate
        self.cfg["video_quality"] = video_quality
        try:
            self.persist_config()
        except OSError as ex:
            messagebox.showerror(
                "Config Error",
                "Settings could not be saved. Check folder permissions or disk availability.\n\n"
                f"Technical detail:\n{ex}",
            )
            return

        is_link = is_media_link(link)
        video_outputs = VIDEO_OUTPUT_KEYS
        video_output_map = {
            "mp4_video": ("MP4_VIDEO", ".mp4", "Encoding MP4 (H.264 + AAC)...", True),
            "webm_video": ("WEBM_VIDEO", ".webm", "Encoding WEBM (VP9 + Opus)...", False),
            "mkv_video": ("MKV_VIDEO", ".mkv", "Encoding MKV (H.264 + AAC)...", False),
            "mov_video": ("MOV_VIDEO", ".mov", "Encoding MOV (H.264 + AAC)...", True),
            "avi_video": ("AVI_VIDEO", ".avi", "Encoding AVI (H.264 + AAC)...", False),
        }

        if not is_link and (not self.input_file or not os.path.exists(self.input_file)):
            messagebox.showwarning("Missing input", "Select/drag a file or paste a link.")
            return

        def job():
            try:
                self.ensure_output_dir_ready()
                if is_link:
                    title = self.ytdlp_title(link)

                    if fmt_choice in video_outputs:
                        self.ui_status(f"Downloading video ({video_quality})...")
                        src_video = self.ytdlp_download_best(link, video_quality)
                        src_resolution = probe_video_resolution(src_video)

                        out_folder, out_ext, status_text, needs_movflags = video_output_map[fmt_choice]
                        outdir = self.output_dir_for(out_folder)
                        out_path = unique_path(os.path.join(outdir, f"{title}{out_ext}"))
                        self.ui_status(f"{status_text} Source resolution: {src_resolution}")
                        last_update = 0.0

                        def on_line(s):
                            nonlocal last_update
                            if "time=" in s:
                                now = time.time()
                                if now - last_update > 0.6:
                                    last_update = now
                                    self.ui_status(s)

                        target_height = parse_quality_height(video_quality)
                        source_has_video = has_video_stream(src_video)
                        if not source_has_video:
                            cover_img = self.optional_cover_image(link)
                            cmd = build_audio_to_video_cmd(src_video, cover_img, out_path, fmt_choice, needs_movflags, target_height)
                        elif fmt_choice == "mp4_video":
                            cmd = build_video_to_mp4_compatible_cmd(src_video, out_path, target_height)
                        elif fmt_choice == "webm_video":
                            cmd = build_webm_convert_cmd(src_video, out_path, source_has_video, target_height)
                        else:
                            cmd = build_video_container_cmd(
                                src_video,
                                out_path,
                                source_has_video,
                                needs_movflags,
                                target_height,
                            )
                        ok, err = run_cmd_live(cmd, on_line=on_line)
                        self.cleanup_temp()
                        if ok:
                            self.ui_done(out_path)
                        else:
                            self.ui_error("Error", err)
                        return

                    if fmt_choice == "mp4_cover":
                        self.ui_status("Downloading audio (temp)...")
                        audio_path = self.ytdlp_download_audio(link)

                        scaled_cover = self.optional_cover_image(
                            link,
                            require_auto_thumb=self._job_auto_thumb,
                        )

                        outdir = self.output_dir_for("MP4_COVER")
                        out_path = unique_path(os.path.join(outdir, f"{title}.mp4"))

                        self.ui_status("Creating MP4 (cover + audio)...")
                        last_update = 0.0

                        def on_line(s):
                            nonlocal last_update
                            if "time=" in s:
                                now = time.time()
                                if now - last_update > 0.6:
                                    last_update = now
                                    self.ui_status(s)

                        ok, err = run_cmd_live(
                            build_audio_to_video_cmd(audio_path, scaled_cover, out_path, "mp4_video", True, COVER_MAX_DIM),
                            on_line=on_line,
                        )
                        self.cleanup_temp()
                        if ok:
                            self.ui_done(out_path)
                        else:
                            self.ui_error("Error", err)
                        return

                    out_fmt = fmt_choice
                    self.ui_status("Downloading audio (temp)...")
                    audio_path = self.ytdlp_download_audio(link)

                    outdir = self.output_dir_for(out_fmt)
                    out_path = unique_path(os.path.join(outdir, f"{title}.{out_fmt}"))

                    self.ui_status("Converting audio...")
                    last_update = 0.0

                    def on_line(s):
                        nonlocal last_update
                        if "time=" in s:
                            now = time.time()
                            if now - last_update > 0.6:
                                last_update = now
                                self.ui_status(s)

                    ok, err = run_cmd_live(build_audio_convert_cmd(audio_path, out_path, out_fmt, mp3_bitrate), on_line=on_line)
                    self.cleanup_temp()
                    if ok:
                        self.ui_done(out_path)
                    else:
                        self.ui_error("Error", err)
                    return

                inp = input_file
                base = safe_filename(os.path.splitext(os.path.basename(inp))[0])

                if fmt_choice in video_outputs:
                    out_folder, out_ext, status_text, needs_movflags = video_output_map[fmt_choice]
                    outdir = self.output_dir_for(out_folder)
                    out_path = unique_path(os.path.join(outdir, f"{base}{out_ext}"))

                    self.ui_status(status_text)
                    last_update = 0.0

                    def on_line(s):
                        nonlocal last_update
                        if "time=" in s:
                            now = time.time()
                            if now - last_update > 0.6:
                                last_update = now
                                self.ui_status(s)

                    target_height = parse_quality_height(video_quality)
                    source_has_video = has_video_stream(inp)
                    if not source_has_video:
                        cover_img = self.optional_cover_image()
                        cmd = build_audio_to_video_cmd(inp, cover_img, out_path, fmt_choice, needs_movflags, target_height)
                    elif fmt_choice == "mp4_video":
                        cmd = build_video_to_mp4_compatible_cmd(inp, out_path, target_height)
                    elif fmt_choice == "webm_video":
                        cmd = build_webm_convert_cmd(inp, out_path, source_has_video, target_height)
                    else:
                        cmd = build_video_container_cmd(
                            inp,
                            out_path,
                            source_has_video,
                            needs_movflags,
                            target_height,
                        )
                    ok, err = run_cmd_live(cmd, on_line=on_line)
                    self.cleanup_temp()
                    if ok:
                        self.ui_done(out_path)
                    else:
                        self.ui_error("Error", err)
                    return

                if fmt_choice == "mp4_cover":
                    scaled_cover = self.optional_cover_image()

                    outdir = self.output_dir_for("MP4_COVER")
                    out_path = unique_path(os.path.join(outdir, f"{base}.mp4"))

                    self.ui_status("Creating MP4 (cover + audio)...")
                    last_update = 0.0

                    def on_line(s):
                        nonlocal last_update
                        if "time=" in s:
                            now = time.time()
                            if now - last_update > 0.6:
                                last_update = now
                                self.ui_status(s)

                    ok, err = run_cmd_live(
                        build_audio_to_video_cmd(inp, scaled_cover, out_path, "mp4_video", True, COVER_MAX_DIM),
                        on_line=on_line,
                    )
                    self.cleanup_temp()
                    if ok:
                        self.ui_done(out_path)
                    else:
                        self.ui_error("Error", err)
                    return

                out_fmt = fmt_choice
                outdir = self.output_dir_for(out_fmt)
                out_path = unique_path(os.path.join(outdir, f"{base}.{out_fmt}"))

                self.ui_status("Converting audio...")
                last_update = 0.0

                def on_line(s):
                    nonlocal last_update
                    if "time=" in s:
                        now = time.time()
                        if now - last_update > 0.6:
                            last_update = now
                            self.ui_status(s)

                ok, err = run_cmd_live(build_audio_convert_cmd(inp, out_path, out_fmt, mp3_bitrate), on_line=on_line)
                if ok:
                    self.ui_done(out_path)
                else:
                    self.ui_error("Error", err)

            except Exception as ex:
                self.cleanup_temp()
                self.ui_error("Error", str(ex))

        self.run_background(job)


if __name__ == "__main__":
    app = CleanConverter()
    app.mainloop()







