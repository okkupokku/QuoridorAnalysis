import sys, os, math
HERE=os.path.dirname(os.path.abspath(__file__))
SD=os.path.join(HERE,'sigmaquoridor'); sys.path.insert(0,SD)
import dataclasses
_d=dataclasses.dataclass
def _dc(*a,**k):
    k.pop('slots',None); return _d(*a,**k)
dataclasses.dataclass=_dc
import numpy as np, onnxruntime as ort
from game import State, PawnAction, WallAction, action_to_index, vert_policy_permutation
from mcts import MCTSAgent
LET='abcdefghi'
N=9
_sess=None
def sess():
    global _sess
    if _sess is None:
        so=ort.SessionOptions(); so.intra_op_num_threads=1; so.inter_op_num_threads=1
        _sess=ort.InferenceSession(os.path.join(SD,'docs/models_9x9/best.onnx'),so,providers=['CPUExecutionProvider'])
    return _sess
_perm=vert_policy_permutation(N)
def evaluator(state, legal):
    x=state.to_nn_input()[None].astype(np.float32)
    logits,val=sess().run(None,{'input':x})
    logits=logits[0]; flip=not state.is_player1_turn()
    idx=np.array([action_to_index(a,N) for a in legal]); 
    if flip: idx=_perm[idx]
    l=logits[idx]; l=l-l.max(); p=np.exp(l); p/=p.sum()
    return p.tolist(), float(val[0][0])
def to_action(state, mv):
    if len(mv)==3: return WallAction(LET.index(mv[0]), int(mv[1])-1, mv[2])
    x=LET.index(mv[0]); y=int(mv[1])-1
    cur=state.player1pos if state.is_player1_turn() else state.player2pos
    dx=x-cur[0]; dy=y-cur[1]
    if abs(dx)+abs(dy)==2 and (dx==0 or dy==0): dx//=2; dy//=2
    return PawnAction((dx,dy))
def from_action(state, a):
    if isinstance(a,WallAction): return LET[a.x]+str(a.y+1)+a.orientation
    cur=state.player1pos if state.is_player1_turn() else state.player2pos
    # find destination by applying
    ns=state.next(a); dest=ns.player1pos if state.is_player1_turn() else ns.player2pos
    return LET[dest[0]]+str(dest[1]+1)
def build(moves):
    s=State(boardsize=N,walls_p1=10,walls_p2=10)
    for mv in moves: s=s.next(to_action(s,mv))
    return s
def search(moves, sims=100):
    """returns (best move, mover win prob 0..1, raw-net win prob)"""
    s=build(moves)
    if s.is_finished(): return None,None,None
    raw=evaluator(s,s.get_legal_actions())[1]
    ag=MCTSAgent(evaluator=evaluator,num_simulations=sims,c_puct=1.0)
    root=ag.search(s)
    ch=max(root.children,key=lambda c:c.visit_count)
    return from_action(s,ch.action),(root.q_value+1)/2,(raw+1)/2
if __name__=='__main__':
    import time
    t=time.time(); print(search([],100),round(time.time()-t,1))
    t=time.time(); print(search(['e2','d9','e3','c9','e4','b9','e5','a9','e6'],100),round(time.time()-t,1))
