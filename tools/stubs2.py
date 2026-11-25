"""re-add J1 fan-out stubs for nets that were ripped up"""
import sys, pcbnew
from pcbnew import FromMM as MM, VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1]); OX = OY = 50.0; nets = set(sys.argv[3].split(','))
jp = {p.GetNumber(): p for f in b.GetFootprints() if f.GetReference() == 'J1' for p in f.Pads()}
for n_, ty in {'A5': 11.9, 'B7': 12.9, 'A6': 13.9, 'A7': 14.9, 'B6': 15.9, 'B5': 16.9}.items():
    p = jp[n_]
    if p.GetNetname() not in nets: continue
    x0, y0 = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
    pts = [(x0, y0), (OX + 7.9, y0), (OX + 9.4, OY + ty), (OX + 9.9, OY + ty)]
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(MM(a[0]), MM(a[1]))); t.SetEnd(VECTOR2I(MM(c[0]), MM(c[1])))
        t.SetWidth(MM(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(p.GetNet()); b.Add(t)
pcbnew.SaveBoard(sys.argv[2], b); print('stubs restored')
