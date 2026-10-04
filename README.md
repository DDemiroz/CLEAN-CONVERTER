# 🎬 CLEAN CONVERTER

[Türkçe](README_TR.md) · [demirdemiroz.com](https://demirdemiroz.com) · [GitHub](https://github.com/DDemiroz)

**Convert audio and video locally, extract sound, create cover videos, or download from supported links—all from one Windows app.** Local conversion works offline.

> ## 📦 Want to use the app?
>
> Download and run **[`CleanConverterSetup.exe`](https://github.com/DDemiroz/CLEAN-CONVERTER/releases/download/v1.0.0/CleanConverterSetup.exe)**. Python, FFmpeg and the other required tools are included. **Code → Download ZIP contains source code; it is not the installer.**

**1.0.0 — current release.** Windows x64 · unsigned installer · GPL-3.0-only.

![Clean Converter](docs/screenshots/home.png)

## 🧭 Start here

[Quick start](#quick-start) · [Installation](#installation) · [Controls](#controls) · [Inputs](#inputs) · [Local workflows](#local) · [Links](#links) · [Output formats](#formats) · [Settings and files](#settings) · [FAQ](#faq) · [Errors](#errors) · [Report a bug](#report) · [Verification](#verification) · [Developers](#developers) · [License](#license)

<a id="quick-start"></a>

## ⚡ Quick start

For a first local conversion: **Choose File → Format → Output folder → Convert → Done**. Leave Link empty. Start with a short, non-private sample; for video-to-audio, the source must contain sound. Detailed instructions follow below.

<a id="installation"></a>

## 📦 Installation: one package for users

Download **CleanConverterSetup.exe** from GitHub **Releases** and run it. **Code → Download ZIP** contains source code, not the installer.

The installer bundles the Python runtime, **FFmpeg, ffprobe, Deno and yt-dlp**. Users do not need separate downloads, terminal commands or PATH configuration. Excluding large tool binaries from source history does not exclude them from the installer.

1. Complete setup; optionally create a desktop shortcut.
2. Open the app and choose an output folder on first launch.
3. Select a file and output format, then click **Convert**.
4. Wait for **Done** before using the output.

The package is unsigned. Verify that it comes from this repository's Releases page and check the published SHA-256 file.

The current development/build target is **Windows x64**; a minimum supported Windows version has not been verified. macOS/Linux installers are not provided. Internet is needed for downloads, not local conversion. Keep free space for the source download, temporary work and final output; required space varies by media.

Canceling the first output-folder selection closes the app. Later, use **Output folder…** while idle to change it. Use Windows Installed apps to remove an installed copy; the uninstall script preserves per-user settings and does not target media saved outside the installation directory. Keep media outside the installation folder. Clean-Windows uninstall verification remains pending.

<a id="controls"></a>

## Meet the controls

![Numbered controls: input, output settings and Convert](docs/screenshots/controls.png)

Numbers are documentation annotations, not part of the actual application.

The screenshots predate the **Questions or report any bugs → demirdemiroz.com** footer. The link is described below; existing images are retained.

| No. | Control | What it does |
|---|---|---|
| 1 | **Choose File** | Select one local audio/video file. Clears the link field. |
| 2 | **Drop a file here** | Drag a file here instead of browsing. This is not a batch queue: use one file. |
| 3 | **Link** | Paste a supported online media URL. Leave empty for local conversion; a valid URL takes precedence over a local file. |
| 4 | **Select Cover Image** | Choose JPG/JPEG/PNG artwork. The filename appears beside the button. Used for audio-to-video and cover exports, not to replace the picture in an ordinary video conversion. |
| 5 | **Use link thumbnail automatically…** | Try the link's thumbnail when no manual cover is selected. Does not automatically extract embedded album art from local audio. A manual cover takes precedence. |
| 6 | **Output folder…** | Change where converted files are saved. Does not relocate the original file. |
| 7 | **Source** summary | Shows whether the selected source is audio, video or a link. Check before starting. |
| 8 | **Output Settings → Format** | Select the produced file format: video formats, MP4 Audio + Cover, or audio formats. This performs conversion rather than simply renaming an extension. |
| 9 | **MP3 Bitrate** | Applies only to MP3 output: 192k, 256k or 320k. Does not change other formats. |
| 10 | **Video Quality** | Maximum height for ordinary video output. Disabled for audio output and the MP4 Audio + Cover preset. |
| 11 | **Convert** | Starts processing the selected source with the selected settings. Disabled while running. Follow the status line at bottom left. |

**Status line:** Ready means idle; downloads may show percentage, speed and ETA; conversions show processing information; Done means finished. Percentages may restart for separate streams and are not a single overall progress bar. Failures open an error dialog. **Website/GitHub** open the author's pages in your browser; the bottom-right credit identifies the author.

<a id="inputs"></a>

## What can I convert?

Common inputs listed in the file picker:

- **Video:** MP4, WebM, MKV, MOV, AVI, M4V.
- **Audio:** MP3, WAV, FLAC, OGG, M4A, AAC, Opus, WMA.
- **Cover:** JPG, JPEG, PNG.

“All” allows selecting other files but does not guarantee support. Actual support depends on the contained codecs and bundled FFmpeg. **This is not a PDF/Word/Excel converter, a general image converter or an archive extractor.** Not every possible input/output combination is guaranteed.

| Input | Output | Example |
|---|---|---|
| Video | Another video format | MOV → MP4, MP4 → WebM, MKV → MP4 |
| Video with audio | Audio | MP4 → MP3, MOV → WAV, MKV → FLAC |
| Audio | Another audio format | WAV → MP3, FLAC → M4A, WMA → WAV |
| Audio + cover | Video | WAV + PNG → MP4 |
| Audio without cover | Black-background video | MP3 → MP4 or WebM |
| Video + cover | Cover with the video's audio | MP4 → MP4 Audio + Cover |
| Supported link | Video, audio or cover export | URL → MP4, MP3 or MP4 Audio + Cover |

<a id="local"></a>

## Local files: step by step

### 1. Convert video to another video format

1. Select a video with **Choose File (1)** or drag it into **(2)**.
2. Choose a target video **Format (8)**, for example **MP4 Video (H.264 + AAC)** for a MOV source.
3. Select **Video Quality (10)**: a 1080p ceiling, or Best for no source-height cap.
4. Set **Output folder (6)** and click **Convert (11)**.
5. After Done, open the relevant video subfolder. Your original file remains unchanged.

Compatible H.264/AAC sources within the height limit may be copied into MP4 without re-encoding. Other conversions can take longer. Best does not mean every conversion is lossless.

### 2. Extract only the audio from video

1. Select a video containing an audio stream.
2. Choose **MP3**, **WAV**, **FLAC**, **OGG**, **M4A** or **AAC**.
3. For MP3, choose a bitrate. Cover and Video Quality do not affect audio-only output.
4. Click Convert. An MP4-to-MP3 export includes sound, not video.

A silent video with no audio stream cannot produce audio. Speech transcription and vocal/music separation are not features.

### 3. Convert audio formats

1. Select WAV, MP3, FLAC, M4A or another supported audio source.
2. Select the target format, such as **FLAC → M4A** or **WAV → MP3**.
3. For MP3, choose 192k/256k/320k, then Convert.
4. Find the result in the audio-format subfolder.

Converting MP3 to FLAC/WAV cannot restore previously discarded detail and may increase file size. A higher bitrate cannot repair a low-quality source.

### 4. Turn audio into a cover video

![Audio and cover example](docs/screenshots/cover.png)

1. Select your audio file.
2. Choose JPG/PNG artwork using **Select Cover Image (4)**.
3. Select **MP4 Audio + Cover**, then Convert.
4. The resulting MP4 displays the cover while the audio plays.

The preset center-crops artwork to a square and scales it to 1080×1080; small covers may be enlarged. Video Quality is disabled for this preset. You can instead select ordinary **MP4 Video / WebM / MKV / MOV / AVI** to create a video from audio with the chosen quality ceiling. Using a video source with **MP4 Audio + Cover** replaces its picture with the cover and uses its audio.

### 5. Turn audio into a video without artwork

Select audio and an ordinary video format without choosing a cover. Choose Video Quality for the black canvas size and click Convert. Output contains a 16:9 black picture and your audio. If a cover was previously selected, restart the app to begin without one; there is currently no separate “remove cover” button.

### 6. Replace a video's picture with a cover

1. Choose a video that contains audio.
2. Select a JPG/PNG cover.
3. Select **MP4 Audio + Cover**, not ordinary MP4 Video.
4. Click Convert. The output uses the source audio with square artwork; the original video remains unchanged.

Choosing a cover does not replace an ordinary video export's picture. Local embedded album artwork is not automatically extracted.

<a id="links"></a>

## Download and convert a supported link

![Supported link example](docs/screenshots/link.png)

1. Paste the media URL into **Link (3)**.
2. For video, choose a video format and quality. For audio only, choose an audio format.
3. For a cover export, choose **MP4 Audio + Cover** and supply artwork or leave **(5)** enabled.
4. Click Convert and wait for downloading and any required conversion to finish.
5. The saved file is a normal local file and can be played offline.

Support depends on the service and yt-dlp version, not a promise of every website. DRM, private/restricted content and some login-required links may not work. Only download content you are entitled to save. Trying another download source means a format/stream fallback, not a different video.

<a id="formats"></a>

## Every output format

A **container** (such as MP4/MKV) holds streams; a **codec** (such as H.264/AAC) encodes their contents. Changing a filename extension does not convert either. The picker lists common inputs, not every codec a container could contain.

| Selection | File and intended use |
|---|---|
| **MP4 Video (H.264 + AAC)** | .mp4; H.264 video and AAC audio when present. A starting choice for general playback. |
| **WEBM Video (VP9 + Opus)** | .webm; VP9 video and Opus audio. Web-oriented output; encoding may take longer. |
| **MKV Video (H.264 + AAC)** | .mkv; H.264/AAC in Matroska. Not an archival mode preserving every subtitle or extra audio track. |
| **MOV Video (H.264 + AAC)** | .mov; H.264/AAC in MOV. Not ProRes or a lossless editing export. |
| **AVI Video (H.264 + AAC)** | .avi; H.264/AAC. Older devices may not support this codec/container combination. |
| **MP4 Audio + Cover** | .mp4; audio video with square artwork, or black picture without artwork. Does not embed album art in an MP3. |
| **MP3** | .mp3; lossy audio at the selected 192/256/320 kbps. |
| **WAV** | .wav; 44.1 kHz audio output. Usually larger; cannot restore missing source quality. |
| **FLAC** | .flac; lossless audio encoding. Does not recover information already lost in the source. |
| **OGG** | .ogg; Vorbis audio with the app's fixed quality setting. Unaffected by MP3 Bitrate. |
| **M4A** | .m4a; AAC audio at 192 kbps. |
| **AAC** | .aac; AAC audio at 192 kbps. Different packaging/extension from M4A. |

<a id="settings"></a>

## Quality, files and settings

### Source priority and storage

A valid Link takes priority over a selected local file. Choosing/dropping a local file clears Link. A manually selected, existing cover takes priority over the link thumbnail; disabling auto-thumbnail does not remove that manual cover. Source, cover, format and quality are captured when a job starts.

With the default format organization, output subfolders are **MP4_VIDEO, WEBM_VIDEO, MKV_VIDEO, MOV_VIDEO, AVI_VIDEO, MP4_COVER, MP3, WAV, FLAC, OGG, M4A, AAC**. For example, sample.mp4 becomes sample (2).mp4 if the first name exists. File names are sanitized for Windows; no fixed maximum path length is promised.

Temporary downloads/covers use an app-owned, isolated folder under the selected output location. Conversion works on a temporary file before publishing the result and reserves the final name during processing. Normal cleanup targets owned work files; crashes or locked files may leave leftovers. Do not treat a visible reserved file as completed before **Done**. Originals are not intentionally overwritten.

Settings are stored at the generic Windows location `%APPDATA%\Clean Converter\config.json` (with a home-folder fallback when APPDATA is unavailable). This is not a user-specific example path. Format, bitrate and output folder persist; video quality resets to 1080p on launch even though a job saves its selection. Input/cover selections are not restored. Folder organization defaults on and has no UI toggle. Invalid settings can fall back to defaults; do not edit settings while the app is running.

- **Best:** no height cap for ordinary source video; re-encoding may still be necessary.
- **2160p (4K), 1440p (2K), 1080p, 720p, 480p, 360p:** maximum video height. Aspect ratio is preserved; not every output is 16:9. Selecting 1080p for a 720p source does not create more detail.
- **MP3 Bitrate:** 192k generally makes smaller files, 320k larger ones, with 256k between them. Source quality remains the limit.
- Files are grouped below your output folder into MP4_VIDEO, WEBM_VIDEO, MP4_COVER, MP3 and similar format folders. Existing names receive numeric alternatives rather than being overwritten.
- Settings are captured at job start. Changing format/quality later does not alter the active job.
- Format, MP3 bitrate and output folder are saved. A new session starts at 1080p; select your input and cover again.
- One operation runs at a time. No batch queue, trimming, joining, subtitle editing or in-app cancellation. Normal closing is blocked until processing finishes.
- Processing time depends on duration, codecs, quality and computer speed. For failures, inspect error details; missing audio, damaged files or a full/unavailable output disk can be causes.
- Local conversion works offline. Downloads and link thumbnails require internet.
- No added analytics/account system. Settings live in the user's application-data folder. Remove personal paths, private URLs and account details before reporting errors.

<a id="faq"></a>

## Frequently asked questions

**Does 1080p guarantee 1920×1080?** No. It is a maximum height for ordinary video. A smaller source stays smaller and portrait/non-16:9 sources have different widths. Link selection also depends on streams the service makes available. Verify the resulting file's properties rather than inferring resolution from the menu.

**Is Best lossless? Does 320k improve a poor recording?** No. Best removes the normal video height cap, not encoding losses. Higher MP3 bitrate preserves more of what the source supplies; it cannot reconstruct missing detail. Repeated lossy conversions may reduce quality.

**Why is the file larger or the conversion slow?** Duration, codec, resolution and encoding settings all matter. WAV or converting already-compressed media can increase size. Video/VP9 encoding can take longer than audio conversion or compatible MP4 stream copying. There is no guaranteed completion time or hardware-acceleration control.

**Can I watch offline?** Yes, a successfully saved local file can be opened with a compatible player without the website. This is different from a streaming service's own offline feature. Local conversion needs no internet; links and online thumbnails do.

**Why is my cover cropped or the video black?** Cover preprocessing center-crops to a square and scales to 1080×1080 before export. Use square artwork with important content away from edges. Audio without artwork produces black video. For ordinary link-to-video fallback, a failed optional thumbnail can also use black. Required auto-thumbnail failure in MP4 Audio + Cover stops the job instead; select your own image or disable auto-thumbnail.

**Why are some settings disabled?** MP3 Bitrate only applies to MP3. Video Quality does not apply to audio-only output or the fixed cover preset. The format menu groups formats by the detected source. Convert is disabled during a job; selecting another input, cover or output folder is blocked until it finishes.

**Can I cancel, queue files or close while processing?** No in-app cancel or batch queue exists. Normal closing asks you to wait. Forced termination/power loss is not a supported cancellation method and can leave temporary or reserved files. Do not remove files while another instance is working.

**Does it preserve every stream and tag?** No guarantee is made for subtitles, chapters, HDR, metadata, multiple audio tracks or every codec. There are no editing controls for these. Compare a short output with your requirements before converting a collection. DRM removal, login/cookie import, transcription, image-format conversion and document conversion are not features.

<a id="errors"></a>

## Error and warning guide

Use the message text, not just the window title. The application interface and error messages are in English; this guide explains the recognizable originals below. Paths, URLs and technical details vary and are intentionally omitted from examples.

### Startup, files and conversion

| Message or identifying text | Short meaning | Possible cause | What to try |
|---|---|---|---|
| Missing tools / FFmpeg not found | Required media tools are missing; startup stops. | Missing ffmpeg.exe or ffprobe.exe, incomplete package. | Reinstall a verified complete package; source users check tools/. Do not disable security software. |
| Config Warning / Output folder was selected, but settings could not be saved yet | Folder selected, but settings not persisted. | Settings directory permissions or disk problem. | Check available space and access to the application-data folder; settings may not survive restart. |
| Config Error / Settings could not be saved | Processing did not start because saving settings failed. | Settings path unavailable or not writable. | Resolve disk/access issue and retry; changing output folder alone may not fix the settings directory. |
| Output folder is missing | No output location is configured. | Missing/invalid setting. | Choose Output folder… while idle. |
| Output folder is not writable | App cannot write to the selected location. | Permissions, disconnected drive or full disk. | Choose an accessible folder with space. |
| Output folder (dialog title) | Changing the folder failed. | Folder creation, write check or settings save failed. | Read the detail; the previous output-folder setting is restored. |
| Missing input / Select/drag a file or paste a link | No usable input selected. | Empty input, missing local file or unrecognized link. | Select an existing media file or supported URL. |
| Conversion running / Please wait for the current operation to finish before closing | Closing is blocked during processing. | A job is active; this is informational. | Wait for completion; there is no in-app cancellation. |
| Error / Failed. Check the error details. | The current operation failed. | Generic wrapper around the specific error. | Read the technical detail and use the matching entry below. |
| Conversion failed / Postprocessing: Conversion failed | Conversion or post-download processing failed. | Codec/input/output/tool issue; this last line alone does not identify which. | Read earlier detail lines, try a short known-good local file and check disk space. Report the sanitized detail if reproducible. |
| Conversion produced an empty file | Tool exited without usable output. | Invalid source or processing issue. | Verify source playback; try another supported format and report persistent failure. |
| No downloaded video file was found in temp. | Expected downloaded video was not located. | Incomplete download or unexpected output from the downloader. | Retry once after checking access and disk space; report if repeatable. |
| No downloaded audio file was found in temp. | Expected downloaded audio was not located. | Audio download/postprocessing did not produce the expected file. | Check preceding detail; retry a supported source and report recurrence. |
| Report a bug / Open … in your browser to report the issue. | The browser could not be opened automatically. | No browser association or browser-launch failure. | Open https://demirdemiroz.com/iletisim/ manually. Nothing was submitted automatically. |

### Supported-link downloads

| Message or identifying text | Short meaning | Possible cause | What to try |
|---|---|---|---|
| YouTube requested additional bot verification / confirm you're not a bot | Extra verification required. | Service anti-automation check. | Wait and retry later; check normal browser availability. The app has no verification/login workflow. |
| This video is private / private video | Private content cannot be fetched. | Access is restricted. | Use content you are authorized to save through a supported access route. |
| This video requires sign-in / login required / sign in | Login or another access condition is required. | Account, age or regional condition; wording alone is not proof of the cause. | Check source availability; no in-app account or cookie import is provided. |
| The video is unavailable / video unavailable | Source is not available. | Removed, hidden, region-limited or temporarily unavailable media. | Verify the original URL in a browser; use another accessible authorized source if needed. |
| This link does not appear to be supported / Unsupported URL | Downloader cannot handle this URL. | Unsupported site or page type. | Use a supported direct media-page URL; not every website is supported. |
| No format compatible with the selected quality was found / Requested format is not available / No video formats found | No usable stream matched. | Available streams, selected height or extraction problem. | Try another quality, including Best if a larger file is acceptable; report if a normally available format fails. |
| The server denied access (403) / HTTP Error 403 / Forbidden | Server refused the media request. | Service restrictions, expired stream URL, client/extractor issue or other access problem. | Retry later and check for a verified updated app release. This does not prove the app is fault-free. |
| Too many requests were detected (429) / Too Many Requests | Request rate was limited. | Too many requests from the connection. | Stop repeated attempts and wait before retrying. |
| The video could not be downloaded / Unknown yt-dlp error | Download failed without a more specific mapped explanation. | Network, extraction or service error. | Read technical details; check source access and network, then report a repeatable failure. |

### Covers and thumbnails

| Message or identifying text | Short meaning | Possible cause | What to try |
|---|---|---|---|
| Cover Error | Cover preprocessing failed. | Unreadable/corrupt artwork or FFmpeg failure. | Try a valid JPG/PNG that opens normally; inspect details. This may also be followed by a general Error dialog. |
| No thumbnail URL found for this video. | Source did not provide a usable thumbnail address. | Missing thumbnail metadata. | Choose a manual cover, or disable auto-thumbnail if black output is acceptable. |
| Auto thumbnail could not be used. | Required automatic cover could not be prepared. | Thumbnail download or image processing failed. | Select a manual cover or disable auto-thumbnail, then retry. |

### Status messages that are not necessarily errors

| Status | Meaning and action |
|---|---|
| Ready; Input file; Link detected; Cover selected; Output folder updated | Idle or selection confirmed. Review source/settings and start when ready. |
| Auto thumbnail enabled / disabled | Preference changed. A manual cover still takes priority. |
| Preparing download source / Preparing audio source | A stream alternative is being prepared for the same URL. |
| Download source … failed. Trying another source… / Audio source … failed. Trying another source… | One alternative failed; automatic attempts continue. Wait for the final result. |
| All download sources failed. Showing error… | Alternatives were exhausted; consult the following error dialog. |
| Downloading video / Downloading audio (temp); percentage, speed and ETA | Downloading, not necessarily the final stage. Separate streams/retries can restart the percentage. |
| … finished. Preparing file… | One download phase finished; merging/conversion may remain. |
| Fetching thumbnail / Processing cover image | Preparing the cover, not final media output. |
| Auto thumbnail could not be fetched. Using black background. | Optional cover failed; this route continues with black video. |
| Encoding MP4/WEBM/MKV/MOV/AVI; Creating MP4 (cover + audio); Converting audio; time=… | FFmpeg is processing. Source resolution describes the input, not proof of final resolution. |
| Done: … | Job completed; find the result in the output folder. |
| Need help? … demirdemiroz.com | Help footer appended to worker errors, not a separate failure. |

### Variable technical details

FFmpeg, yt-dlp and Windows can produce many messages beyond the fixed application text above. These are **illustrative families, not an exhaustive list or a diagnosis**:

| Technical text example | Short meaning / possible cause | Next step |
|---|---|---|
| Permission denied / Access is denied | File/folder cannot be accessed; permissions or a file lock may be involved. | Close programs holding the file; select an accessible output folder. |
| No space left on device / disk full | Not enough room for temporary/final media. | Free space or select another drive. |
| No such file or directory / cannot find the file | Source/tool/folder moved, disappeared or is unavailable. | Reselect the source and check the path/drive. |
| Invalid data found / moov atom not found | Media is incomplete, corrupt or not the expected format. | Test source playback and obtain a valid authorized copy; renaming the extension is not a repair. |
| matches no streams / does not contain any stream | Required audio/video stream was not found. | Confirm the source contains the stream required by the chosen export. |
| Unknown encoder / codec or muxer errors | Requested encoding/container is unavailable or incompatible. | Try another output format; verify the complete supported tool package. |
| timed out / connection reset / name resolution | Network operation failed. | Check connectivity and service availability; retry later. |
| File exists | Destination was already reserved, possibly by another instance. | Retry after the other job finishes; existing files are not overwritten. |

Never disable protection or share credentials/cookies to resolve an error. Before reporting, remove personal paths, private URLs, account data and unrelated screen content. An error code by itself does not establish whether the cause is the app, source, service or environment.

<a id="report"></a>

## Report a bug

Click **demirdemiroz.com** beside **Questions or report any bugs →** at the bottom of the app to open the [contact page](https://demirdemiroz.com/iletisim/). Processing errors also point to this link. The app does not automatically send error logs, files, paths or URLs. Include the app version, selected format and steps to reproduce; remove personal information from screenshots and error details. If the browser cannot open, the app shows the address to open manually.

Copy this template into your message; do not include private source links or original media unless appropriate and specifically needed:

```text
App version:
Windows version:
Running from source or installed EXE:
Source: local file / supported link (service name only)
Input media type:
Output format / video quality / MP3 bitrate:
Manual cover or automatic thumbnail:
Steps to reproduce:
Expected result:
Actual result:
Sanitized error summary and relevant technical lines:
Optional screenshot (personal details removed):
```

The website opens only when you click the button; an error does not automatically open your browser. Online source services still receive download requests, and visiting the website uses your browser normally. This is not an anonymous-reporting guarantee.

<a id="verification"></a>

## Verification and release readiness

**Recorded source check — 2026-10-04: 76 tests passed.** Includes real footer alignment checks at 740×540 and 1080×860. This is a dated test result, not a promise of zero defects.

| Area | Evidence / remaining work |
|---|---|
| Source tests | Configuration types, filename handling, isolated temporary work, failed-output cleanup, existing-output protection, height-limited fallbacks, busy closing, folder rollback and bug-report browser/fallback behavior are covered. |
| Real FFmpeg checks | Short generated audio/video/cover samples exercise the six audio formats, five ordinary video containers, black-background exports and cover mapping/resolution. This is not every codec/input combination. |
| Live download checks | Two previously failing examples were previously downloaded end to end and their MP4 outputs checked as 1920×1080 H.264/AAC. Not rerun for this documentation change; service behavior can change. Private/test URLs are not published here. |
| Still pending | Clean-Windows installation/first run/removal, full display/DPI matrix including 150%, full installed-package checks and complete privacy/licensing verification. The rebuilt EXE starts and its final footer was visually checked; bundled tool hashes and a local-home-path scan passed. |

The EXE and installer were rebuilt from the current source for the 1.0.0 release. Known verification limits remain documented above and in the [publishing guide](PUBLISHING_GUIDE.md).

<a id="developers"></a>

## Developers: run from source

**Regular users do not need these steps.** The installer includes the tools.

Use Windows and Python 3.14. Create a virtual environment, install `requirements-dev.txt`, and place verified FFmpeg/ffprobe/Deno binaries in `tools/`. Run `python app.py`; test with `python -m pytest -q tests`. Media integration tests require FFmpeg.

From the project root in PowerShell (no activation-script change required):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python app.py
.\.venv\Scripts\python -m pytest -q tests
```

The source checkout does not include tool binaries in Git history. Supply verified `tools/ffmpeg.exe`, `tools/ffprobe.exe` and `tools/deno.exe` before launching. Build steps and distribution obligations are in the linked guide; existing EXEs do not automatically incorporate source edits.

[Build and publishing guide](PUBLISHING_GUIDE.md) · [Third-party components](THIRD_PARTY_NOTICES.md)

<a id="license"></a>

## Open source and author

Made by **Demir Demiröz** — [demirdemiroz.com](https://demirdemiroz.com).

**Open source under GPL-3.0-only.** Use, modification and redistribution are permitted, including commercially. Distributed covered derivatives must comply with the same license, required notices and corresponding-source obligations. See [LICENSE.md](LICENSE.md) for the full terms. No warranty is provided. Third-party components retain their own licenses; see [NOTICE](NOTICE.md).
