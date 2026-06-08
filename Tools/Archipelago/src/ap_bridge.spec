# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ap_bridge.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'websockets',
        'websockets.legacy',
        'websockets.legacy.client',
        'websockets.exceptions',
        'websockets.uri',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ap_bridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ap_bridge',
)
# 1.9.13 — upx=False (was True). UPX-compressed PyInstaller binaries are
# one of THE most common antivirus false-positive triggers: AV heuristic
# engines specifically watch for the UPX packer signature/entropy because
# malware authors use it to obfuscate payloads. Disabling it is the
# #1 community-recommended fix for "my frozen Python exe gets flagged as
# a virus" reports. (UPX isn't even installed on this build machine today,
# so this was already a no-op — but leaving `upx=True` in the spec meant
# any future machine that DOES have upx.exe on PATH would silently start
# compressing ap_bridge.exe and reintroducing the exact risk Marco hit.)
