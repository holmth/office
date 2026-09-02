---
name: office-documents
description: 'Handles Word (.docx) and PowerPoint (.pptx) files when a user asks the agent to summarize, review, compare, extract, or otherwise work with the document. Use this skill whenever the user attaches or references a `.docx` or `.pptx` file and includes an instruction for what to do with it. Always run the bundled extractor first instead of trying to read the Office file directly.'
---

# Office documents

## When to use this skill

Use this skill whenever a user attaches or references:

- a Word document (`.docx`)
- a PowerPoint presentation (`.pptx`)

and asks the agent to do something with it, such as:

- summarize it
- extract decisions or action items
- review it
- compare it with another file
- answer questions about it

This skill only supports modern Office Open XML files: `.docx` and `.pptx`.
If the user provides `.doc` or `.ppt`, ask them to save the file again as
`.docx` or `.pptx` first.

## Required workflow

1. Identify each referenced Office file.
2. Run the matching bundled extractor to convert the file into Markdown.
3. Read the generated Markdown.
4. Follow the user's instruction on that extracted content.
5. If multiple Office files are involved, convert all of them before comparing
   or summarizing them.

Do not try to parse Office binaries ad hoc. Always use the bundled script first.

## Usage

The extractors live in `scripts/`.

### Word documents

```bash
python .github/skills/office-documents/scripts/extract_docx_text.py "/absolute/path/to/file.docx" -o /tmp/office-document.md
```

### PowerPoint presentations

```bash
python .github/skills/office-documents/scripts/extract_pptx_text.py "/absolute/path/to/file.pptx" -o /tmp/office-presentation.md
```

If the user asks about the document without giving a fully qualified path,
confirm the file location before running the script.

## Output expectations

- The Word extractor emits Markdown paragraphs from the document body.
- The PowerPoint extractor emits Markdown grouped by slide.
- After conversion, perform the user's requested task on the extracted
  Markdown rather than on the original binary file.

## Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Unsupported file type` | Legacy Office format like `.doc` or `.ppt` | Ask the user to re-save as `.docx` or `.pptx` |
| `Input path not found` | Wrong or incomplete path | Ask the user to confirm the full path |
| `No readable document content found` | Empty, damaged, or unsupported file structure | Tell the user the file could not be read and ask for a new copy |
