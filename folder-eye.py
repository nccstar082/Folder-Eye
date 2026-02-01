import os
import sys
import json
import hashlib
import difflib
import shutil
import time
import subprocess
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import webbrowser
import threading
import chardet
import re
import queue

def get_app_dir(app_name="FolderComparisonTool"):
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

class FolderComparisonTool:
    def __init__(self, root):
        self.root = root
        self.root.title("文件夹比较工具")
        self.root.geometry("900x700")
        self.root.minsize(700, 700)
        
		self.gui_queue = queue.Queue()
		self.root.after(100, self.process_gui_queue) # Start checking queue
		
        self.default_font = ('SimHei', 10)
        self.header_font = ('SimHei', 12, 'bold')
        
        self.style = ttk.Style()
        self.style.configure('Custom.TCheckbutton', font=self.default_font)

        self.app_dir = get_app_dir()
        os.makedirs(self.app_dir, exist_ok=True)  # 确保目录存在
        
        self.config_path = os.path.join(self.app_dir, "config.json")
        self.excluded_config_path = os.path.join(self.app_dir, "exclude_config.json")
        
        self.dir_a = tk.StringVar()
        self.dir_b = tk.StringVar()
        self.output_dir = tk.StringVar(value=os.path.join(self.app_dir, "对比结果"))
        self.is_comparing = tk.BooleanVar(value=False)
        self.stop_flag = False
        self.modified_files = []
        self.added_files = []
        self.deleted_files = []
        
        self.dir_a_history = []
        self.dir_b_history = []
        self.output_dir_history = []
        self.max_history = 10
        
        self.excluded_folders = []
        
        self.create_widgets()
        
        self.load_config()
        self.load_excluded_folders()
        self.refresh_excluded_listbox()

    def process_gui_queue(self):
        while not self.gui_queue.empty():
            try:
                action, args = self.gui_queue.get_nowait()
                if action == 'log':
                    self.log_text.insert(tk.END, args[0])
                    self.log_text.see(tk.END)
                elif action == 'status':
                    self.status_var.set(args[0])
                    if args[1] is not None:
                        self.progress_var.set(args[1])
                elif action == 'tree_insert':
                    tree, values = args
                    tree.insert("", tk.END, values=values)
            except queue.Empty:
                pass
        self.root.after(100, self.process_gui_queue)

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.dir_a.set(config.get('last_dir_a', ''))
                    self.dir_b.set(config.get('last_dir_b', ''))
                    self.output_dir.set(config.get('last_output_dir', os.path.join(self.app_dir, "对比结果")))
                    self.dir_a_history = config.get('dir_a_history', [])
                    self.dir_b_history = config.get('dir_b_history', [])
                    self.output_dir_history = config.get('output_dir_history', [])
                self.log(f"已加载配置: {self.config_path}")
            except Exception as e:
                self.log(f"加载配置失败: {str(e)}")

    def save_config(self):
        self.update_history(self.dir_a.get(), self.dir_a_history)
        self.update_history(self.dir_b.get(), self.dir_b_history)
        self.update_history(self.output_dir.get(), self.output_dir_history)
        
        config = {
            'last_dir_a': self.dir_a.get(),
            'last_dir_b': self.dir_b.get(),
            'last_output_dir': self.output_dir.get(),
            'dir_a_history': self.dir_a_history,
            'dir_b_history': self.dir_b_history,
            'output_dir_history': self.output_dir_history
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.log(f"已保存配置: {self.config_path}")
        except Exception as e:
            self.log(f"保存配置失败: {str(e)}")

    def update_history(self, path, history_list):
        if path and os.path.isdir(path):
            if path in history_list:
                history_list.remove(path)
            history_list.insert(0, path)
            if len(history_list) > self.max_history:
                history_list.pop()

    def load_excluded_folders(self):
        if os.path.exists(self.excluded_config_path):
            try:
                with open(self.excluded_config_path, 'r', encoding='utf-8') as f:
                    self.excluded_folders = json.load(f)
                self.log(f"已从 {self.excluded_config_path} 加载排除文件夹配置，共 {len(self.excluded_folders)} 个排除项")
            except Exception as e:
                messagebox.showwarning("配置文件加载失败", f"加载排除列表失败: {str(e)}")

    def save_excluded_folders(self):
        try:
            with open(self.excluded_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.excluded_folders, f, indent=2, ensure_ascii=False)
            self.log(f"已保存排除文件夹配置到 {self.excluded_config_path}，共 {len(self.excluded_folders)} 个排除项")
        except Exception as e:
            messagebox.showwarning("配置文件保存失败", f"保存排除列表失败: {str(e)}")

    def refresh_excluded_listbox(self):
        self.excluded_listbox.delete(0, tk.END)
        for folder in self.excluded_folders:
            self.excluded_listbox.insert(tk.END, folder)
        self.root.update_idletasks()

    def swap_folders(self):
        try:
            a_path = self.dir_a.get()
            b_path = self.dir_b.get()
            
            self.dir_a.set(b_path)
            self.dir_b.set(a_path)
            
            self.dir_a_combobox['values'] = self.dir_a_history
            self.dir_b_combobox['values'] = self.dir_b_history
            
            self.log(f"已互换文件夹：原始文件夹→{b_path}，修改文件夹→{a_path}")
            messagebox.showinfo("成功", "已互换原始文件夹和修改文件夹！")
        except Exception as e:
            self.log(f"互换文件夹失败: {str(e)}")
            messagebox.showerror("错误", f"互换文件夹失败: {str(e)}")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        folder_frame = ttk.LabelFrame(main_frame, text="文件夹选择", padding="5")
        folder_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(folder_frame, text="原始文件夹 (A):", font=self.default_font).grid(row=0, column=0, sticky=tk.W, pady=1)
        self.dir_a_combobox = ttk.Combobox(folder_frame, textvariable=self.dir_a, width=50, font=self.default_font, values=self.dir_a_history)
        self.dir_a_combobox.grid(row=0, column=1, padx=1, pady=1)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_dir_a, width=8).grid(row=0, column=2, padx=1, pady=1)
        
        swap_btn = ttk.Button(folder_frame, text="↔ 互换", command=self.swap_folders, width=8)
        swap_btn.grid(row=1, column=2, padx=1, pady=1)
        
        ttk.Label(folder_frame, text="修改文件夹 (B):", font=self.default_font).grid(row=2, column=0, sticky=tk.W, pady=1)
        self.dir_b_combobox = ttk.Combobox(folder_frame, textvariable=self.dir_b, width=50, font=self.default_font, values=self.dir_b_history)
        self.dir_b_combobox.grid(row=2, column=1, padx=1, pady=1)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_dir_b, width=8).grid(row=2, column=2, padx=1, pady=1)
        
        ttk.Label(folder_frame, text="输出文件夹:", font=self.default_font).grid(row=3, column=0, sticky=tk.W, pady=1)
        self.output_dir_combobox = ttk.Combobox(folder_frame, textvariable=self.output_dir, width=50, font=self.default_font, values=self.output_dir_history)
        self.output_dir_combobox.grid(row=3, column=1, padx=1, pady=1)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_output_dir, width=8).grid(row=3, column=2, padx=1, pady=1)
        
        history_btn_frame = ttk.Frame(folder_frame)
        history_btn_frame.grid(row=4, column=1, columnspan=2, pady=1, sticky=tk.E)
        ttk.Button(history_btn_frame, text="删选中", command=self.delete_selected_history, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(history_btn_frame, text="清全部", command=self.clear_all_history, width=8).pack(side=tk.LEFT, padx=1)
        
        exclude_frame = ttk.LabelFrame(main_frame, text="排除文件夹", padding="5")
        exclude_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(exclude_frame, text="已排除:", font=self.default_font).grid(row=0, column=0, sticky=tk.W, pady=1)
        self.excluded_listbox = tk.Listbox(exclude_frame, width=55, height=10, font=self.default_font)
        self.excluded_listbox.grid(row=0, column=1, padx=1, pady=1)
        
        scrollbar = ttk.Scrollbar(exclude_frame, orient=tk.VERTICAL, command=self.excluded_listbox.yview)
        self.excluded_listbox.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=2, sticky=tk.NS, pady=1)
        
        button_frame = ttk.Frame(exclude_frame)
        button_frame.grid(row=0, column=3, padx=1, pady=1)
        
        ttk.Button(button_frame, text="添加", command=self.add_excluded_folder, width=6).pack(pady=1)
        ttk.Button(button_frame, text="移除", command=self.remove_excluded_folder, width=6).pack(pady=1)
        ttk.Button(button_frame, text="清空", command=self.clear_excluded_folders, width=6).pack(pady=1)
        
        options_frame = ttk.LabelFrame(main_frame, text="比较选项", padding="5")
        options_frame.pack(fill=tk.X, pady=2)
        
        self.ignore_whitespace = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="忽略空白", variable=self.ignore_whitespace, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1)
        self.ignore_case = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="忽略大小写", variable=self.ignore_case, style='Custom.TCheckbutton').pack(anchor=tk.W, pady=1)
        
        control_frame = ttk.Frame(main_frame, padding="2")
        control_frame.pack(fill=tk.X, pady=2)
        
        self.compare_button = ttk.Button(control_frame, text="开始比较", command=self.start_comparison, width=12)
        self.compare_button.pack(side=tk.LEFT, padx=1)
        self.stop_button = ttk.Button(control_frame, text="停止对比", command=self.stop_comparison, width=12, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=1)
        self.open_result_button = ttk.Button(control_frame, text="打开结果", command=self.open_result_dir, width=12, state=tk.DISABLED)
        self.open_result_button.pack(side=tk.LEFT, padx=1)
        self.open_summary_button = ttk.Button(control_frame, text="查看报告", command=self.open_summary_report, width=12, state=tk.DISABLED)
        self.open_summary_button.pack(side=tk.LEFT, padx=1)
        
        status_frame = ttk.Frame(main_frame, padding="2")
        status_frame.pack(fill=tk.X, pady=1)
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, font=self.default_font).pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=1)
        
        result_notebook = ttk.Notebook(main_frame)
        result_notebook.pack(fill=tk.BOTH, expand=True, pady=1)
        
        self.modified_frame = ttk.Frame(result_notebook)
        result_notebook.add(self.modified_frame, text="修改文件")
        
        self.added_frame = ttk.Frame(result_notebook)
        result_notebook.add(self.added_frame, text="新增文件")
        
        self.deleted_frame = ttk.Frame(result_notebook)
        result_notebook.add(self.deleted_frame, text="删除文件")
        
        self.log_frame = ttk.Frame(result_notebook)
        result_notebook.add(self.log_frame, text="操作日志")
        
        self.create_file_list(self.modified_frame, "modified")
        self.create_file_list(self.added_frame, "added")
        self.create_file_list(self.deleted_frame, "deleted")
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, font=self.default_font, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    def create_file_list(self, parent, file_type):
        columns = ("path", "action")
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        tree.heading("path", text="文件路径")
        tree.heading("action", text="操作")
        
        tree.column("path", width=400, stretch=True)
        tree.column("action", width=80, anchor=tk.CENTER)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        if file_type == "modified":
            self.modified_tree = tree
            self.modified_tree.bind("<Double-1>", self.on_modified_file_double_click)
        elif file_type == "added":
            self.added_tree = tree
        elif file_type == "deleted":
            self.deleted_tree = tree
        
        tree.file_type = file_type

    def delete_selected_history(self):
        focused_widget = self.root.focus_get()
        if focused_widget == self.dir_a_combobox:
            selected = self.dir_a.get()
            if selected in self.dir_a_history:
                self.dir_a_history.remove(selected)
                self.dir_a_combobox['values'] = self.dir_a_history
                self.dir_a.set('')
        elif focused_widget == self.dir_b_combobox:
            selected = self.dir_b.get()
            if selected in self.dir_b_history:
                self.dir_b_history.remove(selected)
                self.dir_b_combobox['values'] = self.dir_b_history
                self.dir_b.set('')
        elif focused_widget == self.output_dir_combobox:
            selected = self.output_dir.get()
            if selected in self.output_dir_history:
                self.output_dir_history.remove(selected)
                self.output_dir_combobox['values'] = self.output_dir_history
                self.output_dir.set(os.path.join(self.app_dir, "对比结果"))
        else:
            messagebox.showinfo("提示", "请先选中要删除的历史记录（点击下拉框选择后再删除）")
            return
        
        self.save_config()
        self.log(f"已删除选中的历史记录: {selected}")

    def clear_all_history(self):
        if messagebox.askyesno("确认", "确定要清除所有文件夹历史记录吗？"):
            self.dir_a_history.clear()
            self.dir_b_history.clear()
            self.output_dir_history.clear()
            
            self.dir_a_combobox['values'] = []
            self.dir_b_combobox['values'] = []
            self.output_dir_combobox['values'] = []
            
            self.dir_a.set('')
            self.dir_b.set('')
            self.output_dir.set(os.path.join(self.app_dir, "对比结果"))
            
            self.save_config()
            self.log("已清除所有文件夹历史记录")

    def browse_dir_a(self):
        directory = filedialog.askdirectory(title="选择原始文件夹 (A)")
        if directory:
            self.dir_a.set(directory)
            self.dir_a_combobox['values'] = self.dir_a_history
            self.save_config()

    def browse_dir_b(self):
        directory = filedialog.askdirectory(title="选择修改文件夹 (B)")
        if directory:
            self.dir_b.set(directory)
            self.dir_b_combobox['values'] = self.dir_b_history
            self.save_config()

    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="选择输出文件夹")
        if directory:
            self.output_dir.set(directory)
            self.output_dir_combobox['values'] = self.output_dir_history
            self.save_config()

    def get_all_subfolders(self, base_dir, root_folder):
        all_folders = []
        for root, dirs, _ in os.walk(os.path.join(base_dir, root_folder)):
            rel_path = os.path.relpath(root, base_dir)
            all_folders.append(rel_path)
        return all_folders

    def add_excluded_folder(self):
        if not self.dir_a.get() or not self.dir_b.get():
            messagebox.showerror("错误", "请先选择要比较的两个文件夹")
            return
        
        dir_a = self.dir_a.get()
        dir_b = self.dir_b.get()
        
        subfolders = set()
        
        for root, dirs, _ in os.walk(dir_a):
            for dir in dirs:
                full_path = os.path.join(root, dir)
                rel_path = os.path.relpath(full_path, dir_a)
                subfolders.add(rel_path)
        
        for root, dirs, _ in os.walk(dir_b):
            for dir in dirs:
                full_path = os.path.join(root, dir)
                rel_path = os.path.relpath(full_path, dir_b)
                subfolders.add(rel_path)
        
        if not subfolders:
            messagebox.showinfo("信息", "未找到子文件夹")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("选择要排除的文件夹")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        listbox = tk.Listbox(dialog, selectmode=tk.MULTIPLE, width=45, height=12)
        listbox.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        for folder in sorted(subfolders):
            listbox.insert(tk.END, folder)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=5)
        
        def on_ok():
            selected_indices = listbox.curselection()
            if not selected_indices:
                dialog.destroy()
                return
            
            folders_to_exclude = set()
            
            for i in selected_indices:
                folder = listbox.get(i)
                a_subfolders = self.get_all_subfolders(dir_a, folder)
                b_subfolders = self.get_all_subfolders(dir_b, folder)
                
                for subfolder in a_subfolders + b_subfolders:
                    folders_to_exclude.add(subfolder)
            
            for folder in folders_to_exclude:
                if folder not in self.excluded_folders:
                    self.excluded_folders.append(folder)
            
            self.refresh_excluded_listbox()
            self.save_excluded_folders()
            dialog.destroy()
            messagebox.showinfo("成功", f"已添加 {len(folders_to_exclude)} 个排除文件夹（含子文件夹）")
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="确定", command=on_ok, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=on_cancel, width=8).pack(side=tk.LEFT, padx=5)
        
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        dialog.geometry(f"+{x}+{y}")

    def remove_excluded_folder(self):
        selected_indices = self.excluded_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("信息", "请先选择要移除的文件夹")
            return
        
        to_remove = []
        for i in selected_indices:
            to_remove.append(self.excluded_listbox.get(i))
        
        for folder in to_remove:
            self.excluded_folders.remove(folder)
        
        self.refresh_excluded_listbox()
        self.save_excluded_folders()
        messagebox.showinfo("成功", f"已移除 {len(to_remove)} 个排除文件夹")

    def clear_excluded_folders(self):
        if messagebox.askyesno("确认", "确定要清空所有排除文件夹吗？"):
            self.excluded_folders.clear()
            self.refresh_excluded_listbox()
            self.save_excluded_folders()
            messagebox.showinfo("成功", "已清空所有排除文件夹")

    def stop_comparison(self):
        self.stop_flag = True
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("正在停止对比...")
        self.log("用户请求停止对比")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        if hasattr(self, 'gui_queue'):
            self.gui_queue.put(('log', [log_msg]))
        else:
            print(log_msg, end='')

    def update_status(self, message, progress=None):
        self.status_var.set(message)
        if progress is not None:
            self.progress_var.set(progress)
        self.root.update_idletasks()

    def detect_encoding(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)
                result = chardet.detect(raw_data)
                confidence = result.get('confidence', 0)
                encoding = result.get('encoding', 'utf-8')
                self.log(f"检测文件编码: {file_path} -> {encoding} (置信度: {confidence:.2f})")
                return encoding
        except Exception as e:
            self.log(f"检测文件编码失败: {file_path} - {str(e)}，使用默认编码 utf-8")
            return 'utf-8'

    def is_text_file(self, file_path):
        try:
            encoding = self.detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read(1024)
                return True
        except UnicodeDecodeError:
            self.log(f"非文本文件: {file_path}")
            return False
        except Exception as e:
            self.log(f"检查文件类型失败: {file_path} - {str(e)}")
            return False

    def read_file_content(self, file_path):
        # Try standard encodings first (Fastest)
        encodings = ['utf-8', 'gb18030', 'gbk', 'cp1252', 'latin-1']
        
        raw_data = b""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
        except Exception:
            return ""
    
        for enc in encodings:
            try:
                return raw_data.decode(enc)
            except UnicodeDecodeError:
                continue
                
        # Only use chardet as a last resort (Slowest)
        try:
            detected = chardet.detect(raw_data[:10000]) # Limit sample size
            encoding = detected.get('encoding')
            if encoding:
                return raw_data.decode(encoding, errors='replace')
        except:
            pass
            
        return raw_data.decode('utf-8', errors='ignore') # Final fallback

    def compare_files(self, file_a, file_b):
        try:
            if self.stop_flag: return False
    
            # 1. Quick Check: File Size
            size_a = os.path.getsize(file_a)
            size_b = os.path.getsize(file_b)
            if size_a != size_b and not getattr(self, 'strict_mode', False):
                self.log(f"差异(大小): {os.path.basename(file_a)}")
                return False # Different
    
            # 2. Fast Check: Hash Comparison (Streaming)
            # This checks if files are identical without loading them into RAM as text
            if self._calculate_file_hash(file_a) == self._calculate_file_hash(file_b):
                self.log(f"相同: {os.path.basename(file_a)}")
                return True # Identical
            
            # If hashes differ, files are different. 
            # Note: We do NOT perform diff logic (difflib) here. 
            # We only do that when generating the HTML report.
            self.log(f"差异(内容): {os.path.basename(file_a)}")
            return False
    
        except Exception as e:
            self.log(f"比较出错: {str(e)}")
            return False
    
    # Add this helper method
    def _calculate_file_hash(self, filepath, block_size=65536):
        """Calculate SHA256 hash of a file efficiently"""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    sha256.update(block)
            return sha256.hexdigest()
        except:
            return ""

    def is_excluded(self, rel_path):
        if not rel_path:
            return False
        
        for excluded_folder in self.excluded_folders:
            if rel_path.startswith(excluded_folder + os.path.sep) or rel_path == excluded_folder:
                return True
        return False

    def _parse_diff_header(self, header_line):
        pattern = r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
        match = re.match(pattern, header_line.strip())
        if not match:
            return None
        
        start_a = int(match.group(1))
        count_a = int(match.group(2)) if match.group(2) else 1
        start_b = int(match.group(3))
        count_b = int(match.group(4)) if match.group(4) else 1
        
        return {
            'start_a': start_a,
            'count_a': count_a,
            'start_b': start_b,
            'count_b': count_b
        }

    def _parse_diff_lines(self, diff_lines):
        skip_lines = 0
        for i, line in enumerate(diff_lines):
            if line.startswith(('---', '+++')):
                skip_lines += 1
            else:
                break
        diff_lines = diff_lines[skip_lines:]

        parsed_lines = []
        core_diff_indices = []
        current_line_num_a = 0
        current_line_num_b = 0
        header_info = None

        for line_idx, line in enumerate(diff_lines):
            line_type = line[0] if line.strip() else ''
            parsed_line = {
                'line': line,
                'line_idx': line_idx,
                'line_type': line_type,
                'num_a': None,
                'num_b': None,
                'is_core_diff': False,
                'content': line[1:].rstrip('\n') if line_type in ('-', '+') else ''
            }

            if line.startswith('@@'):
                header_info = self._parse_diff_header(line)
                if header_info:
                    current_line_num_a = header_info['start_a']
                    current_line_num_b = header_info['start_b']
                parsed_lines.append(parsed_line)
                continue

            if header_info:
                if line_type == '-':
                    parsed_line['is_core_diff'] = True
                    parsed_line['num_a'] = current_line_num_a
                    current_line_num_a += 1
                    core_diff_indices.append(line_idx)
                elif line_type == '+':
                    parsed_line['is_core_diff'] = True
                    parsed_line['num_b'] = current_line_num_b
                    current_line_num_b += 1
                    core_diff_indices.append(line_idx)
                elif line_type == ' ':
                    parsed_line['num_a'] = current_line_num_a
                    parsed_line['num_b'] = current_line_num_b
                    current_line_num_a += 1
                    current_line_num_b += 1
                elif line_type == '?':
                    pass

            parsed_lines.append(parsed_line)
        
        return parsed_lines, core_diff_indices

    # 修复问题1：合并相邻差异片段
    def _merge_contiguous_core_indices(self, core_diff_indices):
        """合并连续的核心差异索引，避免片段拆分"""
        if not core_diff_indices:
            return []
        merged_blocks = []
        current_block = [core_diff_indices[0]]
        for idx in core_diff_indices[1:]:
            if idx == current_block[-1] + 1:
                current_block.append(idx)
            else:
                merged_blocks.append(current_block)
                current_block = [idx]
        merged_blocks.append(current_block)
        return merged_blocks

    def _group_diff_fragments_with_context(self, diff_lines, context_lines=3):
        """重构分组逻辑：先合并连续差异，再生成片段（修复拆分问题）"""
        parsed_lines, core_diff_indices = self._parse_diff_lines(diff_lines)
        
        # 合并连续的核心差异索引块
        merged_core_blocks = self._merge_contiguous_core_indices(core_diff_indices)
        fragments = []
        processed_core_indices = set()

        for core_block in merged_core_blocks:
            # 取块的首尾索引，扩展上下文
            block_start = core_block[0]
            block_end = core_block[-1]
            start_idx = max(0, block_start - context_lines)
            end_idx = min(len(parsed_lines) - 1, block_end + context_lines)
            
            # 标记已处理的核心索引
            for idx in core_block:
                processed_core_indices.add(idx)

            fragment_lines = []
            fragment_line_nums = []
            original_core_diff = []
            modified_core_diff = []

            for idx in range(start_idx, end_idx + 1):
                p_line = parsed_lines[idx]
                fragment_lines.append(p_line['line'])
                fragment_line_nums.append((p_line['num_a'], p_line['num_b']))
                
                if p_line['is_core_diff']:
                    if p_line['line_type'] == '-':
                        original_core_diff.append(p_line['content'])
                    elif p_line['line_type'] == '+':
                        modified_core_diff.append(p_line['content'])

            fragments.append({
                'type': 'changed',
                'lines': fragment_lines,
                'line_numbers': fragment_line_nums,
                'core_indices': core_block,
                'original_core_diff': original_core_diff,
                'modified_core_diff': modified_core_diff,
                'parsed_lines': parsed_lines[start_idx:end_idx+1]
            })

        # 处理无差异的情况
        if not fragments:
            fragments = [{
                'type': 'context',
                'lines': diff_lines,
                'line_numbers': [(None, None)] * len(diff_lines),
                'core_indices': [],
                'original_core_diff': [],
                'modified_core_diff': [],
                'parsed_lines': parsed_lines
            }]

        return fragments

    def _escape_html(self, text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

    def _build_diff_html(self, diff_lines, file_a, file_b):
        fragments = self._group_diff_fragments_with_context(diff_lines, context_lines=3)
        
        # 修复问题3：调整CSS解决窄空白行
        html_header = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件差异对比: {os.path.basename(file_a)} vs {os.path.basename(file_b)}</title>
    <style>
        body {{
            font-family: 'Consolas', 'Microsoft YaHei', monospace;
            margin: 20px;
            background-color: #f5f5f5;
            overflow-x: auto;
            font-size: 14px;
        }}
        .diff-container {{
            max-width: 100%;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .diff-header {{
            background-color: #2c3e50;
            color: white;
            padding: 15px;
            font-size: 16px;
            font-weight: bold;
            white-space: nowrap;
        }}
        .control-bar {{
            padding: 10px 15px;
            background-color: #f1f1f1;
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .control-btn {{
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            background-color: #3498db;
            color: white;
            cursor: pointer;
            transition: background-color 0.2s;
            font-size: 12px;
        }}
        .control-btn.active {{
            background-color: #2980b9;
        }}
        .control-btn:hover {{
            background-color: #2980b9;
        }}
        .legend {{
            display: flex;
            gap: 15px;
            font-size: 14px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .legend-item.deleted {{
            color: #c0392b;
        }}
        .legend-item.added {{
            color: #27ae60;
        }}
        .legend-item.changed {{
            color: #f39c12;
        }}
        .legend-item.reference {{
            color: #7f8c8d;
        }}
        .file-info {{
            margin: 10px 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            white-space: nowrap;
            overflow-x: auto;
        }}
        .diff-fragment {{
            margin: 10px 15px;
            border-radius: 4px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .fragment-header {{
            padding: 8px 12px;
            background-color: #34495e;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .fragment-title {{
            font-weight: bold;
        }}
        .fragment-reference {{
            font-size: 12px;
            color: #bdc3c7;
        }}
        .diff-fragment-deleted {{
            border-left: 4px solid #c0392b;
        }}
        .diff-fragment-added {{
            border-left: 4px solid #27ae60;
        }}
        .diff-fragment-changed {{
            border-left: 4px solid #f39c12;
        }}
        .diff-fragment-context {{
            border-left: 4px solid #bdc3c7;
            background-color: #f8f9fa;
        }}
        .copy-fragment-btn {{
            padding: 4px 8px;
            font-size: 12px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 5px;
        }}
        .copy-fragment-btn:hover {{
            background-color: #2980b9;
        }}
        .fragment-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            table-layout: fixed;
        }}
        .fragment-table th {{
            background-color: #34495e;
            color: white;
            padding: 10px;
            text-align: left;
            position: sticky;
            top: 0;
            white-space: nowrap;
        }}
        /* 修复：调整td样式，设置最小高度和行高，解决窄空白行 */
        .fragment-table td {{
            padding: 8px 10px;
            vertical-align: middle;
            position: relative;
            border-bottom: 1px solid #eee;
            min-height: 32px; /* 增加最小高度 */
            box-sizing: border-box;
            line-height: 1.5; /* 正常行高 */
        }}
        .col-line-num {{
            width: 60px !important;
            min-width: 60px !important;
            max-width: 60px !important;
        }}
        .col-content {{
            width: calc(50% - 60px) !important;
            min-width: calc(50% - 60px) !important;
            padding-right: 40px !important;
        }}
        .line-num {{
            text-align: right;
            color: #7f8c8d;
            background-color: rgba(0,0,0,0.05);
            font-family: monospace;
            white-space: nowrap;
            padding: 0 5px;
            vertical-align: middle;
        }}
        .content {{
            word-wrap: break-word;
            white-space: pre-wrap;
            font-family: 'Consolas', monospace;
            line-height: 1.5; /* 强制正常行高 */
            overflow-wrap: break-word;
            min-height: 24px; /* 内容区最小高度 */
        }}
        .content del {{
            background-color: #ffcccc;
            color: #c0392b;
            text-decoration: none;
        }}
        .content ins {{
            background-color: #ccffcc;
            color: #27ae60;
            text-decoration: none;
        }}
        .reference-line {{
            background-color: #f8f9fa;
            color: #7f8c8d;
        }}
        .reference-line .content {{
            color: #7f8c8d;
        }}
        .diff-line {{
            background-color: rgba(243, 156, 18, 0.1);
        }}
        .delete-line {{
            background-color: rgba(192, 57, 43, 0.1);
        }}
        .add-line {{
            background-color: rgba(39, 174, 96, 0.1);
        }}
        /* 修复：调整复制按钮样式，避免遮挡内容 */
        .copy-btn {{
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            padding: 4px 8px;
            font-size: 12px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s;
            height: 24px;
            line-height: 16px;
        }}
        .diff-row:hover .copy-btn {{
            opacity: 1;
        }}
        .copy-btn:hover {{
            background-color: #2980b9;
        }}
        .copy-toast {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            background-color: #2ecc71;
            color: white;
            border-radius: 4px;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
            z-index: 100;
        }}
        .diff-content {{
            overflow-x: auto;
        }}
        /* 修复：空行强制最小高度 */
        .content:empty {{
            min-height: 24px;
            display: inline-block;
            width: 100%;
        }}
    </style>
</head>
<body>
    <div class="diff-container">
        <div class="diff-header">文件差异对比</div>
        <div class="control-bar">
            <button id="showAllBtn" class="control-btn active" onclick="toggleDisplay('all')">全部显示</button>
            <button id="showDiffBtn" class="control-btn" onclick="toggleDisplay('diff')">只显示差异</button>
            <div class="legend">
                <span class="legend-item deleted">🟥 已删除</span>
                <span class="legend-item added">🟩 已新增</span>
                <span class="legend-item changed">🟨 已修改</span>
                <span class="legend-item reference">⬜ 参考代码</span>
            </div>
        </div>
        <div class="file-info">
            <div><strong>原始文件:</strong> {self._escape_html(file_a)}</div>
            <div><strong>修改文件:</strong> {self._escape_html(file_b)}</div>
            <div><strong>对比时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        <div class="diff-content">"""

        html_fragments = []
        for fragment_idx, fragment in enumerate(fragments):
            frag_type = fragment['type']
            frag_lines = fragment['lines']
            line_numbers = fragment['line_numbers']
            fragment_parsed_lines = fragment['parsed_lines']
            
            min_a = max_a = min_b = max_b = None
            for num_a, num_b in line_numbers:
                if num_a is not None:
                    min_a = num_a if min_a is None else min(min_a, num_a)
                    max_a = num_a if max_a is None else max(max_a, num_a)
                if num_b is not None:
                    min_b = num_b if min_b is None else min(min_b, num_b)
                    max_b = num_b if max_b is None else max(max_b, num_b)
            
            frag_html = f'<div class="diff-fragment diff-fragment-{frag_type}" data-type="{frag_type}">'
            range_text = ""
            if min_a and max_a and min_b and max_b:
                range_text = f"（源文件：{min_a}-{max_a} | 修改文件：{min_b}-{max_b}）"
            elif min_a and max_a:
                range_text = f"（源文件：{min_a}-{max_a}）"
            elif min_b and max_b:
                range_text = f"（修改文件：{min_b}-{max_b}）"
            
            # 修复问题2：修复JSON转义，避免复制函数解析失败
            original_core_json = json.dumps(fragment['original_core_diff'], ensure_ascii=False).replace('"', '\\"')
            modified_core_json = json.dumps(fragment['modified_core_diff'], ensure_ascii=False).replace('"', '\\"')
            
            if frag_type == 'changed':
                frag_html += f'''<div class="fragment-header">
                    <div>
                        <span class="fragment-title">差异片段 #{fragment_idx + 1}</span>
                        <span class="fragment-reference">{range_text}</span>
                    </div>
                    <div>
                        <button class="copy-fragment-btn" onclick="copyCoreDiff('{original_core_json}', 'original')">复制修改前差异</button>
                        <button class="copy-fragment-btn" onclick="copyCoreDiff('{modified_core_json}', 'modified')">复制修改后差异</button>
                    </div>
                </div>'''
            
            frag_html += f'''<table class="fragment-table">
                <thead>
                    <tr>
                        <th class="col-line-num">源文件行号</th>
                        <th class="col-content">原始文件 ({os.path.basename(file_a)})</th>
                        <th class="col-line-num">修改文件行号</th>
                        <th class="col-content">修改文件 ({os.path.basename(file_b)})</th>
                    </tr>
                </thead>
                <tbody>'''
            
            for line_idx, (line, (num_a, num_b)) in enumerate(zip(frag_lines, line_numbers)):
                p_line = fragment_parsed_lines[line_idx] if line_idx < len(fragment_parsed_lines) else None
                is_core_diff = p_line['is_core_diff'] if p_line else False
                line_type = p_line['line_type'] if p_line else (line[0] if line else '')
                
                row_class = ''
                if line_type == '-':
                    row_class = 'delete-line diff-row'
                elif line_type == '+':
                    row_class = 'add-line diff-row'
                elif line_type == ' ':
                    row_class = 'reference-line diff-row'
                elif line_type == '?':
                    row_class = 'diff-line diff-row'
                else:
                    row_class = 'diff-row'
                
                line_content = line[1:].rstrip('\n') if len(line) > 1 else ''
                original_line = ''
                modified_line = ''
                
                if line_type == '-':
                    original_line = self._escape_html(line_content)
                elif line_type == '+':
                    modified_line = self._escape_html(line_content)
                elif line_type == ' ':
                    original_line = self._escape_html(line_content)
                    modified_line = self._escape_html(line_content)
                elif line_type == '?':
                    continue
                
                display_num_a = str(num_a) if num_a is not None else ''
                display_num_b = str(num_b) if num_b is not None else ''
                
                frag_html += f'''<tr class="{row_class}" data-line-type="{line_type}" data-is-core="{str(is_core_diff).lower()}">
                    <td class="line-num col-line-num">{display_num_a}</td>
                    <td class="content col-content">{original_line}<button class="copy-btn" onclick="copyOnlyCoreLine(this)">复制</button></td>
                    <td class="line-num col-line-num">{display_num_b}</td>
                    <td class="content col-content">{modified_line}<button class="copy-btn" onclick="copyOnlyCoreLine(this)">复制</button></td>
                </tr>'''
            
            frag_html += '''</tbody></table></div>'''
            html_fragments.append(frag_html)

        # 修复问题2：重构复制函数，解决无反应问题
        html_footer = f"""
        </div>
        </div>
        
        <div id="copyToast" class="copy-toast">复制成功！</div>
        
        <script>
            // 修复：核心差异复制函数（解决JSON解析和剪贴板兼容）
            async function copyCoreDiff(coreDiffJson, type) {{
                try {{
                    // 还原转义的引号
                    coreDiffJson = coreDiffJson.replace(/\\\\"/g, '"');
                    const diffLines = JSON.parse(coreDiffJson || '[]');
                    
                    if (!diffLines.length || diffLines.every(line => line.trim() === '')) {{
                        alert('该片段无' + (type === 'original' ? '修改前' : '修改后') + '核心差异内容！');
                        return;
                    }}

                    const text = diffLines.join('\\n');
                    
                    // 兼容所有浏览器的剪贴板复制
                    let copySuccess = false;
                    if (navigator.clipboard && window.isSecureContext) {{
                        try {{
                            await navigator.clipboard.writeText(text);
                            copySuccess = true;
                        }} catch (err) {{
                            copySuccess = false;
                        }}
                    }}
                    
                    // 降级方案
                    if (!copySuccess) {{
                        const textArea = document.createElement('textarea');
                        textArea.value = text;
                        textArea.style.position = 'fixed';
                        textArea.style.opacity = 0;
                        document.body.appendChild(textArea);
                        textArea.select();
                        try {{
                            document.execCommand('copy');
                            copySuccess = true;
                        }} catch (err) {{
                            alert('复制失败，请手动复制：\\n' + text);
                            return;
                        }} finally {{
                            document.body.removeChild(textArea);
                        }}
                    }}
                    
                    if (copySuccess) {{
                        showToast();
                    }}
                }} catch (e) {{
                    console.error('复制失败:', e);
                    alert('复制失败：' + e.message);
                }}
            }}

            // 修复：单行复制函数（解决内容获取错误）
            async function copyOnlyCoreLine(btn) {{
                try {{
                    const row = btn.closest('tr');
                    if (row.dataset.isCore !== 'true') {{
                        alert('仅可复制核心差异行，参考行不支持单独复制！');
                        return;
                    }}

                    // 正确获取内容（排除按钮文字）
                    const contentCell = btn.parentElement;
                    const text = contentCell.textContent.replace('复制', '').trim();
                    
                    if (!text) {{
                        alert('该行无内容可复制！');
                        return;
                    }}

                    // 兼容剪贴板复制
                    let copySuccess = false;
                    if (navigator.clipboard && window.isSecureContext) {{
                        try {{
                            await navigator.clipboard.writeText(text);
                            copySuccess = true;
                        }} catch (err) {{
                            copySuccess = false;
                        }}
                    }}
                    
                    if (!copySuccess) {{
                        const textArea = document.createElement('textarea');
                        textArea.value = text;
                        textArea.style.position = 'fixed';
                        textArea.style.opacity = 0;
                        document.body.appendChild(textArea);
                        textArea.select();
                        try {{
                            document.execCommand('copy');
                            copySuccess = true;
                        }} catch (err) {{
                            alert('复制失败，请手动复制：\\n' + text);
                            return;
                        }} finally {{
                            document.body.removeChild(textArea);
                        }}
                    }}
                    
                    if (copySuccess) {{
                        showToast();
                    }}
                }} catch (e) {{
                    console.error('单行复制失败:', e);
                    alert('复制失败：' + e.message);
                }}
            }}

            function showToast() {{
                const toast = document.getElementById('copyToast');
                toast.style.opacity = '1';
                setTimeout(() => {{
                    toast.style.opacity = '0';
                }}, 2000);
            }}

            function toggleDisplay(mode) {{
                const allBtns = document.querySelectorAll('.control-btn');
                allBtns.forEach(btn => btn.classList.remove('active'));
                
                const activeBtn = document.getElementById(mode === 'all' ? 'showAllBtn' : 'showDiffBtn');
                activeBtn.classList.add('active');
                
                const fragments = document.querySelectorAll('.diff-fragment');
                fragments.forEach(fragment => {{
                    fragment.style.display = mode === 'all' ? 'block' : (fragment.dataset.type === 'changed' ? 'block' : 'none');
                }});
            }}
            
            document.addEventListener('DOMContentLoaded', function() {{
                toggleDisplay('all');
            }});
        </script>
        </body>
        </html>"""
        
        full_html = html_header + '\n'.join(html_fragments) + html_footer
        return full_html

    def generate_diff_reports(self, modified_files, dir_a, dir_b, reports_dir):
        for rel_path in modified_files:
            if self.stop_flag:
                self.log("生成差异报告已停止")
                return
                
            file_a = os.path.join(dir_a, rel_path)
            file_b = os.path.join(dir_b, rel_path)
            
            try:
                content_a = self.read_file_content(file_a)
                content_b = self.read_file_content(file_b)
                
                diff_lines = list(difflib.unified_diff(
                    content_a.splitlines(),
                    content_b.splitlines(),
                    fromfile=file_a,
                    tofile=file_b,
                    lineterm='',
                    n=3
                ))
                
                diff_html = self._build_diff_html(diff_lines, file_a, file_b)
                
                report_filename = f"{rel_path.replace(os.path.sep, '_')}_diff.html"
                report_path = os.path.join(reports_dir, report_filename)
                
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(diff_html)
                
                self.log(f"已生成差异报告: {report_path}")
                
            except Exception as e:
                self.log(f"生成差异报告失败: {rel_path} - {str(e)}")

    def generate_summary_html(self, modified_files, added_files, deleted_files, dir_a, dir_b, output_file):
        try:
            modified_list = ""
            for file in modified_files:
                report_filename = f"{file.replace(os.path.sep, '_')}_diff.html"
                report_path = report_filename
                modified_list += f"<li><a href='{self._escape_html(report_path)}' target='_blank'>{self._escape_html(file)}</a></li>"
            
            added_list = ""
            for file in added_files:
                added_list += f"<li>{self._escape_html(file)}</li>"
            
            deleted_list = ""
            for file in deleted_files:
                deleted_list += f"<li>{self._escape_html(file)}</li>"
            
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件夹对比汇总报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            margin: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .info-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        .file-list li {{
            padding: 8px;
            border-bottom: 1px solid #eee;
        }}
        .file-list li:hover {{
            background: #f1f1f1;
        }}
        .file-list a {{
            color: #3498db;
            text-decoration: none;
        }}
        .file-list a:hover {{
            text-decoration: underline;
        }}
        .summary {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-item {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            flex: 1;
            min-width: 200px;
            text-align: center;
        }}
        .summary-item h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .summary-item .count {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>文件夹对比汇总报告</h1>
        
        <div class="info-box">
            <p><strong>原始文件夹:</strong> {self._escape_html(dir_a)}</p>
            <p><strong>修改文件夹:</strong> {self._escape_html(dir_b)}</p>
            <p><strong>对比时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-item">
                <h3>修改的文件</h3>
                <div class="count">{len(modified_files)}</div>
            </div>
            <div class="summary-item">
                <h3>新增的文件</h3>
                <div class="count">{len(added_files)}</div>
            </div>
            <div class="summary-item">
                <h3>删除的文件</h3>
                <div class="count">{len(deleted_files)}</div>
            </div>
            <div class="summary-item">
                <h3>总计差异</h3>
                <div class="count">{len(modified_files) + len(added_files) + len(deleted_files)}</div>
            </div>
        </div>
        
        <h2>修改的文件 ({len(modified_files)})</h2>
        {f"<ul class='file-list'>{modified_list}</ul>" if modified_files else "<p>无修改的文件</p>"}
        
        <h2>新增的文件 ({len(added_files)})</h2>
        {f"<ul class='file-list'>{added_list}</ul>" if added_files else "<p>无新增的文件</p>"}
        
        <h2>删除的文件 ({len(deleted_files)})</h2>
        {f"<ul class='file-list'>{deleted_list}</ul>" if deleted_files else "<p>无删除的文件</p>"}
    </div>
</body>
</html>"""
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.log(f"已生成汇总报告: {output_file}")
            
        except Exception as e:
            self.log(f"生成汇总报告失败: {str(e)}")

    def compare_directories(self):
        try:
            self.is_comparing.set(True)
            self.stop_flag = False
            self.compare_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.open_result_button.config(state=tk.DISABLED)
            self.open_summary_button.config(state=tk.DISABLED)
            
            for item in self.modified_tree.get_children():
                self.modified_tree.delete(item)
            for item in self.added_tree.get_children():
                self.added_tree.delete(item)
            for item in self.deleted_tree.get_children():
                self.deleted_tree.delete(item)
            self.log_text.delete(1.0, tk.END)
            
            dir_a = self.dir_a.get()
            dir_b = self.dir_b.get()
            output_dir = self.output_dir.get()
            
            if not os.path.isdir(dir_a):
                messagebox.showerror("错误", f"原始文件夹不存在: {dir_a}")
                return
            if not os.path.isdir(dir_b):
                messagebox.showerror("错误", f"修改文件夹不存在: {dir_b}")
                return
            
            if self.excluded_folders:
                self.log("排除的文件夹:")
                for folder in self.excluded_folders:
                    self.log(f"  - {folder}")
            else:
                self.log("未排除任何文件夹")
            
            self.strict_mode = messagebox.askyesno(
                "严格模式", 
                "是否启用严格模式？\n\n严格模式会在文件大小不同时仍然比较内容，可能会增加比较时间，但可以避免因编码不同导致的误判。"
            )
            
            self.log(f"{'启用' if self.strict_mode else '未启用'}严格模式")
            
            os.makedirs(output_dir, exist_ok=True)
            reports_dir = os.path.join(output_dir, "报告")
            modified_files_dir = os.path.join(output_dir, "修改文件")
            added_files_dir = os.path.join(output_dir, "新增文件")
            deleted_files_dir = os.path.join(output_dir, "删除文件")
            
            os.makedirs(reports_dir, exist_ok=True)
            os.makedirs(modified_files_dir, exist_ok=True)
            os.makedirs(added_files_dir, exist_ok=True)
            os.makedirs(deleted_files_dir, exist_ok=True)
            
            self.log(f"开始比较文件夹: {dir_a} 和 {dir_b}")
            self.log(f"结果将保存到: {output_dir}")
            
            self.log("正在扫描原始文件夹...")
            text_files_a = {}
            total_files_a = 0
            processed_files = 0
            
            for root, _, files in os.walk(dir_a):
                if self.stop_flag:
                    self.log("扫描原始文件夹已停止")
                    break
                
                for file in files:
                    if self.stop_flag:
                        break
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, dir_a)
                    
                    if self.is_excluded(rel_path):
                        self.log(f"跳过排除的文件: {rel_path}")
                        continue
                    
                    if self.is_text_file(file_path):
                        text_files_a[rel_path] = file_path
                        self.log(f"发现文本文件: {rel_path}")
                        total_files_a += 1
                    else:
                        self.log(f"跳过非文本文件: {rel_path}")
            
            if self.stop_flag:
                self.log("对比操作已停止")
                return
            
            self.log(f"在原始文件夹中发现 {total_files_a} 个文本文件")
            
            self.log("正在扫描修改文件夹并比较...")
            modified_files = []
            added_files = []
            
            for root, _, files in os.walk(dir_b):
                if self.stop_flag:
                    self.log("扫描修改文件夹已停止")
                    break
                
                for file in files:
                    if self.stop_flag:
                        break
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, dir_b)
                    
                    processed_files += 1
                    progress = (processed_files / max(total_files_a, 1)) * 100
                    self.update_status(f"正在比较: {processed_files}/{max(total_files_a, 1)}", progress)
                    
                    if self.is_excluded(rel_path):
                        self.log(f"跳过排除的文件: {rel_path}")
                        continue
                    
                    if self.is_text_file(file_path):
                        self.log(f"检查文件: {rel_path}")
                        
                        if rel_path in text_files_a:
                            original_file = text_files_a[rel_path]
                            if not self.compare_files(original_file, file_path):
                                modified_files.append(rel_path)
                                self.log(f"发现差异: {rel_path}")
                            else:
                                self.log(f"文件内容相同: {rel_path}")
                        else:
                            added_files.append(rel_path)
                            self.log(f"发现新增文件: {rel_path}")
                    else:
                        self.log(f"跳过非文本文件: {rel_path}")
            
            self.log("正在检测删除文件...")
            deleted_files = []
            processed_deleted = 0
            
            for rel_path in text_files_a.keys():
                if self.stop_flag:
                    break
                
                processed_deleted += 1
                progress = (processed_deleted / len(text_files_a)) * 100
                self.update_status(f"检测删除文件: {processed_deleted}/{len(text_files_a)}", progress)
                
                if self.is_excluded(rel_path):
                    continue
                
                file_b_path = os.path.join(dir_b, rel_path)
                if not os.path.exists(file_b_path):
                    deleted_files.append(rel_path)
                    self.log(f"发现删除文件: {rel_path}")
            
            if self.stop_flag:
                self.log("对比操作已停止")
                return
            
            self.modified_files = modified_files
            self.added_files = added_files
            self.deleted_files = deleted_files
            
            # 补全中断的日志输出
            self.log(f"比较完成: 发现 {len(modified_files)} 个修改的文件，{len(added_files)} 个新增的文件，{len(deleted_files)} 个删除的文件")
            
            self.update_file_lists()
            
            if modified_files:
                self.log("正在生成差异报告...")
                self.generate_diff_reports(modified_files, dir_a, dir_b, reports_dir)
            
            if modified_files or added_files or deleted_files:
                self.log("正在复制差异文件...")
                self.copy_modified_files(modified_files, dir_a, dir_b, modified_files_dir)
                self.copy_added_files(added_files, dir_b, added_files_dir)
                self.copy_deleted_files(deleted_files, dir_a, deleted_files_dir)
            
            self.log("正在生成汇总报告...")
            summary_file = os.path.join(reports_dir, "汇总报告.html")
            self.generate_summary_html(modified_files, added_files, deleted_files, dir_a, dir_b, summary_file)
            
            self.log("比较完成!")
            self.update_status("比较完成", 100)
            
            self.open_result_button.config(state=tk.NORMAL)
            self.open_summary_button.config(state=tk.NORMAL)
            
            messagebox.showinfo("完成", f"比较完成!\n发现 {len(modified_files)} 个修改的文件、{len(added_files)} 个新增的文件、{len(deleted_files)} 个删除的文件")
            
        except Exception as e:
            self.log(f"比较文件夹时发生错误: {str(e)}")
            messagebox.showerror("错误", f"比较失败: {str(e)}")
        finally:
            self.is_comparing.set(False)
            self.compare_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_status("就绪", 0)

    def copy_modified_files(self, modified_files, dir_a, dir_b, target_dir):
        try:
            for rel_path in modified_files:
                if self.stop_flag:
                    self.log("复制修改文件已停止")
                    return
                    
                src_a = os.path.join(dir_a, rel_path)
                src_b = os.path.join(dir_b, rel_path)
                
                dest_a = os.path.join(target_dir, "原始文件", rel_path)
                dest_b = os.path.join(target_dir, "修改文件", rel_path)
                
                os.makedirs(os.path.dirname(dest_a), exist_ok=True)
                os.makedirs(os.path.dirname(dest_b), exist_ok=True)
                
                shutil.copy2(src_a, dest_a)
                shutil.copy2(src_b, dest_b)
                
                self.log(f"已复制修改文件: {rel_path}")
                
        except Exception as e:
            self.log(f"复制修改文件失败: {str(e)}")
            messagebox.showwarning("警告", f"部分修改文件复制失败: {str(e)}")

    def copy_added_files(self, added_files, dir_b, target_dir):
        try:
            for rel_path in added_files:
                if self.stop_flag:
                    self.log("复制新增文件已停止")
                    return
                    
                src = os.path.join(dir_b, rel_path)
                dest = os.path.join(target_dir, rel_path)
                
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src, dest)
                
                self.log(f"已复制新增文件: {rel_path}")
                
        except Exception as e:
            self.log(f"复制新增文件失败: {str(e)}")
            messagebox.showwarning("警告", f"部分新增文件复制失败: {str(e)}")

    def copy_deleted_files(self, deleted_files, dir_a, target_dir):
        try:
            for rel_path in deleted_files:
                if self.stop_flag:
                    self.log("复制删除文件已停止")
                    return
                    
                src = os.path.join(dir_a, rel_path)
                dest = os.path.join(target_dir, rel_path)
                
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src, dest)
                
                self.log(f"已复制删除文件: {rel_path}")
                
        except Exception as e:
            self.log(f"复制删除文件失败: {str(e)}")
            messagebox.showwarning("警告", f"部分删除文件复制失败: {str(e)}")

    def update_file_lists(self):
        try:
            for rel_path in self.modified_files:
                self.modified_tree.insert("", tk.END, values=(rel_path, "修改"))
            
            for rel_path in self.added_files:
                self.added_tree.insert("", tk.END, values=(rel_path, "新增"))
            
            for rel_path in self.deleted_files:
                self.deleted_tree.insert("", tk.END, values=(rel_path, "删除"))
                
            self.root.update_idletasks()
            
        except Exception as e:
            self.log(f"更新文件列表失败: {str(e)}")

    def start_comparison(self):
        if self.is_comparing.get():
            messagebox.showinfo("提示", "正在比较中，请等待完成或停止当前操作")
            return
            
        # 启动线程执行比较，避免UI阻塞
        comparison_thread = threading.Thread(target=self.compare_directories)
        comparison_thread.daemon = True
        comparison_thread.start()

    def on_modified_file_double_click(self, event):
        try:
            selected_item = self.modified_tree.selection()[0]
            rel_path = self.modified_tree.item(selected_item, "values")[0]
            
            dir_a = self.dir_a.get()
            dir_b = self.dir_b.get()
            file_a = os.path.join(dir_a, rel_path)
            file_b = os.path.join(dir_b, rel_path)
            
            if not os.path.exists(file_a) or not os.path.exists(file_b):
                messagebox.showwarning("警告", "文件不存在，无法打开")
                return
                
            # 生成临时差异报告并打开
            temp_dir = os.path.join(self.output_dir.get(), "临时报告")
            os.makedirs(temp_dir, exist_ok=True)
            temp_report = os.path.join(temp_dir, f"{rel_path.replace(os.path.sep, '_')}_temp_diff.html")
            
            content_a = self.read_file_content(file_a)
            content_b = self.read_file_content(file_b)
            
            diff_lines = list(difflib.unified_diff(
                content_a.splitlines(),
                content_b.splitlines(),
                fromfile=file_a,
                tofile=file_b,
                lineterm='',
                n=3
            ))
            
            diff_html = self._build_diff_html(diff_lines, file_a, file_b)
            
            with open(temp_report, 'w', encoding='utf-8') as f:
                f.write(diff_html)
            
            webbrowser.open(temp_report)
            self.log(f"已打开临时差异报告: {temp_report}")
            
        except Exception as e:
            self.log(f"打开修改文件差异报告失败: {str(e)}")
            messagebox.showerror("错误", f"打开文件失败: {str(e)}")

    def open_result_dir(self):
        try:
            output_dir = self.output_dir.get()
            if os.path.exists(output_dir):
                if sys.platform == "win32":
                    os.startfile(output_dir)
                elif sys.platform == "darwin":
                    subprocess.run(["open", output_dir])
                else:
                    subprocess.run(["xdg-open", output_dir])
                self.log(f"已打开结果文件夹: {output_dir}")
            else:
                messagebox.showwarning("警告", "结果文件夹不存在")
        except Exception as e:
            self.log(f"打开结果文件夹失败: {str(e)}")
            messagebox.showerror("错误", f"打开文件夹失败: {str(e)}")

    def open_summary_report(self):
        try:
            summary_file = os.path.join(self.output_dir.get(), "报告", "汇总报告.html")
            if os.path.exists(summary_file):
                webbrowser.open(summary_file)
                self.log(f"已打开汇总报告: {summary_file}")
            else:
                messagebox.showwarning("警告", "汇总报告不存在，请先执行比较操作")
        except Exception as e:
            self.log(f"打开汇总报告失败: {str(e)}")
            messagebox.showerror("错误", f"打开报告失败: {str(e)}")


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FolderComparisonTool(root)
        
        # 窗口关闭时保存配置
        def on_closing():
            app.save_config()
            app.save_excluded_folders()
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        input("按回车键退出...")
