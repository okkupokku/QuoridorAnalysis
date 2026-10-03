import sys, json, random
sys.path.insert(0,'.')
from mine import Mine
def play_game(m, rng, eps, depth, maxply=120):
    moves=[]
    while len(moves)<maxply:
        L=m.q(cmd='legal',moves=moves)
        if L['winner']>=0: break
        r=rng.random()
        if r<eps:
            # random move, biased: 35% wall
            if L['walls'] and L['wl'][L['turn']]>0 and rng.random()<0.35: mv=rng.choice(L['walls'])
            else: mv=rng.choice(L['pawn'])
        else:
            b=m.q(cmd='best',moves=moves,depth=depth); mv=b['move']
        moves.append(mv)
    return moves
if __name__=='__main__':
    n=int(sys.argv[1]); seed=int(sys.argv[2]); out=sys.argv[3]
    rng=random.Random(seed); m=Mine(); games=[]
    for i in range(n):
        eps=rng.choice([0.15,0.3,0.5]); games.append(play_game(m,rng,eps,rng.choice([2,3])))
    json.dump(games,open(out,'w')); print(len(games),sum(map(len,games))/len(games))
