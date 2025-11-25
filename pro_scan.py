#!/usr/bin/env python3
"""
FlatSource: Professional File Aggregation & Migration Tool.
Scans recursive directories, applies filters, and flattens files into a 
single directory with metadata headers for auditing or LLM context ingestion.
"""

import os
import sys
import argparse
import datetime
import fnmatch
from typing import List

# ------------------------------------------------------------------------
# OPTIONAL DEPENDENCY: PROGRESS BAR
# ------------------------------------------------------------------------
try:
    from tqdm import tqdm
except ImportError:
    # Fallback if user doesn't have tqdm installed
    def tqdm(iterable, total=None, unit=""):
        return iterable

# ------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------

def get_header_comment(extension: str, source_path: str, root_dir: str) -> str:
    """
    Generates a standardized metadata header based on file extension.
    Example: // ORIGINAL_PATH: src/app.ts | ARCHIVED: 2023-10-27
    """
    ext = extension.lower()
    if not ext.startswith('.'): 
        ext = '.' + ext
    
    prefix = ":: "
    
    # Hash Style (Python, Shell, YAML, TOML, Configs)
    if ext in ['.py', '.rb', '.sh', '.yaml', '.yml', '.conf', '.toml', '.pl', '.dockerfile']:
        prefix = "# "
    # Double Slash Style (C, Java, JS, TS, Solidity, Go, Rust, PHP, Swift)
    elif ext in ['.c', '.cpp', '.cs', '.java', '.js', '.jsx', '.ts', '.tsx', 
                 '.sol', '.go', '.rs', '.php', '.swift', '.dart', '.txt', '.css', '.scss']:
        prefix = "// "
    # Dash Style (SQL, Lua, Haskell)
    elif ext in ['.sql', '.lua', '.hs']:
        prefix = "-- "
    # HTML/XML Style (Requires closing tag)
    elif ext in ['.html', '.xml', '.htm', '.svg', '.ejs', '.vue', '.jsp']:
        prefix = "<!-- "

    # Calculate relative path safely
    try:
        relative_path = os.path.relpath(source_path, root_dir)
    except ValueError:
        relative_path = source_path 

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"{prefix}ORIGINAL_PATH: {relative_path} | ARCHIVED: {timestamp}"
    
    if prefix == "<!-- ":
        header += " -->"
        
    return header

def check_exclusions(dirname: str, exclude_patterns: List[str]) -> bool:
    """Returns True if a directory name matches any exclusion pattern."""
    if not exclude_patterns:
        return False
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(dirname, pattern):
            return True
    return False

def is_target_file(filename: str, extensions: List[str]) -> bool:
    """Checks if filename ends with ANY of the provided extensions (Case Insensitive)."""
    for ext in extensions:
        if filename.lower().endswith(ext.lower()):
            return True
    return False

def count_total_files(root_dir: str, in_exts: List[str], excludes: List[str]) -> int:
    """Pre-scans the directory tree to calculate total workload for the progress bar."""
    count = 0
    for current_root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip excluded folders
        for i in range(len(dirs) - 1, -1, -1):
            if check_exclusions(dirs[i], excludes):
                del dirs[i]
        
        for filename in files:
            if is_target_file(filename, in_exts):
                count += 1
    return count

# ------------------------------------------------------------------------
# CORE LOGIC
# ------------------------------------------------------------------------

