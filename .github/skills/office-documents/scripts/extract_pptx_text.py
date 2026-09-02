#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

DRAWING_NAMESPACE = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
SLIDE_PATTERN = re.compile(r"ppt/slides/slide(\d+)\.xml$")
NOTES_PATTERN = "ppt/notesSlides/notesSlide{slide_number}.xml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract readable Markdown text from a .pptx file."
    )
    parser.add_argument("input_path", help="Path to a .pptx file")
    parser.add_argument("-o", "--output", help="Write Markdown output to this file")
    return parser.parse_args()


def extract_paragraphs(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    paragraphs: list[str] = []

    for paragraph in root.findall(".//a:p", DRAWING_NAMESPACE):
        runs = [node.text or "" for node in paragraph.findall(".//a:t", DRAWING_NAMESPACE)]
        text = "".join(runs).strip()
        if text:
            paragraphs.append(text)

    return paragraphs


def extract_markdown(input_path: Path) -> str:
    if input_path.suffix.lower() != ".pptx":
        raise ValueError("Unsupported file type. Expected a .pptx file.")

    try:
        with zipfile.ZipFile(input_path) as archive:
            slide_names = sorted(
                (
                    name
                    for name in archive.namelist()
                    if SLIDE_PATTERN.match(name)
                ),
                key=lambda name: int(SLIDE_PATTERN.match(name).group(1)),
            )

            if not slide_names:
                raise ValueError("No readable presentation content found in the .pptx file.")

            sections: list[str] = [f"# {input_path.stem}"]

            for slide_name in slide_names:
                slide_number = int(SLIDE_PATTERN.match(slide_name).group(1))
                slide_lines = extract_paragraphs(archive.read(slide_name))
                notes_name = NOTES_PATTERN.format(slide_number=slide_number)
                notes_lines = (
                    extract_paragraphs(archive.read(notes_name))
                    if notes_name in archive.namelist()
                    else []
                )

                section_lines = [f"## Slide {slide_number}"]
                if slide_lines:
                    section_lines.extend(f"- {line}" for line in slide_lines)
                if notes_lines:
                    section_lines.append("")
                    section_lines.append("### Speaker notes")
                    section_lines.extend(f"- {line}" for line in notes_lines)

                sections.append("\n".join(section_lines))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input path not found: {input_path}") from exc
    except zipfile.BadZipFile as exc:
        raise ValueError("The .pptx file is invalid or corrupted.") from exc
    except ET.ParseError as exc:
        raise ValueError("No readable presentation content found in the .pptx file.") from exc

    return "\n\n".join(sections) + "\n"


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_path).expanduser()

    try:
        markdown = extract_markdown(input_path)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
