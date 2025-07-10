import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import difflib
import chardet
from pathlib import Path
import threading
from datetime import datetime


class FileCompareTool:
    def __init__(self, root):
        self.root = root
        self.root.title("文件夹对比工具")
        self.root.geometry("800x600")

        # 变量
        self.folder1_var = tk.StringVar()
        self.folder2_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.extension_var = tk.StringVar(value=".txt")

        self.create_widgets()

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 文件夹1选择
        ttk.Label(main_frame, text="文件夹1:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.folder1_var, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览", command=self.select_folder1).grid(row=0, column=2, padx=5)

        # 文件夹2选择
        ttk.Label(main_frame, text="文件夹2:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.folder2_var, width=60).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览", command=self.select_folder2).grid(row=1, column=2, padx=5)

        # 输出文件夹选择
        ttk.Label(main_frame, text="输出文件夹:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_var, width=60).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览", command=self.select_output).grid(row=2, column=2, padx=5)

        # 文件后缀名输入
        ttk.Label(main_frame, text="文件后缀:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.extension_var, width=20).grid(row=3, column=1, sticky=tk.W, padx=5)

        # 开始对比按钮
        ttk.Button(main_frame, text="开始对比", command=self.start_comparison).grid(row=4, column=1, pady=20)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="准备就绪")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=5)

        # 日志文本框
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="5")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(7, weight=1)

        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def select_folder1(self):
        folder = filedialog.askdirectory(title="选择文件夹1")
        if folder:
            self.folder1_var.set(folder)

    def select_folder2(self):
        folder = filedialog.askdirectory(title="选择文件夹2")
        if folder:
            self.folder2_var.set(folder)

    def select_output(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_var.set(folder)

    def log(self, message):
        """添加日志信息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def detect_encoding(self, file_path):
        """检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']

                # 如果置信度较低，尝试常见编码
                if confidence < 0.7:
                    for enc in ['utf-8', 'gb2312', 'gbk', 'gb18030']:
                        try:
                            raw_data.decode(enc)
                            return enc
                        except UnicodeDecodeError:
                            continue

                return encoding if encoding else 'utf-8'
        except Exception as e:
            self.log(f"检测编码失败 {file_path}: {e}")
            return 'utf-8'

    def read_file_content(self, file_path):
        """读取文件内容，自动检测编码"""
        encoding = self.detect_encoding(file_path)
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read().splitlines()
        except UnicodeDecodeError:
            # 如果检测的编码失败，尝试其他编码
            for enc in ['utf-8', 'gb2312', 'gbk', 'gb18030', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        self.log(f"使用 {enc} 编码读取: {file_path}")
                        return f.read().splitlines()
                except UnicodeDecodeError:
                    continue

            # 如果所有编码都失败，使用错误处理
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.log(f"使用 utf-8 (忽略错误) 读取: {file_path}")
                return f.read().splitlines()

    def get_files_with_extension(self, folder, extension):
        """获取指定文件夹中指定后缀的所有文件"""
        files = {}
        folder_path = Path(folder)

        if not extension.startswith('.'):
            extension = '.' + extension

        for file_path in folder_path.rglob(f"*{extension}"):
            if file_path.is_file():
                # 使用相对路径作为键，这样可以匹配两个文件夹中的同名文件
                relative_path = file_path.relative_to(folder_path)
                files[str(relative_path)] = file_path

        return files

    def compare_files(self, file1_path, file2_path, output_path):
        """对比两个文件并生成差异报告"""
        try:
            # 读取文件内容
            lines1 = self.read_file_content(file1_path)
            lines2 = self.read_file_content(file2_path)

            # 生成差异
            diff = list(difflib.unified_diff(
                lines1, lines2,
                fromfile=f"文件夹1/{file1_path.name}",
                tofile=f"文件夹2/{file2_path.name}",
                lineterm='',
                n=3
            ))

            if diff:
                # 写入差异文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# 文件对比报告\n\n")
                    f.write(f"**文件1:** {file1_path}\n")
                    f.write(f"**文件2:** {file2_path}\n")
                    f.write(f"**对比时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## 差异内容\n\n")
                    f.write("```diff\n")
                    f.write('\n'.join(diff))
                    f.write("\n```\n")

                return True, len(diff)
            else:
                return False, 0

        except Exception as e:
            self.log(f"对比文件时出错: {e}")
            return False, 0

    def compare_folders(self):
        """对比两个文件夹"""
        folder1 = self.folder1_var.get()
        folder2 = self.folder2_var.get()
        output_folder = self.output_var.get()
        extension = self.extension_var.get()

        if not all([folder1, folder2, output_folder, extension]):
            messagebox.showerror("错误", "请填写所有必需的字段")
            return

        if not os.path.exists(folder1):
            messagebox.showerror("错误", "文件夹1不存在")
            return

        if not os.path.exists(folder2):
            messagebox.showerror("错误", "文件夹2不存在")
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        self.log("开始文件对比...")
        self.log(f"文件夹1: {folder1}")
        self.log(f"文件夹2: {folder2}")
        self.log(f"输出文件夹: {output_folder}")
        self.log(f"文件后缀: {extension}")

        try:
            # 获取两个文件夹中的文件
            files1 = self.get_files_with_extension(folder1, extension)
            files2 = self.get_files_with_extension(folder2, extension)

            self.log(f"文件夹1中找到 {len(files1)} 个 {extension} 文件")
            self.log(f"文件夹2中找到 {len(files2)} 个 {extension} 文件")

            # 找到公共文件
            common_files = set(files1.keys()) & set(files2.keys())
            self.log(f"找到 {len(common_files)} 个同名文件")

            if not common_files:
                self.log("没有找到同名文件")
                messagebox.showinfo("完成", "没有找到同名文件进行对比")
                return

            # 对比每个公共文件
            compared_count = 0
            diff_count = 0

            for relative_path in common_files:
                file1_path = files1[relative_path]
                file2_path = files2[relative_path]

                # 生成输出文件名
                output_name = f"{Path(relative_path).stem}-diff.md"
                output_path = Path(output_folder) / output_name

                self.log(f"对比: {relative_path}")

                has_diff, diff_lines = self.compare_files(file1_path, file2_path, output_path)
                compared_count += 1

                if has_diff:
                    diff_count += 1
                    self.log(f"  -> 发现差异，已保存到: {output_path}")
                else:
                    self.log(f"  -> 文件内容相同")
                    # 删除可能存在的空差异文件
                    if output_path.exists():
                        output_path.unlink()

            self.log(f"\n对比完成!")
            self.log(f"总共对比: {compared_count} 个文件")
            self.log(f"发现差异: {diff_count} 个文件")

            messagebox.showinfo("完成", f"对比完成!\n总共对比: {compared_count} 个文件\n发现差异: {diff_count} 个文件")

        except Exception as e:
            self.log(f"处理过程中出错: {e}")
            messagebox.showerror("错误", f"处理过程中出错: {e}")

    def start_comparison(self):
        """启动对比过程"""
        self.progress.start()
        self.status_label.config(text="正在处理...")
        self.log_text.delete(1.0, tk.END)

        # 在新线程中运行对比，避免阻塞UI
        thread = threading.Thread(target=self.run_comparison)
        thread.daemon = True
        thread.start()

    def run_comparison(self):
        """在线程中运行对比"""
        try:
            self.compare_folders()
        finally:
            # 停止进度条
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.status_label.config(text="处理完成"))


def main():
    root = tk.Tk()
    app = FileCompareTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