def run_scan_and_move(
    root_dir: str, 
    dest_dir: str, 
    in_exts: List[str], 
    out_ext: str, 
    excludes: List[str],
    dry_run: bool
) -> None:
    
    # 1. Normalize Input Extensions (Ensure they start with dot)
    normalized_in_exts = []
    for ext in in_exts:
        if not ext.startswith('.'):
            normalized_in_exts.append('.' + ext)
        else:
            normalized_in_exts.append(ext)

    # Normalize Output Extension
    if not out_ext.startswith('.'): 
        out_ext = '.' + out_ext

    # 2. Print Configuration
    print(f"\n[CONFIGURATION]")
    print(f" Mode:       {'[DRY RUN - SIMULATION]' if dry_run else 'LIVE EXECUTION'}")
    print(f" Root:       {os.path.abspath(root_dir)}")
    print(f" Dest:       {os.path.abspath(dest_dir)}")
    print(f" Targets:    {normalized_in_exts} -> *{out_ext}")
    print(f" Excluding:  {excludes}")

    # 3. Validation
    if not os.path.exists(root_dir):
        print(f"[FATAL] Root directory not found: {root_dir}")
        sys.exit(1)

    if not dry_run:
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir)
            except OSError as e:
                print(f"[FATAL] Failed to create destination: {e}")
                sys.exit(1)

    # 4. Pre-Scan Analysis
    print("\n[INFO] Analyzing file structure...")
    total_files = count_total_files(root_dir, normalized_in_exts, excludes)
    
    if total_files == 0:
        print("[INFO] No files found matching criteria.")
        return

    print(f"[INFO] Found {total_files} files to process.\n")

    # 5. Execution Loop
    files_processed = 0
    
    # Initialize Progress Bar
    with tqdm(total=total_files, unit='file') as pbar:
        for current_root, dirs, files in os.walk(root_dir):
            
            # Smart Exclusion: Remove excluded folders from walk traversal
            for i in range(len(dirs) - 1, -1, -1):
                if check_exclusions(dirs[i], excludes):
                    del dirs[i]

            for filename in files:
                if is_target_file(filename, normalized_in_exts):
                    source_full_path = os.path.join(current_root, filename)
                    
                    try:
                        # --- DRY RUN BRANCH ---
                        if dry_run:
                            pbar.update(1)
                            files_processed += 1
                            continue 

                        # --- LIVE EXECUTION BRANCH ---
                        
                        # A. Safe Read
                        with open(source_full_path, 'r', encoding='utf-8', errors='replace') as f_src:
                            content = f_src.read()

                        # B. Determine Destination Path
                        base_name = os.path.splitext(filename)[0]
                        dest_name = f"{base_name}{out_ext}"
                        dest_path = os.path.join(dest_dir, dest_name)

                        # C. Collision Handling (Append _1, _2...)
                        counter = 1
                        while os.path.exists(dest_path):
                            dest_name = f"{base_name}_{counter}{out_ext}"
                            dest_path = os.path.join(dest_dir, dest_name)
                            counter += 1

                        # D. Generate Metadata Header
                        header = get_header_comment(out_ext, source_full_path, root_dir)

                        # E. Safe Write
                        with open(dest_path, 'w', encoding='utf-8') as f_dest:
                            f_dest.write(header + "\n\n")
                            f_dest.write(content)
                        
                        pbar.update(1)
                        files_processed += 1

                    except Exception as e:
                        # Fail-Fast on critical errors
                        tqdm.write(f"\n[FATAL ERROR] Processing {source_full_path}")
                        tqdm.write(f"Reason: {str(e)}")
                        sys.exit(1)

    print(f"\n[SUCCESS] {'Simulation' if dry_run else 'Operation'} complete.")
    print(f"Processed: {files_processed}/{total_files} files.")

# ------------------------------------------------------------------------
# ENTRY POINT & CLI CONFIGURATION
# ------------------------------------------------------------------------

def main() -> None:
    TOOL_NAME = "FlatSource"
    VERSION = "1.2.0"

    epilog_text = """
EXAMPLES:
  1. Dry Run (Check what will happen):
     pro_scan --dest ./backup --in-ext js ts --out-ext txt --dry-run

  2. Standard Usage (Multiple Extensions):
     pro_scan --dest ./output --in-ext js jsx ts tsx --out-ext txt --exclude node_modules

  3. Smart Contract Audit (Solidity to Text):
     pro_scan --dest ./audit --in-ext sol --out-ext txt --exclude build tests

  4. Exclude Specific Patterns:
     pro_scan --dest ./flat --in-ext py --out-ext txt --exclude "test*" "mock*"
    """

    parser = argparse.ArgumentParser(
        description="PROFESSIONAL FILE MIGRATOR: Recursive scan, flatten, and header stamping.",
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-v', '--version', action='version', version=f'{TOOL_NAME} v{VERSION}')
    
    parser.add_argument('--root', default='.', 
                        help='Root directory to start scanning (Default: current dir).')
    
    parser.add_argument('--dest', required=True, 
                        help='Destination directory for flattened files.')
    
    parser.add_argument('--in-ext', nargs='+', required=True, 
                        help='List of input extensions to find (e.g. js ts css html).')
    
    parser.add_argument('--out-ext', required=True, 
                        help='Output extension for the new files (e.g. txt).')
    
    parser.add_argument('--exclude', nargs='*', default=[], 
                        help='List of folder patterns to ignore (supports wildcards *).')
    
    parser.add_argument('--dry-run', action='store_true', 
                        help='Simulate the process without writing any files.')

    args = parser.parse_args()

    run_scan_and_move(
        root_dir=args.root,
        dest_dir=args.dest,
        in_exts=args.in_ext,
        out_ext=args.out_ext,
        excludes=args.exclude,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()