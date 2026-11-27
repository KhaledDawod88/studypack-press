# Samples

Rendered output from the pipeline in this repo, committed so the result can be checked without building anything.

| File | What it is |
| --- | --- |
| `studypack-intro-statistics.pdf` | The full nine-page study pack for the sample course (A4, print-ready) |
| `preview-cover.png` | Page 1, the cover |
| `preview-topic.png` | Page 3, a topic page (objectives, key ideas, formula cards, worked example, self-check) |
| `preview-formula-sheet.png` | Page 9, the one-page formula sheet |

Rebuild them with:

```bash
python3 build.py configs/intro-statistics.json --preview-pages 1,3,9
```

The PNGs are page 1, 3 and 9 at 110 dpi. The PDF embeds three SIL Open Font License typefaces, which is why it is about 2 MB.
