<p align="right">
  <a href="README.md">中文</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# Tiny Pomodoro

## One-line Introduction

Tiny Pomodoro is a lightweight Pomodoro work/rest management tool based on the system tray, featuring a dark theme design, real-time statistics, and notifications, focusing on a minimalist experience.

## Project Structure

<details>
<summary>Click to expand</summary>

```
Tiny Pomodoro/
├── build.sh                # One-click build script (Windows)
├── LICENSE                 # MIT License
├── main.py                 # Program entry point
├── requirements.txt        # Dependencies list
├── assets/                 # Resource files
│   └── icon.png            # Tray and window icon
└── tiny_pomodoro_stats.json  # Generated stats data (created on first run)
```

</details>

## Quick Start

1. Clone the repository:

   ```bash
   git clone https://github.com/xcczach/tiny-pomodoro.git
   cd tiny-pomodoro
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python main.py
   ```

4. (Optional) Build standalone executable (run in Git Bash on Windows):

   ```bash
   bash build.sh
   ```

## Commands

- `python main.py`: Start Tiny Pomodoro
- `bash build.sh`: Build standalone executable (Windows)

## Contribution Guide

Feel free to submit issues, feature requests, or pull requests:

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature-desc`.
3. Commit your changes: `git commit -m 'Add your feature'`.
4. Push to the branch: `git push origin feature/your-feature-desc`.
5. Open a pull request describing your changes.

Please ensure code style consistency and pass existing tests.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
