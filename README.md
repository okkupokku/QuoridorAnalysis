# Quoridor Analysis

Mobile-friendly web app for recording a physical Quoridor game and analyzing it afterwards:
move-by-move ratings (best / good / inaccuracy / mistake / blunder), a win-chance graph, and
the point where the game turned.

- Analysis uses the [SigmaQuoridor](https://github.com/bartolomeo3000/SigmaQuoridor) neural network
  (MIT, vendored in `engine/sigma/`) with a short tree search, run in Web Workers via
  [ONNX Runtime Web](https://github.com/microsoft/onnxruntime) (MIT, `engine/ort/`). It works offline once loaded
  and needs a web server (GitHub Pages or `python3 -m http.server`), not `file://`.
  If the network cannot load, the app falls back to the built-in alpha-beta engine (`src/engine.js`).
- `index.html` is built from `src/app.html` + `src/engine.js` by `python3 build.py`; `sigma_worker.js` runs the network.
- Accuracy measurements: `bench/REPORT.md`.

Notation: pawn moves are the destination square (`e2`); walls are the bottom-left square of the
2x2 block they sit in plus `h` or `v` (`e3h`).
