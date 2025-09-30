#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 数据处理和图片下载工具（app 包内）
"""

# 文件路径配置
INPUT_EXCEL_FILE = "数据样例.xlsx"
OUTPUT_EXCEL_FILE = "数据样例_updated.xlsx"

# 支持的文件格式
SUPPORTED_FORMATS = {
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.csv': 'csv'
}

# 批量处理配置
BATCH_CONFIG = {
    # 是否启用批量处理模式
    'enable_batch_mode': False,

    # 批量处理的文件夹路径
    'batch_folder_path': './data',

    # 输出文件夹路径
    'output_folder_path': './output',

    # 是否递归搜索子文件夹
    'recursive_search': False
}

# 必需的数据字段
REQUIRED_FIELDS = [
    'account_id',
    'company_id',
    'image_url',
    'url',
    'title',
    'user_id',
    'create_time'
]

# 下载配置
DOWNLOAD_CONFIG = {
    # 请求超时时间（秒）
    'timeout': 30,

    # 请求间隔时间（秒），避免请求过快
    'delay_between_requests': 0.5,

    # 重试次数
    'max_retries': 3,

    # 用户代理字符串
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 多线程下载配置
MULTITHREADING_CONFIG = {
    # 是否启用多线程下载
    'enable_multithreading': True,

    # 最大下载线程数
    'max_download_threads': 6,

    # 单个文件下载超时时间（秒）
    'download_timeout': 60,

    # 线程池关闭等待时间（秒）
    'shutdown_timeout': 30
}

# 文件夹命名配置
FOLDER_NAME_TEMPLATE = "{company_id}_{account_id}_{user_id}"

# 文件命名配置
FILENAME_CONFIG = {
    # 时间格式（用于文件名）：月_日 空格 时-分-秒
    'time_format': "%m_%d %H-%M-%S",

    # 默认文件扩展名（当无法从URL获取时）
    'default_extension': '.jpg'
}

# 日志配置
LOG_CONFIG = {
    'log_file': 'logs/download.log',
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(levelname)s - %(message)s',
    'date_format': '%m/%d %H:%M:%S'
}

# 错误日志配置
ERROR_LOG_CONFIG = {
    # 错误日志文件路径模板
    'error_log_dir': 'logs',
    'error_log_filename_template': 'download_errors_{timestamp}.txt',

    # 错误日志格式
    'error_log_format': '{timestamp} | 行号:{row_num} | 账户ID:{account_id} | 用户ID:{user_id} | 公司ID:{company_id} | 创建时间戳:{create_time} | URL:{url} | 文件:{file_path} | 错误:{error}',

    # 时间戳格式
    'timestamp_format': '%Y%m%d_%H%M%S',
    'log_timestamp_format': '%Y-%m-%d %H:%M:%S'
}

# 数据排序配置
SORT_CONFIG = {
    # 排序字段和顺序
    'sort_by': ['account_id', 'create_time'],
    'ascending': [True, True]  # True为升序，False为降序
}

