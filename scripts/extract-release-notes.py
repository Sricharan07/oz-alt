#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def extract_notes(changelog: Path, version: str) -> str:
    text = changelog.read_text(encoding="utf-8")
    headings: list[tuple[int, str, int]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            headings.append((offset, line[3:].strip(), len(line)))
        offset += len(line)
    wanted = version.removeprefix("v")
    for index, (start, heading, heading_len) in enumerate(headings):
        normalized = heading.removeprefix("v")
        if normalized == wanted or heading.lower() == "unreleased":
            end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
            notes = text[start + heading_len : end].strip()
            if notes:
                return notes + "\n"
    return f"Release {version}\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changelog", default="CHANGELOG.md")
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    Path(args.output).write_text(
        extract_notes(Path(args.changelog), args.version),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
