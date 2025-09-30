#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件重命名工具 - 将旧的文件名格式更新为新的包含URL信息的格式
"""

import os
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import logging

# 导入配置
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import FILENAME_CONFIG

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FileRenamer:
    """文件重命名工具类"""
    
    def __init__(self):
        self.renamed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def sanitize_filename_component(self, text, max_len=None):
        """
        将任意文本转为适于文件名的安全片段：
        - 移除控制字符
        - 替换非法字符 / \ : * ? " < > | & % + # 空格 等为下划线
        - 可选长度截断
        - 去除首尾下划线，合并重复下划线
        保留中文、字母、数字、点、短横线、下划线
        """
        if text is None:
            s = ''
        else:
            s = str(text)
        # 去除控制字符
        s = ''.join(ch for ch in s if ord(ch) >= 32)
        # 替换非法字符为下划线
        s = re.sub(r"[\\/\:*?\"<>|&%+#\s]+", "_", s)
        # 合并连续下划线
        s = re.sub(r"_+", "_", s)
        s = s.strip("._ ")
        if max_len and len(s) > max_len:
            s = s[:max_len]
        return s
    
    def get_image_extension(self, url):
        """从URL获取图片扩展名"""
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            extension = os.path.splitext(path)[1]
            return extension if extension else FILENAME_CONFIG['default_extension']
        except:
            return FILENAME_CONFIG['default_extension']
    
    def timestamp_to_filename(self, timestamp):
        """将时间戳转换为文件名格式"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            filename = dt.strftime(FILENAME_CONFIG['time_format'])
            return filename
        except Exception as e:
            logger.error(f"时间戳转换失败: {timestamp}, 错误: {e}")
            return str(timestamp)
    
    def build_new_filename(self, row, max_total_len=200):
        """
        基于数据行生成新的文件名：
        格式：{时间戳}_{处理后的URL}_{处理后的title}.{扩展名}
        """
        try:
            base = self.timestamp_to_filename(row.get('create_time'))
            # 使用 url 字段来构建文件名
            url = row.get('url', '')
            title = row.get('title', '')
            # 获取扩展名时使用 image_url（因为这是实际下载的图片URL）
            ext = self.get_image_extension(row.get('image_url', ''))

            # 去掉协议前缀（http://、https:// 等）后再做清洗
            if url:
                url = re.sub(r'^[a-zA-Z]+://', '', str(url))
            url_part = self.sanitize_filename_component(url, max_len=120)
            title_part = self.sanitize_filename_component(title, max_len=60) if title else ''

            parts = [p for p in [base, url_part, title_part] if p]
            stem = "_".join(parts)

            # 控制总长（包含点与扩展名）
            allow = max_total_len - len(ext) - 1 if ext else max_total_len
            if allow < 10:
                allow = 10
            if len(stem) > allow:
                stem = stem[:allow]
            filename = f"{stem}{ext}"
            return filename
        except Exception:
            # 回退：仅时间戳+扩展名
            base = self.timestamp_to_filename(row.get('create_time'))
            ext = self.get_image_extension(row.get('image_url', ''))
            return f"{base}{ext}"
    
    def parse_old_filename(self, filename):
        """
        解析旧的文件名格式，提取时间戳信息
        旧格式：09_28 10-12-06_标题.jpg
        """
        try:
            # 移除扩展名
            name_without_ext = os.path.splitext(filename)[0]
            
            # 匹配时间格式：MM_DD HH-MM-SS
            time_pattern = r'^(\d{2}_\d{2} \d{2}-\d{2}-\d{2})'
            match = re.match(time_pattern, name_without_ext)
            
            if match:
                time_part = match.group(1)
                # 提取标题部分（如果有的话）
                title_part = name_without_ext[len(time_part):].lstrip('_')
                return time_part, title_part
            
            return None, None
        except Exception:
            return None, None
    
    def find_matching_data_row(self, df, old_filename, file_path):
        """
        根据旧文件名和路径信息，在数据中找到匹配的行
        """
        try:
            # 从文件路径中提取 company_id, account_id, user_id
            path_parts = Path(file_path).parts
            if len(path_parts) >= 3:
                company_id = path_parts[-3]
                account_id = path_parts[-2] 
                user_id = path_parts[-1]
                
                # 解析旧文件名获取时间信息
                time_part, title_part = self.parse_old_filename(old_filename)
                
                if time_part:
                    # 在数据中查找匹配的行
                    # 首先按 company_id, account_id, user_id 筛选
                    filtered_df = df[
                        (df['company_id'].astype(str) == company_id) &
                        (df['account_id'].astype(str) == account_id) &
                        (df['user_id'].astype(str) == user_id)
                    ]
                    
                    if not filtered_df.empty:
                        # 如果有标题信息，尝试匹配标题
                        if title_part:
                            title_matches = filtered_df[
                                filtered_df['title'].astype(str).str.contains(
                                    re.escape(title_part), case=False, na=False
                                )
                            ]
                            if not title_matches.empty:
                                return title_matches.iloc[0]
                        
                        # 如果没有标题匹配或没有标题，返回第一个匹配的行
                        return filtered_df.iloc[0]
            
            return None
        except Exception as e:
            logger.error(f"查找匹配数据行失败: {e}")
            return None
    
    def rename_files_in_directory(self, directory_path, data_file_path, dry_run=True):
        """
        重命名指定目录下的所有文件

        Args:
            directory_path (str): 要处理的目录路径
            data_file_path (str): 包含数据的Excel或CSV文件路径
            dry_run (bool): 是否只是预览，不实际重命名
        """
        try:
            # 加载数据文件
            logger.info(f"加载数据文件: {data_file_path}")

            # 根据文件扩展名选择读取方式
            file_ext = Path(data_file_path).suffix.lower()
            if file_ext == '.csv':
                df = pd.read_csv(data_file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(data_file_path)
            else:
                logger.error(f"不支持的文件格式: {file_ext}")
                return False
            
            # 扫描目录下的所有图片文件
            directory = Path(directory_path)
            if not directory.exists():
                logger.error(f"目录不存在: {directory_path}")
                return False
            
            # 查找所有图片文件
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(directory.rglob(f"*{ext}"))
                image_files.extend(directory.rglob(f"*{ext.upper()}"))
            
            logger.info(f"找到 {len(image_files)} 个图片文件")
            
            if dry_run:
                logger.info("=== 预览模式 - 不会实际重命名文件 ===")
            else:
                logger.info("=== 开始重命名文件 ===")
            
            for file_path in image_files:
                try:
                    old_filename = file_path.name
                    
                    # 查找匹配的数据行
                    matching_row = self.find_matching_data_row(df, old_filename, str(file_path))
                    
                    if matching_row is not None:
                        # 生成新文件名
                        new_filename = self.build_new_filename(matching_row)
                        
                        if new_filename != old_filename:
                            new_file_path = file_path.parent / new_filename
                            
                            if dry_run:
                                logger.info(f"预览: {old_filename} -> {new_filename}")
                            else:
                                # 检查新文件名是否已存在
                                if new_file_path.exists():
                                    logger.warning(f"新文件名已存在，跳过: {new_filename}")
                                    self.skipped_count += 1
                                else:
                                    # 执行重命名
                                    file_path.rename(new_file_path)
                                    logger.info(f"重命名: {old_filename} -> {new_filename}")
                                    self.renamed_count += 1
                        else:
                            logger.info(f"文件名已是新格式，跳过: {old_filename}")
                            self.skipped_count += 1
                    else:
                        logger.warning(f"未找到匹配的数据行: {old_filename}")
                        self.skipped_count += 1
                        
                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {e}")
                    self.error_count += 1
            
            # 输出统计信息
            logger.info("=== 重命名统计 ===")
            logger.info(f"重命名文件数: {self.renamed_count}")
            logger.info(f"跳过文件数: {self.skipped_count}")
            logger.info(f"错误文件数: {self.error_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"重命名过程失败: {e}")
            return False


def main():
    """主函数"""
    renamer = FileRenamer()
    
    print("=" * 60)
    print("📁 文件重命名工具")
    print("=" * 60)
    print("功能: 将旧格式文件名更新为包含URL信息的新格式")
    print("=" * 60)
    
    # 获取用户输入
    directory_path = input("请输入要处理的目录路径: ").strip().strip("'\"")
    data_file_path = input("请输入数据文件路径 (.xlsx/.csv): ").strip().strip("'\"")

    if not directory_path or not data_file_path:
        print("❌ 路径不能为空")
        return
    
    # 展开用户目录路径
    directory_path = os.path.expanduser(directory_path)
    data_file_path = os.path.expanduser(data_file_path)
    
    # 检查路径是否存在
    if not os.path.exists(directory_path):
        print(f"❌ 目录不存在: {directory_path}")
        return
    
    if not os.path.exists(data_file_path):
        print(f"❌ 数据文件不存在: {data_file_path}")
        return
    
    # 询问是否预览
    preview_choice = input("是否先预览重命名结果？(y/n): ").strip().lower()
    
    if preview_choice in ['y', 'yes', '是']:
        print("\n🔍 预览重命名结果...")
        renamer.rename_files_in_directory(directory_path, data_file_path, dry_run=True)
        
        confirm = input("\n确认执行重命名？(y/n): ").strip().lower()
        if confirm in ['y', 'yes', '是']:
            print("\n🚀 开始重命名...")
            renamer.renamed_count = 0  # 重置计数器
            renamer.skipped_count = 0
            renamer.error_count = 0
            renamer.rename_files_in_directory(directory_path, data_file_path, dry_run=False)
        else:
            print("❌ 重命名已取消")
    else:
        print("\n🚀 开始重命名...")
        renamer.rename_files_in_directory(directory_path, data_file_path, dry_run=False)
    
    print("\n✅ 重命名工具运行完成")


if __name__ == "__main__":
    main()
