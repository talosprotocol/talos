"""Talos Wiki Sync Script."""

# nosec

import os
import subprocess  # nosec
import sys


def sync_wiki(src_dir: str, dest_dir: str) -> None:
    """Synchronize source documentation to destination wiki."""
    if not os.path.exists(src_dir):
        print(f"Source directory {src_dir} does not exist.")
        return

    if not os.path.exists(dest_dir):
        print(f"Destination directory {dest_dir} does not exist.")
        return

    # 1. Clean destination (except .git)
    for root, dirs, files in os.walk(dest_dir):
        if ".git" in dirs:
            dirs.remove(".git")
        for file in files:
            os.remove(os.path.join(root, file))

    # 2. Copy and transform files
    # Flattening structure as GitHub Wikis are flat
    for root, _dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
            src_path = os.path.join(root, file)
            # Flatten name: dir-subdir-file.md
            rel_path = os.path.relpath(src_path, src_dir)
            dest_name = rel_path.replace(os.sep, "-")
            dest_path = os.path.join(dest_dir, dest_name)

            print(f"Syncing {rel_path} -> {dest_name}")
            with open(src_path, encoding="utf-8") as f:
                content = f.read()

            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(content)

    # 3. Git operations
    try:
        subprocess.check_output(  # nosec
            ["git", "add", "."], cwd=dest_dir, stderr=subprocess.STDOUT
        )
        status = subprocess.check_output(  # nosec
            ["git", "status", "--porcelain"],
            cwd=dest_dir,
            stderr=subprocess.STDOUT,
        ).decode()
        if not status.strip():
            print("No changes to sync.")
            return

        subprocess.check_output(  # nosec
            ["git", "commit", "-m", "Sync wiki from docs"],
            cwd=dest_dir,
            stderr=subprocess.STDOUT,
        )
        print("Changes committed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e.output.decode()}")
        sys.exit(1)


def update_home(dest_dir: str, src_rel: str) -> None:
    """Special handling for Home.md."""
    src_file = os.path.join(dest_dir, src_rel.replace(os.sep, "-"))
    home_file = os.path.join(dest_dir, "Home.md")

    if os.path.exists(src_file):
        print(f"Updating Home.md from {src_rel}")
        with open(src_file, encoding="utf-8") as f:
            content = f.read()
        with open(home_file, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print(f"  Warning: Root file {src_rel} not found")

    # 3. Handle specific transformations inside files (link updating)
    # handles [[Page-Name]] or [Link](Page-Name) correctly in a
    # flattened space.


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sync_wiki.py <src_dir> <dest_dir>")
        sys.exit(1)
    sync_wiki(sys.argv[1], sys.argv[2])
