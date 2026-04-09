import re
from pathlib import Path

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FENCED_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)


def strip_fenced_blocks(content: str) -> str:
    return FENCED_BLOCK_PATTERN.sub("", content)


def check_markdown_links(docs_dir: str):
    files = sorted(Path(docs_dir).rglob("*.md"))
    broken = []

    for markdown_file in files:
        content = strip_fenced_blocks(markdown_file.read_text(encoding="utf-8", errors="ignore"))
        for label, target in LINK_PATTERN.findall(content):
            target = target.strip()

            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue

            if target.startswith("file://"):
                broken.append((markdown_file, label, target))
                continue

            clean_target = target.split("#", 1)[0].split("?", 1)[0]
            if not clean_target:
                continue

            resolved = (markdown_file.parent / clean_target).resolve()
            if not resolved.exists():
                broken.append((markdown_file, label, target))

    return broken

if __name__ == "__main__":
    broken_links = check_markdown_links("docs")
    if broken_links:
        print("Found broken links:")
        for source, label, target in broken_links:
            print(f"{source}: [{label}]({target})")
    else:
        print("No broken internal links found.")
