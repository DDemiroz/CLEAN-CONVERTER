# Publishing Clean Converter 1.0.0

Version 1.0.0 is distributed through this repository's GitHub Releases page.

## Build from source

Use Windows x64, Python 3.14.2 and Inno Setup 6. Install requirements-lock.txt in a
fresh virtual environment. Put verified ffmpeg.exe, ffprobe.exe and deno.exe in
tools/. Record the versions and checksums of these external binaries.

The current candidate uses FFmpeg/ffprobe 9.0.2 essentials and Deno 2.9.7.
Keep the verified FFmpeg distribution LICENSE and README as
release-metadata/licenses/FFmpeg/LICENSE.txt and BUILD.txt, and the exact Deno
release's LICENSE.md under release-metadata/licenses/Deno/. These generated/local
materials are embedded in the packaged application. The public notice identifies
the exact FFmpeg revision, build configuration and upstream build/source locations.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-lock.txt
.\.venv\Scripts\python -m pytest -q tests
.\.venv\Scripts\python scripts/prepare_bundle.py
.\.venv\Scripts\python -m PyInstaller --noconfirm --clean CleanConverter.spec
```

After completing every item in the public-upload checklist, regenerate the final
embedded inventory with `scripts/prepare_bundle.py --publication-ready` before
the final PyInstaller build. The flag records the completed human release gate;
it does not perform or replace the review.

Compile installer/clean_converter.iss using Inno Setup's ISCC.exe after reviewing
the build. Existing dist and installer/Output directories may contain OLD builds;
they do not automatically reflect source edits.

## Before public upload

- Run tests and real conversion/download checks; record any skipped cases.
- Test the packaged application and installation/removal on clean Windows.
- Verify that uninstall preserves user media.
- Uninstall intentionally preserves per-user settings; the elevated installer
  must not delete a guessed user's AppData directory.
- Inventory dependencies and include their license texts and required corresponding
  source/build materials. See THIRD_PARTY_NOTICES.md; a notices table alone is insufficient.
- Scan the source allowlist, images, Git metadata, executable bundle and installer.
  Remove private paths, tokens, cookies, private URLs, credentials and user settings.
- Verify the Git repository root and use the author's verified GitHub noreply email.
- Review the exact staged files and history. Never add a parent user directory.
- Generate SHA-256 checksums for the final installer and release assets.
- Obtain the owner's final approval for the repository and exact upload contents.

Only reviewed source, tests, assets, documentation, license/notice files and build
recipes belong in Git. Installers belong in Releases. Caches, old builds, logs,
test media, private development notes, settings and backups remain excluded.

No certificate purchase is included. The existing build is unsigned; do not claim
code signing or ask users to disable security protections.

## Release maintenance

Keep the verified download link, checksum, language switcher, screenshots, known
limits and third-party attribution consistent in both languages for every release.
