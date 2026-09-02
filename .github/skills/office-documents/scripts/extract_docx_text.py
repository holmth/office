#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract readable Markdown text from a .docx file."
    )
    parser.add_argument("input_path", help="Path to a .docx file")
    parser.add_argument("-o", "--output", help="Write Markdown output to this file")
    return parser.parse_args()


def paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []

    for node in paragraph.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "t" and node.text:
            parts.append(node.text)
        elif tag == "tab":
            parts.append("\t")
        elif tag in {"br", "cr"}:
            parts.append("\n")

    return "".join(parts).strip()


def table_to_markdown(table: ET.Element) -> list[str]:
    rows: list[list[str]] = []

    for row in table.findall("w:tr", WORD_NAMESPACE):
        cells: list[str] = []
        for cell in row.findall("w:tc", WORD_NAMESPACE):
            cell_lines = [
                text
                for paragraph in cell.findall(".//w:p", WORD_NAMESPACE)
                if (text := paragraph_text(paragraph))
            ]
            cells.append("<br>".join(cell_lines))
        if cells:
            rows.append(cells)

    if not rows:
        return []

    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]

    header = normalized_rows[0]
    separator = ["---"] * column_count
    body = normalized_rows[1:]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return lines


def extract_markdown(input_path: Path) -> str:
    if input_path.suffix.lower() != ".docx":
        raise ValueError("Unsupported file type. Expected a .docx file.")

    try:
        with zipfile.ZipFile(input_path) as archive:
            xml_bytes = archive.read("word/document.xml")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input path not found: {input_path}") from exc
    except KeyError as exc:
        raise ValueError("No readable document content found in the .docx file.") from exc
    except zipfile.BadZipFile as exc:
        raise ValueError("The .docx file is invalid or corrupted.") from exc

    root = ET.fromstring(xml_bytes)
    body = root.find("w:body", WORD_NAMESPACE)
    if body is None:
        raise ValueError("No readable document content found in the .docx file.")

    blocks: list[str] = [f"# {input_path.stem}"]

    for child in body:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = paragraph_text(child)
            if text:
                blocks.append(text)
        elif tag == "tbl":
            table_lines = table_to_markdown(child)
            if table_lines:
                blocks.append("\n".join(table_lines))

    if len(blocks) == 1:
        raise ValueError("No readable document content found in the .docx file.")

    return "\n\n".join(blocks) + "\n"


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
