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
