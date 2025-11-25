# FlatSource: Intelligent Code Context Aggregator

![Version](https://img.shields.io/badge/version-1.3.0-blue) ![Python](https://img.shields.io/badge/python-3.8%2B-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

**FlatSource** is a production-grade CLI automation tool designed to "flatten" complex project directories into a linear, readable format.

It is specifically engineered for **LLM Context Injection** (ChatGPT/Claude) and **Code Auditing**, allowing developers to convert entire repositories into a safe, metadata-tagged format without manual copy-pasting.

---

## 🚀 Key Features (v1.3.0)

*   **🧠 Smart Extension Mapping:** Automatically maps input extensions to output extensions.
    *   *1-to-1 Mapping:* `.js` → `.txt`, `.css` → `.css`
    *   *Many-to-1 Mapping:* `.js` & `.ts` → `.txt`
    *   *Auto-Fallback:* Any input without a paired output defaults to `.txt` automatically.
*   **🔮 Visual Configuration Plan:** Prints a detailed "Mappings Table" before execution, showing exactly how extensions will be converted (Terraform-style planning).
*   **🛡️ Fail-Safe Architecture:**
    *   **Read-Only Source:** Never opens source files in write mode.
    *   **Collision Handling:** Auto-renames duplicates (e.g., `index.js` → `index_1.txt`) to prevent overwriting.
    *   **Stop-on-Error:** terminates immediately on permission/IO errors to preserve data integrity.
*   **📝 Metadata Injection:** Stamps every file with a header containing the `ORIGINAL_PATH` and `ARCHIVED` timestamp.
*   **🧪 Dry Run Simulation:** Verify exclusion patterns and file counts without touching the disk.

---

## 📦 Installation

### Prerequisites
*   Python 3.8+
*   `tqdm` (Optional, for progress bars)

```bash
pip install tqdm
```

### Option A: Quick Run (Local)
Just run the script directly:
```bash
python pro_scan.py --help
```

### Option B: Global Install (Recommended)
To use the command `pro_scan` from any terminal window:

1.  Run the included setup script (if available) or create a `pro_scan.bat` file in the script directory:
    ```bat
    @echo off
    python "%~dp0pro_scan.py" %*
    ```
2.  Add the script directory to your Windows **System PATH**.

---

## 🛠️ Usage

```bash
pro_scan --dest <DIR> --in-ext <EXT LIST> --out-ext <EXT LIST> [OPTIONS]
```

### Arguments

| Flag | Required | Description |
| :--- | :---: | :--- |
| `--dest` | ✅ | Destination directory for the flattened files. |
| `--in-ext` | ✅ | List of input extensions to scan (e.g., `js ts css`). |
| `--out-ext` | ✅ | List of output extensions. Maps to inputs by order. |
| `--exclude` | ❌ | Folder patterns to ignore (e.g., `node_modules .git`). |
| `--root` | ❌ | Root directory to scan (Default: Current Dir). |
| `--dry-run` | ❌ | Simulates the process without writing files. |
| `-v` / `--version` | ❌ | specific version info. |

---

## 💡 Advanced Examples

### 1. The "Smart Fallback" (Mixed Output)
You want to keep CSS files as `.css`, but convert everything else (EJS, JS, HTML) to `.txt`.

```bash
pro_scan --dest ./backup --in-ext ejs js css html --out-ext txt txt css
```

**How FlatSource interprets this:**
*   `.ejs` ➜ `.txt` (Mapped)
*   `.js`  ➜ `.txt` (Mapped)
*   `.css` ➜ `.css` (Mapped)
*   `.html` ➜ `.txt` **(Auto-Fallback)**

### 2. Strict 1-to-1 Mapping
Keep original formats for specific files.
```bash
pro_scan --dest ./audit --in-ext py js --out-ext py js
```

### 3. The "Convert All" (Classic Mode)
Flatten an entire web project into text files for an LLM.
```bash
pro_scan --dest ./llm_context --in-ext js ts jsx tsx css html --out-ext txt --exclude node_modules dist
```

---

## 🔍 Visual Verification

When running in `--dry-run` or live mode, FlatSource provides a transparent configuration block so you trust the execution:

```text
[CONFIGURATION]
 Mode:       [DRY RUN - SIMULATION]
 Root:       D:\GITHUB\cryptonium.cloud
 Dest:       D:\GITHUB\cryptonium.cloud\backup
 Excluding:  ['node_modules', '.env', 'venv']
 Mappings:
   .ejs     -> .txt
   .js      -> .txt
   .css     -> .css
   .html    -> .txt
```

---

## 🗓️ Recommended Workflow for Code Auditing

1.  **Visualize:** Use `tree` or `ls` to identify heavy folders to exclude.
2.  **Simulate:** Run `pro_scan ... --dry-run` to verify your extension mappings and exclusion logic.
3.  **Execute:** Run the command without the dry-run flag.
4.  **Ingest:** Drag and drop the flattened files into your LLM or auditing tool.

---

## ⚖️ License

Open Source (MIT).