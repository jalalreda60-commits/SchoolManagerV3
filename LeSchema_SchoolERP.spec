# -*- mode: python ; coding: utf-8 -*-
# LeSchema School ERP - PyInstaller Spec File

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all necessary packages
reportlab_datas, reportlab_binaries, reportlab_hiddenimports = collect_all('reportlab')
sqlalchemy_datas, sqlalchemy_binaries, sqlalchemy_hiddenimports = collect_all('sqlalchemy')
qrcode_datas, qrcode_binaries, qrcode_hiddenimports = collect_all('qrcode')
pil_datas, pil_binaries, pil_hiddenimports = collect_all('PIL')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=reportlab_binaries + sqlalchemy_binaries + qrcode_binaries + pil_binaries,
    datas=[
        ('assets', 'assets'),
        ('database', 'database'),
        ('utils', 'utils'),
    ] + reportlab_datas + sqlalchemy_datas + qrcode_datas + pil_datas,
    hiddenimports=[
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.ext.declarative',
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageTk',
        'qrcode.image.pil',
        'reportlab.graphics.barcode.qr',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
    ] + reportlab_hiddenimports + sqlalchemy_hiddenimports + qrcode_hiddenimports + pil_hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LeSchema_SchoolERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/school_logo.ico',
    version='version_info.txt',
)
