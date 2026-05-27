# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # pandas tslibs are routinely missed by static analysis
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.timestamps',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.periods',
        'pandas._libs.tslibs.offsets',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.calendars',
        'pandas._libs.tslibs.tzconversion',
        'pandas._libs.tslibs.fields',
        'pandas._libs.tslibs.parsing',
        'pandas._libs.tslibs.strptime',
        'pandas.io.formats.excel',
        'pandas.io.excel._openpyxl',
        # openpyxl cell writer is missed without explicit listing
        'openpyxl.cell._writer',
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
    name='ICE',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ICE',
)
