#!/usr/bin/env python3
"""Prepare paired Markdown posts and standalone HTML notes for Hugo."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path


RETURN_LABEL = "Biography &amp; Blog"
RETURN_STYLE = """<style id="biography-blog-return-style">
  .biography-blog-return {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 10000;
    display: inline-flex;
    align-items: center;
    padding: 0.55rem 0.8rem;
    border: 1px solid #ddd8d0;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
    color: #4a3868 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 0.8rem;
    font-weight: 650;
    line-height: 1.2;
    text-decoration: none !important;
  }
  .biography-blog-return:hover {
    border-color: #8a4baf;
    color: #6f368f !important;
  }
  @media (max-width: 700px) {
    .biography-blog-return {
      top: 0.6rem;
      right: 0.6rem;
      padding: 0.45rem 0.65rem;
      font-size: 0.74rem;
    }
  }
</style>"""
RETURN_LINK = (
    '<a class="biography-blog-return" href="/" '
    'aria-label="Return to biography and blog">&larr; Biography &amp; Blog</a>'
)


def yaml_string(value: str) -> str:
    """Return a JSON-quoted string, which is also valid YAML."""
    return json.dumps(value, ensure_ascii=False)


def find_repository(path: Path) -> Path | None:
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def file_date(path: Path, default_date: str | None) -> str:
    if default_date:
        return default_date

    repository = find_repository(path.resolve())
    if repository:
        try:
            relative_path = path.resolve().relative_to(repository)
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cs", "--", str(relative_path)],
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
            )
            commit_date = result.stdout.strip()
            if commit_date:
                return commit_date
        except (OSError, ValueError):
            pass

    return dt.date.today().isoformat()


def clean_inline_markdown(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", value)
    value = re.sub(r"[*_~]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def extract_title_and_subtitle(text: str, slug: str) -> tuple[str, str, str]:
    lines = text.splitlines()
    title_index = next(
        (index for index, line in enumerate(lines) if re.match(r"^#\s+\S", line)),
        None,
    )
    title = slug.replace("-", " ").title()
    subtitle = ""

    if title_index is not None:
        title = clean_inline_markdown(re.sub(r"^#\s+", "", lines[title_index]))
        del lines[title_index]

        while title_index < len(lines) and not lines[title_index].strip():
            del lines[title_index]

        if title_index < len(lines):
            match = re.fullmatch(r"\s*([*_])([^*_].*?)\1\s*", lines[title_index])
            if match:
                subtitle = clean_inline_markdown(match.group(2))
                del lines[title_index]

    body = "\n".join(lines).lstrip("\n").rstrip() + "\n"
    return title, subtitle, body


def add_external_link(front_matter: str, slug: str) -> str:
    if re.search(r"(?m)^external_link\s*:", front_matter):
        return front_matter
    return front_matter.rstrip() + f'\nexternal_link: "/notes/{slug}/"\n'


def prepare_markdown(path: Path, has_html: bool, default_date: str | None) -> bool:
    original = path.read_text(encoding="utf-8")
    slug = path.parent.name

    if original.startswith("---\n"):
        closing_match = re.search(r"(?m)^---\s*$", original[4:])
        if not closing_match or not has_html:
            return False

        closing_start = 4 + closing_match.start()
        front_matter = original[4:closing_start]
        updated_front_matter = add_external_link(front_matter, slug)
        if updated_front_matter == front_matter:
            return False

        body_start = 4 + closing_match.end()
        updated = f"---\n{updated_front_matter}---{original[body_start:]}"
    else:
        title, subtitle, body = extract_title_and_subtitle(original, slug)
        date = file_date(path, default_date)
        summary = subtitle or f"Technical notes on {title}."
        metadata = [
            "---",
            f"title: {yaml_string(title)}",
        ]
        if subtitle:
            metadata.append(f"subtitle: {yaml_string(subtitle)}")
        metadata.extend(
            [
                f"summary: {yaml_string(summary)}",
                "authors:",
                "  - admin",
                "tags:",
                "  - Bioinformatics",
                "categories:",
                "  - Technical Notes",
                f'date: "{date}"',
                f'lastmod: "{date}"',
                "featured: false",
                "draft: false",
                "toc: true",
                "math: true",
            ]
        )
        if has_html:
            metadata.append(f'external_link: "/notes/{slug}/"')
        metadata.extend(["---", ""])
        updated = "\n".join(metadata) + "\n" + body

    path.write_text(updated, encoding="utf-8")
    return True


def prepare_html(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = original

    if not re.search(r"<meta\s+[^>]*name=[\"']viewport[\"']", updated, re.I):
        updated, count = re.subn(
            r"</head\s*>",
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>',
            updated,
            count=1,
            flags=re.I,
        )
        if count == 0:
            print(f"warning: {path} has no closing </head>; viewport was not added")

    if "Biography &amp; Blog" not in updated and "Biography & Blog" not in updated:
        updated, style_count = re.subn(
            r"</head\s*>",
            RETURN_STYLE + "\n</head>",
            updated,
            count=1,
            flags=re.I,
        )
        updated, link_count = re.subn(
            r"(<body(?:\s[^>]*)?>)",
            lambda match: match.group(1) + "\n" + RETURN_LINK,
            updated,
            count=1,
            flags=re.I,
        )
        if style_count == 0 or link_count == 0:
            print(f"warning: {path} is not a complete HTML document; return button was not added")

    if updated == original:
        return False

    path.write_text(updated.rstrip() + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "academic-start",
        help="Hugo site root (defaults to source/academic-start)",
    )
    parser.add_argument(
        "--default-date",
        help="Date for new front matter when Git has no file date (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    site_root = args.site_root.resolve()
    posts_root = site_root / "content" / "post"
    notes_root = site_root / "static" / "notes"
    changes: list[str] = []

    for markdown_path in sorted(posts_root.glob("*/index.md")):
        html_path = notes_root / markdown_path.parent.name / "index.html"
        if prepare_markdown(markdown_path, html_path.exists(), args.default_date):
            changes.append(str(markdown_path.relative_to(site_root)))

    for html_path in sorted(notes_root.glob("*/index.html")):
        if prepare_html(html_path):
            changes.append(str(html_path.relative_to(site_root)))

    if changes:
        print("Prepared blog files:")
        for changed_path in changes:
            print(f"  {changed_path}")
    else:
        print("Blog files are already prepared.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
