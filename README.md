<p align="right">
  <a href="./docs/README.en.md">English</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# 番茄粒 Tiny Pomodoro

 番茄粒 Tiny Pomodoro 是一款基于系统托盘的轻量级番茄工作/休息管理工具，采用深色主题设计，支持即时统计与通知，专注于极简体验。

 Tiny Pomodoro is a lightweight Pomodoro work/rest management tool based on the system tray, featuring a dark theme design, real-time statistics, and notifications, focusing on a minimalist experience.

 目前仅支持Windows

## 下载 Windows 可执行文件

[⬇️番茄粒](https://github.com/xcczach/tiny-pomodoro/releases/download/v1.0.0/tiny_pomodoro.exe)（双击即可运行，无需安装）

## 使用说明

运行程序后点击“开始工作”按钮即开始计时！

### 呼出菜单

右键点击托盘图标即可呼出菜单。
![托盘图标](./docs/imgs/tray_menu.png)

菜单支持查看当前工作状态与统计信息，也可以打开设置调整语言、工作时长、休息时长。

### 开机自启动

创建快捷方式后，将其复制到 `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup` 目录下。

## 从代码构建

1. 克隆仓库：

   ```bash
   git clone https://github.com/xcczach/tiny-pomodoro.git
   cd tiny-pomodoro
   ```

2. 打包可执行文件（Windows）（要求Python已安装）：

   - Git Bash：`bash build.sh`
   - PowerShell：`powershell -ExecutionPolicy Bypass -File .\build.ps1`
   - CMD：`build.cmd`

## 许可证

本项目基于 MIT 协议开源。详情见 [LICENSE](LICENSE)。