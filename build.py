#!/usr/bin/env python3
"""Inline src/engine.js into src/app.html -> index.html (single self-contained file)."""
import pathlib
root = pathlib.Path(__file__).parent
engine = (root / "src/engine.js").read_text()
html = (root / "src/app.html").read_text().replace("/*ENGINE*/", engine)
(root / "index.html").write_text(html)
print("built index.html", len(html), "bytes")
