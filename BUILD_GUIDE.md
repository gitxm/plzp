# 构建指南

本项目支持通过 GitHub Actions 自动构建 Windows 和 macOS 可执行文件。

## 通过 GitHub Actions 自动构建

### 方法 1: 创建 Release Tag

1. 提交代码到 GitHub
2. 创建一个新的 tag（版本号）:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. GitHub Actions 会自动开始构建
4. 构建完成后，会自动创建 Release 并上传可执行文件

### 方法 2: 手动触发构建

1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择 "Build Executables" 工作流
4. 点击 "Run workflow" 按钮
5. 选择分支并点击 "Run workflow"
6. 等待构建完成
7. 在 "Artifacts" 中下载构建好的文件

## 本地构建

### 前置要求

```bash
pip install pyinstaller
```

### 构建步骤

#### 使用自动化脚本（推荐）

```bash
python build_local.py
```

按照提示操作即可。

#### 手动构建

**Windows:**
```bash
pyinstaller --onefile --name image-downloader-windows --add-data "app;app" main.py
```

**macOS/Linux:**
```bash
pyinstaller --onefile --name image-downloader-macos --add-data "app:app" main.py
```

### 构建输出

构建完成后，可执行文件位于 `dist/` 目录：
- Windows: `dist/image-downloader-windows.exe`
- macOS: `dist/image-downloader-macos`

## 分发可执行文件

构建好的可执行文件可以直接分发给用户，用户无需安装 Python 环境即可运行。

### 注意事项

1. **Windows 版本**只能在 Windows 系统上运行
2. **macOS 版本**只能在 macOS 系统上运行
3. 首次运行时，macOS 可能需要在"系统偏好设置 > 安全性与隐私"中允许运行
4. 可执行文件体积较大（约 50-100MB），因为包含了 Python 运行时和所有依赖库

## 故障排除

### 构建失败

1. 确保所有依赖都在 `requirements.txt` 中
2. 检查 Python 版本（建议使用 3.11）
3. 清理旧的构建文件后重试

### 运行时错误

1. 确保所有数据文件（如配置文件）都被正确打包
2. 检查文件路径是否正确（使用相对路径）
3. 查看错误日志获取详细信息

## GitHub Actions 配置说明

工作流文件位于 `.github/workflows/build.yml`

### 触发条件

- 推送 tag（以 `v` 开头）
- 手动触发（workflow_dispatch）

### 构建矩阵

- Windows (windows-latest)
- macOS (macos-latest)

### 输出

- Artifacts（每次构建）
- Release（仅 tag 触发时）

