#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版数据处理和图片下载工具
支持多种文件格式和批量处理功能（app.processors 版本）
"""

import pandas as pd
import requests
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from app.config import (
    REQUIRED_FIELDS, DOWNLOAD_CONFIG,
    FILENAME_CONFIG, LOG_CONFIG, SORT_CONFIG, SUPPORTED_FORMATS,
    MULTITHREADING_CONFIG, ERROR_LOG_CONFIG
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


class EnhancedDataProcessor:
    """增强版数据处理和图片下载类"""

    def __init__(self):
        """初始化增强版数据处理器"""
        self.required_fields = REQUIRED_FIELDS
        self.supported_formats = SUPPORTED_FORMATS
        self.multithreading_enabled = MULTITHREADING_CONFIG['enable_multithreading']
        self.max_threads = MULTITHREADING_CONFIG['max_download_threads']
        self.download_timeout = MULTITHREADING_CONFIG['download_timeout']
        # 线程安全的锁
        self._progress_lock = threading.Lock()
        self._success_count_lock = threading.Lock()
        self._folders_created_lock = threading.Lock()
        # 错误日志相关
        self._error_log_lock = threading.Lock()
        self.error_log_file = None
        self.error_count = 0
        self._init_error_log()
        # 高级错误日志与统计
        self._init_advanced_error_logging()

    def _init_advanced_error_logging(self):
        """
        初始化增强错误日志（详细日志+汇总统计），按日期轮转
        """
        try:
            log_dir = Path(ERROR_LOG_CONFIG['error_log_dir']) if 'error_log_dir' in ERROR_LOG_CONFIG else Path('logs')
            log_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime('%Y%m%d')
            self.detailed_log_path = log_dir / f"detailed_errors_{date_str}.log"
            self.summary_log_path = log_dir / f"error_summary_{date_str}.log"
            # 统计容器
            self.error_type_counts = Counter()
            self.error_time_buckets = Counter()  # 按小时统计: 'YYYY-MM-DD HH:00'
            self.error_reasons = Counter()       # 常见原因统计
        except Exception as e:
            logger.error(f"初始化增强错误日志失败: {e}")

    def _classify_exception(self, e):
        """将异常类型映射为可读错误类型标签"""
        from requests.exceptions import Timeout, ConnectionError, HTTPError
        import errno
        if isinstance(e, (Timeout, ConnectionError)):
            return "网络连接错误"
        if isinstance(e, HTTPError):
            return "HTTP状态错误"
        if isinstance(e, PermissionError):
            return "文件权限错误"
        if isinstance(e, FileNotFoundError):
            return "文件不存在错误"
        if isinstance(e, OSError) and getattr(e, 'errno', None) == errno.EACCES:
            return "文件权限错误"
        if isinstance(e, ValueError):
            return "URL格式错误"
        return "未知错误"

    def _log_detailed_error(self, error_type, context, exc):
        """
        写入详细错误日志（无堆栈，仅关键信息，便于定位Excel数据行）。
        期望包含：时间、错误类型、Excel行号与数据行号、账户/用户/公司、image_url、title、目标文件、异常简述。
        """
        try:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 读取上下文
            excel_row = context.get('excel_row', 'N/A')
            data_row = context.get('row', 'N/A')
            file_path = context.get('file_path', '')
            row_data = context.get('row_data', {}) or {}
            account_id = row_data.get('account_id', 'N/A')
            user_id = row_data.get('user_id', 'N/A')
            company_id = row_data.get('company_id', 'N/A')
            image_url = row_data.get('image_url', 'N/A')
            title = row_data.get('title', '')
            create_time = row_data.get('create_time', 'N/A')

            lines = [
                f"[{ts}] [{error_type}] 下载失败",
                f"  创建时间: {create_time}",
                f"  账户ID: {account_id}    用户ID: {user_id}    公司ID: {company_id}",
                f"  图片URL: {image_url}",
                f"  标题: {title}",
                f"  目标文件: {file_path}",
                f"  异常: {type(exc).__name__}: {exc}",
                "-" * 80,
            ]
            with open(self.detailed_log_path, 'a', encoding='utf-8') as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            logger.error(f"写入详细错误日志失败: {e}")

    def _accumulate_error_stats(self, error_type, exc):
        """累计错误统计数据"""
        self.error_type_counts[error_type] += 1
        bucket = datetime.now().strftime('%Y-%m-%d %H:00')
        self.error_time_buckets[bucket] += 1
        reason = f"{type(exc).__name__}: {str(exc)[:120]}"
        self.error_reasons[reason] += 1

    def _write_error_summary(self):
        """将当前统计写入汇总日志文件"""
        try:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            lines = [
                "=" * 80,
                f"错误汇总快照 @ {ts}",
                "- 错误类型统计:",
            ]
            for et, cnt in self.error_type_counts.most_common():
                lines.append(f"  • {et}: {cnt}")
            lines.append("- 时间分布(按小时):")
            for t, cnt in sorted(self.error_time_buckets.items()):
                lines.append(f"  • {t}: {cnt}")
            lines.append("- 最常见错误原因:")
            for r, cnt in self.error_reasons.most_common(5):
                lines.append(f"  • {r}  ×{cnt}")
            # 简单建议
            lines.append("- 处理建议:")
            if any(k in self.error_type_counts for k in ["网络连接错误", "HTTP状态错误"]):
                lines.append("  • 检查网络连接/代理，适当增大超时时间，必要时重试")
            if self.error_type_counts.get("文件权限错误", 0) > 0:
                lines.append("  • 检查输出目录/文件权限，使用有写权限的路径运行程序")
            if self.error_type_counts.get("URL格式错误", 0) > 0:
                lines.append("  • 清洗URL字段，确保为有效的HTTP(S)链接")
            if self.error_type_counts.get("URL无效", 0) > 0:
                lines.append("  • 清理或修复数据中的无效URL（空值、'nan'、非http/https），必要时跳过该行")
            with open(self.summary_log_path, 'a', encoding='utf-8') as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            logger.error(f"写入错误汇总日志失败: {e}")

    def clean_logs(self, retention_days=7):
        """
        清理日志目录内超过保留天数的日志文件；retention_days<=0 表示清理全部
        返回删除的文件数量
        """
        try:
            log_dir = Path(ERROR_LOG_CONFIG['error_log_dir']) if 'error_log_dir' in ERROR_LOG_CONFIG else Path('logs')
            if not log_dir.exists():
                return 0
            removed = 0
            now = time.time()
            for fp in log_dir.glob('*errors*.log'):
                if retention_days <= 0:
                    fp.unlink(missing_ok=True)
                    removed += 1
                else:
                    if (now - fp.stat().st_mtime) > (retention_days * 86400):
                        fp.unlink(missing_ok=True)
                        removed += 1
            # 兼容清理下载错误txt
            for fp in log_dir.glob('download_errors_*.txt'):
                if retention_days <= 0 or (now - fp.stat().st_mtime) > (retention_days * 86400):
                    fp.unlink(missing_ok=True)
                    removed += 1
            return removed
        except Exception as e:
            logger.error(f"清理日志失败: {e}")
            return 0

    def _init_error_log(self):
        """初始化错误日志文件"""
        try:
            # 创建错误日志目录
            error_log_dir = Path(ERROR_LOG_CONFIG['error_log_dir'])
            error_log_dir.mkdir(parents=True, exist_ok=True)

            # 生成错误日志文件名
            timestamp = datetime.now().strftime(ERROR_LOG_CONFIG['timestamp_format'])
            filename = ERROR_LOG_CONFIG['error_log_filename_template'].format(timestamp=timestamp)
            self.error_log_file = error_log_dir / filename

            # 写入文件头
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                f.write(f"下载错误日志 - 开始时间: {datetime.now().strftime(ERROR_LOG_CONFIG['log_timestamp_format'])}\n")
                f.write("=" * 80 + "\n\n")

            logger.info(f"错误日志文件已创建: {self.error_log_file}")

        except Exception as e:
            logger.error(f"创建错误日志文件失败: {e}")
            self.error_log_file = None

    def _log_download_error(self, row_num, row_data, file_path, error_msg):
        """记录下载错误到文件"""
        if not self.error_log_file:
            return

        try:
            with self._error_log_lock:
                self.error_count += 1

                # 准备错误信息
                timestamp = datetime.now().strftime(ERROR_LOG_CONFIG['log_timestamp_format'])
                url = str(row_data.get('image_url', 'N/A'))
                if len(url) > 100:
                    url = url[:100] + '...'

                error_line = ERROR_LOG_CONFIG['error_log_format'].format(
                    timestamp=timestamp,
                    row_num=row_num,
                    account_id=row_data.get('account_id', 'N/A'),
                    user_id=row_data.get('user_id', 'N/A'),
                    company_id=row_data.get('company_id', 'N/A'),
                    create_time=row_data.get('create_time', 'N/A'),
                    url=url,
                    file_path=file_path,
                    error=str(error_msg)
                )

                # 写入错误日志文件
                with open(self.error_log_file, 'a', encoding='utf-8') as f:
                    f.write(error_line + '\n')

        except Exception as e:
            logger.error(f"写入错误日志失败: {e}")

    def get_error_log_summary(self):
        """获取错误日志摘要"""
        return {
            'error_count': self.error_count,
            'error_log_file': str(self.error_log_file) if self.error_log_file else None
        }

    def detect_file_format(self, file_path):
        """
        检测文件格式

        Args:
            file_path (str): 文件路径

        Returns:
            str: 文件格式类型 ('excel', 'csv', 'unknown')
        """
        file_extension = Path(file_path).suffix.lower()
        return self.supported_formats.get(file_extension, 'unknown')

    def load_data_file(self, file_path):
        """
        根据文件格式加载数据

        Args:
            file_path (str): 文件路径

        Returns:
            pandas.DataFrame or None: 加载的数据
        """
        try:
            file_format = self.detect_file_format(file_path)
            logger.info(f"检测到文件格式: {file_format} - {file_path}")

            if file_format == 'excel':
                df = pd.read_excel(file_path)
            elif file_format == 'csv':
                # 尝试不同的编码格式
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.info(f"成功使用编码 {encoding} 读取CSV文件")
                        break
                    except UnicodeDecodeError:
                        continue

                if df is None:
                    raise ValueError(f"无法读取CSV文件，尝试了编码: {encodings}")
            else:
                raise ValueError(f"不支持的文件格式: {file_format}")

            logger.info(f"文件加载成功: {file_path}, 数据行数: {len(df)}")
            return df

        except Exception as e:
            logger.error(f"文件加载失败: {file_path}, 错误: {e}")
            return None

    def validate_data_fields(self, df, file_path):
        """
        验证数据字段是否完整

        Args:
            df (pandas.DataFrame): 数据框
            file_path (str): 文件路径

        Returns:
            bool: 验证是否通过
        """
        try:
            missing_fields = [field for field in self.required_fields if field not in df.columns]
            if missing_fields:
                logger.error(f"文件 {file_path} 缺少必需字段: {missing_fields}")
                logger.info(f"文件现有字段: {df.columns.tolist()}")
                return False

            logger.info(f"文件 {file_path} 字段验证通过")
            return True

        except Exception as e:
            logger.error(f"字段验证失败: {file_path}, 错误: {e}")
            return False

    def process_single_file(self, input_file_path, output_folder=None, account_filter=None):
        """
        处理单个文件

        Args:
            input_file_path (str): 输入文件路径
            output_folder (str): 输出文件夹路径

        Returns:
            bool: 处理是否成功
        """
        try:
            logger.info(f"开始处理文件: {input_file_path}")

            # 加载数据
            df = self.load_data_file(input_file_path)
            if df is None:
                return False

            # 验证字段
            if not self.validate_data_fields(df, input_file_path):
                return False

            # 提取所需字段
            processed_df = df[self.required_fields].copy()

            # 排序
            processed_df = processed_df.sort_values(
                by=SORT_CONFIG['sort_by'],
                ascending=SORT_CONFIG['ascending']
            ).reset_index(drop=True)

            # 可选：按 account_id 过滤
            if account_filter:
                filt = {str(a).strip() for a in account_filter}
                processed_df = processed_df[processed_df['account_id'].astype(str).isin(filt)].reset_index(drop=True)
                logger.info(f"应用账户筛选，共保留 {len(processed_df)} 行")

            # 添加file_name列
            processed_df['file_name'] = ''

            # 生成输出路径
            input_path = Path(input_file_path)
            if output_folder:
                output_folder_path = Path(output_folder)
                output_folder_path.mkdir(parents=True, exist_ok=True)
                output_file_path = output_folder_path / f"{input_path.stem}_updated.xlsx"
                #     
                #  
                base_folder = output_folder_path
            else:
                # 默认使用配置文件中指定的输出文件夹
                from app.config import DEFAULT_OUTPUT_FOLDER
                output_folder_path = Path(DEFAULT_OUTPUT_FOLDER)
                output_folder_path.mkdir(parents=True, exist_ok=True)
                output_file_path = output_folder_path / f"{input_path.stem}_updated.xlsx"
                base_folder = output_folder_path

            # 创建基础文件夹
            base_folder.mkdir(parents=True, exist_ok=True)

            # 显示开始下载的提示（绝对路径）
            output_abs_path = output_folder_path.resolve()
            base_folder_abs_path = base_folder.resolve()
            logger.info(f"📁 输出目录: {output_abs_path}")
            logger.info(f"💾 图片将保存在: {base_folder_abs_path}")
            logger.info(f"🚀 开始下载 {len(processed_df)} 张图片...")

            # 下载图片
            success_count = self.download_images_for_dataframe(processed_df, base_folder)

            # 保存更新后的文件
            processed_df.to_excel(output_file_path, index=False)

            # 显示完成信息（使用绝对路径）
            output_file_abs_path = output_file_path.resolve()

            logger.info("=" * 60)
            logger.info("✅ 文件处理完成！")
            logger.info("=" * 60)
            logger.info(f"📁 输出目录: {output_abs_path}")
            logger.info(f"📄 数据文件: {output_file_abs_path}")
            logger.info(f"🖼️  图片目录: {base_folder_abs_path}")
            logger.info(f"📊 成功下载: {success_count}/{len(processed_df)} 张图片")

            # 显示错误日志摘要
            error_summary = self.get_error_log_summary()
            if error_summary['error_count'] > 0:
                logger.info(f"❌ 下载错误: {error_summary['error_count']} 个")
                logger.info(f"📋 错误日志: {error_summary['error_log_file']}")
            else:
                logger.info("✅ 所有图片下载成功，无错误记录")
            logger.info("=" * 60)

            # 写入错误汇总日志并提示详细日志位置
            self._write_error_summary()
            try:
                logger.info(f"详细错误日志: {getattr(self, 'detailed_log_path', None)}")
                logger.info(f"错误汇总日志: {getattr(self, 'summary_log_path', None)}")
            except Exception:
                pass

            return True

        except Exception as e:
            logger.error(f"文件处理失败: {input_file_path}, 错误: {e}")
            return False

    def download_images_for_dataframe(self, df, base_folder):
        """
        为数据框下载图片（根据配置选择单线程或多线程）

        Args:
            df (pandas.DataFrame): 数据框

        #     
        #  URL  
            base_folder (Path): 基础文件夹路径

        Returns:
            int: 成功下载的图片数量
        """
        # 统计无效URL跳过数量（当前下载批次）
        self.invalid_url_skipped = 0

        if self.multithreading_enabled and len(df) > 1:
            logger.info("使用多线程下载模式")
            return self.download_images_for_dataframe_multithreaded(df, base_folder)
        else:
            logger.info("使用单线程下载模式")
            return self.download_images_for_dataframe_singlethreaded(df, base_folder)

    def download_images_for_dataframe_singlethreaded(self, df, base_folder):
        """
        单线程为数据框下载图片

        Args:
            df (pandas.DataFrame): 数据框
            base_folder (Path): 基础文件夹路径

        Returns:
            int: 成功下载的图片数量
        """
        success_count = 0
        total_count = len(df)

        # 创建文件夹结构
        folders_created = set()

        for index, row in df.iterrows():
            try:
                # 生成文件名（时间戳 + URL片段 + 可选title，带长度与字符安全处理）
                filename = self.build_output_filename(row)

                # 生成多级文件夹路径：{company_id}/{account_id}/{user_id}
                company_id = str(row.get('company_id', 'unknown'))
                account_id = str(row.get('account_id', 'unknown'))
                user_id = str(row.get('user_id', 'unknown'))
                folder_path = base_folder / company_id / account_id / user_id

                # 创建文件夹
                key = f"{company_id}/{account_id}/{user_id}"
                if key not in folders_created:
                    folder_path.mkdir(parents=True, exist_ok=True)
                    folders_created.add(key)

                file_path = folder_path / filename

                # URL有效性校验，若无效则记录并跳过
                url_val = row.get('image_url', '')
                if not self.is_valid_http_url(url_val):
                    err_type = "URL无效"
                    err = ValueError(f"无效URL: {url_val}")
                    # 简要错误日志
                    self._log_download_error(index + 1, row, str(file_path), str(err))
                    # 详细错误日志与统计
                    row_data = {
                        'account_id': row.get('account_id', 'N/A'),
                        'user_id': row.get('user_id', 'N/A'),
                        'company_id': row.get('company_id', 'N/A'),
                        'image_url': url_val,
                        'title': row.get('title', ''),
                        'create_time': row.get('create_time', 'N/A')
                    }
                    context = {
                        'excel_row': (index + 2),
                        'row': index + 1,
                        'file_path': str(file_path),
                        'row_data': row_data,
                    }
                    self._log_detailed_error(err_type, context, err)
                    self._accumulate_error_stats(err_type, err)
                    logger.error(f"[URL无效] 下载跳过 - 第 {index + 1} 行, URL: {url_val}")
                    df.at[index, 'file_name'] = ''
                    self.invalid_url_skipped += 1
                    # 下一行
                    continue

                # 重复文件检查：同名存在则跳过下载
                if file_path.exists():
                    logger.info(f"已存在同名文件，跳过下载: {file_path}")
                    df.at[index, 'file_name'] = filename
                    continue

                # 下载图片
                if self.download_image(url_val, str(file_path)):
                    df.at[index, 'file_name'] = filename
                    success_count += 1
                else:
                    df.at[index, 'file_name'] = ''

                # 添加延迟
                time.sleep(DOWNLOAD_CONFIG['delay_between_requests'])

                # 显示进度
                progress = (index + 1) / total_count * 100
                if (index + 1) % 10 == 0 or index == total_count - 1:
                    logger.info(f"下载进度: {index + 1}/{total_count} ({progress:.1f}%)")

            except Exception as e:
                # 记录错误到日志文件
                self._log_download_error(index + 1, row, str(file_path), str(e))

                # 错误分类与详细日志
                err_type = self._classify_exception(e)
                row_data = {
                    'account_id': row.get('account_id', 'N/A'),
                    'user_id': row.get('user_id', 'N/A'),
                    'company_id': row.get('company_id', 'N/A'),
                    'image_url': row.get('image_url', 'N/A'),
                    'title': row.get('title', ''),
                    'create_time': row.get('create_time', 'N/A')
                }
                context = {
                    'excel_row': (index + 2),  # Excel 实际行号（含表头）
                    'row': index + 1,          # 数据行号（1-based）
                    'file_path': str(file_path),
                    'row_data': row_data,
                }
                self._log_detailed_error(err_type, context, e)
                self._accumulate_error_stats(err_type, e)

                # 控制台输出（带错误类型）
                error_info = {
                    '行号': index + 1,
                    '账户ID': row.get('account_id', 'N/A'),
                    '用户ID': row.get('user_id', 'N/A'),
                    '公司ID': row.get('company_id', 'N/A'),
                    '图片URL': row.get('image_url', 'N/A')[:100] + '...' if len(str(row.get('image_url', ''))) > 100 else row.get('image_url', 'N/A'),
                    '错误': f'[{err_type}] {str(e)}'
                }
                logger.error(f"[{err_type}] 下载失败 - 第 {index + 1} 行数据:")
                for key, value in error_info.items():
                    logger.error(f"  {key}: {value}")
                df.at[index, 'file_name'] = ''

        logger.info(f"单线程下载完成，成功: {success_count}/{total_count}，无效URL跳过: {self.invalid_url_skipped}")
        return success_count

    def download_images_for_dataframe_multithreaded(self, df, base_folder):
        """
        多线程为数据框下载图片

        Args:
            df (pandas.DataFrame): 数据框
            base_folder (Path): 基础文件夹路径

        Returns:
            int: 成功下载的图片数量
        """
        success_count = 0

        # 创建文件夹结构
        folders_created = set()

        # 准备下载任务
        download_tasks = []

        for index, row in df.iterrows():
            try:
                # 生成文件名（时间戳 + URL片段 + 可选title，带长度与字符安全处理）
                filename = self.build_output_filename(row)

                # 生成文件夹路径
                # 生成多级文件夹路径：{company_id}/{account_id}/{user_id}
                company_id = str(row.get('company_id', 'unknown'))
                account_id = str(row.get('account_id', 'unknown'))
                user_id = str(row.get('user_id', 'unknown'))
                folder_path = base_folder / company_id / account_id / user_id

                # 创建文件夹（线程安全）
                key = f"{company_id}/{account_id}/{user_id}"
                with self._folders_created_lock:
                    if key not in folders_created:
                        folder_path.mkdir(parents=True, exist_ok=True)
                        folders_created.add(key)

                file_path = folder_path / filename

                # URL有效性校验，若无效则记录并跳过
                url_val = row.get('image_url', '')
                if not self.is_valid_http_url(url_val):
                    err_type = "URL无效"
                    err = ValueError(f"无效URL: {url_val}")
                    self._log_download_error(index + 1, row, str(file_path), str(err))
                    row_data = {
                        'account_id': row.get('account_id', 'N/A'),
                        'user_id': row.get('user_id', 'N/A'),
                        'company_id': row.get('company_id', 'N/A'),
                        'image_url': url_val,
                        'title': row.get('title', ''),
                        'create_time': row.get('create_time', 'N/A')
                    }
                    context = {
                        'excel_row': (index + 2),
                        'row': index + 1,
                        'file_path': str(file_path),
                        'row_data': row_data,
                    }
                    self._log_detailed_error(err_type, context, err)
                    self._accumulate_error_stats(err_type, err)
                    logger.error(f"[URL无效] 下载跳过 - 第 {index + 1} 行, URL: {url_val}")
                    df.at[index, 'file_name'] = ''
                    self.invalid_url_skipped += 1
                    continue

                # 重复文件检查：同名存在则跳过下载
                if file_path.exists():
                    logger.info(f"已存在同名文件，跳过下载: {file_path}")
                    df.at[index, 'file_name'] = filename
                    continue

                # 添加到下载任务列表
                download_tasks.append({
                    'index': index,
                    'url': url_val,
                    'file_path': str(file_path),
                    'filename': filename
                })

            except Exception as e:
                logger.error(f"准备第 {index + 1} 行下载任务时出错: {e}")
                df.at[index, 'file_name'] = ''

        if not download_tasks:
            logger.info("没有需要下载的图片")
            return 0

        logger.info(f"开始多线程下载 {len(download_tasks)} 个图片，使用 {self.max_threads} 个线程")

        # 使用线程池执行下载
        completed_count = 0
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # 提交所有下载任务
            future_to_task = {
                executor.submit(self._download_single_image_task, task): task
                for task in download_tasks
            }

            # 处理完成的任务
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                completed_count += 1

                try:
                    download_success = future.result()
                    if download_success:
                        df.at[task['index'], 'file_name'] = task['filename']
                        with self._success_count_lock:
                            success_count += 1
                    else:
                        df.at[task['index'], 'file_name'] = ''

                except Exception as e:
                    # 获取对应行的数据信息
                    row = df.iloc[task['index']]

                    # 记录错误到日志文件
                    self._log_download_error(task['index'] + 1, row, task['file_path'], str(e))

                    # 错误分类与详细日志
                    err_type = self._classify_exception(e)
                    row_data = {
                        'account_id': row.get('account_id', 'N/A'),
                        'user_id': row.get('user_id', 'N/A'),
                        'company_id': row.get('company_id', 'N/A'),
                        'image_url': row.get('image_url', 'N/A'),
                        'title': row.get('title', ''),
                        'create_time': row.get('create_time', 'N/A')
                    }
                    context = {
                        'excel_row': (task['index'] + 2),  # Excel 实际行号
                        'row': task['index'] + 1,          # 数据行号（1-based）
                        'file_path': task['file_path'],
                        'row_data': row_data,
                    }
                    self._log_detailed_error(err_type, context, e)
                    self._accumulate_error_stats(err_type, e)

                    error_info = {
                        '行号': task['index'] + 1,
                        '账户ID': row.get('account_id', 'N/A'),
                        '用户ID': row.get('user_id', 'N/A'),
                        '公司ID': row.get('company_id', 'N/A'),
                        '图片URL': row.get('image_url', 'N/A')[:100] + '...' if len(str(row.get('image_url', ''))) > 100 else row.get('image_url', 'N/A'),
                        '目标文件': task['file_path'],
                        '错误': f'[{err_type}] {str(e)}'
                    }
                    logger.error(f"[{err_type}] 多线程下载失败 - 第 {task['index'] + 1} 行数据:")
                    for key, value in error_info.items():
                        logger.error(f"  {key}: {value}")
                    df.at[task['index'], 'file_name'] = ''

                # 显示进度（线程安全）
                with self._progress_lock:
                    progress = completed_count / len(download_tasks) * 100
                    if completed_count % 10 == 0 or completed_count == len(download_tasks):
                        logger.info(f"下载进度: {completed_count}/{len(download_tasks)} ({progress:.1f}%)")

        logger.info(f"多线程下载完成，成功: {success_count}/{len(download_tasks)}，无效URL跳过: {self.invalid_url_skipped}")
        return success_count

    def _download_single_image_task(self, task):
        """
        单个图片下载任务（用于多线程）

        Args:
            task (dict): 包含下载信息的字典

        Returns:
            bool: 下载是否成功
        """
        try:
            return self.download_image(task['url'], task['file_path'], timeout=self.download_timeout)
        except Exception as e:
            # 这里的错误信息会在上层的多线程处理中显示更详细的信息
            # 这里只记录基本的下载失败信息
            logger.debug(f"下载图片失败: {task['file_path']}, 错误: {e}")
            return False

    def set_multithreading_enabled(self, enabled):
        """设置是否启用多线程下载"""
        self.multithreading_enabled = enabled
        logger.info(f"多线程下载已{'启用' if enabled else '禁用'}")

    def set_max_threads(self, max_threads):
        """设置最大线程数"""
        if max_threads < 1:
            max_threads = 1
        elif max_threads > 20:  # 限制最大线程数
            max_threads = 20
        self.max_threads = max_threads
        logger.info(f"最大下载线程数设置为: {max_threads}")

    def set_download_timeout(self, timeout):
        """设置下载超时时间"""
        if timeout < 10:
            timeout = 10
        elif timeout > 300:  # 限制最大超时时间
            timeout = 300
        self.download_timeout = timeout
        logger.info(f"下载超时时间设置为: {timeout} 秒")

    def get_multithreading_status(self):
        """获取多线程配置状态"""
        return {
            'enabled': self.multithreading_enabled,
            'max_threads': self.max_threads,
            'download_timeout': self.download_timeout
        }

    def timestamp_to_filename(self, timestamp):
        """将时间戳转换为文件名格式"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            filename = dt.strftime(FILENAME_CONFIG['time_format'])
            return filename
        except Exception as e:
            logger.error(f"时间戳转换失败: {timestamp}, 错误: {e}")
            return str(timestamp)


    def sanitize_filename_component(self, text, max_len=None):
        """
        将任意文本转为适于文件名的安全片段：
        - 移除控制字符
        - 替换非法字符 / \ : * ? " < > | & % + # 空格 等为下划线
        - 可选长度截断
        - 去除首尾下划线，合并重复下划线
        保留中文、字母、数字、点、短横线、下划线
        """
        import re
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

    def build_output_filename(self, row, max_total_len=200):
        """
        基于时间戳、完整URL、可选title生成最终文件名：
        格式：{时间戳}_{处理后的URL}_{处理后的title}.{扩展名}
        - URL 使用 url 字段来构建文件名
        - title 不存在或为空则跳过
        - 总长度不超过 max_total_len（含扩展名）
        """
        try:
            base = self.timestamp_to_filename(row.get('create_time'))
            # 使用 url 字段来构建文件名
            url = row.get('url', '')
            title = row.get('title', '')
            # 获取扩展名时仍使用 image_url（因为这是实际下载的图片URL）
            ext = self.get_image_extension(row.get('image_url', ''))

            # 去掉协议前缀（http://、https:// 等）后再做清洗
            if url:
                import re
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
            # 获取扩展名时使用 image_url（实际下载URL），文件名使用 url 字段
            ext = self.get_image_extension(row.get('image_url', ''))
            return f"{base}{ext}"

    def get_image_extension(self, url):
        """从URL获取图片扩展名"""
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            extension = os.path.splitext(path)[1]
            return extension if extension else FILENAME_CONFIG['default_extension']
        except:
            return FILENAME_CONFIG['default_extension']

    def download_image(self, url, file_path, timeout=None):
        """下载单个图片"""
        if timeout is None:
            timeout = DOWNLOAD_CONFIG['timeout']

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

            return True

        except Exception as e:
            err_type = self._classify_exception(e)
            logger.error(f"[{err_type}] 图片下载失败: {url}, 错误: {e}")
            # 详细日志与统计
            context = {
                'url': url,
                'file_path': file_path,
                'timeout': timeout,
            }
            self._log_detailed_error(err_type, context, e)
            self._accumulate_error_stats(err_type, e)
            return False


    def is_valid_http_url(self, url: str) -> bool:
        """
        校验URL有效性：非空、非'nan'/'none'/'null'，http/https协议且含主机。
        """
        try:
            if url is None:
                return False
            s = str(url).strip()
            if not s:
                return False
            if s.lower() in {"nan", "none", "null"}:
                return False
            parsed = urlparse(s)
            if parsed.scheme not in {"http", "https"}:
                return False
            if not parsed.netloc:
                return False
            return True
        except Exception:
            return False

    def find_data_files(self, folder_path, recursive=False):
        """
        查找文件夹中的数据文件

        Args:
            folder_path (str): 文件夹路径
            recursive (bool): 是否递归搜索

        Returns:
            list: 找到的文件路径列表
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            logger.error(f"文件夹不存在: {folder_path}")
            return []

        files = []
        patterns = ['*.xlsx', '*.xls', '*.csv']

        for pattern in patterns:
            if recursive:
                files.extend(folder_path.rglob(pattern))
            else:
                files.extend(folder_path.glob(pattern))

        file_paths = [str(f) for f in files]
        logger.info(f"在文件夹 {folder_path} 中找到 {len(file_paths)} 个数据文件")

        return file_paths

    def process_batch_files(self, input_folder, output_folder=None, recursive=False, account_filter=None):
        """
        批量处理文件夹中的文件

        Args:
            input_folder (str): 输入文件夹路径
            output_folder (str): 输出文件夹路径
            recursive (bool): 是否递归搜索

        Returns:
            dict: 处理结果统计
        """
        logger.info("=" * 60)
        logger.info("开始批量处理文件")
        logger.info("=" * 60)

        # 显示输出目录（绝对路径）
        if output_folder:
            output_path = Path(output_folder).resolve()
        else:
            from app.config import DEFAULT_OUTPUT_FOLDER
            output_path = Path(DEFAULT_OUTPUT_FOLDER).resolve()

        logger.info(f"📁 输出目录: {output_path}")
        logger.info(f"💾 所有文件将保存在: {output_path}")

        # 查找文件
        file_paths = self.find_data_files(input_folder, recursive)

        if not file_paths:
            logger.warning(f"在文件夹 {input_folder} 中没有找到支持的数据文件")
            return {'total': 0, 'success': 0, 'failed': 0}

        # 处理统计
        total_files = len(file_paths)
        success_count = 0
        failed_count = 0

        logger.info(f"🚀 找到 {total_files} 个文件，开始处理...")

        for i, file_path in enumerate(file_paths, 1):
            logger.info(f"处理文件 {i}/{total_files}: {file_path}")

            if self.process_single_file(file_path, output_folder, account_filter=account_filter):
                success_count += 1
            else:
                failed_count += 1

        # 输出统计结果
        logger.info("=" * 60)
        logger.info("✅ 批量处理完成！")
        logger.info("=" * 60)
        logger.info(f"📊 处理统计:")
        logger.info(f"  总文件数: {total_files}")
        logger.info(f"  成功处理: {success_count}")
        logger.info(f"  处理失败: {failed_count}")
        logger.info(f"\n📁 文件保存位置: {output_path}")
        logger.info(f"🖼️  图片目录结构: {output_path}/company_id/account_id/user_id/")
        logger.info("=" * 60)

        # 写入一次汇总日志，并提示位置
        self._write_error_summary()
        try:
            logger.info(f"详细错误日志: {getattr(self, 'detailed_log_path', None)}")
            logger.info(f"错误汇总日志: {getattr(self, 'summary_log_path', None)}")
        except Exception:
            pass

        return {
            'total': total_files,
            'success': success_count,
            'failed': failed_count
        }

