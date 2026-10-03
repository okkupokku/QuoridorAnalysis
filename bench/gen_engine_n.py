import re,sys
src=open("/Users/oskarpersonal/Library/Application Support/Claude/scratch-workspaces/126827e7-00bf-4d74-b4b8-f51b0ed4cb35/69757adc-68f8-4bff-bbc5-7fdaca37bb4b/scratch-2026-10-03-854b6c/quoridor/src/engine.js").read()
def R(a,b,count=None):
    global src
    n=src.count(a)
    assert n>=1, 'missing: '+a
    if count is not None: assert n==count,(a,n)
    src=src.replace(a,b)
# state / constants
R("var Quor = (function () {","var Quor = (function () {\n  var N = 9, M = 8, SC = 4, NW = 10;",1)
R("return { px: [4, 4], py: [0, 8], wl: [10, 10], h: new Uint8Array(64), v: new Uint8Array(64), turn: 0 };","return { px: [SC, SC], py: [0, N - 1], wl: [NW, NW], h: new Uint8Array(M * M), v: new Uint8Array(M * M), turn: 0 };",1)
R("return p === 0 ? 8 : 0;","return p === 0 ? N - 1 : 0;",1)
# blocked
R("case 0: return y === 8 || (x < 8 && h[y * 8 + x] === 1) || (x > 0 && h[y * 8 + x - 1] === 1);","case 0: return y === N - 1 || (x < M && h[y * M + x] === 1) || (x > 0 && h[y * M + x - 1] === 1);",1)
R("case 1: return y === 0 || (x < 8 && h[(y - 1) * 8 + x] === 1) || (x > 0 && h[(y - 1) * 8 + x - 1] === 1);","case 1: return y === 0 || (x < M && h[(y - 1) * M + x] === 1) || (x > 0 && h[(y - 1) * M + x - 1] === 1);",1)
R("case 2: return x === 8 || (y < 8 && v[y * 8 + x] === 1) || (y > 0 && v[(y - 1) * 8 + x] === 1);","case 2: return x === N - 1 || (y < M && v[y * M + x] === 1) || (y > 0 && v[(y - 1) * M + x] === 1);",1)
R("default: return x === 0 || (y < 8 && v[y * 8 + x - 1] === 1) || (y > 0 && v[(y - 1) * 8 + x - 1] === 1);","default: return x === 0 || (y < M && v[y * M + x - 1] === 1) || (y > 0 && v[(y - 1) * M + x - 1] === 1);",1)
# bfs
R("var Q = new Int8Array(81), D = new Int8Array(81), PAR = new Int8Array(81);","var Q = new Int8Array(81), D = new Int8Array(81), PAR = new Int8Array(81);\n  function configure(n, w) { N = n; M = n - 1; SC = n >> 1; NW = w; Q = new Int8Array(n * n); D = new Int8Array(n * n); PAR = new Int8Array(n * n); }",1)
R("s.py[p] * 9 + s.px[p]","s.py[p] * N + s.px[p]",1)
R("x = c % 9, y = (c / 9) | 0;","x = c % N, y = (c / N) | 0;",1)
R("var n = (y + DY[d]) * 9 + x + DX[d];","var n = (y + DY[d]) * N + x + DX[d];",1)
# overlaps / wallProblem
R("i = r * 8 + c;\n    if (t === 1) return h[i] === 1 || (c > 0 && h[i - 1] === 1) || (c < 7 && h[i + 1] === 1) || v[i] === 1;\n    return v[i] === 1 || (r > 0 && v[i - 8] === 1) || (r < 7 && v[i + 8] === 1) || h[i] === 1;","i = r * M + c;\n    if (t === 1) return h[i] === 1 || (c > 0 && h[i - 1] === 1) || (c < M - 1 && h[i + 1] === 1) || v[i] === 1;\n    return v[i] === 1 || (r > 0 && v[i - M] === 1) || (r < M - 1 && v[i + M] === 1) || h[i] === 1;",1)
R("if (c < 0 || c > 7 || r < 0 || r > 7) return 'Outside the board';","if (c < 0 || c > M - 1 || r < 0 || r > M - 1) return 'Outside the board';",1)
R("var arr = t === 1 ? s.h : s.v, i = r * 8 + c;","var arr = t === 1 ? s.h : s.v, i = r * M + c;",1)
R("y > 8) return null;","y > N - 1) return null;",1)
R("(m.t === 1 ? s.h : s.v)[m.y * 8 + m.x] = 1;","(m.t === 1 ? s.h : s.v)[m.y * M + m.x] = 1;",1)
R("(m.t === 1 ? s.h : s.v)[m.y * 8 + m.x] = 0;","(m.t === 1 ? s.h : s.v)[m.y * M + m.x] = 0;",1)
R("if (s.py[0] === 8) return 0;","if (s.py[0] === N - 1) return 0;",1)
# genMoves
R("var seen = new Uint8Array(128), walls = [];","var seen = new Uint8Array(2 * M * M), walls = [];",1)
R("ax = a % 9, ay = (a / 9) | 0, bx = b % 9, by = (b / 9) | 0;","ax = a % N, ay = (a / N) | 0, bx = b % N, by = (b / N) | 0;",1)
R("if (c < 0 || c > 7 || r < 0 || r > 7) continue;","if (c < 0 || c > M - 1 || r < 0 || r > M - 1) continue;",1)
R("var key = (t - 1) * 64 + r * 8 + c;","var key = (t - 1) * M * M + r * M + c;",1)
R("arr[r * 8 + c] = 1;","arr[r * M + c] = 1;",1)
R("arr[r * 8 + c] = 0;","arr[r * M + c] = 0;",1)
R("LET: LET,","LET: LET, configure: configure, size: function () { return N; },",1)
open('engine_n.js','w').write(src)
print('ok')
