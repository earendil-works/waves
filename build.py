#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["minijinja", "pyyaml", "markdown"]
# ///
from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path
from typing import Any, Tuple

from minijinja import Environment, safe, load_from_path

import yaml
import markdown as md_lib

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "_templates"
STATIC_DIR = ROOT / "_static"
BUILD_DIR = ROOT / "_build"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_frontmatter(raw: str) -> Tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    fm_text = match.group(1)
    body = raw[match.end() :]
    if yaml is not None:
        data = yaml.safe_load(fm_text) or {}
    else:
        data = {}
        for line in fm_text.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data, body


def render_markdown(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    return md_lib.markdown(text, extensions=["extra"])


def slug_for_path(path: Path) -> str:
    rel = path.relative_to(ROOT)
    if rel.name == "_index.md":
        return "/"
    without_ext = rel.with_suffix("")
    return "/" + "/".join(without_ext.parts) + "/"


def output_path_for(path: Path) -> Path:
    rel = path.relative_to(ROOT)
    if rel.name == "_index.md":
        return BUILD_DIR / "index.html"
    without_ext = rel.with_suffix("")
    return BUILD_DIR / without_ext / "index.html"


def iter_markdown_files() -> list[Path]:
    markdown_files: list[Path] = []
    for root, dirs, files in os.walk(ROOT):
        root_path = Path(root)
        # Skip build artifacts and template/static dirs
        dirs[:] = [d for d in dirs if d not in {"_build", "_templates", "_static", ".git"}]
        for filename in files:
            if not filename.endswith(".md"):
                continue
            path = root_path / filename
            markdown_files.append(path)
    return markdown_files


def build() -> None:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, BUILD_DIR / "static")

    env = Environment(loader=load_from_path(str(TEMPLATES_DIR)))

    for md_path in iter_markdown_files():
        raw = md_path.read_text()
        frontmatter, body = parse_frontmatter(raw)
        template_name = frontmatter.get("template", "index") + ".html"
        html_body = render_markdown(body)
        output_path = output_path_for(md_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rendered = env.render_template(
            template_name,
            title=frontmatter.get("title", "Earendil"),
            page=frontmatter,
            content=safe(html_body),
            slug=slug_for_path(md_path),
        )
        output_path.write_text(rendered)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the site.")
    parser.add_argument("command", nargs="?", default="build")
    args = parser.parse_args()

    if args.command != "build":
        raise SystemExit(f"Unknown command: {args.command}")
    build()


if __name__ == "__main__":
    main()
