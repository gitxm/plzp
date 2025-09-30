#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 提交准备脚本
检查项目文件并准备提交到 GitHub
"""

import os
import subprocess
from pathlib import Path


def check_git_installed():
    """检查 Git 是否已安装"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        print(f"✅ Git 已安装: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Git 未安装，请先安装 Git")
        return False


def check_git_repo():
    """检查是否是 Git 仓库"""
    if os.path.exists('.git'):
        print("✅ 当前目录是 Git 仓库")
        return True
    else:
        print("⚠️  当前目录不是 Git 仓库")
        return False


def init_git_repo():
    """初始化 Git 仓库"""
    try:
        subprocess.run(['git', 'init'], check=True)
        print("✅ Git 仓库初始化成功")
        return True
    except subprocess.CalledProcessError:
        print("❌ Git 仓库初始化失败")
        return False


def check_required_files():
    """检查必需的文件是否存在"""
    required_files = {
        'main.py': 'Python 主程序',
        'requirements.txt': '依赖列表',
        '.gitignore': 'Git 忽略文件',
        'README.md': '项目说明',
        '.github/workflows/build.yml': 'GitHub Actions 工作流'
    }
    
    print("\n📋 检查必需文件:")
    all_exist = True
    
    for file, description in required_files.items():
        if os.path.exists(file):
            print(f"  ✅ {file} - {description}")
        else:
            print(f"  ❌ {file} - {description} (缺失)")
            all_exist = False
    
    return all_exist


def check_python_files():
    """检查 Python 源文件"""
    py_files = list(Path('.').rglob('*.py'))
    
    # 排除虚拟环境和构建目录
    py_files = [f for f in py_files if 'venv' not in str(f) and 'build' not in str(f) and 'dist' not in str(f)]
    
    print(f"\n📄 找到 {len(py_files)} 个 Python 文件:")
    for f in py_files[:10]:  # 只显示前10个
        print(f"  - {f}")
    
    if len(py_files) > 10:
        print(f"  ... 还有 {len(py_files) - 10} 个文件")
    
    return len(py_files) > 0


def show_git_status():
    """显示 Git 状态"""
    try:
        result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
        if result.stdout.strip():
            print("\n📊 Git 状态:")
            print(result.stdout)
        else:
            print("\n✅ 工作目录干净，没有未提交的更改")
        return True
    except subprocess.CalledProcessError:
        print("❌ 无法获取 Git 状态")
        return False


def suggest_git_commands():
    """建议 Git 命令"""
    print("\n💡 建议的 Git 操作步骤:")
    print("\n1. 添加所有文件到暂存区:")
    print("   git add .")
    
    print("\n2. 提交更改:")
    print("   git commit -m \"Initial commit: 图片下载工具\"")
    
    print("\n3. 添加远程仓库（如果还没有）:")
    print("   git remote add origin https://github.com/你的用户名/你的仓库名.git")
    
    print("\n4. 推送到 GitHub:")
    print("   git push -u origin main")
    
    print("\n5. 创建 Release Tag（触发自动构建）:")
    print("   git tag v1.0.0")
    print("   git push origin v1.0.0")


def check_gitignore():
    """检查 .gitignore 文件"""
    if not os.path.exists('.gitignore'):
        print("\n⚠️  .gitignore 文件不存在")
        return False
    
    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()
    
    important_patterns = ['venv/', '*.log', 'output/', '__pycache__/']
    missing_patterns = []
    
    for pattern in important_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"\n⚠️  .gitignore 可能缺少以下模式: {', '.join(missing_patterns)}")
        return False
    else:
        print("\n✅ .gitignore 文件配置正确")
        return True


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Git 提交准备检查")
    print("=" * 60)
    
    # 检查 Git
    if not check_git_installed():
        return
    
    # 检查是否是 Git 仓库
    is_repo = check_git_repo()
    if not is_repo:
        init_choice = input("\n是否初始化 Git 仓库？(y/n): ").strip().lower()
        if init_choice in ['y', 'yes', '是']:
            if not init_git_repo():
                return
        else:
            print("❌ 需要 Git 仓库才能继续")
            return
    
    # 检查必需文件
    print("\n" + "=" * 60)
    if not check_required_files():
        print("\n⚠️  缺少必需文件，请先创建")
    
    # 检查 Python 文件
    print("\n" + "=" * 60)
    if not check_python_files():
        print("\n⚠️  没有找到 Python 文件")
    
    # 检查 .gitignore
    print("\n" + "=" * 60)
    check_gitignore()
    
    # 显示 Git 状态
    if is_repo:
        print("\n" + "=" * 60)
        show_git_status()
    
    # 建议命令
    print("\n" + "=" * 60)
    suggest_git_commands()
    
    print("\n" + "=" * 60)
    print("✅ 检查完成！")
    print("=" * 60)
    
    print("\n📚 更多信息请查看 BUILD_GUIDE.md")


if __name__ == "__main__":
    main()

