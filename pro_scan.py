import os
import sys
import argparse
import datetime
import fnmatch
from typing import List, Optional

# Try to import tqdm for progress bar, handle it gracefully if missing
try:
    from tqdm import tqdm
except ImportError:
    # If tqdm is not installed, create a dummy wrapper that just returns the iterable
    # This ensures the script runs even without the library.
    def tqdm(iterable, total=None, unit=""):
        return iterable
    print("[INFO] 'tqdm' library not found. Running without progress bar.")
    print("       (Tip: run 'pip install tqdm' for a better experience)")

# ------------------------------------------------------------------------
# TYPE-HINTED HELPER FUNCTIONS
# ------------------------------------------------------------------------

def get_header_comment(extension: str, source_path: str, root_dir: str) -> str:
    """
    Generates the metadata header string.
    """
    ext: str = extension.lower()
    if not ext.startswith('.'): 
        ext = '.' + ext
    
    prefix: str = ":: "
    
    # Python, Ruby, YAML, Shell, Configs
    if ext in ['.py', '.rb', '.sh', '.yaml', '.yml', '.conf', '.toml', '.pl']:
        prefix = "# "
    # C-style, Java, JS, TS, Go, Rust
    elif ext in ['.c', '.cpp', '.cs', '.java', '.js', '.jsx', '.ts', '.tsx', '.sol', '.go', '.rs', '.php', '.swift', '.dart', '.txt']:
        prefix = "// "
    # SQL, Lua
    elif ext in ['.sql', '.lua', '.hs']:
        prefix = "-- "
    # HTML/XML
    elif ext in ['.html', '.xml', '.htm', '.svg']:
        prefix = "<!-- "

    relative_path: str = "UNKNOWN_PATH"
    try:
        relative_path = os.path.relpath(source_path, root_dir)
    except ValueError:
        relative_path = source_path 

    timestamp: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header: str = f"{prefix}ORIGINAL_PATH: {relative_path} | ARCHIVED: {timestamp}"
    
    if prefix == "<!-- ":
        header += " -->"
        
    return header

def check_exclusions(dirname: str, exclude_patterns: List[str]) -> bool:
    """
    Checks if a directory name matches the exclusion list.
    """
    if not exclude_patterns:
        return False
    
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(dirname, pattern):
            return True
    return False

def count_total_files(root_dir: str, in_ext: str, excludes: List[str]) -> int:
    """
    Pre-scans the directory to get a total count for the progress bar.
    """
    count: int = 0
    for current_root, dirs, files in os.walk(root_dir):
        # In-place filtering of directories
        for i in range(len(dirs) - 1, -1, -1):
            if check_exclusions(dirs[i], excludes):
                del dirs[i]
        
        for filename in files:
            if filename.endswith(in_ext):
                count += 1
    return count

# ------------------------------------------------------------------------
# CORE LOGIC
# ------------------------------------------------------------------------

def run_scan_and_move(
    root_dir: str, 
    dest_dir: str, 
    in_ext: str, 
    out_ext: str, 
    excludes: List[str],
    dry_run: bool
) -> None:
    
    # 1. Normalize Extensions
    if not in_ext.startswith('.'): in_ext = '.' + in_ext
    if not out_ext.startswith('.'): out_ext = '.' + out_ext

    print(f"\n[CONFIGURATION]")
    print(f" Mode:       {'[DRY RUN - SIMULATION]' if dry_run else 'LIVE EXECUTION'}")
    print(f" Root:       {os.path.abspath(root_dir)}")
    print(f" Dest:       {os.path.abspath(dest_dir)}")
    print(f" Target:     *{in_ext} -> *{out_ext}")
    print(f" Excluding:  {excludes}")

    # 2. Safety Checks
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

    # 3. Pre-Scan for Progress Bar
    print("\n[INFO] Analyzing file structure...")
    total_files: int = count_total_files(root_dir, in_ext, excludes)
    
    if total_files == 0:
        print("[INFO] No files found matching criteria.")
        return

    print(f"[INFO] Found {total_files} files to process.\n")

    # 4. Processing Loop
    files_processed: int = 0
    
    # Initialize Progress Bar
    # unit='file' makes the bar show "5/100 files"
    with tqdm(total=total_files, unit='file', disable=None) as pbar:
        
        for current_root, dirs, files in os.walk(root_dir):
            
            # Exclusion Logic
            for i in range(len(dirs) - 1, -1, -1):
                if check_exclusions(dirs[i], excludes):
                    del dirs[i]

            for filename in files:
                if filename.endswith(in_ext):
                    source_full_path: str = os.path.join(current_root, filename)
                    
                    try:
                        # --- DRY RUN BRANCH ---
                        if dry_run:
                            # Simulate destination path calculation
                            base_name = os.path.splitext(filename)[0]
                            dest_name = f"{base_name}{out_ext}"
                            dest_path = os.path.join(dest_dir, dest_name)
                            
                            # Using tqdm.write prevents breaking the progress bar layout
                            # tqdm.write(f"[DRY-RUN] Found: {filename} -> Would save to: {dest_name}")
                            pbar.update(1)
                            files_processed += 1
                            continue 

                        # --- LIVE EXECUTION BRANCH ---
                        
                        # A. READ
                        with open(source_full_path, 'r', encoding='utf-8', errors='replace') as f_src:
                            content = f_src.read()

                        # B. RESOLVE PATH
                        base_name = os.path.splitext(filename)[0]
                        dest_name = f"{base_name}{out_ext}"
                        dest_path = os.path.join(dest_dir, dest_name)

                        # C. COLLISION CHECK
                        counter = 1
                        while os.path.exists(dest_path):
                            dest_name = f"{base_name}_{counter}{out_ext}"
                            dest_path = os.path.join(dest_dir, dest_name)
                            counter += 1

                        # D. HEADER GENERATION
                        header = get_header_comment(out_ext, source_full_path, root_dir)

                        # E. WRITE
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
    epilog_text = """
EXAMPLES:
  1. Dry Run (See what happens without moving files):
     python pro_scan.py --dest ./backup --in-ext ts --out-ext txt --dry-run

  2. Real Run (With Progress Bar):
     python pro_scan.py --dest ./backup --in-ext ts --out-ext txt --exclude node_modules
    """

    parser = argparse.ArgumentParser(
        description="PROFESSIONAL FILE MIGRATOR: Recursive scan, flatten, and header stamping.",
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--root', default='.', help='Root directory to scan.')
    parser.add_argument('--dest', required=True, help='Destination directory.')
    parser.add_argument('--in-ext', required=True, help='Input extension.')
    parser.add_argument('--out-ext', required=True, help='Output extension.')
    parser.add_argument('--exclude', nargs='*', default=[], help='Patterns to exclude.')
    
    # The new Dry Run flag
    parser.add_argument('--dry-run', action='store_true', help='Simulate the process without writing files.')

    args = parser.parse_args()

    run_scan_and_move(
        root_dir=args.root,
        dest_dir=args.dest,
        in_ext=args.in_ext,
        out_ext=args.out_ext,
        excludes=args.exclude,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()