# Third-party components

The original application's license does not apply to dependencies.

| Component | Local candidate | Distribution requirement |
|---|---|---|
| FFmpeg / ffprobe | 9.0.2 essentials, gyan.dev; GPL + version3 enabled | Preserve GPL notices and provide exact corresponding source/build materials, including incorporated libraries. |
| Deno | 2.9.7 | Preserve the upstream license and bundled third-party notices. |
| yt-dlp / yt-dlp-ejs | 2026.8.19 / 0.8.0 | Preserve distribution license files and notices for included dependencies. |
| CustomTkinter / tkinterdnd2 | 6.0.0 / 0.6.3 | Preserve Python-package and bundled Tcl/Tk/TkDnD license files. |
| Python / Tcl/Tk / other packaged libraries | Determined by build environment | Inventory the actual bundle, not only direct requirements. |

**Release gate:** this document is an inventory, not a replacement for license texts
or corresponding source. Do not publish the bundled installer until the exact
binary inventory, license texts and required source materials have been verified.

Upstream references: [FFmpeg legal](https://ffmpeg.org/legal.html),
[FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/),
[Deno](https://github.com/denoland/deno), [yt-dlp](https://github.com/yt-dlp/yt-dlp).
