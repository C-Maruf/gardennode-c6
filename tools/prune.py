"""remove U1 escape stubs whose far end connects to nothing"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
fp = {f.GetReference(): f for f in b.GetFootprints()}
centers = {(p.GetPosition().x, p.GetPosition().y) for p in fp["U1"].Pads()}
tr = list(b.GetTracks())
def touches(pt, net, skip):
    for t in tr:
        if t is skip or t.GetNetCode() != net: continue
        if t.GetClass() == 'PCB_VIA':
            if (t.GetPosition() - pt).EuclideanNorm() < pcbnew.FromMM(0.31): return True
        elif t.HitTest(pt, 0): return True
    return False
n = 0
for t in tr:
    if t.GetClass() == 'PCB_VIA' or abs(pcbnew.ToMM(t.GetLength()) - 1.3) > 0.01: continue
    if (t.GetStart().x, t.GetStart().y) in centers and not touches(t.GetEnd(), t.GetNetCode(), t):
        b.Remove(t); n += 1
rip = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else set()
for t in list(b.GetTracks()):
    if t.GetNetname() in rip: b.Delete(t); n += 1
pcbnew.SaveBoard(sys.argv[2], b); print('pruned', n)
