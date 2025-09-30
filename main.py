#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理和图片下载工具 - 主启动脚本
整合所有功能的统一入口
"""

import sys
import os


def check_dependencies():
    """检查依赖库"""
    try:
        import pandas
        import requests
        import openpyxl
        print("✅ 依赖库检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("\n📦 请先安装依赖:")
        print("pip install pandas openpyxl requests")
        print("\n或者运行自动安装脚本:")
        print("python setup.py")
        return False


def print_main_menu():
    """打印主菜单"""
    print("=" * 60)
    print("📊 数据处理和图片下载工具")
    print("=" * 60)
    print("功能: 从Excel/CSV提取数据，下载图片，整理文件")
    print("支持: 单文件处理、批量处理、递归处理")
    print("=" * 60)
    print("\n🚀 请选择启动模式:")
    print("  1. 简单模式 (推荐) - 菜单界面操作")
    print("  2. 环境设置和安装")
    print("  3. 退出")
    print("-" * 60)


def get_user_choice():
    """获取用户选择"""
    while True:
        try:
            choice = input("请输入选择 (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("❌ 请输入有效选择 (1-3)")
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
            sys.exit(0)
        except:
            print("❌ 输入无效，请重新输入")


def launch_simple_mode():
    """启动简单模式"""
    try:
        from app.ui.simple_processor import SimpleProcessor
        print("\n🚀 启动简单模式...")
        processor = SimpleProcessor()
        processor.run()
    except ImportError as e:
        print(f"❌ 无法启动简单模式: {e}")
        print("请确保 app/ui/simple_processor.py 文件存在")
    except Exception as e:
        print(f"❌ 简单模式运行错误: {e}")


def setup_environment():
    """环境设置和安装"""
    try:
        print("\n🔧 环境设置和安装")
        print("=" * 40)
        print("1. 运行自动安装脚本")
        print("2. 手动安装依赖")
        print("3. 检查环境状态")
        print("4. 返回主菜单")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == '1':
            print("\n🚀 运行自动安装脚本...")
            try:
                from setup import main as setup_main
                setup_main()
            except ImportError:
                print("❌ 找不到安装脚本 setup.py")
            except Exception as e:
                print(f"❌ 安装脚本运行错误: {e}")
                
        elif choice == '2':
            print("\n📦 手动安装依赖:")
            print("pip install pandas openpyxl requests")
            print("\n或者使用虚拟环境:")
            print("python -m venv venv")
            print("source venv/bin/activate  # Linux/Mac")
            print("venv\\Scripts\\activate     # Windows")
            print("pip install -r requirements.txt")
            
        elif choice == '3':
            print("\n🔍 检查环境状态...")
            check_dependencies()
            
            # 检查文件
            files_to_check = [
                'app/processors/enhanced_data_processor.py',
                'app/processors/data_processor.py',
                'examples/interactive_processor.py',
                'examples/batch_processor.py',
                'app/config.py',
                'simple_processor.py',
                'requirements.txt'
            ]

            print("\n📁 文件检查:")
            for file_name in files_to_check:
                if os.path.exists(file_name):
                    print(f"  ✅ {file_name}")
                else:
                    print(f"  ❌ {file_name} (缺失)")
            
        elif choice == '4':
            return
        else:
            print("❌ 无效选择")
            
    except Exception as e:
        print(f"❌ 环境设置错误: {e}")


def main():
    """主函数"""
    # 检查依赖
    if not check_dependencies():
        print("\n⚠️  请先安装依赖库后再运行程序")
        return
    
    while True:
        try:
            print_main_menu()
            choice = get_user_choice()
            
            if choice == 1:
                launch_simple_mode()
            elif choice == 2:
                setup_environment()
            elif choice == 3:
                print("\n👋 感谢使用，再见！")
                break
            
            # 询问是否继续
            print("\n" + "=" * 60)
            continue_choice = input("是否返回主菜单？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是']:
                print("👋 感谢使用，再见！")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
            break
        except Exception as e:
            print(f"\n❌ 程序出现错误: {e}")
            print("请重试或退出程序")


if __name__ == "__main__":
    main()
