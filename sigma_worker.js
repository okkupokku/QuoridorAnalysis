'use strict';
// Analysis worker backed by the SigmaQuoridor network (MIT, engine/sigma/).
// Search (PUCT MCTS) follows SigmaQuoridor's docs/mcts_worker.js.
//
// in : {type:'job', gen, kind:'full'|'live'|'line', moves:[...], sims, max}
//      {type:'cancel', gen}
// out: {type:'ready'} | {type:'failed', reason}
//      {type:'progress', gen, p, n} | {type:'result', gen, kind, data}

importScripts('engine/sigma/game.js', 'engine/ort/ort.wasm.min.js');

const BASE = new URL('./', self.location.href).href;
const N = 9, WALLS = 10, LET = 'abcdefghi';
let session = null, active = -1;

try {
  ort.env.wasm.wasmPaths = BASE + 'engine/ort/';
  ort.env.wasm.numThreads = self.crossOriginIsolated ? Math.max(1, Math.min(navigator.hardwareConcurrency || 4, 4)) : 1;
  ort.env.wasm.proxy = false;
} catch (e) { /* reported by the load below */ }

const ready = ort.InferenceSession.create(BASE + 'engine/sigma/model.onnx', { executionProviders: ['wasm'] })
  .then(s => { session = s; postMessage({ type: 'ready' }); })
  .catch(e => { postMessage({ type: 'failed', reason: String((e && e.message) || e) }); throw e; });

// ── notation <-> SigmaQuoridor actions ────────────────────────────────────────
function toAction(s, mv) {
  if (mv.length === 3) return { type: 'wall', x: LET.indexOf(mv[0]), y: +mv[1] - 1, orientation: mv[2] };
  const x = LET.indexOf(mv[0]), y = +mv[1] - 1;
  const cur = s.isPlayer1Turn() ? s.player1pos : s.player2pos;
  let dx = x - cur[0], dy = y - cur[1];
  if (Math.abs(dx) + Math.abs(dy) === 2 && (dx === 0 || dy === 0)) { dx /= 2; dy /= 2; }   // straight jump
  return { type: 'pawn', direction: [dx, dy] };
}
function fromAction(s, a) {
  if (a.type === 'wall') return LET[a.x] + (a.y + 1) + a.orientation;
  const n = s.next(a), p = s.isPlayer1Turn() ? n.player1pos : n.player2pos;
  return LET[p[0]] + (p[1] + 1);
}
function stateAfter(moves) {
  let s = new State({ boardsize: N, walls_p1: WALLS, walls_p2: WALLS });
  for (const mv of moves) s = s.next(toAction(s, mv));
  return s;
}

// ── network evaluation (value is for the side to move, in [-1, 1]) ───────────
async function evaluate(s, legal) {
  const t = new ort.Tensor('float32', s.toNNInput(), [1, 8, N, N]);
  const r = await session.run({ input: t });
  const logits = r.policy_logits.data, value = r.value.data[0];
  const flip = !s.isPlayer1Turn(), perm = flip ? vertPolicyPermutation(N) : null;
  let max = -Infinity;
  const idx = legal.map(a => { const i = actionToIndex(a, N); return flip ? perm[i] : i; });
  for (const i of idx) if (logits[i] > max) max = logits[i];
  let sum = 0;
  const ex = idx.map(i => { const e = Math.exp(logits[i] - max); sum += e; return e; });
  return [ex.map(e => e / sum), value];
}

// ── MCTS (PUCT, same constants as SigmaQuoridor) ──────────────────────────────
class Node {
  constructor(state, parent, action, prior, parentState) {
    this.state = state; this.parentState = parentState || null; this.parent = parent || null;
    this.action = action || null; this.prior = prior; this.children = [];
    this.n = 0; this.w = 0; this.expanded = false;
  }
  ensure() { if (!this.state) { this.state = this.parentState.next(this.action); this.parentState = null; } }
  get q() { return this.n ? this.w / this.n : 0; }
  pick() {
    const sq = Math.sqrt(this.n); let visited = 0;
    for (const c of this.children) if (c.n > 0) visited += c.prior;
    let best = null, bs = -Infinity;
    for (const c of this.children) {
      const u = 1.0 * c.prior * sq / (1 + c.n);
      const q = c.n === 0 ? this.q - 0.2 * Math.sqrt(visited) : -c.q;
      if (q + u > bs) { bs = q + u; best = c; }
    }
    return best;
  }
}
async function expand(node) {
  const legal = node.state.getLegalActions();
  if (!legal.length) { node.expanded = true; return 0; }
  const [pri, v] = await evaluate(node.state, legal);
  for (let i = 0; i < legal.length; i++) node.children.push(new Node(null, node, legal[i], pri[i], node.state));
  node.expanded = true;
  return v;
}
function backup(node, v) { for (let n = node; n; n = n.parent) { n.n++; n.w += v; v = -v; } }
async function search(s, sims, gen) {
  const root = new Node(s);
  backup(root, await expand(root));
  for (let i = 0; i < sims; i++) {
    if (gen !== active) return null;
    let node = root;
    for (;;) { node.ensure(); if (!node.expanded || node.state.isFinished()) break; node = node.pick(); }
    node.ensure();
    const v = node.state.isFinished() ? (node.state.winner() !== 0 ? -1 : 0) : await expand(node);
    backup(node, v);
  }
  return root;
}

