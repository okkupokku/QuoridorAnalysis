// JSON-lines bridge around Quor (engine.js is prepended by build step)
function legalAll(moves){
  var s=Quor.replay(moves), out={pawn:[],walls:[],turn:s.turn,wl:s.wl,winner:Quor.winner(s)};
  if(out.winner>=0) return out;
  Quor.pawnMoves(s,s.turn).forEach(function(t){out.pawn.push(Quor.fmt({t:0,x:t[0],y:t[1]}));});
  for(var t=1;t<=2;t++) for(var r=0;r<Quor.size()-1;r++) for(var c=0;c<Quor.size()-1;c++) if(!Quor.wallProblem(s,t,c,r)) out.walls.push(Quor.fmt({t:t,x:c,y:r}));
  return out;
}
while(true){
  var line=readline(); if(line===null||line===undefined) break; if(!line) continue;
  var q=JSON.parse(line), res;
  try{
    if(q.cmd==='config'){ Quor.configure(q.n,q.w); res={ok:1}; }
    else if(q.cmd==='best'){ var b=Quor.bestFrom(q.moves,q.moves.length,q.depth); res=b; }
    else if(q.cmd==='legal'){ res=legalAll(q.moves); }
    else if(q.cmd==='analyze'){ res=Quor.analyze(q.moves,q.depth); }
    else if(q.cmd==='ply'){ res=Quor.analyzePly(q.moves,q.ply,q.depth); }
    else if(q.cmd==='dist'){ var s=Quor.replay(q.moves); res=[Quor.bfs(s,0,false),Quor.bfs(s,1,false)]; }
    else res={error:'unknown'};
  }catch(e){ res={error:String(e)}; }
  print(JSON.stringify(res));
}
