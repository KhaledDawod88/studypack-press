# Samples

Output from the pipeline in this repo, committed so the result can be checked without building anything.

| File | What it is |
| --- | --- |
| `preview-cover.svg` | Page 1 of the sample pack, the cover, as vector artwork written by `build.py --svg-cover` |

The repository holds text only, so the PDF is not committed. Build it with:

```bash
python3 build.py configs/intro-statistics.json --svg-cover samples/preview-cover.svg
```

or download it from the artifact of the **build sample** workflow run (Actions tab). The PDF embeds three SIL Open Font License typefaces, which is why it is about 2 MB.
