import tkinter as tk
from tkinter import messagebox
import time
import re
from collections import defaultdict
import threading
import os
from pathlib import Path


class KeyboardHeatmap:
    def __init__(self, root):
        self.root = root
        self.root.title("键盘按键频率热力图")
        self.root.geometry("1000x600")
        self.root.configure(bg="#f0f0f0")

        # 使用相对路径
        self.log_path = 'keyboard_log.txt'

        # 键盘布局
        self.keyboard_layout = [
            ['Esc', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace', '', '', 'Insert', 'Home', 'PgUp', '', '', '', '', ''],
            ['Tab', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\', '', 'Delete', 'End', 'PgDn', '', '', '', '', '', ''],
            ['CapsLock', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", 'Enter', '', '', '', '', '', '', '', '', '', '', ''],
            ['Shift', '', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'Shift', '', '', '', '↑', '', '', '', '', '', '', ''],
            # 优化底部一行：去掉space两侧空格，方向键区单独处理
        ]

        # 特殊按键映射
        self.special_key_map = {
            'Key.space': ' ',
            'Key.enter': 'Enter',
            'Key.backspace': 'Backspace',
            'Key.tab': 'Tab',
            'Key.caps_lock': 'CapsLock',
            'Key.shift': 'Shift',  # 左 Shift
            'Key.shift_r': 'Shift_R',  # 右 Shift
            'Key.ctrl_l': 'Ctrl_L',  # 左 Ctrl
            'Key.ctrl_r': 'Ctrl_R',  # 右 Ctrl
            'Key.alt_l': 'Alt_L',    # 左 Alt
            'Key.alt_gr': 'Alt_R',   # 右 Alt
            'Key.cmd': 'Win',
            'Key.menu': 'Menu',
            'Key.esc': 'Esc',
            'Key.f1': 'F1', 'Key.f2': 'F2', 'Key.f3': 'F3', 'Key.f4': 'F4',
            'Key.f5': 'F5', 'Key.f6': 'F6', 'Key.f7': 'F7', 'Key.f8': 'F8',
            'Key.f9': 'F9', 'Key.f10': 'F10', 'Key.f11': 'F11', 'Key.f12': 'F12',
            'Key.print_screen': 'PrintScr',
            'Key.scroll_lock': 'ScrollLk',
            'Key.insert': 'Insert',
            'Key.home': 'Home',
            'Key.page_up': 'PgUp',
            'Key.delete': 'Delete',
            'Key.end': 'End',
            'Key.page_down': 'PgDn',
            'Key.up': '↑',
            'Key.down': '↓',
            'Key.left': '←',
            'Key.right': '→'
        }

        # 频率-颜色映射 (百分比区间 -> 颜色)
        self.color_map = {
            (0, 1): "#ffffff",  # 0-1%: 白色
            (1, 3): "#808080",  # 1-3%: 灰色
            (3, 5): "#bae7ff",  # 3-5%: 天蓝色
            (5, 7): "#ffcccc",  # 5-7%: 浅红色
            (7, 10): "#FFA500",  # 7-10%: 橙色
            (10, float('inf')): "#ff3333"  # 10%+: 深红色
        }

        # 按键统计
        self.key_counts = defaultdict(int)
        self.total_presses = 0

        # 存储按键组件
        self.key_widgets = {}

        # 创建UI
        self.create_ui()

        # 启动日志监控
        self.running = True
        self.update_thread = threading.Thread(target=self.update_stats)
        self.update_thread.daemon = True
        self.update_thread.start()

    def create_ui(self):
        # 顶部控制区
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            control_frame, text="刷新统计", bg="#4CAF50", fg="white",
            command=self.refresh_stats
        ).pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(
            control_frame, text="总按键数: 0", bg="#f0f0f0", font=("Arial", 12)
        )
        self.status_label.pack(side=tk.LEFT, padx=20)

        # 颜色图例
        legend_frame = tk.Frame(self.root, bg="#f0f0f0")
        legend_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(
            legend_frame, text="频率图例:", bg="#f0f0f0", font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)

        for (low, high), color in self.color_map.items():
            label = f"{low}%-{'∞' if high == float('inf') else high}%"
            tk.Label(
                legend_frame, text=label, bg=color, fg="#000", width=8, bd=1, relief=tk.SOLID
            ).pack(side=tk.LEFT, padx=2)

        # 键盘显示区
        keyboard_frame = tk.Frame(self.root, bg="#f0f0f0")
        keyboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建键盘
        self.create_keyboard(keyboard_frame)

    def create_keyboard(self, parent):
        # 标准104键布局，主区、功能区、方向区整体对齐
        # 每行长度一致，空位用''占位
        self.keyboard_layout = [
            ['Esc', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'Delete'],
            ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace', 'Home'],
            ['Tab', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\', 'PgUp' ],
            ['CapsLock', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", 'Enter', 'PgDn'],
            ['Shift',  'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'Shift_R', '↑','End'],
            ['Ctrl_L', 'Win', 'Alt_L',  ' ',  'Alt_R', 'Win', 'Menu', 'Ctrl_R', '←', '↓', '→']
        ]
        key_width = 60
        key_height = 40
        padding = 3

        # 清空现有按键
        for widget in parent.winfo_children():
            widget.destroy()

        # 创建键盘画布
        canvas = tk.Canvas(parent, bg="#f0f0f0", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        # 添加滚动条
        scrollbar = tk.Scrollbar(canvas, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 绘制键盘
        for y, row in enumerate(self.keyboard_layout):
            current_x = 0
            for x, key_text in enumerate(row):
                if not key_text:  # 空位置
                    current_x += key_width + padding
                    continue

                # 计算按键宽度（特殊按键）
                width = key_width
                if key_text == 'Backspace':
                    width = key_width * 1.8
                elif key_text == 'Tab':
                    width = key_width * 1.5
                elif key_text == '\\':
                    width = key_width * 1.3
                elif key_text == 'CapsLock':
                    width = key_width * 1.8
                elif key_text == 'Enter':
                    width = key_width * 2.05
                elif key_text == 'Shift':
                    width = key_width * 1.92
                elif key_text == 'Shift_R':
                    width = key_width * 1.92
                elif key_text == ' ':
                    width = key_width * 6

                # 创建按键（初始为白色）
                key_frame = tk.Frame(
                    canvas, bg="#ffffff", bd=1, relief=tk.RAISED,
                    highlightthickness=1, highlightbackground="#888"
                )
                key_frame.place(x=current_x, y=y * (key_height + padding), width=width, height=key_height)

                # 按键文本
                tk.Label(
                    key_frame, text=key_text, bg="#ffffff", font=("Arial", 10)
                ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)

                # 存储按键组件
                self.key_widgets[key_text] = key_frame

                # 添加点击事件（显示详情）
                key_frame.bind("<Button-1>", lambda event, k=key_text: self.show_key_stats(k))

                current_x += width + padding

        # 更新画布滚动区域
        canvas.configure(scrollregion=canvas.bbox("all"))

    def update_stats(self):
        """定期更新按键统计"""
        last_mtime = 0

        while self.running:
            try:
                # 检查文件是否有更新
                if os.path.exists(self.log_path):
                    mtime = os.path.getmtime(self.log_path)
                    if mtime != last_mtime:
                        last_mtime = mtime
                        self.refresh_stats()
            except Exception as e:
                messagebox.showerror("错误", f"更新统计失败: {str(e)}")

            time.sleep(1)  # 每秒检查一次

    def refresh_stats(self):
        """刷新按键统计数据"""
        self.key_counts = defaultdict(int)
        self.total_presses = 0

        try:
            if not os.path.exists(self.log_path):
                messagebox.showwarning("警告", f"日志文件不存在: {self.log_path}")
                return

            with open(self.log_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 将内容按 Key. 分割，保留分隔符
            parts = re.split(r'(Key\.[a-z_]+)', content)

            for part in parts:
                if part.startswith('Key.'):
                    # 处理特殊按键
                    key = self.special_key_map.get(part, part)
                    if key in ['Shift', 'Shift_R']:
                        self.key_counts[key] += 1
                        self.total_presses += 1
                    elif any(key in row for row in self.keyboard_layout):
                        self.key_counts[key] += 1
                        self.total_presses += 1
                else:
                    # 处理普通字符
                    for char in part:
                        if char.isalnum() or char in "`,.-=[];'\\,./":  # 添加其他需要的符号
                            display_key = char.upper()
                            if any(display_key in row for row in self.keyboard_layout):
                                self.key_counts[display_key] += 1
                                self.total_presses += 1

            self.update_key_colors()
            self.status_label.config(text=f"总按键数: {self.total_presses}")

        except Exception as e:
            messagebox.showerror("错误", f"解析日志失败: {str(e)}")

    def update_key_colors(self):
        """根据按键频率更新颜色"""
        if not self.total_presses:
            return

        for key_text, count in self.key_counts.items():
            if key_text in self.key_widgets:
                # 计算百分比
                percentage = (count / self.total_presses) * 100

                # 查找对应的颜色区间
                for (low, high), color in self.color_map.items():
                    if low <= percentage < high:
                        # 更新按键颜色
                        self.key_widgets[key_text].config(bg=color)
                        for child in self.key_widgets[key_text].winfo_children():
                            child.config(bg=color)
                        break

    def show_key_stats(self, key_text):
        """显示按键详情"""
        count = self.key_counts.get(key_text, 0)
        percentage = (count / self.total_presses * 100) if self.total_presses > 0 else 0

        messagebox.showinfo(
            f"按键统计: {key_text}",
            f"按键: {key_text}\n"
            f"次数: {count}\n"
            f"频率: {percentage:.2f}%\n\n"
            f"排名: {sorted(self.key_counts.values(), reverse=True).index(count) + 1}/"
            f"{len(self.key_counts)}"
        )

    def close_window(self):
        """关闭程序"""
        self.running = False
        self.root.destroy()

def start_heatmap():
    root = tk.Tk()
    app = KeyboardHeatmap(root)
    root.protocol("WM_DELETE_WINDOW", app.close_window)
    root.mainloop()

if __name__ == "__main__":
    start_heatmap()