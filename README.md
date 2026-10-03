# Quoridor Analysis

Mobile-friendly web app for recording a physical Quoridor game and analyzing it afterwards:
move-by-move ratings (best / good / inaccuracy / mistake / blunder), a win-chance graph, and
the point where the game turned.

- `index.html` is the built, self-contained app (open it directly or host it, e.g. GitHub Pages).
- `src/engine.js` holds the rules and the alpha-beta analysis engine; `src/app.html` is the UI.
- `python3 build.py` inlines the engine into `src/app.html` and writes `index.html`.

Notation: pawn moves are the destination square (`e2`); walls are the bottom-left square of the
2x2 block they sit in plus `h` or `v` (`e3h`).
