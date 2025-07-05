#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Work-Rest Manager – tray-based, dark theme, lightweight
2025-04-26  f2-flush 版
在 f2 版基础上：
▪ **即时记账**：查看统计 / 打开设置时把当前已过秒数写入 json
▪ **防止重复累加**：同一工作/休息段只记一次
▪ 休息/开始窗口仍保持 always-on-top
"""

import sys, json, threading, time, platform
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import pystray
from PIL import Image, ImageDraw, ImageTk

try:
    from plyer import notification  # 备用通知
except ImportError:
    notification = None

# Windows-11 toast（可选）
use_win11_toast = False
if platform.system() == "Windows":
    try:
        from win11toast import toast  # 仅函数形式

        use_win11_toast = True
    except ImportError:
        pass


# ---------- 常量 ----------
ICON_PATH = (
    Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    / "assets"
    / "icon.png"
)  # ← 自定义图标
if getattr(sys, "frozen", False):  # 打包态
    DATA_DIR = Path(sys.executable).resolve().parent
else:  # 源码态
    DATA_DIR = Path(__file__).resolve().parent
DATA_FILE = DATA_DIR / "tiny_pomodoro_stats.json"  # 保存统计
DEF_WORK_S = 50 * 60
DEF_REST_S = 10 * 60

DARK_BG, DARK_FG = "#222831", "#eeeeee"
ACCENT = "#00adb5"
MARGIN = 32
SHIFT_X, SHIFT_Y = 0, 60  # 向屏幕内偏移
AUTO_SAVE_MS = 5 * 60 * 1000  # 5 分钟 (ms)

# ---------- 语言/Localization ----------
STRINGS = {
    "zh": {
        # generic
        "pause": "暂停",
        "resume": "继续",
        "current_status": "当前状态",
        "view_stats": "查看统计",
        "open_settings": "打开设置",
        "exit": "退出",
        # windows / buttons
        "start_work_btn": "开始工作",
        "end_rest_btn": "结束休息",
        "settings_title": "设置",
        "work_min_label": "工作时长 (分钟):",
        "rest_min_label": "休息时长 (分钟):",
        "save_close_btn": "保存并关闭",
        "language_label": "语言:",
        "lang_zh": "中文",
        "lang_en": "English",
        # notifications
        "notif_work_begin_title": "开始工作",
        "notif_work_begin_msg": "专注 {duration}",
        "notif_rest_begin_title": "开始休息",
        "notif_rest_begin_msg": "放松 {duration}",
        "notif_continue_title": "继续",
        "notif_continue_msg": "计时器已继续",
        "notif_paused_title": "已暂停",
        "notif_paused_msg": "计时器已暂停",
        "notif_stats_title": "统计",
        # rest labels
        "resting": "休息 {elapsed} / {target}",
        "resting_overtime": "休息 {elapsed} (已超时 {overtime})",
        "auto_start_label": "开机自启动",
        "stats_today": "今日",
        "stats_total": "总计",
        "stats_work": "工作",
        "stats_rest": "休息",
        "status_work_progress": "已工作 {elapsed} / {target}",
        "status_rest_progress": "已休息 {elapsed} / {target}",
        "status_paused_label": "暂停中",
        "status_running_label": "计时中",
        "timer_not_started": "未开始计时",
        # stats strings (left Chinese to avoid large refactor)
    },
    "en": {
        "pause": "Pause",
        "resume": "Resume",
        "current_status": "Status",
        "view_stats": "Statistics",
        "open_settings": "Settings",
        "exit": "Quit",
        "start_work_btn": "Start Working",
        "end_rest_btn": "End Rest",
        "settings_title": "Settings",
        "work_min_label": "Work duration (minutes):",
        "rest_min_label": "Rest duration (minutes):",
        "save_close_btn": "Save && Close",
        "language_label": "Language:",
        "lang_zh": "Chinese",
        "lang_en": "English",
        "notif_work_begin_title": "Work Started",
        "notif_work_begin_msg": "Focus for {duration}",
        "notif_rest_begin_title": "Break Started",
        "notif_rest_begin_msg": "Relax for {duration}",
        "notif_continue_title": "Resumed",
        "notif_continue_msg": "Timer resumed",
        "notif_paused_title": "Paused",
        "notif_paused_msg": "Timer paused",
        "notif_stats_title": "Statistics",
        "resting": "Rest {elapsed} / {target}",
        "resting_overtime": "Rest {elapsed} (overtime {overtime})",
        "auto_start_label": "Launch at startup",
        "stats_today": "Today",
        "stats_total": "Total",
        "stats_work": "Work",
        "stats_rest": "Rest",
        "status_work_progress": "Worked {elapsed} / {target}",
        "status_rest_progress": "Rested {elapsed} / {target}",
        "status_paused_label": "paused",
        "status_running_label": "running",
        "timer_not_started": "Timer not started",
    },
}


# ---------- 工具 ----------
def fmt_sec(sec: int) -> str:
    """mm:ss 格式字符串"""
    return f"{sec // 60:02d}:{sec % 60:02d}"


# ---------- 数据 ----------
def load_stats():
    """读取 / 初始化统计文件"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}
    data.setdefault("total_work", 0)  # 秒
    data.setdefault("total_rest", 0)
    data.setdefault("days", {})
    data.setdefault("config", {"work_sec": DEF_WORK_S, "rest_sec": DEF_REST_S, "lang": "zh", "auto_start": False})
    return data


