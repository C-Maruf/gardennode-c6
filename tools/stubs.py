"""add fixed fan-out stubs at J1 (USB-C) and U1 pin 13, then save"""
import sys, pcbnew
from pcbnew import FromMM as MM, VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1]); OX = OY = 50.0
fp = {f.GetReference(): f for f in b.GetFootprints()}
def trk(net, pts, w=0.2):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(MM(a[0]), MM(a[1]))); t.SetEnd(VECTOR2I(MM(c[0]), MM(c[1])))
        t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); b.Add(t)
pads = {p.GetNumber(): p for p in fp['J1'].Pads()}
fan = {'A5': 11.9, 'B7': 12.9, 'A6': 13.9, 'A7': 14.9, 'B6': 15.9, 'B5': 16.9}
for n, ty in fan.items():
    p = pads[n]; x0 = pcbnew.ToMM(p.GetPosition().x); y0 = pcbnew.ToMM(p.GetPosition().y)
    trk(p.GetNet(), [(x0, y0), (OX + 7.9, y0), (OX + 9.4, OY + ty), (OX + 9.9, OY + ty)])
u = {p.GetNumber(): p for p in fp['U1'].Pads()}['13']
x0 = pcbnew.ToMM(u.GetPosition().x); y0 = pcbnew.ToMM(u.GetPosition().y)
trk(u.GetNet(), [(x0, y0), (x0, y0 - 1.3)])
pcbnew.SaveBoard(sys.argv[2], b); print('stubs added')
