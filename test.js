const Q=require('./src/engine.js');
// random-ish game: alternate pawn path steps and occasional walls
let s=Q.newState(), moves=[];
let seed=7; const rnd=()=> (seed=(seed*1103515245+12345)&0x7fffffff)/0x7fffffff;
while(Q.winner(s)<0 && moves.length<120){
  const p=s.turn; let m=null;
  if(rnd()<0.3 && s.wl[p]>0){
    for(let k=0;k<30;k++){const t=1+(rnd()<.5?0:1),c=Math.floor(rnd()*8),r=Math.floor(rnd()*8);
      if(!Q.wallProblem(s,t,c,r)){m={t,x:c,y:r};break;}}
  }
  if(!m){const pm=Q.pawnMoves(s,p); pm.sort((a,b)=>p==0?b[1]-a[1]:a[1]-b[1]); const pick=rnd()<.8?pm[0]:pm[Math.floor(rnd()*pm.length)]; m={t:0,x:pick[0],y:pick[1]};}
  moves.push(Q.fmt(m)); Q.doMove(s,m);
}
console.log(moves.length, moves.join(' '), 'winner',Q.winner(s));
for(const d of [2,3,4]){const t=Date.now(); const r=Q.analyze(moves.slice(0,30),d); console.log('depth',d,(Date.now()-t)+'ms');
 if(d==3) console.log(r.entries.map(e=>e.move+':'+e.cls[0]+(e.best!==e.move?'('+e.best+')':'')).join(' '), r.series.map(x=>Math.round(x*100)).join(','));}
