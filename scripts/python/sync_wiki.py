"""Talos Wiki Sync Script (Premium Edition)."""

# nosec

import os
import re
import subprocess  # nosec
import sys


def transform_links(content: str) -> str:
    """Transform relative markdown links to flattened wiki format."""

    def replacer(match):
        text = match.group(1)
        path = match.group(2)
        anchor = match.group(3) or ""

        if path.startswith("http") or path.startswith("mailto"):
            return match.group(0)

        clean_path = re.sub(r"^[./\\]+", "", path)
        new_path = clean_path.replace(".md", "").replace("/", "-").replace("\\", "-")
        return f"[{text}]({new_path}{anchor})"

    pattern = r"\[([^\]]+)\]\(([^)#\s]+\.md)(#[^)]+)?\)"
    return re.sub(pattern, replacer, content)


def generate_sidebar(dest_dir: str) -> None:
    """Generate _Sidebar.md with professional styling."""

    # Header & Status
    sidebar_content = "## 🛡️ Talos Protocol\n"
    sidebar_content += "> **v5.15** | Phase 15\n\n"
    sidebar_content += "### 🏛️ [[Home]]\n\n"

    sections = [
        ("🚀 Get Started", ["getting-started"]),
        ("🏛️ Architecture", ["architecture"]),
        ("✨ Core Features", ["features"]),
        ("🛠️ SDKs", ["sdk"]),
        ("📖 Guides", ["guides"]),
        ("🔒 Security", ["security"]),
        ("📊 Testing & Health", ["testing"]),
        ("📍 Roadmap & Research", ["research"]),
        ("📚 Reference", ["reference"]),
        ("💼 Business", ["business"]),
        ("🎨 Templates", ["templates"]),
    ]

    # Get all flattened files
    files = sorted(
        [
            f
            for f in os.listdir(dest_dir)
            if f.endswith(".md") and not f.startswith("_") and f != "Home.md"
        ]
    )

    for title, prefixes in sections:
        sidebar_content += f"### {title}\n"
        count = 0
        for f in files:
            for prefix in prefixes:
                if f.startswith(f"{prefix}-"):
                    name = f.replace(f"{prefix}-", "").replace(".md", "").replace("-", " ").title()
                    link = f.replace(".md", "")
                    sidebar_content += f"- [[{name}|{link}]]\n"
                    count += 1
                    break
        if count == 0:
            sidebar_content += "- (None)\n"
        sidebar_content += "\n"

    with open(os.path.join(dest_dir, "_Sidebar.md"), "w", encoding="utf-8") as f:
        f.write(sidebar_content)
    print("Generated Premium _Sidebar.md")


def update_home(dest_dir: str, src_rel: str) -> None:
    """Special handling for Home.md."""
    src_file_name = src_rel.replace(os.sep, "-")
    src_path = os.path.join(dest_dir, src_file_name)
    home_file = os.path.join(dest_dir, "Home.md")

    if os.path.exists(src_path):
        print(f"Updating Home.md from {src_file_name}")
        with open(src_path, encoding="utf-8") as f:
            content = f.read()

        content = transform_links(content)

        with open(home_file, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print(f"  Warning: Root file {src_rel} not found")


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
    for root, _dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, src_dir)

            if rel_path.startswith("."):  # Skip .agent, etc.
                continue

            dest_name = rel_path.replace(os.sep, "-")
            dest_path = os.path.join(dest_dir, dest_name)

            print(f"Syncing {rel_path} -> {dest_name}")
            with open(src_path, encoding="utf-8") as f:
                content = f.read()

            content = transform_links(content)

            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(content)

    # 3. Special handling for Home.md
    update_home(dest_dir, "README-Home.md")

    # 4. Generate Sidebar
    generate_sidebar(dest_dir)

    # 5. Git operations
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
            ["git", "commit", "-m", "Sync wiki: Redesign v5.15"],
            cwd=dest_dir,
            stderr=subprocess.STDOUT,
        )
        print("Changes committed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e.output.decode()}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sync_wiki.py <src_dir> <dest_dir>")
        sys.exit(1)
    sync_wiki(sys.argv[1], sys.argv[2])
