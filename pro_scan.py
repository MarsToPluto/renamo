#!/usr/bin/env python3
"""
FlatSource v1.3.0
Professional File Aggregation Tool with Smart Extension Mapping.
"""

import os
import sys
import argparse
import datetime
import fnmatch
from typing import List, Dict

# ------------------------------------------------------------------------
# OPTIONAL DEPENDENCY: PROGRESS BAR
# ------------------------------------------------------------------------
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, total=None, unit=""):
        return iterable

# ------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------

def normalize_ext(ext: str) -> str:
    """Ensures extension starts with a dot and is lowercase."""
    ext = ext.strip().lower()
    return ext if ext.startswith('.') else '.' + ext

def get_header_comment(extension: str, source_path: str, root_dir: str) -> str:
    """Generates metadata header based on the OUTPUT extension."""
    ext = normalize_ext(extension)
    
    prefix = ":: "
    
    # Hash Style
    if ext in ['.py', '.rb', '.sh', '.yaml', '.yml', '.conf', '.toml', '.pl', '.dockerfile']:
        prefix = "# "
    # Double Slash Style
    elif ext in ['.c', '.cpp', '.cs', '.java', '.js', '.jsx', '.ts', '.tsx', 
                 '.sol', '.go', '.rs', '.php', '.swift', '.dart', '.txt', '.css', '.scss']:
        prefix = "// "
    # Dash Style
    elif ext in ['.sql', '.lua', '.hs']:
        prefix = "-- "
    # HTML/XML Style
    elif ext in ['.html', '.xml', '.htm', '.svg', '.ejs', '.vue', '.jsp']:
        prefix = "<!-- "

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
    if not exclude_patterns:
        return False
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(dirname, pattern):
            return True
    return False

def count_total_files(root_dir: str, target_exts: List[str], excludes: List[str]) -> int:
    """Pre-scan for progress bar."""
    count = 0
    for current_root, dirs, files in os.walk(root_dir):
        for i in range(len(dirs) - 1, -1, -1):
            if check_exclusions(dirs[i], excludes):
                del dirs[i]
        
        for filename in files:
            # Check if file ends with any of the valid input extensions
            if any(filename.lower().endswith(ext) for ext in target_exts):
                count += 1
    return count

def create_extension_mapping(in_exts: List[str], out_exts: List[str]) -> Dict[str, str]:
    """
    Creates a dictionary mapping Input Extension -> Output Extension.
    Logic:
    1. If only 1 out_ext is provided, map ALL inputs to that 1 output.
    2. If multiple out_exts provided, map 1-to-1.
    3. If out_exts runs out, default to .txt.
    """
    mapping = {}
    normalized_in = [normalize_ext(e) for e in in_exts]
    normalized_out = [normalize_ext(e) for e in out_exts]
    
    # Scenario 1: User wants everything to become ONE format (e.g. .txt)
    if len(normalized_out) == 1:
        target = normalized_out[0]
        for ext in normalized_in:
            mapping[ext] = target
        return mapping

    # Scenario 2: Mixed mapping
    default_fallback = ".txt"
    
    for i, in_ext in enumerate(normalized_in):
        if i < len(normalized_out):
            # Map index to index
            mapping[in_ext] = normalized_out[i]
        else:
            # Fallback if user didn't provide enough output extensions
            mapping[in_ext] = default_fallback
            
    return mapping

# ------------------------------------------------------------------------
# CORE LOGIC
# ------------------------------------------------------------------------

