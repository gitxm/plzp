#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装和设置脚本
用于初始化项目环境和安装依赖
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ 需要Python 3.7或更高版本")
        print(f"当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True


def create_virtual_environment():
    """创建虚拟环境"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ 虚拟环境已存在")
        return True
    
    try:
        print("📦 创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ 虚拟环境创建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 虚拟环境创建失败: {e}")
        return False


def install_dependencies():
    """安装依赖包"""
    try:
        print("📦 安装依赖包...")
        
        # 确定pip路径
        if os.name == 'nt':  # Windows
            pip_path = Path("venv/Scripts/pip")
        else:  # Unix/Linux/Mac
            pip_path = Path("venv/bin/pip")
        
        # 升级pip
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        # 安装依赖
        subprocess.run([
            str(pip_path), "install", 
            "--trusted-host", "pypi.org",
            "--trusted-host", "pypi.python.org", 
            "--trusted-host", "files.pythonhosted.org",
            "-r", "requirements.txt"
        ], check=True)
        
        print("✅ 依赖包安装成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False


def create_folder_structure():
    """创建项目文件夹结构"""
    folders = [
        "data",
        "output", 
        "logs"
    ]
    
    print("📁 创建项目文件夹结构...")
    
    for folder in folders:
        folder_path = Path(folder)
        folder_path.mkdir(exist_ok=True)
        print(f"  创建文件夹: {folder}")
    
    print("✅ 文件夹结构创建完成")


def create_sample_files():
    """创建示例文件"""
    print("📄 创建示例配置文件...")
    
    # 创建.gitignore文件
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Output
output/
*.xlsx
*.csv
!数据样例.xlsx

# OS
.DS_Store
Thumbs.db
"""
    
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content.strip())
    
    print("✅ 示例文件创建完成")


def print_usage_instructions():
    """打印使用说明"""
    print("\n" + "=" * 60)
    print("🎉 安装完成！")
    print("=" * 60)
    
    print("\n📋 使用说明:")
    print("1. 激活虚拟环境:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/Mac
        print("   source venv/bin/activate")
    
    print("\n2. 运行工具:")
    print("   # 交互式模式")
    print("   python run_enhanced_processor.py")
    print()
    print("   # 处理单个文件")
    print("   python run_enhanced_processor.py --file 数据样例.xlsx")
    print()
    print("   # 批量处理文件夹")
    print("   python run_enhanced_processor.py --folder ./data --output ./output")
    print()
    print("   # 快速批量处理")
    print("   python batch_processor.py")
    print()
    print("   # 查看使用示例")
    print("   python usage_examples.py")
    
    print("\n📁 文件夹说明:")
    print("   data/    - 放置要处理的Excel/CSV文件")
    print("   output/  - 处理结果输出文件夹")
    print("   logs/    - 日志文件存储文件夹")
    
    print("\n📚 支持的文件格式:")
    print("   - Excel文件: .xlsx, .xls")
    print("   - CSV文件: .csv")
    
    print("\n🔧 配置文件:")
    print("   config.py - 修改此文件来自定义处理参数")
    
    print("\n📖 更多帮助:")
    print("   python run_enhanced_processor.py --help")


def main():
    """主安装函数"""
    print("=" * 60)
    print("增强版数据处理和图片下载工具 - 安装程序")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    # 创建虚拟环境
    if not create_virtual_environment():
        return False
    
    # 安装依赖
    if not install_dependencies():
        return False
    
    # 创建文件夹结构
    create_folder_structure()
    
    # 创建示例文件
    create_sample_files()
    
    # 打印使用说明
    print_usage_instructions()
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 安装过程中出现错误")
        sys.exit(1)
    else:
        print("\n✅ 安装成功完成！")
