# Third-party components

The original application's license does not apply to dependencies.

| Component | Local candidate | Distribution requirement |
|---|---|---|
| FFmpeg / ffprobe | 9.0.2 essentials, gyan.dev; GPL + version3 enabled | Preserve GPL notices and provide exact corresponding source/build materials, including incorporated libraries. |
| Deno | 2.9.7 | Preserve the upstream license and bundled third-party notices. |
| yt-dlp / yt-dlp-ejs | 2026.8.19 / 0.8.0 | Preserve distribution license files and notices for included dependencies. |
| CustomTkinter / tkinterdnd2 | 6.0.0 / 0.6.3 | Preserve Python-package and bundled Tcl/Tk/TkDnD license files. |
| Python / Tcl/Tk / other packaged libraries | Determined by build environment | Inventory the actual bundle, not only direct requirements. |

The installer includes the collected license texts and generated binary inventory.
The bundled FFmpeg 9.0.2 build identifies the exact FFmpeg revision and build
configuration in its included `BUILD.txt`. The corresponding FFmpeg revision is
available at <https://github.com/FFmpeg/FFmpeg/tree/946fcce07b>; the distributor's
build page records the variant, linked libraries and source reference at
<https://www.gyan.dev/ffmpeg/builds/>. Clean Converter's complete source and build
recipe are published with the matching GitHub tag.

Upstream references: [FFmpeg legal](https://ffmpeg.org/legal.html),
[FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/),
[Deno](https://github.com/denoland/deno), [yt-dlp](https://github.com/yt-dlp/yt-dlp).
