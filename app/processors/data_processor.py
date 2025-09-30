#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理和图片下载工具（app.processors 版本）
"""

import pandas as pd
import requests
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import logging
from app.config import (
    REQUIRED_FIELDS, DOWNLOAD_CONFIG, FOLDER_NAME_TEMPLATE,
    FILENAME_CONFIG, LOG_CONFIG, SORT_CONFIG
)

# 配置日志
# 确保日志目录存在
_log_dir = os.path.dirname(LOG_CONFIG['log_file'])
if _log_dir:
    os.makedirs(_log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['log_level']),
    format=LOG_CONFIG['log_format'],
    datefmt=LOG_CONFIG.get('date_format'),
    handlers=[
        logging.FileHandler(LOG_CONFIG['log_file'], encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理和图片下载类"""

    def __init__(self, excel_file_path):
        """
        初始化数据处理器

        Args:
            excel_file_path (str): Excel文件路径
        """
        self.excel_file_path = excel_file_path
        self.required_fields = REQUIRED_FIELDS
        self.df = None
        self.processed_df = None

    def load_data(self):
        """加载Excel数据"""
        try:
            logger.info(f"正在加载数据文件: {self.excel_file_path}")
            self.df = pd.read_excel(self.excel_file_path)
            logger.info(f"数据加载成功，共 {len(self.df)} 行数据")

            # 检查必需字段是否存在
            missing_fields = [field for field in self.required_fields if field not in self.df.columns]
            if missing_fields:
                raise ValueError(f"缺少必需字段: {missing_fields}")

            logger.info("所有必需字段都存在")
            return True

        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            return False

    def extract_and_sort_data(self):
        """提取所需字段并按要求排序"""
        try:
            logger.info("开始提取和排序数据...")

            # 提取所需字段
            self.processed_df = self.df[self.required_fields].copy()

            # 按配置进行排序
            self.processed_df = self.processed_df.sort_values(
                by=SORT_CONFIG['sort_by'],
                ascending=SORT_CONFIG['ascending']
            ).reset_index(drop=True)

            # 添加file_name列（初始为空）
            self.processed_df['file_name'] = ''

            logger.info(f"数据提取和排序完成，共 {len(self.processed_df)} 行数据")

            # 显示分组统计
            group_stats = self.processed_df.groupby('account_id').size()
            logger.info(f"按account_id分组统计: \n{group_stats}")

            return True

        except Exception as e:
            logger.error(f"数据提取和排序失败: {e}")
            return False

    def timestamp_to_filename(self, timestamp):
        """
        将时间戳转换为文件名格式：月日小时分钟秒

        Args:
            timestamp (int): Unix时间戳

        Returns:
            str: 格式化的文件名（不含扩展名）
        """
        try:
            dt = datetime.fromtimestamp(timestamp)
            # 使用配置中的时间格式
            filename = dt.strftime(FILENAME_CONFIG['time_format'])
            return filename
        except Exception as e:
            logger.error(f"时间戳转换失败: {timestamp}, 错误: {e}")
            return str(timestamp)

    def get_image_extension(self, url):
        """
        从URL获取图片扩展名

        Args:
            url (str): 图片URL

        Returns:
            str: 文件扩展名
        """
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            extension = os.path.splitext(path)[1]
            return extension if extension else FILENAME_CONFIG['default_extension']
        except:
            return FILENAME_CONFIG['default_extension']

    def create_folder_structure(self):
        """创建文件夹结构"""
        folders_created = set()

        for _, row in self.processed_df.iterrows():
            folder_name = FOLDER_NAME_TEMPLATE.format(
                company_id=row['company_id'],
                account_id=row['account_id'],
                user_id=row['user_id']
            )
            folder_path = Path(folder_name)

            if folder_name not in folders_created:
                folder_path.mkdir(exist_ok=True)
                folders_created.add(folder_name)
                logger.info(f"创建文件夹: {folder_name}")

        return folders_created

    def download_image(self, url, file_path, timeout=30):
        """
        下载单个图片

        Args:
            url (str): 图片URL
            file_path (str): 保存路径
            timeout (int): 超时时间

        Returns:
            bool: 下载是否成功
        """
        try:
            headers = {
                'User-Agent': DOWNLOAD_CONFIG['user_agent']
            }

            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"图片下载成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"图片下载失败: {url}, 错误: {e}")
            return False

    def download_all_images(self):
        """批量下载所有图片"""
        try:
            logger.info("开始批量下载图片...")

            # 创建文件夹结构
            self.create_folder_structure()

            success_count = 0
            total_count = len(self.processed_df)

            for index, row in self.processed_df.iterrows():
                # 生成文件名
                base_filename = self.timestamp_to_filename(row['create_time'])
                extension = self.get_image_extension(row['image_url'])
                filename = f"{base_filename}{extension}"

                # 生成文件夹路径
                folder_name = FOLDER_NAME_TEMPLATE.format(
                    company_id=row['company_id'],
                    account_id=row['account_id'],
                    user_id=row['user_id']
                )
                file_path = Path(folder_name) / filename

                # 重复文件检查：同名存在则跳过下载
                if file_path.exists():
                    logger.info(f"已存在同名文件，跳过下载: {file_path}")
                    self.processed_df.at[index, 'file_name'] = filename
                    continue

                # 下载图片
                if self.download_image(row['image_url'], str(file_path)):
                    # 更新DataFrame中的file_name字段
                    self.processed_df.at[index, 'file_name'] = filename
                    success_count += 1
                else:
                    # 下载失败时记录空文件名
                    self.processed_df.at[index, 'file_name'] = ''

                # 添加延迟避免请求过快
                time.sleep(DOWNLOAD_CONFIG['delay_between_requests'])

                # 显示进度
                progress = (index + 1) / total_count * 100
                logger.info(f"下载进度: {index + 1}/{total_count} ({progress:.1f}%)")

            logger.info(f"图片下载完成！成功: {success_count}/{total_count}")
            return True

        except Exception as e:
            logger.error(f"批量下载失败: {e}")
            return False

    def save_updated_excel(self, output_path=None):
        """保存更新后的Excel文件"""
        try:
            if output_path is None:
                # 生成输出文件名
                base_name = os.path.splitext(self.excel_file_path)[0]
                output_path = f"{base_name}_updated.xlsx"

            logger.info(f"正在保存更新后的Excel文件: {output_path}")

            # 保存到Excel文件
            self.processed_df.to_excel(output_path, index=False)

            logger.info(f"Excel文件保存成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Excel文件保存失败: {e}")
            return False

    def run(self, output_path=None):
        """运行完整的数据处理流程"""
        logger.info("=" * 50)
        logger.info("开始数据处理和图片下载流程")
        logger.info("=" * 50)

        # 1. 加载数据
        if not self.load_data():
            return False

        # 2. 提取和排序数据
        if not self.extract_and_sort_data():
            return False

        # 3. 下载图片
        if not self.download_all_images():
            return False

        # 4. 保存更新后的Excel文件
        if not self.save_updated_excel(output_path):
            return False

        logger.info("=" * 50)
        logger.info("数据处理和图片下载流程完成！")
        logger.info("=" * 50)

        return True


def main():
    """主函数"""
    # Excel文件路径
    excel_file = "数据样例.xlsx"

    # 检查文件是否存在
    if not os.path.exists(excel_file):
        print(f"错误：找不到文件 {excel_file}")
        return

    # 创建数据处理器并运行
    processor = DataProcessor(excel_file)
    success = processor.run()

    if success:
        print("\n✅ 所有任务完成成功！")
        print("📁 请检查生成的文件夹和更新后的Excel文件")
    else:
        print("\n❌ 任务执行过程中出现错误，请查看日志文件")


if __name__ == "__main__":
    main()

