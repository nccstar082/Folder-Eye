# 📂 Folder-Eye

**Folder-Eye** is a powerful, Python-based graphical tool designed to audit, compare, and visualize differences between two directories. Whether you are performing code reviews, verifying backups, or tracking version changes, Folder-Eye provides a clear "eye" on exactly what has changed.

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://github.com/nccstar082/Folder-Eye)
[![License](https://img.shields.io/github/license/nccstar082/Folder-Eye?color=green)](https://github.com/nccstar082/Folder-Eye/blob/main/LICENSE)

## ✨ Key Features

*   **Intelligent Directory Scanning**: Recursively compares a **Source (A)** and **Target (B)** directory to identify:
    *   **Modified Files**: Text files that have changed content.
    *   **Added Files**: New files present in Target but not Source.
    *   **Deleted Files**: Files missing from Target that exist in Source.
*   **Visual HTML Reporting**:
    *   Generates a **Side-by-Side Diff Report** for every modified file (Git-style).
    *   Includes syntax highlighting (Red for deletions, Green for additions).
    *   **Interactive Copy**: Copy specific code blocks or single lines directly from the HTML report.
*   **Smart Content Detection**:
    *   **Auto-Encoding**: Automatically detects file encodings (UTF-8, GBK, Latin-1) using `chardet`.
    *   **Binary Filtering**: Skips non-text files to focus on source code and configuration.
    *   **Comparison Logic**: Options to ignore whitespace or ignore case.
    *   **Strict Mode**: Forces content comparison even if file sizes differ.
*   **Audit Archiving**: Automatically exports the actual files (Source vs. Target) into a structured output folder for safe record-keeping.
*   **Exclusion System**: Built-in GUI to select and exclude specific subfolders (e.g., `.git`, `node_modules`, `__pycache__`).
*   **Session Memory**: Remembers your directory paths and exclusion settings for faster workflow.

## 🛠️ Installation

Folder-Eye requires **Python 3.x**.

1.  **Clone or Download** this repository.
2.  **Install Dependencies**:
    The tool relies on `chardet` for accurate text encoding detection.

    ```bash
    pip install chardet
    ```
    *(Note: On Linux, you may also need `sudo apt-get install python3-tk`)*

## 🚀 Usage

1.  **Run the Application**:
    ```bash
    python folder_eye.py
    ```
    *(Replace `folder_eye.py` with the actual name of your script file)*

2.  **Select Directories**:
    *   **Source Folder (A)**: The baseline/original directory.
    *   **Target Folder (B)**: The modified/new directory.
    *   **Output Folder**: Where the reports and backup files will be saved.
    *   *(Use the "↔" button to swap Source and Target quickly)*

3.  **Configure Filters (Optional)**:
    *   Click **Add** in the "Exclude Folders" section to ignore specific subdirectories.
    *   Toggle **Ignore Whitespace** or **Ignore Case** based on your needs.

4.  **Start Comparison**:
    *   Click **Start Comparison**. The tool will scan files and generate reports.

5.  **Analyze Results**:
    *   Navigate through the **Modified**, **Added**, and **Deleted** tabs.
    *   **Double-click** a modified file in the list to open an instant Diff view in your browser.
    *   Click **View Report** to open the full summary dashboard.

## 📂 Output Structure

Folder-Eye generates an organized output directory. 
*Note: The tool's internal naming convention for folders is currently in Chinese.*

```text
Output Directory/
├── 报告 (Reports)/
│   ├── 汇总报告.html           # Main HTML Dashboard linking to all changes
│   └── [filename]_diff.html    # Individual file difference reports
├── 修改文件 (Modified Files)/
│   ├── 原始文件/               # Copies of the 'Source' version of changed files
│   └── 修改文件/               # Copies of the 'Target' version of changed files
├── 新增文件 (Added Files)/     # Copies of new files found in Target
└── 删除文件 (Deleted Files)/   # Copies of files found only in Source
```

## ⚙️ Configuration

The tool creates local JSON files to save your preferences:
*   `config.json`: Saves directory history.
*   `exclude_config.json`: Saves the list of excluded folder paths.
---------------------------------------------------------------------------------------------
📂 Folder-Eye
Folder-Eye是一款功能强大的基于 Python 的图形化工具，旨在审核、比较和可视化两个目录之间的差异。无论您是在进行代码审查、验证备份还是跟踪版本变更，Folder-Eye 都能让您清晰地看到究竟发生了哪些变化。

Python 执照

✨ 主要特点
智能目录扫描：递归地比较源目录 (A)和目标目录 (B)以识别：
已修改文件：内容已更改的文本文件。
新增文件：目标目录中存在但源目录中不存在的新文件。
已删除文件：源文件中存在但目标文件中缺失的文件。
可视化 HTML 报表：
为每个修改过的文件生成并排差异报告（Git 风格）。
包含语法高亮显示（红色表示删除，绿色表示添加）。
交互式复制：直接从 HTML 报告复制特定的代码块或单行代码。
智能内容检测：
自动编码：使用chardet.
二进制过滤：跳过非文本文件，专注于源代码和配置。
比较逻辑：可忽略空格或忽略大小写。
严格模式：即使文件大小不同，也强制进行内容比较。
审计归档：自动将实际文件（源文件与目标文件）导出到结构化的输出文件夹中，以便安全保存记录。
排除系统：内置 GUI，用于选择和排除特定子文件夹（例如.git，，，node_modules）__pycache__。
会话记忆：记住您的目录路径和排除设置，以加快工作流程。
🛠️ 安装
Folder-Eye 需要Python 3.x。

克隆或下载此存储库。

安装依赖项：该工具依赖chardet于精确的文本编码检测。

pip install chardet
（注：在 Linux 系统上，您可能还需要sudo apt-get install python3-tk）

🚀 用法
运行应用程序：

python folder_eye.py
（请替换folder_eye.py为您的脚本文件的实际名称）

选择目录：

源文件夹（A）：基线/原始目录。
目标文件夹（B）：修改后的/新的目录。
输出文件夹：报告和备份文件将保存到此文件夹。
（使用“↔”按钮可快速交换源和目标）
配置筛选器（可选）：

在“排除文件夹”部分点击“添加”，即可忽略特定子目录。
根据需要切换忽略空格或忽略大小写。
开始比较：

点击“开始比较”。该工具将扫描文件并生成报告。
分析结果：

浏览“已修改”、“已添加”和“已删除”选项卡。
双击列表中已修改的文件，即可在浏览器中打开即时差异视图。
点击“查看报告”打开完整摘要仪表板。
📂 输出结构
Folder-Eye 会生成一个井然有序的输出目录。 注意：该工具内部的文件夹命名规则目前为中文。

Output Directory/
├── 报告 (Reports)/
│   ├── 汇总报告.html           # Main HTML Dashboard linking to all changes
│   └── [filename]_diff.html    # Individual file difference reports
├── 修改文件 (Modified Files)/
│   ├── 原始文件/               # Copies of the 'Source' version of changed files
│   └── 修改文件/               # Copies of the 'Target' version of changed files
├── 新增文件 (Added Files)/     # Copies of new files found in Target
└── 删除文件 (Deleted Files)/   # Copies of files found only in Source
⚙️ 配置
该工具会创建本地 JSON 文件来保存您的偏好设置：

config.json保存目录历史记录。
exclude_config.json保存排除的文件夹路径列表。
