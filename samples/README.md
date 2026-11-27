# Samples

Output from the pipeline in this repo, committed so the result can be checked without building anything.

| File | What it is |
| --- | --- |
| `studypack-intro-statistics.html` | The full nine-page study pack for the sample course, as one self-contained HTML document (open it in any browser) |
| `preview-cover.svg` | Page 1, the cover, as vector artwork written by `build.py --svg-cover` |

The PDF is not committed: the repository holds text only. Build it with:

```bash
python3 build.py configs/intro-statistics.json
```

or download it from the artifact of the `build sample` workflow run (Actions tab). The PDF embeds three SIL Open Font License typefaces, which is why it is about 2 MB.
