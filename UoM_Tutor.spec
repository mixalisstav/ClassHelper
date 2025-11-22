# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['interface.py'],
    pathex=[],
    binaries=[],
    datas=[('users.csv', '.')],
    hiddenimports=['sqlite3', 'pandas'],
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
    name='UoM_Tutor',
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
    icon=['tutor_icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UoM_Tutor',
)
app = BUNDLE(
    coll,
    name='UoM_Tutor.app',
    icon='tutor_icon.icns',
    bundle_identifier=None,
)
