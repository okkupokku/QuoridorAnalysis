// Quoridor rules + analysis engine. Runs in the page (rules) and in a Web Worker (analysis).
// Coordinates: x = column 0..8 (a..i), y = row 0..8 (1..9). White (player 0) starts e1 and
// races to row 9; Black (player 1) starts e9 and races to row 1.
// Walls sit on an 8x8 grid of intersections (c, r): the corner shared by cells
// (c,r),(c+1,r),(c,r+1),(c+1,r+1). Notation uses the bottom-left cell: "e3h" / "e3v".
//   h wall: lies on the top edge of cells (c,r),(c+1,r)   (blocks vertical movement)
//   v wall: lies on the right edge of cells (c,r),(c,r+1) (blocks horizontal movement)
var Quor = (function () {
  var LET = 'abcdefghi';
  var DX = [0, 0, 1, -1], DY = [1, -1, 0, 0];

  function newState() {
    return { px: [4, 4], py: [0, 8], wl: [10, 10], h: new Uint8Array(64), v: new Uint8Array(64), turn: 0 };
  }
  function goalRow(p) { return p === 0 ? 8 : 0; }

  function blocked(s, x, y, d) {
    var h = s.h, v = s.v;
    switch (d) {
      case 0: return y === 8 || (x < 8 && h[y * 8 + x] === 1) || (x > 0 && h[y * 8 + x - 1] === 1);
      case 1: return y === 0 || (x < 8 && h[(y - 1) * 8 + x] === 1) || (x > 0 && h[(y - 1) * 8 + x - 1] === 1);
      case 2: return x === 8 || (y < 8 && v[y * 8 + x] === 1) || (y > 0 && v[(y - 1) * 8 + x] === 1);
      default: return x === 0 || (y < 8 && v[y * 8 + x - 1] === 1) || (y > 0 && v[(y - 1) * 8 + x - 1] === 1);
    }
  }

  // Legal pawn destinations for player p (includes jumps), as [[x,y],...]
  function pawnMoves(s, p) {
    var o = 1 - p, x = s.px[p], y = s.py[p], out = [];
    for (var d = 0; d < 4; d++) {
      if (blocked(s, x, y, d)) continue;
      var tx = x + DX[d], ty = y + DY[d];
      if (tx !== s.px[o] || ty !== s.py[o]) { out.push([tx, ty]); continue; }
      if (!blocked(s, tx, ty, d)) { out.push([tx + DX[d], ty + DY[d]]); continue; }
      for (var e = 0; e < 4; e++) {
        if (e === d || e === (d ^ 1)) continue;
        if (!blocked(s, tx, ty, e)) out.push([tx + DX[e], ty + DY[e]]);
      }
    }
    return out;
  }

  var Q = new Int8Array(81), D = new Int8Array(81), PAR = new Int8Array(81);
  var lastPath = [];
  // Shortest distance (ignoring pawns) for player p to its goal row, or -1 if cut off.
  function bfs(s, p, wantPath) {
    var goal = goalRow(p);
    D.fill(-1);
    var start = s.py[p] * 9 + s.px[p], head = 0, tail = 0;
    Q[tail++] = start; D[start] = 0; PAR[start] = -1;
    while (head < tail) {
      var c = Q[head++], x = c % 9, y = (c / 9) | 0;
      if (y === goal) {
        if (wantPath) {
          lastPath.length = 0;
          for (var k = c; k !== -1; k = PAR[k]) lastPath.push(k);
          lastPath.reverse();
        }
        return D[c];
      }
      // prefer forward direction first so paths are deterministic
      for (var i = 0; i < 4; i++) {
        var d = p === 0 ? i : (i === 0 ? 1 : i === 1 ? 0 : i);
        if (blocked(s, x, y, d)) continue;
        var n = (y + DY[d]) * 9 + x + DX[d];
        if (D[n] < 0) { D[n] = D[c] + 1; PAR[n] = c; Q[tail++] = n; }
      }
    }
    return -1;
  }

  function overlaps(s, t, c, r) {
    var h = s.h, v = s.v, i = r * 8 + c;
    if (t === 1) return h[i] === 1 || (c > 0 && h[i - 1] === 1) || (c < 7 && h[i + 1] === 1) || v[i] === 1;
    return v[i] === 1 || (r > 0 && v[i - 8] === 1) || (r < 7 && v[i + 8] === 1) || h[i] === 1;
  }
  // returns null if legal, else a reason string
  function wallProblem(s, t, c, r) {
    if (c < 0 || c > 7 || r < 0 || r > 7) return 'Outside the board';
    if (s.wl[s.turn] <= 0) return 'No walls left';
    if (overlaps(s, t, c, r)) return 'Overlaps another wall';
    var arr = t === 1 ? s.h : s.v, i = r * 8 + c;
    arr[i] = 1;
    var ok = bfs(s, 0, false) >= 0 && bfs(s, 1, false) >= 0;
    arr[i] = 0;
    return ok ? null : 'Would block a player completely';
  }

  function fmt(m) {
    if (m.t === 0) return LET[m.x] + (m.y + 1);
    return LET[m.x] + (m.y + 1) + (m.t === 1 ? 'h' : 'v');
  }
  function parse(str) {
    str = str.trim().toLowerCase();
    var x = LET.indexOf(str[0]), y = parseInt(str[1], 10) - 1;
    if (x < 0 || isNaN(y) || y < 0 || y > 8) return null;
    if (str.length === 2) return { t: 0, x: x, y: y };
    if (str[2] === 'h' || str[2] === 'v') return { t: str[2] === 'h' ? 1 : 2, x: x, y: y };
    return null;
  }

  function doMove(s, m) {
    var p = s.turn;
    if (m.t === 0) { m.ox = s.px[p]; m.oy = s.py[p]; s.px[p] = m.x; s.py[p] = m.y; }
    else { (m.t === 1 ? s.h : s.v)[m.y * 8 + m.x] = 1; s.wl[p]--; }
    s.turn = 1 - p;
  }
  function undoMove(s, m) {
    var p = 1 - s.turn;
    s.turn = p;
    if (m.t === 0) { s.px[p] = m.ox; s.py[p] = m.oy; }
    else { (m.t === 1 ? s.h : s.v)[m.y * 8 + m.x] = 0; s.wl[p]++; }
  }
  function clone(s) {
    return { px: s.px.slice(), py: s.py.slice(), wl: s.wl.slice(), h: s.h.slice(), v: s.v.slice(), turn: s.turn };
  }
  function winner(s) {
    if (s.py[0] === 8) return 0;
    if (s.py[1] === 0) return 1;
    return -1;
  }
  // Replays notation strings; returns the final state
  function replay(moves, upto) {
    var s = newState(), n = upto === undefined ? moves.length : upto;
    for (var i = 0; i < n; i++) doMove(s, parse(moves[i]));
    return s;
  }

  // ---------- analysis ----------
  function genMoves(s, wallLimit) {
    var p = s.turn, o = 1 - p, moves = [];
    var pm = pawnMoves(s, p);
    pm.sort(function (a, b) { return p === 0 ? b[1] - a[1] : a[1] - b[1]; });
    for (var i = 0; i < pm.length; i++) moves.push({ t: 0, x: pm[i][0], y: pm[i][1] });
    if (s.wl[p] > 0) {
      var dO = bfs(s, o, true), path = lastPath.slice(), dM = bfs(s, p, false);
      var seen = new Uint8Array(128), walls = [];
      for (var k = 0; k + 1 < path.length; k++) {
        var a = path[k], b = path[k + 1], ax = a % 9, ay = (a / 9) | 0, bx = b % 9, by = (b / 9) | 0;
        var cand;
        if (by > ay) cand = [[1, ax, ay], [1, ax - 1, ay]];
        else if (by < ay) cand = [[1, ax, by], [1, ax - 1, by]];
        else if (bx > ax) cand = [[2, ax, ay], [2, ax, ay - 1]];
        else cand = [[2, bx, ay], [2, bx, ay - 1]];
        for (var j = 0; j < 2; j++) {
          var t = cand[j][0], c = cand[j][1], r = cand[j][2];
          if (c < 0 || c > 7 || r < 0 || r > 7) continue;
          var key = (t - 1) * 64 + r * 8 + c;
          if (seen[key]) continue;
          seen[key] = 1;
          if (overlaps(s, t, c, r)) continue;
          var arr = t === 1 ? s.h : s.v;
          arr[r * 8 + c] = 1;
          var d1 = bfs(s, o, false), d2 = bfs(s, p, false);
          arr[r * 8 + c] = 0;
          if (d1 < 0 || d2 < 0) continue;
          var benefit = (d1 - dO) - (d2 - dM);
          if (benefit >= 1) walls.push({ t: t, x: c, y: r, score: benefit });
        }
      }
      walls.sort(function (x, y) { return y.score - x.score; });
      for (var w = 0; w < walls.length && w < wallLimit; w++) moves.push(walls[w]);
    }
    return moves;
  }

  function evaluate(s) {
    var p = s.turn;
    var dM = bfs(s, p, false), dO = bfs(s, 1 - p, false);
    return (dO - dM) + 0.35 * (s.wl[p] - s.wl[1 - p]) + 0.3;
  }

  function search(s, depth, alpha, beta, limit) {
    if (depth === 0) return evaluate(s);
    var p = s.turn, goal = goalRow(p);
    var moves = genMoves(s, limit), best = -Infinity;
    for (var i = 0; i < moves.length; i++) {
      var m = moves[i], v;
      doMove(s, m);
      if (m.t === 0 && s.py[p] === goal) v = 1000 + depth;
      else v = -search(s, depth - 1, -beta, -alpha, limit);
      undoMove(s, m);
      if (v > best) best = v;
      if (best > alpha) alpha = best;
      if (alpha >= beta) break;
    }
    return best;
  }

  function rootSearch(s, depth, limit) {
    var p = s.turn, goal = goalRow(p), moves = genMoves(s, limit + 4);
    var best = -Infinity, bestM = null, alpha = -Infinity;
    for (var i = 0; i < moves.length; i++) {
      var m = moves[i], v;
      doMove(s, m);
      if (m.t === 0 && s.py[p] === goal) v = 1000 + depth;
      else v = -search(s, depth - 1, -Infinity, -alpha, limit);
      undoMove(s, m);
      if (v > best) { best = v; bestM = m; }
      if (best > alpha) alpha = best;
    }
    return { value: best, move: bestM };
  }

  function playedValue(s, m, depth, limit) {
    var p = s.turn, v;
    doMove(s, m);
    if (m.t === 0 && s.py[p] === goalRow(p)) v = 1000 + depth;
    else v = -search(s, depth - 1, -Infinity, Infinity, limit);
    undoMove(s, m);
    return v;
  }

  function winProb(v) {            // value (pawn-steps, mover perspective) -> 0..1
    if (v > 900) return 1;
    if (v < -900) return 0;
    return 1 / (1 + Math.exp(-v / 2.5));
  }

  function classify(drop, isBest) {
    if (isBest || drop < 0.01) return 'best';
    if (drop < 0.04) return 'good';
    if (drop < 0.10) return 'inaccuracy';
    if (drop < 0.22) return 'mistake';
    return 'blunder';
  }

  // Analysis of one move from position s (s is left unchanged). Returns the entry plus
  // wpBeforeWhite: white's win chance in the position before the move, assuming best play.
  function evalPly(s, moveStr, ply, depth) {
    var limit = depth >= 4 ? 8 : 10;
    var mv = parse(moveStr), p = s.turn;
    var root = rootSearch(s, depth, limit);
    var pv = playedValue(s, mv, depth, limit);
    var bestVal = root.value, bestMove = root.move ? fmt(root.move) : moveStr;
    if (pv >= bestVal) { bestVal = pv; bestMove = moveStr; }
    var wpBefore = winProb(bestVal), wpAfter = winProb(pv), drop = wpBefore - wpAfter;
    return {
      ply: ply, player: p, move: moveStr, best: bestMove,
      bestVal: bestVal, playedVal: pv, drop: drop,
      cls: classify(drop, bestMove === moveStr),
      wpWhite: p === 0 ? wpAfter : 1 - wpAfter,
      wpBeforeWhite: p === 0 ? wpBefore : 1 - wpBefore
    };
  }

  // Analyze just move number `ply` (0-based) of a game; used for live analysis.
  function analyzePly(moves, ply, depth) {
    var s = replay(moves, ply);
    var e = evalPly(s, moves[ply], ply, depth || 3);
    var after = replay(moves, ply + 1), w = winner(after);
    if (w >= 0) e.wpWhite = w === 0 ? 1 : 0;
    return e;
  }

  // Best move for the side to move in the position after n moves (null if the game is over).
  function bestFrom(moves, n, depth) {
    var s = replay(moves, n);
    if (winner(s) >= 0) return null;
    var root = rootSearch(s, depth, depth >= 4 ? 8 : 10);
    if (!root.move) return null;
    var wp = winProb(root.value);
    return { move: fmt(root.move), player: s.turn, wpWhite: s.turn === 0 ? wp : 1 - wp };
  }

  // The engine playing both sides from the position after n moves; list of move strings.
  function bestLine(moves, n, depth, max) {
    var s = replay(moves, n), limit = depth >= 4 ? 8 : 10, line = [];
    while (line.length < max && winner(s) < 0) {
      var r = rootSearch(s, depth, limit);
      if (!r.move) break;
      line.push(fmt(r.move));
      doMove(s, { t: r.move.t, x: r.move.x, y: r.move.y });
    }
    return line;
  }

  // Everything the live panel needs after a move: rating of the last move + best next move.
  function liveInfo(moves, depth) {
    var n = moves.length;
    return { entry: n ? analyzePly(moves, n - 1, depth) : null, next: bestFrom(moves, n, depth) };
  }

  // Full-game analysis. Returns one entry per ply plus the white win-probability series.
  function analyze(moves, depth, onProgress) {
    depth = depth || 3;
    var s = newState(), entries = [], series = [];
    for (var i = 0; i < moves.length; i++) {
      if (onProgress) onProgress(i, moves.length);
      var e = evalPly(s, moves[i], i, depth);
      if (i === 0) series.push(e.wpBeforeWhite);
      entries.push(e);
      series.push(e.wpWhite);
      doMove(s, parse(moves[i]));
    }
    var w = winner(s);
    if (w >= 0) series[series.length - 1] = w === 0 ? 1 : 0;
    if (onProgress) onProgress(moves.length, moves.length);
    return { entries: entries, series: series, winner: w, depth: depth };
  }

  return {
    LET: LET, newState: newState, clone: clone, blocked: blocked, pawnMoves: pawnMoves,
    wallProblem: wallProblem, doMove: doMove, undoMove: undoMove, fmt: fmt, parse: parse,
    winner: winner, replay: replay, bfs: bfs, analyze: analyze, analyzePly: analyzePly, bestFrom: bestFrom, bestLine: bestLine, liveInfo: liveInfo, goalRow: goalRow
  };
})();
if (typeof module !== 'undefined') module.exports = Quor;
