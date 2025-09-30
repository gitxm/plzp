#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理配置脚本（examples 版本）
用于快速配置和执行批量处理任务
"""

from app.processors.enhanced_data_processor import EnhancedDataProcessor
from app.config import BATCH_CONFIG
import os
from pathlib import Path


class BatchProcessor:
    """批量处理配置类"""

    def __init__(self):
        self.processor = EnhancedDataProcessor()
        self.config = BATCH_CONFIG.copy()

    def set_input_folder(self, folder_path):
        """设置输入文件夹"""
        self.config['batch_folder_path'] = folder_path
        return self

    def set_output_folder(self, folder_path):
        """设置输出文件夹"""
        self.config['output_folder_path'] = folder_path
        return self

    def enable_recursive(self, recursive=True):
        """启用/禁用递归搜索"""
        self.config['recursive_search'] = recursive
        return self

    def run(self):
        """执行批量处理"""
        input_folder = self.config['batch_folder_path']
        output_folder = self.config['output_folder_path']
        recursive = self.config['recursive_search']

        print(f"输入文件夹: {input_folder}")
        print(f"输出文件夹: {output_folder}")
        print(f"递归搜索: {'是' if recursive else '否'}")

        # 创建输出文件夹
        if output_folder:
            Path(output_folder).mkdir(parents=True, exist_ok=True)

        # 执行批量处理
        results = self.processor.process_batch_files(
            input_folder,
            output_folder,
            recursive
        )

        return results


def quick_batch_process():
    """快速批量处理函数"""
    print("=" * 50)
    print("快速批量处理工具")
    print("=" * 50)

    # 默认配置
    input_folder = "./data"
    output_folder = "./output"

    # 检查默认输入文件夹
    if not os.path.exists(input_folder):
        print(f"创建默认输入文件夹: {input_folder}")
        os.makedirs(input_folder, exist_ok=True)
        print(f"请将要处理的Excel/CSV文件放入 {input_folder} 文件夹中")
        return

    # 执行批量处理
    batch = BatchProcessor()
    results = (batch
               .set_input_folder(input_folder)
               .set_output_folder(output_folder)
               .enable_recursive(False)
               .run())

    print("\n处理完成！")
    print(f"结果: {results}")


def custom_batch_process():
    """自定义批量处理函数"""
    print("=" * 50)
    print("自定义批量处理工具")
    print("=" * 50)

    # 获取用户输入
    input_folder = input("请输入数据文件夹路径: ").strip()
    if not input_folder:
        print("❌ 输入文件夹路径不能为空")
        return

    output_folder = input("请输入输出文件夹路径（可选）: ").strip()
    output_folder = output_folder if output_folder else None

    recursive_input = input("是否递归搜索子文件夹？(y/n): ").strip().lower()
    recursive = recursive_input in ['y', 'yes', '是']

    # 执行批量处理
    batch = BatchProcessor()
    batch.set_input_folder(input_folder)

    if output_folder:
        batch.set_output_folder(output_folder)

    batch.enable_recursive(recursive)

    results = batch.run()

    print("\n处理完成！")
    print(f"结果: {results}")


def main():
    """主函数"""
    print("选择批量处理模式:")
    print("1. 快速处理 (使用默认配置)")
    print("2. 自定义处理")
    print("3. 退出")

    choice = input("\n请输入选择 (1-3): ").strip()

    if choice == '1':
        quick_batch_process()
    elif choice == '2':
        custom_batch_process()
    elif choice == '3':
        print("👋 再见！")
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()

