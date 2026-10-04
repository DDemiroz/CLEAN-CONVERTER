# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from pathlib import Path

datas = [('assets/icon.png', 'assets'), ('assets/icon.ico', 'assets'), ('LICENSE.md', '.'), ('NOTICE.md', '.'), ('THIRD_PARTY_NOTICES.md', '.')]
binaries = [('tools/ffmpeg.exe', 'tools'), ('tools/ffprobe.exe', 'tools'), ('tools/deno.exe', 'tools')]
hiddenimports = []
if not Path('release-metadata/BUILD-INVENTORY.json').is_file():
    raise RuntimeError('Run scripts/prepare_bundle.py before building.')
datas += [('release-metadata', 'release-metadata')]
for package in ['tkinterdnd2', 'customtkinter']:
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += [entry for entry in package_datas if Path(entry[0]).name != '.DS_Store']
    binaries += package_binaries
    hiddenimports += package_imports
tmp_ret = collect_all('yt_dlp_ejs')
datas += [entry for entry in tmp_ret[0] if Path(entry[0]).name != '.DS_Store']
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'tests'],
    noarchive=False,
    optimize=0,
)
a.datas = [entry for entry in a.datas if Path(entry[0]).name != '.DS_Store']
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CleanConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
    version='installer/version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CleanConverter',
)
