<p align="right">
  <a href="README.en.md">English</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# Tiny Pomodoro

## 一句话介绍

Tiny Pomodoro 是一款基于系统托盘的轻量级番茄工作/休息管理工具，采用深色主题设计，支持即时统计与通知，专注于极简体验。

## 项目结构

<details>
<summary>点击展开</summary>

```
Tiny Pomodoro/
├── build.sh                # 一键打包脚本（Windows）
├── LICENSE                 # MIT 许可证
├── main.py                 # 程序入口
├── requirements.txt        # 依赖列表
├── assets/                 # 资源文件
│   └── icon.png            # 托盘和窗口图标
└── tiny_pomodoro_stats.json  # 运行后生成的统计数据（首次运行后创建）
```

</details>

## 快速开始

1. 克隆仓库：

   ```bash
   git clone https://github.com/xcczach/tiny-pomodoro.git
   cd tiny-pomodoro
   ```

2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

3. 运行应用：

   ```bash
   python main.py
   ```

4. （可选）打包执行文件（Windows 下运行 Git Bash）：

   ```bash
   bash build.sh
   ```

## 命令

- `python main.py`：启动 Tiny Pomodoro
- `bash build.sh`：一键打包为独立可执行文件（Windows）

## 贡献指南

欢迎提交 Issue、Feature Request 或 Pull Request：

1. Fork 本项目。
2. 创建分支：`git checkout -b feature/你的功能描述`。
3. 提交修改：`git commit -m 'Add your feature'`。
4. 推送分支：`git push origin feature/你的功能描述`。
5. 提交 PR，描述你的改动。

请确保代码风格统一，并通过现有测试。

## 许可证

本项目基于 MIT 协议开源。详情见 [LICENSE](LICENSE)。