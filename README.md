# 数据处理和图片下载工具

这是一个Python工具，用于从Excel文件中提取数据，按指定规则排序，并批量下载图片文件。

## 功能特性

- ✅ 从Excel文件提取指定字段数据
- ✅ 按account_id分组，组内按create_time正序排序
- ✅ 批量下载图片并按时间格式命名
- ✅ 创建以company_id_account_id_user_id命名的文件夹
- ✅ 更新Excel文件添加file_name列
- ✅ 详细的日志记录
- ✅ 可配置的参数设置

## 环境要求

- Python 3.7+
- 依赖库：pandas, openpyxl, requests

## 安装步骤

1. 创建虚拟环境（推荐）：
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

2. 安装依赖：
```bash
pip install pandas openpyxl requests
```

## 使用方法

### 快速开始

1. 将Excel数据文件命名为 `数据样例.xlsx` 并放在项目目录中
2. 运行处理脚本：
```bash
python run_processor.py
```

### 自定义使用

```python
from data_processor import DataProcessor

# 创建处理器实例
processor = DataProcessor("你的数据文件.xlsx")

# 运行完整流程
processor.run("输出文件.xlsx")
```

## 配置说明

可以通过修改 `config.py` 文件来自定义各种参数：

### 文件路径配置
```python
INPUT_EXCEL_FILE = "数据样例.xlsx"
OUTPUT_EXCEL_FILE = "数据样例_updated.xlsx"
```

### 下载配置
```python
DOWNLOAD_CONFIG = {
    'timeout': 30,                    # 请求超时时间
    'delay_between_requests': 0.5,    # 请求间隔时间
    'max_retries': 3,                 # 重试次数
    'user_agent': '...'               # 用户代理字符串
}
```

### 文件命名配置
```python
FILENAME_CONFIG = {
    'time_format': "%m%d%H%M%S",      # 时间格式：月日小时分钟秒
    'default_extension': '.jpg'        # 默认文件扩展名
}
```

## 输入数据格式

Excel文件必须包含以下字段：
- `account_id`: 账户ID
- `company_id`: 公司ID
- `image_url`: 图片URL
- `title`: 标题
- `user_id`: 用户ID
- `create_time`: 创建时间（Unix时间戳）

## 输出结果

### 文件夹结构
```
项目目录/
├── 17225833017123_27242246776103_17228554645593/
│   ├── 09281430262.webp
│   ├── 09281430262.webp
│   └── 09281430263.webp
├── 17225833017123_27491927174429_17557384532482/
│   └── 09281430230.webp
├── 数据样例_updated.xlsx
└── download.log
```

### 更新后的Excel文件
原始数据 + 新增的 `file_name` 列，包含对应的图片文件名。

## 日志文件

程序运行时会生成 `download.log` 文件，记录：
- 数据处理进度
- 图片下载状态
- 错误信息
- 统计信息

## 错误处理

- 网络连接失败：自动重试
- 图片下载失败：记录错误并继续处理其他图片
- 数据格式错误：详细错误提示
- 文件权限问题：清晰的错误信息

## 注意事项

1. 确保有足够的磁盘空间存储下载的图片
2. 网络连接稳定，避免下载中断
3. 图片URL必须是有效的直链地址
4. 时间戳格式必须是Unix时间戳（秒）

## 故障排除

### 常见问题

**Q: 提示缺少依赖库**
A: 运行 `pip install pandas openpyxl requests`

**Q: 图片下载失败**
A: 检查网络连接和图片URL是否有效

**Q: 时间格式转换错误**
A: 确认create_time字段是有效的Unix时间戳

**Q: 文件夹创建失败**
A: 检查目录权限和磁盘空间

### 查看详细错误
查看 `download.log` 文件获取详细的错误信息和处理进度。

## 技术实现

- 使用pandas进行数据处理和Excel文件操作
- 使用requests库进行HTTP图片下载
- 支持多种图片格式（jpg, png, webp等）
- 异常处理和错误恢复机制
- 详细的日志记录系统

## 许可证

MIT License
