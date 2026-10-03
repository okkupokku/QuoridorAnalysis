# Accuracy evaluation of the Quoridor analysis engine

Run on 2026-10-03. Engine under test: `src/engine.js` (alpha-beta search, evaluation = path-length difference + wall count).
Everything here is reproducible with the scripts in this folder (third-party engines are cloned separately, see bottom).

## 1. What was compared against what

| Reference | What it is | Used for |
|---|---|---|
| Exact solver (`solver.cpp`, written for this test) | Retrograde analysis of every reachable position of small boards: win / loss / draw with perfect play. Validated against the published results at grantslatton.com/solving-quoridor (5x5: second player wins at 0-3 walls; even-height boards: first player wins). | Ground truth for move quality |
| pavlos/Quoridor (C, alpha-beta, ~6 s per move) | Open-source engine | Head-to-head games, move agreement, rules cross-check |
| georgen2003/Quoridor-with-MCTS-agent (C, MCTS) | Open-source engine | Same |
| dimitrijekaranfilovic/quoridor (Python bots) | Open-source engine | Not usable: its wall legality check mutates the shared board (shallow copy), so legality results depend on call order. Excluded. |
| dzionek/quoridorAI (Haskell) | Open-source engine | Not run (no Haskell toolchain; installing one was not approved). |

No open-source tool exists that rates a recorded game move by move, so there is nothing to compare the "analysis report" to directly.
The comparison is therefore at the move/position level.

## 2. Rules agreement (do all engines agree on what is legal?)

209 candidate moves (81 pawn squares + 128 walls) tested in each of 761 positions from varied games.

* Own engine vs exact solver: 0 mismatches in ~77,000 small-board positions (every legal move, every position).
* vs pavlos: identical, except pavlos does not enforce the 10-wall limit when a wall is played by command (267 positions), and in one position it allows a diagonal "jump" through a wall that separates the pawns.
* vs georgen: 6 positions where it allows a diagonal sidestep although the straight jump is possible (the official rules only allow the diagonal when the straight jump is blocked).

In every disagreement, the own engine follows the official rules.

## 3. Ground truth on small boards (exact solver)

Positions come from ~1,500 games per board (mixed random and engine moves). "Winning position" means the side to move can force a win.
"Real error" = the played move turns a won position into a lost one.

| Board | Positions | Depth | Real errors caught (flagged mistake/blunder) | Flags that were real errors | Best move keeps the win | Correct "who is winning" |
|---|---|---|---|---|---|---|
| 4x4, 2 walls | 16,663 | 4 | 88% | 61% | 98.3% | 97% |
| | | 7 | 91% | 78% | 98.5% | 98% |
| 4x4, 3 walls | 17,771 | 4 | 88% | 62% | 98.0% | 96% |
| | | 7 | 90% | 76% | 98.5% | 97% |
| 5x5, 1 wall | 18,741 | 4 | 82% | 68% | 99.9% | 91% |
| | | 7 | 98% | 86% | 100% | 92% |
| 5x5, 2 walls | 24,085 | 4 | 75% | 59% | 97.3% | 89% |
| | | 7 | 79% | 69% | 99.2% | 88% |

* Of the "false alarms" (flagged but the win was kept), 56-87% made the win at least 3 plies slower than the fastest win, so they are real inefficiencies, not noise.
* The drop in win chance separates real errors from non-errors well (AUC 0.88-0.99).
* Accuracy falls as the board and wall count grow, at a fixed depth. That is the direction of travel towards 9x9.
* Caveat: on small boards depth 7 looks over a large part of the whole game. These numbers show the method is sound; they are not a 9x9 accuracy figure.

## 4. 9x9 behaviour (no ground truth exists, so: stability and calibration)

3,061 moves from 45 real games (the engine playing pavlos). Verdicts at each depth compared with a depth-8 reference:

| Depth | Mistake/blunder flags that depth-8 agrees with | Mistakes depth 8 sees that this depth misses | Same best move as depth 8 | Avg. time per move (this Mac, loaded) |
|---|---|---|---|---|
| 3 | 78% | 68% | 75% | not measured |
| 4 (default) | 83% | 66% | 77% | 23 ms |
| 5 | 79% | 48% | 83% | 96 ms |
| 6 | 91% | 35% | 86% | 346 ms |
| 7 | 83% | 22% | 91% | 1.1 s |

* Flags it does raise are usually confirmed by deeper search, but at the default depth it misses about two thirds of what a depth-8 search finds. Verdicts have not converged by depth 8.
* Win-chance calibration against actual outcomes: Brier score 0.167-0.175 (coin flip = 0.25). Correct winner prediction: ~55% early game, ~77% middle, ~90% late. Depth hardly changes this, so the early-game win percentage should be read as "roughly even".

## 5. Against the other engines

**Head-to-head** (own engine at depth 3/4/5 with 2-23 ms per move; 4 random opening plies, both colours):

| Opponent | Wins | Losses | Draws (150-ply cap) | Opponent forfeits (illegal move) | Voided |
|---|---|---|---|---|---|
| pavlos (5-13 s per move) | 13 | 14 | 8 | 55 | 0 |
| georgen MCTS (3-6 s per move) | 54 | 7 | 2 | 7 | 20 (engine crashed / hung / state errors) |

