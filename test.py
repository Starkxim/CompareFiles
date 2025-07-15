#!/usr/bin/env python3
# compare_folders_gui.py
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import difflib
import chardet

def detect_encoding(path):
    """返回文件编码，失败返回 None"""
    with open(path, 'rb') as f:
        raw = f.read()
    if not raw:
        return 'utf-8'  # 空文件
    result = chardet.detect(raw)
    enc = result['encoding']
    if enc is None:
        return None
    # 常见中文编码别名统一
    if enc.lower() in ('gb2312', 'gbk', 'gb18030'):
        return 'gb18030'
    return enc

def read_lines(path):
    """按探测到的编码读取文件，返回行列表"""
    enc = detect_encoding(path)
    if enc is None:
        raise RuntimeError("无法识别编码")
    with open(path, encoding=enc, errors='replace') as f:
        return [line.rstrip('\r\n') for line in f]

def make_diff(path1, path2, name):
    """生成两个文件的 diff Markdown 文本"""
    try:
        lines1 = read_lines(path1)
        lines2 = read_lines(path2)
    except RuntimeError as e:
        return f"**{name} 编码识别失败，跳过比较**"
    diff = difflib.unified_diff(
        lines1, lines2,
        fromfile=os.path.basename(path1),
        tofile=os.path.basename(path2),
        lineterm=''
    )
    diff_lines = list(diff)
    if not diff_lines:
        return f"**{name} 无差异**"
    # 转成 Markdown 代码块
    md = f"### {name}\n\n```diff\n"
    md += '\n'.join(diff_lines)
    md += "\n```\n\n"
    return md

def run_compare(folder1, folder2, suffix, out_folder):
    """执行比较并写入结果"""
    suffix = suffix.lstrip('.')
    if not suffix:
        messagebox.showerror("错误", "请输入文件后缀")
        return
    if not os.path.isdir(folder1) or not os.path.isdir(folder2) or not os.path.isdir(out_folder):
        messagebox.showerror("错误", "请选择有效的文件夹")
        return

    # 收集文件
    files1 = {f.lower(): f for f in os.listdir(folder1) if f.lower().endswith(f'.{suffix.lower()}')}
    files2 = {f.lower(): f for f in os.listdir(folder2) if f.lower().endswith(f'.{suffix.lower()}')}
    common = set(files1) & set(files2)

    if not common:
        messagebox.showinfo("结果", "未找到同名文件")
        return

    os.makedirs(out_folder, exist_ok=True)
    summary = []

    for name in sorted(common):
        path1 = os.path.join(folder1, files1[name])
        path2 = os.path.join(folder2, files2[name])
        diff_md = make_diff(path1, path2, name)
        summary.append(diff_md)

    out_file = os.path.join(out_folder, f"{suffix}-diff.md")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(f"# {suffix} 文件差异汇总\n\n")
        f.write(''.join(summary))

    messagebox.showinfo("完成", f"已生成差异文件：\n{out_file}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("文件夹差异比较工具")
        self.geometry("600x280")
        self.resizable(False, False)

        # 变量
        self.folder1 = tk.StringVar()
        self.folder2 = tk.StringVar()
        self.out_folder = tk.StringVar(value=os.getcwd())
        self.suffix = tk.StringVar()

        # 布局
        ttk.Label(self, text="文件夹 1：").grid(row=0, column=0, padx=10, pady=8, sticky='e')
        ttk.Entry(self, textvariable=self.folder1, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self, text="浏览...", command=lambda: self.choose_dir(self.folder1)).grid(row=0, column=2, padx=10)

        ttk.Label(self, text="文件夹 2：").grid(row=1, column=0, padx=10, pady=8, sticky='e')
        ttk.Entry(self, textvariable=self.folder2, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(self, text="浏览...", command=lambda: self.choose_dir(self.folder2)).grid(row=1, column=2, padx=10)

        ttk.Label(self, text="输出文件夹：").grid(row=2, column=0, padx=10, pady=8, sticky='e')
        ttk.Entry(self, textvariable=self.out_folder, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(self, text="浏览...", command=lambda: self.choose_dir(self.out_folder)).grid(row=2, column=2, padx=10)

        ttk.Label(self, text="文件后缀：").grid(row=3, column=0, padx=10, pady=8, sticky='e')
        ttk.Entry(self, textvariable=self.suffix, width=15).grid(row=3, column=1, sticky='w', padx=5)
        ttk.Label(self, text="（如 txt、py，不含点）").grid(row=3, column=1, sticky='e')

        ttk.Button(self, text="开始比较", command=self.start).grid(row=4, column=1, pady=20)

    def choose_dir(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def start(self):
        run_compare(
            self.folder1.get(),
            self.folder2.get(),
            self.suffix.get(),
            self.out_folder.get()
        )

if __name__ == '__main__':
    App().mainloop()