def run_scan_and_move(
    root_dir: str, 
    dest_dir: str, 
    in_exts: List[str], 
    out_exts: List[str], 
    excludes: List[str],
    dry_run: bool
) -> None:
    
    # 1. Create the Mapping
    ext_map = create_extension_mapping(in_exts, out_exts)
    
    # Get list of targets for scanning
    valid_targets = list(ext_map.keys())

    # 2. Print Configuration
    print(f"\n[CONFIGURATION]")
    print(f" Mode:       {'[DRY RUN - SIMULATION]' if dry_run else 'LIVE EXECUTION'}")
    print(f" Root:       {os.path.abspath(root_dir)}")
    print(f" Dest:       {os.path.abspath(dest_dir)}")
    print(f" Excluding:  {excludes}")
    print(f" Mappings:")
    for k, v in ext_map.items():
        print(f"   {k:<8} -> {v}")

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

    # 4. Pre-Scan
    print("\n[INFO] Analyzing file structure...")
    total_files = count_total_files(root_dir, valid_targets, excludes)
    
    if total_files == 0:
        print("[INFO] No files found matching criteria.")
        return

    print(f"[INFO] Found {total_files} files to process.\n")

    # 5. Execution Loop
    files_processed = 0
    
    with tqdm(total=total_files, unit='file') as pbar:
        for current_root, dirs, files in os.walk(root_dir):
            
            # Exclusion Logic
            for i in range(len(dirs) - 1, -1, -1):
                if check_exclusions(dirs[i], excludes):
                    del dirs[i]

            for filename in files:
                # Determine file extension
                _, f_ext = os.path.splitext(filename)
                f_ext = f_ext.lower()
                
                # Check if it's in our map
                if f_ext in ext_map:
                    target_ext = ext_map[f_ext]
                    source_full_path = os.path.join(current_root, filename)
                    
                    try:
                        # --- DRY RUN ---
                        if dry_run:
                            pbar.update(1)
                            files_processed += 1
                            continue 

                        # --- LIVE RUN ---
                        
                        # A. Read
                        with open(source_full_path, 'r', encoding='utf-8', errors='replace') as f_src:
                            content = f_src.read()

                        # B. Destination Path
                        base_name = os.path.splitext(filename)[0]
                        dest_name = f"{base_name}{target_ext}"
                        dest_path = os.path.join(dest_dir, dest_name)

                        # C. Collision Check
                        counter = 1
                        while os.path.exists(dest_path):
                            dest_name = f"{base_name}_{counter}{target_ext}"
                            dest_path = os.path.join(dest_dir, dest_name)
                            counter += 1

                        # D. Header (Pass target_ext so we get correct comment style)
                        header = get_header_comment(target_ext, source_full_path, root_dir)

                        # E. Write
                        with open(dest_path, 'w', encoding='utf-8') as f_dest:
                            f_dest.write(header + "\n\n")
                            f_dest.write(content)
                        
                        pbar.update(1)
                        files_processed += 1

                    except Exception as e:
                        tqdm.write(f"\n[FATAL ERROR] Processing {source_full_path}")
                        tqdm.write(f"Reason: {str(e)}")
                        sys.exit(1)

    print(f"\n[SUCCESS] {'Simulation' if dry_run else 'Operation'} complete.")
    print(f"Processed: {files_processed}/{total_files} files.")

# ------------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------------

def main() -> None:
    TOOL_NAME = "FlatSource"
    VERSION = "1.3.0"

    epilog_text = """
EXAMPLES:
  1. Mixed Mapping (Specific outputs):
     pro_scan --dest ./backup --in-ext js css html --out-ext txt css html
     (Result: .js->.txt, .css->.css, .html->.html)

  2. Default Fallback (Missing output extensions default to .txt):
     pro_scan --dest ./backup --in-ext js css html --out-ext txt css
     (Result: .js->.txt, .css->.css, .html->.txt)

  3. Single Output (Convert everything to .txt):
     pro_scan --dest ./backup --in-ext js css html --out-ext txt
    """

    parser = argparse.ArgumentParser(
        description="PROFESSIONAL FILE MIGRATOR: Recursive scan, flatten, and smart extension mapping.",
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-v', '--version', action='version', version=f'{TOOL_NAME} v{VERSION}')
    
    parser.add_argument('--root', default='.', 
                        help='Root directory to scan.')
    
    parser.add_argument('--dest', required=True, 
                        help='Destination directory.')
    
    parser.add_argument('--in-ext', nargs='+', required=True, 
                        help='List of input extensions (e.g. js css html).')
    
    # CHANGED: nargs='+' allows multiple output extensions
    parser.add_argument('--out-ext', nargs='+', required=True, 
                        help='List of output extensions. Maps 1-to-1 with inputs.')
    
    parser.add_argument('--exclude', nargs='*', default=[], 
                        help='Folder patterns to exclude.')
    
    parser.add_argument('--dry-run', action='store_true', 
                        help='Simulate process.')

    args = parser.parse_args()

    run_scan_and_move(
        root_dir=args.root,
        dest_dir=args.dest,
        in_exts=args.in_ext,
        out_exts=args.out_ext, # Pass list
        excludes=args.exclude,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()