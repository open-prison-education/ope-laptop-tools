# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Add parent directory to path for imports
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

block_cipher = None

a = Analysis(
    ['credential.py'],
    pathex=[current_dir, parent_dir],
    binaries=[],
    datas=[
        (os.path.join(parent_dir, 'common'), 'common'),
        (os.path.join(parent_dir, 'mgmt'), 'mgmt'),
        ('bin', 'bin'),
    ],
    hiddenimports=[
        'win32api',
        'win32security',
        'win32service',
        'win32event',
        'win32evtlog',
        'win32ts',
        'win32gui',
        'win32gui_struct',
        'win32con',
        'pythoncom',
        'pyad',
        'pyad.pyad',
        'wmi',
        'winsys',
        'winsys.accounts',
        'winsys.registry',
        'winsys.security',
        'win32process',
        'mgmt',
        'win32profile',
        'win32netcon',
        'win32net',
        'ntsecuritycon',
        'ctypes',
        'threading',
        'subprocess',
        'traceback',
        'collections',
        'random',
        'time',
        'socket',
        'sys',
        'os',
        'shutil',
        'psutil',
        'logging',
        'logging.handlers',
        'colorama',
        'PIL',
        'PIL.Image',
        'PIL.ImageFont',
        'PIL.ImageDraw',
        'simplejson',
        'pathlib',
        'json',
        'pyaes',
        'win32timezone',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='credential',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(parent_dir, 'common', 'logo_icon.ico'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='credential',
)
