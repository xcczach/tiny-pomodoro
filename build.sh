#!/usr/bin/env bash
# build.sh —— Windows 平台（Git Bash）一键打包 Tiny Pompdoro
set -euo pipefail                  # 出错即停 & 抓未定义变量

# === 可自行调整的变量 ===
PY_CMD="python"                    # 或改成 py -3.12
VENV_DIR="tiny-pomodoro"
APP_NAME="Tiny Pomodoro"
ENTRY="main.py"
ICON="assets/icon.png"
ASSETS="assets/*;assets"           # ← Windows 下分隔符必须是分号“;”

# 1. 创建 / 激活虚拟环境（如果不存在）
if [[ ! -d "$VENV_DIR" ]]; then
  $PY_CMD -m venv "$VENV_DIR"
fi
source "$VENV_DIR/Scripts/activate"

# 2. 安装依赖
[[ -f requirements.txt ]] && pip install -r requirements.txt
pip install -U pyinstaller

# 3. 清理旧产物（可选）
rm -rf build dist "${APP_NAME}.spec"

# 4. 打包
opts=(
  --name "$APP_NAME"
  --onefile
  --windowed
  --icon "$ICON"
  --add-data "$ASSETS"
  "$ENTRY"
)
pyinstaller "${opts[@]}"

# 5. 清理临时文件
rm -rf "build" "${VENV_DIR}" "${APP_NAME}.spec"

echo -e "\n✅ 完成！可执行文件位于 dist/${APP_NAME}.exe"
