# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\dev\\ope-laptop-tools\\opeService\\OPEService.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\dev\\ope-laptop-tools\\common', 'common'), ('D:\\dev\\ope-laptop-tools\\mgmt', 'mgmt')],
    hiddenimports=['win32timezone', 'servicemanager', 'simplejson', 'pathlib', 'win32service', 'win32event', 'win32evtlog', 'win32ts', 'win32gui', 'win32gui_struct', 'win32con', 'pythoncom', 'pyad', 'pyad.pyad', 'wmi', 'winsys', 'winsys.accounts', 'winsys.registry', 'winsys.security', 'win32api', 'win32security', 'win32process', 'win32profile', 'win32netcon', 'win32net', 'ntsecuritycon', 'ctypes', 'threading', 'subprocess', 'traceback', 'collections', 'random', 'time', 'socket', 'sys', 'os', 'shutil', 'psutil', 'logging', 'logging.handlers', 'colorama', 'PIL', 'PIL.Image', 'PIL.ImageFont', 'PIL.ImageDraw'],
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
    name='OPEService',
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
    icon=['D:\\dev\\ope-laptop-tools\\common\\logo_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='OPEService',
)