pavlos answers `A1` (never legal) when it has no non-losing move. My depth-6 evaluation said the own engine was clearly ahead in 50 of those 55 positions, so they are counted as pavlos losses, but excluding them the games vs pavlos are even.

**Move agreement** on 140 real positions each (engine asked for its move, own engine asked for its):

| Engine | Same move as own depth 4 / depth 6 | Own depth-6 rating of that engine's move |
|---|---|---|
| pavlos | 59% / 54% | best 68%, good 5%, inaccuracy 13%, mistake 8%, blunder 6% |
| georgen | 43% / 43% | best 66%, good 10%, inaccuracy 8%, mistake 13%, blunder 3% |

## 6. Conclusions

1. Rules are correct (verified against an exact solver and two independent engines).
2. Move choice is strong for its cost: on par with a 6 s-per-move alpha-beta engine, clearly ahead of a 20,000-simulation MCTS engine.
3. Verdicts are reliable when raised and incomplete when not: the default depth finds only about a third of the errors a deeper search finds on 9x9. Depth 6 is about 15x more costly than depth 4 but catches roughly twice as many.
4. The win percentage is a heuristic. Treat it as meaningful in the late game and as "roughly even" early.
5. Limits of this evaluation: no perfect-play reference exists for 9x9; the test games came mostly from engine play, which differs from human games; the opponent engines have their own rule bugs.

## Reproducing

```
git clone https://github.com/pavlosdais/Quoridor pavlos            # make CFLAGS="-O2 -Duint=unsigned"
git clone https://github.com/georgen2003/Quoridor-with-MCTS-agent georgen   # cc -O2 -w -Iinclude src/*.c -lm -o qmcts
clang++ -O2 -std=c++17 -o solver solver.cpp
python3 gen_engine_n.py; cat engine_n.js bridge_n_tail.js > bridge_n.js; cat ../src/engine.js bridge_tail.js > bridge.js
python3 eval_small.py 4 2 1500 2,3,4,5,6,7 gt_4_2.json && python3 gt_report.py gt_4_2.json
python3 match.py pavlos 4 15 m_pavlos_d4.json 12
```

## 7. Stronger reference engines (2026-10-04)

Compared on the same 3,061 9x9 positions (45 games). zquoridor: NNUE + MCTS/alpha-beta, 400 ms per position, root value patched into the UCI output. SigmaQuoridor: AlphaZero-style network (`docs/models_9x9/best.onnx`) with 100 MCTS simulations. Neither tool is vendored here; scripts `zq*.py`, `sigma*.py`, `cmp_engines.py`.

| | Own engine d4 | Own engine d6 | zquoridor | Sigma (100 sims) |
|---|---|---|---|---|
| Games vs zquoridor (500 ms/move, 10 openings x 2 colours) | 0 W / 20 L | 1 W / 19 L | | |
| Brier score vs real outcomes (lower is better) | 0.168 | 0.173 | 0.173 | 0.155 |
| Winner predicted late in game | 90% | 90% | 86% | 96% |
| Same best move as zquoridor | 54% | 55% | | 62% |
| Same best move as Sigma | 57% | 58% | 62% | |
| Moves flagged as mistakes (drop >= 10%) | 201 | 347 | 649 | 507 |
| Own flags confirmed by zquoridor / Sigma | 58% / 49% | 50% / 52% | | 61% (by zquoridor) |
| Reference mistakes also flagged (recall) vs zquoridor / Sigma | 18% / 20% | 27% / 36% | | 48% (vs zquoridor) |

Conclusions: zquoridor is far stronger than the own engine at move choice. The two strong engines agree on mistakes and best moves only moderately (62% best move), so single-move verdicts are inherently uncertain even for strong engines. Sigma is MIT-licensed, ships its weights, and already has a browser (ONNX + JS) implementation, so it is the engine to integrate. zquoridor has no licence file found and is used as a reference only. gedik was not tested (needs a Rust toolchain).

## 8. Integrated engine (SigmaQuoridor in the browser)

The app now analyses with SigmaQuoridor's network plus PUCT search in Web Workers (positions are spread over up to 4 workers; 2 on touch devices). The browser implementation reproduces the Python reference exactly (largest difference 0.0000 at 100 simulations, 0.00005 for the raw network).

Search budget vs quality, same 3,061 positions, judged against zquoridor:

| Simulations per position | Flags confirmed by zquoridor | zquoridor mistakes caught | Same best move | Brier |
|---|---|---|---|---|
| 0 (network only) | 37% | 30% | n/a | 0.162 |
| 8 (Quick) | 60% | 49% | 62% | 0.150 |
| 16 (Normal, default) | 61% | 50% | 63% | 0.150 |
| 100 | 61% | 48% | 62% | 0.155 |
| Old built-in engine, depth 4 | 58% | 18% | 54% | 0.168 |

Speed: a 40-move game at Normal takes about 3 s on an M-series Mac (4 workers); expect several times longer on a phone.
