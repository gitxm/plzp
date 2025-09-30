#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话式数据处理和图片下载工具（examples 版本）
支持通过对话方式进行批量处理和单文件处理
"""

from app.processors.enhanced_data_processor import EnhancedDataProcessor
import os
import sys
from pathlib import Path
import re


class InteractiveProcessor:
    """对话式处理器"""

    def __init__(self):
        self.processor = EnhancedDataProcessor()
        self.current_mode = None
        self.settings = {
            'input_path': None,
            'output_path': None,
            'recursive': False,
            'file_format': None,
            'account_filter': None
        }

    def print_welcome(self):
        """打印欢迎信息"""
        print("=" * 60)
        print("🤖 智能数据处理助手")
        print("=" * 60)
        print("我可以帮您处理Excel和CSV文件，下载图片并整理数据。")
        print("支持单文件处理和批量处理模式。")
        print()
        print("💬 您可以直接告诉我您想要做什么，例如：")
        print("  - '处理这个Excel文件: 数据样例.xlsx'")
        print("  - '批量处理data文件夹中的所有文件'")
        print("  - '递归处理所有子文件夹'")
        print("  - '帮助' 或 'help' 查看更多命令")
        print("  - '退出' 或 'quit' 结束程序")
        print("=" * 60)

    def print_help(self):
        """打印帮助信息"""
        print("\n📚 可用命令和示例：")
        print()
        print("🔹 单文件处理：")
        print("  - '处理文件 数据样例.xlsx'")
        print("  - '处理 /path/to/file.csv'")
        print("  - '单文件处理 data.xlsx 输出到 output文件夹'")
        print()
        print("🔹 批量处理：")
        print("  - '批量处理 data文件夹'")
        print("  - '处理文件夹 ./data 输出到 ./output'")
        print("  - '递归处理 data文件夹'")
        print()
        print("🔹 查看信息：")
        print("  - '查看文件夹 data' - 查看文件夹中的文件")
        print("  - '检测格式 file.csv' - 检测文件格式")
        print("  - '状态' 或 'status' - 查看当前设置")
        print()
        print("🔹 设置命令：")
        print("  - '设置输出文件夹 ./output'")
        print("  - '启用递归搜索' / '禁用递归搜索'")
        print()
        print("🔹 其他：")
        print("  - '帮助' 或 'help' - 显示此帮助")
        print("  - '清除设置' - 重置所有设置")
        print("  - '退出' 或 'quit' - 退出程序")

    def parse_command(self, user_input):
        """解析用户输入的命令"""
        user_input = user_input.strip()

        # 帮助命令
        if re.match(r'^(帮助|help)$', user_input, re.IGNORECASE):
            return 'help', {}

        # 退出命令
        if re.match(r'^(退出|quit|exit)$', user_input, re.IGNORECASE):
            return 'quit', {}

        # 状态查看
        if re.match(r'^(状态|status)$', user_input, re.IGNORECASE):
            return 'status', {}

        # 清除设置
        if re.match(r'^清除设置$', user_input):
            return 'clear_settings', {}

        # 单文件处理
        single_file_patterns = [
            r'^处理文件\s+(.+)$',
            r'^处理\s+(.+)$',
            r'^单文件处理\s+(.+?)(?:\s+输出到\s+(.+))?$'
        ]

        for pattern in single_file_patterns:
            match = re.match(pattern, user_input)
            if match:
                file_path = match.group(1).strip()
                output_path = match.group(2).strip() if match.lastindex > 1 and match.group(2) else None
                return 'process_file', {'file_path': file_path, 'output_path': output_path}

        # 批量处理
        batch_patterns = [
            r'^批量处理\s+(.+)$',
            r'^处理文件夹\s+(.+?)(?:\s+输出到\s+(.+))?$',
            r'^递归处理\s+(.+?)(?:\s+输出到\s+(.+))?$'
        ]

        for i, pattern in enumerate(batch_patterns):
            match = re.match(pattern, user_input)
            if match:
                folder_path = match.group(1).strip()
                output_path = match.group(2).strip() if match.lastindex > 1 and match.group(2) else None
                recursive = (i == 2)  # 第三个模式是递归处理
                return 'process_folder', {
                    'folder_path': folder_path,
                    'output_path': output_path,
                    'recursive': recursive
                }

        # 查看文件夹
        view_folder_match = re.match(r'^查看文件夹\s+(.+)$', user_input)
        if view_folder_match:
            folder_path = view_folder_match.group(1).strip()
            return 'view_folder', {'folder_path': folder_path}

        # 检测文件格式
        detect_format_match = re.match(r'^检测格式\s+(.+)$', user_input)
        if detect_format_match:
            file_path = detect_format_match.group(1).strip()
            return 'detect_format', {'file_path': file_path}

        # 设置输出文件夹
        set_output_match = re.match(r'^设置输出文件夹\s+(.+)$', user_input)
        if set_output_match:
            output_path = set_output_match.group(1).strip()
            return 'set_output', {'output_path': output_path}

        # 递归设置
        if re.match(r'^启用递归搜索$', user_input):
            return 'set_recursive', {'recursive': True}

        if re.match(r'^禁用递归搜索$', user_input):
            return 'set_recursive', {'recursive': False}

        # 筛选账户
        filter_match = re.match(r'^筛选账户\s+(.+)$', user_input)
        if filter_match:
            ids_raw = filter_match.group(1)
            parts = re.split(r'[，,\s]+', ids_raw)
            ids = [s.strip() for s in parts if s.strip()]
            return 'set_account_filter', {'ids': ids}

        # 清除账户筛选
        if re.match(r'^清除账户筛选$', user_input):
            return 'clear_account_filter', {}

        # 未识别的命令
        return 'unknown', {'input': user_input}

    def execute_command(self, command, params):
        """执行解析后的命令"""
        if command == 'help':
            self.print_help()

        elif command == 'quit':
            print("👋 感谢使用！再见！")
            return False

        elif command == 'status':
            self.show_status()

        elif command == 'clear_settings':
            self.clear_settings()

        elif command == 'process_file':
            self.handle_process_file(params)

        elif command == 'set_account_filter':
            ids = params.get('ids', [])
            self.settings['account_filter'] = ids if ids else None
            if ids:
                print(f"✅ 已设置账户筛选: {', '.join(ids)}")
            else:
                print("✅ 已清空账户筛选")

        elif command == 'clear_account_filter':
            self.settings['account_filter'] = None
            print("✅ 已清空账户筛选")

        elif command == 'process_folder':
            self.handle_process_folder(params)

        elif command == 'view_folder':
            self.handle_view_folder(params)

        elif command == 'detect_format':
            self.handle_detect_format(params)

        elif command == 'set_output':
            self.handle_set_output(params)

        elif command == 'set_recursive':
            self.handle_set_recursive(params)

        elif command == 'unknown':
            self.handle_unknown_command(params)

        return True

    def show_status(self):
        """显示当前状态"""
        print("\n📊 当前设置状态：")
        print(f"  输入路径: {self.settings['input_path'] or '未设置'}")
        print(f"  输出路径: {self.settings['output_path'] or '未设置'}")
        print(f"  递归搜索: {'启用' if self.settings['recursive'] else '禁用'}")
        print(f"  文件格式: {self.settings['file_format'] or '自动检测'}")
        print(f"  账户筛选: {', '.join(self.settings['account_filter']) if self.settings['account_filter'] else '未设置（执行前将询问是否全量）'}")

    def clear_settings(self):

        """清除所有设置"""
        self.settings = {
            'input_path': None,
            'output_path': None,
            'recursive': False,
            'file_format': None
        }
        print("✅ 设置已清除")

    def handle_process_file(self, params):
        """处理单文件命令"""
        file_path = params['file_path']
        output_path = params.get('output_path') or self.settings['output_path']

        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return

        print(f"🔄 开始处理文件: {file_path}")
        if output_path:
            print(f"📁 输出到: {output_path}")

        account_filter = self.settings['account_filter']
        if account_filter is None:
            confirm = input("未设置账户筛选，是否全量下载？(y/n): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
                print("❌ 已取消。请先通过 '筛选账户 1001,1002' 设置筛选后再执行。")
                return
        success = self.processor.process_single_file(file_path, output_path, account_filter=account_filter)

        if success:
            print("✅ 文件处理完成！")
        else:
            print("❌ 文件处理失败，请查看日志")

    def handle_process_folder(self, params):
        """处理批量文件夹命令"""
        folder_path = params['folder_path']
        output_path = params.get('output_path') or self.settings['output_path']
        recursive = params.get('recursive', self.settings['recursive'])

        if not os.path.exists(folder_path):
            print(f"❌ 文件夹不存在: {folder_path}")
            return

        print(f"🔄 开始批量处理文件夹: {folder_path}")
        if output_path:
            print(f"📁 输出到: {output_path}")
        print(f"🔍 递归搜索: {'启用' if recursive else '禁用'}")

        account_filter = self.settings['account_filter']
        if account_filter is None:
            confirm = input("未设置账户筛选，是否全量下载？(y/n): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
                print("❌ 已取消。请先通过 '筛选账户 1001,1002' 设置筛选后再执行。")
                return
        results = self.processor.process_batch_files(folder_path, output_path, recursive, account_filter=account_filter)

        print(f"\n📊 批量处理完成！")
        print(f"  总文件数: {results['total']}")
        print(f"  成功处理: {results['success']}")
        print(f"  处理失败: {results['failed']}")

    def handle_view_folder(self, params):
        """查看文件夹内容"""
        folder_path = params['folder_path']

        if not os.path.exists(folder_path):
            print(f"❌ 文件夹不存在: {folder_path}")
            return

        files = self.processor.find_data_files(folder_path, recursive=False)

        print(f"\n📁 文件夹 {folder_path} 中的数据文件:")
        if files:
            for i, file_path in enumerate(files, 1):
                file_format = self.processor.detect_file_format(file_path)
                print(f"  {i}. {file_path} ({file_format})")
        else:
            print("  (没有找到支持的数据文件)")

    def handle_detect_format(self, params):
        """检测文件格式"""
        file_path = params['file_path']

        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return

        file_format = self.processor.detect_file_format(file_path)
        print(f"📄 文件 {file_path} 的格式: {file_format}")

    def handle_set_output(self, params):
        """设置输出文件夹"""
        output_path = params['output_path']
        self.settings['output_path'] = output_path
        print(f"✅ 输出文件夹已设置为: {output_path}")

    def handle_set_recursive(self, params):
        """设置递归搜索"""
        recursive = params['recursive']
        self.settings['recursive'] = recursive
        status = "启用" if recursive else "禁用"
        print(f"✅ 递归搜索已{status}")

    def handle_unknown_command(self, params):
        """处理未识别的命令"""
        user_input = params['input']
        print(f"❓ 抱歉，我不理解命令: '{user_input}'")
        print("💡 输入 '帮助' 查看可用命令，或尝试更清楚地描述您的需求")

        # 提供一些建议
        suggestions = []
        if '处理' in user_input:
            suggestions.append("尝试: '处理文件 文件名.xlsx' 或 '批量处理 文件夹名'")
        if '文件夹' in user_input:
            suggestions.append("尝试: '查看文件夹 文件夹名' 或 '批量处理 文件夹名'")
        if '文件' in user_input:
            suggestions.append("尝试: '处理文件 文件名' 或 '检测格式 文件名'")

        if suggestions:
            print("💡 建议命令:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")

    def run(self):
        """运行对话式处理器"""
        self.print_welcome()

        while True:
            try:
                print("\n" + "-" * 40)
                user_input = input("🤖 请告诉我您想要做什么: ").strip()

                if not user_input:
                    continue

                command, params = self.parse_command(user_input)

                if not self.execute_command(command, params):
                    break

            except KeyboardInterrupt:
                print("\n\n⚠️  程序被中断")
                break
            except Exception as e:
                print(f"\n❌ 处理过程中出现错误: {e}")
                print("请重试或输入 '帮助' 查看使用说明")


def main():
    """主函数"""
    processor = InteractiveProcessor()
    processor.run()


if __name__ == "__main__":
    main()

