#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地打包脚本
用于在本地环境中使用 PyInstaller 打包可执行文件
"""

import os
import sys
import platform
import subprocess
import shutil

def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        print("✅ PyInstaller 已安装")
        return True
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("\n请先安装 PyInstaller:")
        print("pip install pyinstaller")
        return False


def clean_build_files():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist']
    files_to_remove = ['*.spec']
    
    print("\n🧹 清理旧的构建文件...")
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  删除目录: {dir_name}")
    
    import glob
    for pattern in files_to_remove:
        for file in glob.glob(pattern):
            os.remove(file)
            print(f"  删除文件: {file}")


def build_executable():
    """构建可执行文件"""
    system = platform.system()
    
    if system == "Windows":
        exe_name = "image-downloader-windows"
        separator = ";"
    elif system == "Darwin":  # macOS
        exe_name = "image-downloader-macos"
        separator = ":"
    else:  # Linux
        exe_name = "image-downloader-linux"
        separator = ":"
    
    print(f"\n🚀 开始构建 {system} 版本...")
    print(f"可执行文件名: {exe_name}")
    
    # PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name', exe_name,
        '--add-data', f'app{separator}app',
        '--hidden-import', 'pandas',
        '--hidden-import', 'openpyxl',
        '--hidden-import', 'requests',
        '--hidden-import', 'urllib3',
        '--hidden-import', 'certifi',
        '--console',
        'main.py'
    ]
    
    print(f"\n执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("\n✅ 构建成功！")
        print(f"\n可执行文件位置: dist/{exe_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败:")
        print(e.stderr)
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("📦 本地打包工具")
    print("=" * 60)
    print(f"当前系统: {platform.system()}")
    print(f"Python 版本: {sys.version}")
    print("=" * 60)
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        return
    
    # 询问是否清理旧文件
    clean_choice = input("\n是否清理旧的构建文件？(y/n): ").strip().lower()
    if clean_choice in ['y', 'yes', '是']:
        clean_build_files()
    
    # 确认开始构建
    build_choice = input("\n开始构建可执行文件？(y/n): ").strip().lower()
    if build_choice not in ['y', 'yes', '是']:
        print("❌ 构建已取消")
        return
    
    # 构建
    if build_executable():
        print("\n" + "=" * 60)
        print("✅ 打包完成！")
        print("=" * 60)
        print("\n📁 输出目录: dist/")
        print("\n💡 提示:")
        print("  1. 可执行文件位于 dist/ 目录")
        print("  2. 可以将可执行文件分发给其他用户")
        print("  3. 用户无需安装 Python 即可运行")
    else:
        print("\n" + "=" * 60)
        print("❌ 打包失败，请检查错误信息")
        print("=" * 60)


if __name__ == "__main__":
    main()