def save_stats(stats):
    """将统计信息写入 json 文件"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # 写盘失败时不终止程序，但给出调试信息
        print("[save_stats] 写文件失败:", e)


def add_seconds(stats, key, seconds: int):
    """累计秒数到 total_work / total_rest，并写入当天"""
    if seconds <= 0:
        return
    stats[key] += seconds
    today = str(date.today())
    day = stats["days"].setdefault(today, {"work": 0, "rest": 0})
    day[key.split("_")[1]] += seconds
    save_stats(stats)


# ---------- 开机自启动（仅 Windows 实现） ----------
def set_auto_start(enable: bool, app_name: str = "TinyPomodoro", exe_path: str | None = None):
    """Add or remove registry Run key for current user to launch app on Windows startup."""
    if platform.system() != "Windows":
        return  # 其它平台暂不实现

    import winreg  # type: ignore

    if exe_path is None:
        exe_path = sys.executable if getattr(sys, "frozen", False) else str(Path(__file__).resolve())
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
    except PermissionError as e:
        print("[auto_start] Registry write failed:", e)


# ---------- 通用深色 ttk Style ----------
def apply_dark_style(widget):
    style = ttk.Style(widget)
    style.theme_use("clam")
    style.configure("TLabel", background=DARK_BG, foreground=DARK_FG)
    style.configure("TEntry", fieldbackground="#393e46", foreground=DARK_FG)
    style.configure("TButton", background=ACCENT, foreground=DARK_FG)
    style.map("TButton", background=[("active", "#019ca3")])


# ---------- 启动弹窗 ----------
class StartWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)

        # === 去掉左上角图标 ===
        if platform.system() == "Windows":
            # Win32 "tool window" 样式：无图标、标题栏更窄，也不会在任务栏占位
            self.wm_attributes("-toolwindow", True)
            # 去掉右上角的关闭按钮
            self.overrideredirect(True)
        else:
            # 其它平台直接去掉全部窗口装饰
            self.overrideredirect(True)

        # self.iconphoto(True, app.tk_icon)   # ← 这一行删除或注释掉

        self.app = app
        self.title("")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # 置顶
        apply_dark_style(self)

        ttk.Button(self, text=self.app.t("start_work_btn"), width=18, command=self._begin).grid(
            row=0, column=0, padx=25, pady=25
        )

        self.after(10, self._place_pos)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    def _place_pos(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = self.winfo_width(), self.winfo_height()
        x = sw - w - (MARGIN + SHIFT_X)
        y = sh - h - (MARGIN + SHIFT_Y)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _begin(self):
        self.withdraw()
        self.app.start()

    def update_language(self):
        """Refresh button texts when language is switched."""
        # Iterate over children to find the start button and update its text
        for child in self.winfo_children():
            if isinstance(child, ttk.Button):
                child.config(text=self.app.t("start_work_btn"))


# ---------- 休息弹窗 ----------
class RestWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        # === 去掉左上角图标 ===
        if platform.system() == "Windows":
            # Win32 "tool window" 样式：无图标、标题栏更窄，也不会在任务栏占位
            self.wm_attributes("-toolwindow", True)
            # 去掉右上角的关闭按钮
            self.overrideredirect(True)
        else:
            # 其它平台直接去掉全部窗口装饰
            self.overrideredirect(True)

        # self.iconphoto(True, app.tk_icon)   # ← 这一行删除或注释掉

        self.app = app
        self.title("")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # 置顶
        apply_dark_style(self)

        self.var_info = tk.StringVar()
        ttk.Label(self, textvariable=self.var_info).grid(
            row=0, column=0, padx=20, pady=(20, 10)
        )
        ttk.Button(self, text=self.app.t("end_rest_btn"), command=self._end_rest, width=14).grid(
            row=1, column=0, pady=(0, 20)
        )

        self.after(10, self._place_pos)
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._end_rest)

    def _place_pos(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = self.winfo_width(), self.winfo_height()
        x = sw - w - (MARGIN + SHIFT_X)
        y = sh - h - (MARGIN + SHIFT_Y)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _tick(self):
        elapsed = int(self.app.elapsed_seconds)
        target = self.app.rest_sec
        if elapsed >= target:
            self.var_info.set(self.app.t("resting_overtime", elapsed=fmt_sec(elapsed), overtime=fmt_sec(elapsed - target)))
        else:
            self.var_info.set(self.app.t("resting", elapsed=fmt_sec(elapsed), target=fmt_sec(target)))
        # Recalculate size in case text length (especially in English) changes
        self._place_pos()
        if self.app.state in ("resting", "paused_rest"):
            self.after(1000, self._tick)

    def _end_rest(self):
        self.destroy()
        self.app.end_rest()

    def refresh_info(self):
        """立刻把标签更新为最新休息上限，并调整窗口大小"""
        elapsed = int(self.app.elapsed_seconds)
        target = self.app.rest_sec
        if elapsed >= target:
            self.var_info.set(self.app.t("resting_overtime", elapsed=fmt_sec(elapsed), overtime=fmt_sec(elapsed - target)))
        else:
            self.var_info.set(self.app.t("resting", elapsed=fmt_sec(elapsed), target=fmt_sec(target)))
        # Update geometry to fit new text (important when switching languages)
        self._place_pos()

    def update_language(self):
        """Refresh button and label texts based on new language."""
        self.title("")  # title is empty currently
        # update button text
        for child in self.winfo_children():
            if isinstance(child, ttk.Button):
                child.config(text=self.app.t("end_rest_btn"))
        self.refresh_info()


# ---------- 主应用 ----------
class WorkRestApp:
    # Translation helper will be instantiated later
    def t(self, key: str, **kwargs):
        """Return localized text by key, formatted with kwargs."""
        txt = STRINGS.get(self.lang, STRINGS["zh"]).get(key, key)
        if kwargs:
            return txt.format(**kwargs)
        return txt

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        # --- 窗口 / 任务栏图标 ------------------------
        self.tk_icon = self._load_tk_icon()
        # 如需兼容 Windows16×16，可再生成一张小图：
        # small = self.tk_icon.subsample(4, 4)
        # self.root.iconphoto(True, small, self.tk_icon)
        self.root.iconphoto(True, self.tk_icon)
        # -------------------------------------------

        self.stats = load_stats()
        # --- Language setting ---
        self.lang = self.stats["config"].get("lang", "zh")
        self.stats["config"].setdefault("lang", self.lang)

        self.auto_start = self.stats["config"].get("auto_start", False)
        # Ensure registry matches preference
        set_auto_start(self.auto_start)

        self.work_sec = self.stats["config"]["work_sec"]
        self.rest_sec = self.stats["config"]["rest_sec"]

        self.state = "idle"
        self.elapsed_seconds = 0
        self.session_flushed = 0  # 本轮已写入 stats 的秒数

        self.running = threading.Event()
        self.paused = threading.Event()

        self.icon = None
        self.tray_thread = None
        self.timer_thread = None
        self.settings_win = None
        self.rest_win = None

        # 启动自动保存循环
        self._auto_save()

        # Keep reference so we can refresh its texts when language changes
        self.start_win = StartWindow(self)

    def _load_tk_icon(self):
        """返回 tk.PhotoImage，用于窗口左上角和任务栏"""
        try:
            # 优先直接加载文件，速度更快
            return tk.PhotoImage(file=str(ICON_PATH))
        except Exception:
            # 如果文件缺失或损坏，则用备用托盘图生成
            pil_img = self._create_icon()  # PIL.Image
            return ImageTk.PhotoImage(pil_img)  # 转成 PhotoImage

    # === 自动保存 ===
    def _auto_save(self):
        """每 5 分钟持久化一次统计数据"""
        save_stats(self.stats)
        try:
            self.root.after(AUTO_SAVE_MS, self._auto_save)
        except RuntimeError:
            pass

    # === 即时冲账方法（核心） ===
    def _flush_elapsed(self):
        """把尚未计入 stats 的当前秒数写入文件，并更新 session_flushed"""
        if self.state in ("working", "paused_work"):
            delta = self.elapsed_seconds - self.session_flushed
            if delta > 0:
                add_seconds(self.stats, "total_work", delta)
                self.session_flushed += delta
        elif self.state in ("resting", "paused_rest"):
            delta = self.elapsed_seconds - self.session_flushed
            if delta > 0:
                add_seconds(self.stats, "total_rest", delta)
                self.session_flushed += delta

    # === 静音通知 ===
    def _notify(self, title, msg):
        if use_win11_toast and platform.system() == "Windows":
            try:
                toast(title, msg, audio={"silent": "true"}, duration="short")
                return
            except Exception as e:
                print("[通知] win11toast 调用失败:", e)

        if notification:
            notification.notify(title=title, message=msg, timeout=3)
        else:
            print(f"[通知] {title}: {msg}")

    # === 主计时线程 ===
    # ---------- 主计时线程 ----------
    def _timer_loop(self):
        while self.running.is_set():

            # ------ 工作 ------
            self.session_flushed = 0
            self.state = "working"
            self.elapsed_seconds = 0
            self._notify(self.t("notif_work_begin_title"), self.t("notif_work_begin_msg", duration=fmt_sec(self.work_sec)))

            # 修改：支持 paused_work 状态，暂停时 stay in work loop
            while (
                self.running.is_set()
                and self.state in ("working", "paused_work")
                and self.elapsed_seconds < self.work_sec
            ):
                if self.paused.is_set():
                    time.sleep(0.5)
                    continue
                time.sleep(1)
                self.elapsed_seconds += 1
            self._flush_elapsed()

            # 退出后不再启动休息段
            if not self.running.is_set():
                break

            # ------ 休息 ------
            self.session_flushed = 0
            self.state = "resting"
            self.elapsed_seconds = 0
            self._notify(self.t("notif_rest_begin_title"), self.t("notif_rest_begin_msg", duration=fmt_sec(self.rest_sec)))
            self.root.after(0, self._show_rest_window)

            while (
                self.running.is_set()
                and self.state in ("resting", "paused_rest")
            ):
                while self.paused.is_set():
                    time.sleep(0.5)
                time.sleep(1)
                self.elapsed_seconds += 1
            # 休息段的计入仍由 end_rest() 负责

    # === 托盘图标 ===
    @staticmethod
    def _create_icon():
        """优先使用 asset/icon.png；若失败则绘制备用图标"""
        try:
            img = Image.open(ICON_PATH).convert("RGBA")
            if img.size != (64, 64):  # pystray 建议 64×64
                img = img.resize((64, 64), Image.LANCZOS)
            return img
        except Exception as e:
            print(f"[托盘] 加载 {ICON_PATH} 失败，使用默认图标 →", e)

        # --- 备用：用 Pillow 绘制 ---
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((8, 8, 56, 56), fill=(0, 173, 181))
        draw.polygon([(32, 16), (48, 32), (32, 48), (16, 32)], fill=(34, 40, 49))
        return img

    def _build_tray_menu(self):
        pause_item = pystray.MenuItem(
            lambda _, app=self: app.t("resume") if app.paused.is_set() else app.t("pause"),
            self._menu_pause,
        )
        return pystray.Menu(
            pause_item,
            pystray.MenuItem(self.t("current_status"), self._menu_status),
            pystray.MenuItem(self.t("view_stats"), self._menu_stats),
            pystray.MenuItem(self.t("open_settings"), self._menu_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(self.t("exit"), self._quit),
        )

    def _run_tray(self):
        menu = self._build_tray_menu()
        self.icon = pystray.Icon("WorkRest", self._create_icon(), "Tiny Pomodoro", menu)
        self.icon.run()

    # === 控制 ===
    def start(self):
        if self.state != "idle":
            return
        self.running.set()
        self.paused.clear()
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()

    def pause_resume(self):
        if self.state not in ("working", "resting", "paused_work", "paused_rest"):
            return
        if self.paused.is_set():  # 继续
            self.paused.clear()
            self.state = "working" if self.state == "paused_work" else "resting"
            self._notify(self.t("notif_continue_title"), self.t("notif_continue_msg"))
        else:  # 暂停
            self.paused.set()
            self.state = "paused_work" if self.state == "working" else "paused_rest"
            self._notify(self.t("notif_paused_title"), self.t("notif_paused_msg"))

    def end_rest(self):
        self._flush_elapsed()  # 用冲账替代整段累加
        self.state = "working"

    def stop(self):
        self.running.clear()
        self.paused.clear()
        self.state = "idle"

    # === 子窗 ===
    def _show_rest_window(self):
        if self.rest_win and self.rest_win.winfo_exists():
            self.rest_win.destroy()
        self.rest_win = RestWindow(self)

    # === 设置窗口 ===
    def open_settings(self):
        self._flush_elapsed()  # 确保数据显示最新
        if not self.settings_win or not self.settings_win.winfo_exists():
            self.settings_win = SettingsWindow(self)
        self.settings_win.deiconify()
        self.settings_win.lift()

    # === 托盘回调 ===
    def _menu_pause(self, *_):
        self.pause_resume()

    def _menu_status(self, *_):
        paused = self.paused.is_set()
        if self.state in ("working", "paused_work"):
            progress = self.t(
                "status_work_progress",
                elapsed=fmt_sec(self.elapsed_seconds),
                target=fmt_sec(self.work_sec),
            )
            state_label = self.t("status_paused_label") if paused else self.t("status_running_label")
            self._notify(self.t("current_status"), f"{progress} ({state_label})")
        elif self.state in ("resting", "paused_rest"):
            progress = self.t(
                "status_rest_progress",
                elapsed=fmt_sec(self.elapsed_seconds),
                target=fmt_sec(self.rest_sec),
            )
            state_label = self.t("status_paused_label") if paused else self.t("status_running_label")
            self._notify(self.t("current_status"), f"{progress} ({state_label})")
        else:
            self._notify(self.t("current_status"), self.t("timer_not_started"))

    def _menu_stats(self, *_):
        self._flush_elapsed()
        s, today = self.stats, str(date.today())
        d = s["days"].get(today, {"work": 0, "rest": 0})
        # 使用多语言字符串构建统计信息
        today_label = self.t("stats_today")
        total_label = self.t("stats_total")
        work_label = self.t("stats_work")
        rest_label = self.t("stats_rest")
        self._notify(
            self.t("notif_stats_title"),
            f"{today_label} {work_label} {fmt_sec(d['work'])}  {rest_label} {fmt_sec(d['rest'])}\n"
            f"{total_label} {work_label} {fmt_sec(s['total_work'])}  {rest_label} {fmt_sec(s['total_rest'])}",
        )
        save_stats(self.stats)  # 已是最新

    def _menu_settings(self, *_):
        self.open_settings()

    # === 彻底退出 ===
    def _quit(self, *_):
        self.stop()
        if self.timer_thread:
            self.timer_thread.join(timeout=1)
        if self.icon:
            try:
                self.icon.visible = False
                self.icon.stop()
            except Exception:
                pass
        if (
            self.tray_thread
            and self.tray_thread.is_alive()
            and threading.current_thread() is not self.tray_thread
        ):
            self.tray_thread.join(timeout=1)
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    # === 入口 ===
    def run(self):
        self.tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        self.tray_thread.start()
        self.root.mainloop()

    def _rebuild_tray_menu(self):
        """Recreate tray menu to reflect current language."""
        if not self.icon:
            return
        self.icon.menu = self._build_tray_menu()

    def apply_language_change(self):
        """Called after self.lang is modified to refresh UI labels."""
        # Rebuild tray menu if icon exists
        if self.icon:
            self._rebuild_tray_menu()
        # Update rest window
        if self.rest_win and self.rest_win.winfo_exists():
            self.rest_win.update_language()
        # Update start window
        if getattr(self, "start_win", None) and self.start_win.winfo_exists():
            self.start_win.update_language()


# ---------- 设置窗口 ----------
class SettingsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.transient(app.root)

        if platform.system() == "Windows":
            # "tool window" 样式：更窄的标题栏，也避免任务栏占位
            self.wm_attributes("-toolwindow", True)
        self.iconphoto(True, app.tk_icon)
        self.app = app
        self.title(app.t("settings_title"))
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # 置顶
        apply_dark_style(self)

        self.work_min = tk.IntVar(value=app.work_sec // 60)
        self.rest_min = tk.IntVar(value=app.rest_sec // 60)

        # --- validation function for positive integers ---
        vcmd = (self.register(self._validate_positive_int), "%P")

        self.lbl_work = ttk.Label(self, text=app.t("work_min_label"))
        self.lbl_work.grid(
            row=0, column=0, pady=8, padx=8, sticky="w"
        )
        ttk.Entry(self, textvariable=self.work_min, width=10, validate="key", validatecommand=vcmd).grid(
            row=0, column=1, pady=8, padx=8
        )
        self.lbl_rest = ttk.Label(self, text=app.t("rest_min_label"))
        self.lbl_rest.grid(
            row=1, column=0, pady=8, padx=8, sticky="w"
        )
        ttk.Entry(self, textvariable=self.rest_min, width=10, validate="key", validatecommand=vcmd).grid(
            row=1, column=1, pady=8, padx=8
        )

        # --- Language selection ---
        self.lbl_lang = ttk.Label(self, text=app.t("language_label"))
        self.lbl_lang.grid(row=3, column=0, pady=8, padx=8, sticky="w")
        self.lang_var = tk.StringVar(value="中文" if app.lang == "zh" else "English")
        self.cmb_lang = ttk.Combobox(self, textvariable=self.lang_var, values=[app.t("lang_zh"), app.t("lang_en")], state="readonly", width=12)
        self.cmb_lang.grid(row=3, column=1, pady=8, padx=8)

        # Save button
        self.save_btn = ttk.Button(self, text=app.t("save_close_btn"), command=self.save_close, width=18)
        self.save_btn.grid(row=4, column=0, columnspan=2, pady=12)

        # Bind language change event for realtime update
        self.lang_var.trace_add("write", self._on_lang_change)

        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    def save_close(self):
        self.app.work_sec = max(60, self.work_min.get() * 60)
        self.app.rest_sec = max(60, self.rest_min.get() * 60)
        self.app.stats["config"]["work_sec"] = self.app.work_sec
        self.app.stats["config"]["rest_sec"] = self.app.rest_sec
        save_stats(self.app.stats)
        # ✨ 如果正在休息，就立即刷新窗口显示
        if self.app.rest_win and self.app.rest_win.winfo_exists():
            self.app.rest_win.refresh_info()
        if (
            self.app.state in ("working", "paused_work")
            and self.app.elapsed_seconds >= self.app.work_sec
        ):
            # 让工作段立即结束
            self.app.paused.clear()
        self.withdraw()

        # --- language ---
        sel = self.lang_var.get()
        new_lang = "en" if sel.lower().startswith("e") else "zh"
        if new_lang == self.app.lang:
            return
        self.app.lang = new_lang
        self.app.stats["config"]["lang"] = new_lang
        save_stats(self.app.stats)

        # Update texts of widgets in this window
        self.title(self.app.t("settings_title"))
        self.lbl_work.config(text=self.app.t("work_min_label"))
        self.lbl_rest.config(text=self.app.t("rest_min_label"))
        self.lbl_lang.config(text=self.app.t("language_label"))
        self.save_btn.config(text=self.app.t("save_close_btn"))
        # Update combobox values labels
        self.cmb_lang.config(values=[self.app.t("lang_zh"), self.app.t("lang_en")])

        # Notify app to rebuild other UI parts
        self.app.apply_language_change()

    def _on_lang_change(self, *_):
        sel = self.lang_var.get()
        new_lang = "en" if sel.lower().startswith("e") else "zh"
        if new_lang == self.app.lang:
            return
        self.app.lang = new_lang
        self.app.stats["config"]["lang"] = new_lang
        save_stats(self.app.stats)

        # Update texts of widgets in this window
        self.title(self.app.t("settings_title"))
        self.lbl_work.config(text=self.app.t("work_min_label"))
        self.lbl_rest.config(text=self.app.t("rest_min_label"))
        self.lbl_lang.config(text=self.app.t("language_label"))
        self.save_btn.config(text=self.app.t("save_close_btn"))
        # Update combobox values labels
        self.cmb_lang.config(values=[self.app.t("lang_zh"), self.app.t("lang_en")])

        # Notify app to rebuild other UI parts
        self.app.apply_language_change()

    # --- validation helper ---
    @staticmethod
    def _validate_positive_int(p: str) -> bool:
        """Return True if p is empty (in-progress edit) or represents a positive integer."""
        if p == "":
            return True
        return p.isdigit() and int(p) > 0


# -------- main --------
if __name__ == "__main__":
    WorkRestApp().run()
