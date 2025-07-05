@echo off
+chcp 65001 >nul
:: build.cmd —— Windows CMD one-click packager for Tiny Pomodoro
:: 功能与 build.sh / build.ps1 等效

:: === 可自行调整的变量 ===
set "PY_CMD=python"          :: 或改成 "py -3.12"
set "VENV_DIR=tiny-pomodoro"
set "APP_NAME=Tiny Pomodoro"
set "ENTRY=main.py"
set "ICON=assets/icon.png"
set "ASSETS=assets/*;assets"   :: Windows 下分号分隔

echo [Tiny Pomodoro] Building (CMD)...

:: 1. 创建 / 激活虚拟环境（如果不存在）
if not exist "%VENV_DIR%" (
    %PY_CMD% -m venv "%VENV_DIR%"
)
call "%VENV_DIR%\Scripts\activate.bat"

:: 2. 安装依赖
if exist requirements.txt pip install -r requirements.txt
pip install -U pyinstaller

:: 3. 清理旧产物（可选）
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

:: 4. 打包
pyinstaller --name "%APP_NAME%" --onefile --windowed --icon "%ICON%" --add-data "%ASSETS%" "%ENTRY%"

:: 5. 清理临时文件
rmdir /s /q build 2>nul
rmdir /s /q "%VENV_DIR%" 2>nul
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

echo.
echo ✅ 完成！可执行文件位于 dist\%APP_NAME%.exe
echo Done! Executable located at dist\%APP_NAME%.exe