// ── position evaluation, cached ───────────────────────────────────────────────
// Returns {wp: side-to-move win probability, best: move string or null, over: bool}
const cache = new Map();
async function evalPosition(moves, s, sims, gen) {
  const key = sims + '|' + moves.join(' ');
  if (cache.has(key)) return cache.get(key);
  let out;
  if (s.winner() !== 0) out = { wp: 0, best: null, over: true };          // previous mover won
  else if (s.isFinished()) out = { wp: 0.5, best: null, over: true };      // draw by move limit
  else if (sims <= 0) {
    const legal = s.getLegalActions();
    const [pri, v] = await evaluate(s, legal);
    let bi = 0; for (let i = 1; i < pri.length; i++) if (pri[i] > pri[bi]) bi = i;
    out = { wp: (v + 1) / 2, best: fromAction(s, legal[bi]), over: false };
  } else {
    const root = await search(s, sims, gen);
    if (!root) return null;
    let bc = root.children[0];
    for (const c of root.children) if (c.n > bc.n) bc = c;
    out = { wp: (root.q + 1) / 2, best: bc ? fromAction(s, bc.action) : null, over: false };
  }
  if (cache.size > 20000) cache.clear();
  cache.set(key, out);
  return out;
}

function classify(drop, isBest) {
  if (isBest || drop < 0.01) return 'best';
  if (drop < 0.04) return 'good';
  if (drop < 0.10) return 'inaccuracy';
  if (drop < 0.22) return 'mistake';
  return 'blunder';
}
// Rating of move i from the evaluations of the positions before (a) and after (b) it.
function entryFor(i, move, a, b) {
  const p = i % 2;
  const before = a.wp;
  const after = b.over ? (b.wp === 0 ? 1 : 0.5) : 1 - b.wp;
  let drop = Math.max(0, before - after);
  let best = a.best || move;
  if (drop < 0.005) best = move;
  const wpBest = Math.max(before, after);
  return {
    ply: i, player: p, move: move, best: best, drop: drop,
    cls: classify(drop, best === move),
    wpWhite: p === 0 ? after : 1 - after,
    wpBeforeWhite: p === 0 ? wpBest : 1 - wpBest,
    wpBest: wpBest
  };
}
function winnerOf(s) { const w = s.winner(); return w === 1 ? 0 : w === 2 ? 1 : -1; }

async function full(moves, sims, gen) {
  let s = new State({ boardsize: N, walls_p1: WALLS, walls_p2: WALLS });
  const vals = [];
  for (let i = 0; i <= moves.length; i++) {
    if (gen !== active) return null;
    postMessage({ type: 'progress', gen, p: i, n: moves.length + 1 });
    const v = await evalPosition(moves.slice(0, i), s, sims, gen);
    if (!v) return null;
    vals.push(v);
    if (i < moves.length) s = s.next(toAction(s, moves[i]));
  }
  const entries = [], series = [vals[0].wp];
  for (let i = 0; i < moves.length; i++) {
    const e = entryFor(i, moves[i], vals[i], vals[i + 1]);
    entries.push(e); series.push(e.wpWhite);
  }
  const w = winnerOf(s);
  if (w >= 0) series[series.length - 1] = w === 0 ? 1 : 0;
  return { entries, series, winner: w, depth: sims, engine: 'sigma' };
}

async function live(moves, sims, gen) {
  const n = moves.length;
  const sNow = stateAfter(moves);
  const now = await evalPosition(moves, sNow, sims, gen);
  if (!now) return null;
  let entry = null;
  if (n > 0) {
    const prev = await evalPosition(moves.slice(0, -1), stateAfter(moves.slice(0, -1)), sims, gen);
    if (!prev) return null;
    entry = entryFor(n - 1, moves[n - 1], prev, now);
    if (winnerOf(sNow) >= 0) entry.wpWhite = winnerOf(sNow) === 0 ? 1 : 0;
  }
  const next = now.over || !now.best ? null
    : { move: now.best, player: n % 2, wpWhite: n % 2 === 0 ? now.wp : 1 - now.wp };
  return { entry, next };
}

// Evaluate the positions after moves[0..i) for each i in idx (used by the parallel pool).
async function evals(moves, idx, sims, gen) {
  const want = new Set(idx), last = Math.max(...idx), out = [];
  let s = new State({ boardsize: N, walls_p1: WALLS, walls_p2: WALLS });
  for (let i = 0; i <= last; i++) {
    if (want.has(i)) {
      const v = await evalPosition(moves.slice(0, i), s, sims, gen);
      if (!v) return null;
      out.push({ i: i, wp: v.wp, best: v.best, over: v.over });
      postMessage({ type: 'progress', gen, p: 1 });
    }
    if (i < moves.length) s = s.next(toAction(s, moves[i]));
  }
  return out;
}

async function line(moves, sims, max, gen) {
  const out = [], hist = moves.slice();
  let s = stateAfter(hist);
  while (out.length < max && !s.isFinished()) {
    const v = await evalPosition(hist, s, sims, gen);
    if (!v) return null;
    if (!v.best) break;
    out.push(v.best); hist.push(v.best); s = s.next(toAction(s, v.best));
    postMessage({ type: 'progress', gen, move: v.best });
  }
  return out;
}

onmessage = async function (e) {
  const d = e.data;
  if (d.type === 'cancel') { active = d.gen; return; }
  if (d.type !== 'job') return;
  active = d.gen;
  try { await ready; } catch (err) { return; }
  if (d.gen !== active) return;
  let data;
  try {
    if (d.kind === 'full') data = await full(d.moves, d.sims, d.gen);
    else if (d.kind === 'live') data = await live(d.moves, d.sims, d.gen);
    else if (d.kind === 'line') data = await line(d.moves, Math.min(d.sims, 32), d.max || 60, d.gen);
    else if (d.kind === 'evals') data = await evals(d.moves, d.idx, d.sims, d.gen);
  } catch (err) {
    postMessage({ type: 'failed', reason: String((err && err.message) || err) });
    return;
  }
  if (data && d.gen === active) postMessage({ type: 'result', gen: d.gen, kind: d.kind, data });
};
