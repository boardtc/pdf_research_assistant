# todo
line deleted from manifest:

The corrupt file was:

```
Session 7/Sadler 2013 Opening-up-feedback-Teaching-learners-to-see Chapter.pdf
```

The error was `/SymbolSetEncoding` — an unusual font encoding that pypdf can't handle. This is a PDF quality issue, not a missing file.

Options:

1. **Try re-downloading** — if you got it from a database, a fresh download might be a cleaner PDF
2. **Install pymupdf** — a better PDF parser that handles more encodings: `pip install paper-qa[pymupdf] --break-system-packages`. This might parse it where pypdf fails.
3. **Leave it out** — it's one chapter, the rest of your Sadler papers are indexed fine.

Option 2 is worth trying. If pymupdf can read it, add the row back to the manifest and delete the index to rebuild.