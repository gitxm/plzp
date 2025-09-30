#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller 打包配置脚本
用于生成 Windows 和 macOS 可执行文件
"""

import os
import sys
import platform

def create_spec_file():
    """创建 PyInstaller spec 文件"""
    
    system = platform.system()
    
    if system == "Windows":
        separator = ";"
        exe_name = "image-downloader-windows"
    elif system == "Darwin":  # macOS
        separator = ":"
        exe_name = "image-downloader-macos"
    else:  # Linux
        separator = ":"
        exe_name = "image-downloader-linux"
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('app', 'app')],
    hiddenimports=[
        'pandas',
        'openpyxl',
        'requests',
        'urllib3',
        'certifi',
    ],
    hookspath=[],
    hooksconfig={{}},
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
    name='{exe_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    # 写入 spec 文件
    spec_filename = f"{exe_name}.spec"
    with open(spec_filename, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ 已创建 spec 文件: {spec_filename}")
    print(f"\n使用以下命令打包:")
    print(f"pyinstaller {spec_filename}")
    
    return spec_filename


if __name__ == "__main__":
    create_spec_file()

