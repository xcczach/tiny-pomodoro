#!/usr/bin/env pwsh
<##
  build.ps1 —— Windows PowerShell one-click packager for Tiny Pomodoro
  功能与 build.sh 等效：
  1. 创建/激活虚拟环境
  2. 安装依赖 + PyInstaller
  3. 清理旧产物
  4. 打包为单文件 GUI 可执行
  5. 清理临时目录

  用法（推荐在 PowerShell 7+）：
    PS> ./build.ps1

  如需自定义 Python 版本或 App 名称，编辑脚本顶部变量即可。
##>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# 避免中文输出乱码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# === 可自行调整的变量 ===
$PY_CMD   = 'python'          # 或改成 'py -3.12'
$VENV_DIR = 'tiny-pomodoro'
$APP_NAME = 'Tiny Pomodoro'
$ENTRY    = 'main.py'
$ICON     = 'assets/icon.png'
$ASSETS   = 'assets/*;assets' # Windows 下分隔符必须是分号

Write-Host "Tiny Pomodoro build script (PowerShell)" -ForegroundColor Cyan

# 1. 创建 / 激活虚拟环境（如果不存在）
if (-not (Test-Path $VENV_DIR)) {
    & $PY_CMD -m venv $VENV_DIR
}

# 在当前脚本进程中激活 venv
. "$VENV_DIR\Scripts\Activate.ps1"

# 2. 安装依赖
if (Test-Path 'requirements.txt') {
    pip install -r requirements.txt
}
pip install -U pyinstaller

# 3. 清理旧产物（可选）
Remove-Item -Recurse -Force build, dist, "$APP_NAME.spec" -ErrorAction SilentlyContinue

# 4. 打包
$opts = @(
    '--name', "$APP_NAME",
    '--onefile',
    '--windowed',
    '--icon', $ICON,
    '--add-data', $ASSETS,
    $ENTRY
)
pyinstaller @opts

# 5. 清理临时文件
Remove-Item -Recurse -Force build, "$VENV_DIR", "$APP_NAME.spec" -ErrorAction SilentlyContinue

Write-Host "Done! Executable located at dist/${APP_NAME}.exe" -ForegroundColor Green 