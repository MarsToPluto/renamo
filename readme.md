# FlatSource: Code Context Aggregator

**FlatSource** is a robust CLI automation tool designed to flatten complex project directories into a linear format. It is specifically engineered for preparing codebases for Large Language Model (LLM) context windows (e.g., ChatGPT, Claude) or for simplifying code auditing processes.

It recursively scans directories, respects exclusion patterns, and migrates files to a "flat" safe-directory with metadata headers, ensuring no data loss and zero impact on the source code.

---

## 🚀 Key Features

*   **🛡️ Fail-Safe Architecture:** Read-only access to source files. The script terminates immediately upon any error (permission/IO) to preserve data integrity.
*   **🚫 Collision Handling:** Automatically resolves filename conflicts (e.g., `index.tsx` vs `utils/index.tsx`) by appending counters, ensuring no file is ever overwritten.
*   **📝 Metadata Injection:** Injects a standard header into every output file containing the original relative path and a migration timestamp.
*   **🧪 Dry Run Mode:** Simulate the entire process without writing to the disk to verify paths and exclusion logic.
*   **📊 Progress Feedback:** Integrated `tqdm` progress bar for large repositories (gracefully degrades if dependency is missing).
*   **✨ Type-Hinted & Modern:** Written in modern Python 3 with strict typing conventions.

---

## 📦 Installation

No complex build steps required. Just ensure you have Python 3 installed.

For the best experience (Progress Bar support), install `tqdm`:

```bash
pip install tqdm
```

*(Note: The script will run fine without `tqdm`, falling back to a standard console log.)*

---

## 🛠️ Usage

### Basic Syntax
```bash
python pro_scan.py --dest <OUTPUT_DIR> --in-ext <INPUT_EXT> --out-ext <OUTPUT_EXT> [OPTIONS]
```

### The "Helper" Commands (Flags)

| Flag | Description |
| :--- | :--- |
| `--help` | Shows the built-in manual with all available commands and examples. |
| `--dry-run` | **Safe Mode.** Scans files and prints what *would* happen, but creates no files. |
| `--exclude` | A list of folder names or wildcard patterns to ignore (e.g., `node_modules`). |
| `--root` | Specify a different starting folder (defaults to current directory). |

---

## 💡 Examples

### 1. The "Safety First" Check (Dry Run)
Before moving files, see how many files will be touched without actually doing it.
```bash
python pro_scan.py --dest ./backup --in-ext tsx --out-ext txt --exclude node_modules --dry-run
```

### 2. React/Next.js to Text for LLM
Flatten a React project, ignoring heavy folders and git metadata.
```bash
python pro_scan.py --dest ./llm_context --in-ext tsx --out-ext txt --exclude node_modules .git .next dist
```

### 3. Solidity Smart Contract Audit
Gather all `.sol` files into a single folder for manual review.
```bash
python pro_scan.py --dest ./audit_prep --in-ext sol --out-ext txt --exclude build tests
```

### 4. Advanced Wildcards
Exclude any folder starting with `test` or `mock`.
```bash
# Note: Wrap wildcards in quotes on Linux/Mac
python pro_scan.py --dest ./output --in-ext py --out-ext txt --exclude "test*" "mock*"
```

---

## 🔍 How It Works

1.  **Scan:** Recursively walks the directory tree from `--root`.
2.  **Filter:** Removes directories matching `--exclude` patterns **before** entering them (efficiency optimization).
3.  **Read:** Opens source files in `r` (Read-Only) mode.
4.  **Header:** Generates a comment based on output extension:
    *   `// ORIGINAL_PATH: src/App.tsx | ARCHIVED: 2023-10-27`
5.  **Write:** Saves to `--dest`. If `App.txt` exists, it saves as `App_1.txt`.

---

## ⚖️ License
Open Source. Feel free to use and modify for your personal workflow.
