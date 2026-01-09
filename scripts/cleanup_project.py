import os
import shutil
import argparse

def cleanup(dry_run=True):
    targets = [
        # Cache folders
        "backend/app/**/__pycache__",
        "backend/app/**/.pytest_cache",
        "frontend/dist",
        # Logs and temp files
        "backend/error.log",
        "backend/logs/*.log",
        "**/*.tmp",
        "**/*.bak",
        "**/.DS_Store",
    ]

    found_items = []
    
    print(f"{' [DRY RUN] ' if dry_run else ' [EXECUTE] '} Starting project cleanup...")
    
    # Simple glob-like recursion for pycache
    for root, dirs, files in os.walk("."):
        if "node_modules" in root:
            continue
            
        for d in dirs:
            if d in ["__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build"]:
                found_items.append(os.path.join(root, d))
        
        for f in files:
            if f.endswith((".log", ".tmp", ".bak", ".DS_Store")) or f == "error.log":
                found_items.append(os.path.join(root, f))

    if not found_items:
        print("No cleanup targets found.")
        return

    print("\nTargets identified for removal:")
    for item in found_items:
        print(f" - {item}")

    if dry_run:
        print("\nDry run completed. No files were deleted.")
        print("Run with '--confirm' to perform actual deletion.")
    else:
        confirm = input(f"\nAre you sure you want to delete {len(found_items)} items? (y/N): ")
        if confirm.lower() == 'y':
            for item in found_items:
                try:
                    if os.path.isdir(item):
                        shutil.rmtree(item)
                    else:
                        os.remove(item)
                    print(f"Deleted: {item}")
                except Exception as e:
                    print(f"Failed to delete {item}: {e}")
            print("\nCleanup finished.")
        else:
            print("\nOperation cancelled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up project artifacts.")
    parser.add_argument("--confirm", action="store_true", help="Perform actual deletion instead of dry run.")
    args = parser.parse_args()
    
    cleanup(dry_run=not args.confirm)
