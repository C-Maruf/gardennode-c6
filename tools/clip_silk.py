"""split footprint silkscreen lines so they stop 0.2 mm short of any copper pad (what a fab does anyway)"""
import sys, pcbnew
from pcbnew import FromMM as MM, VECTOR2I
fn = sys.argv[1]; b = pcbnew.LoadBoard(fn)
boxes = []
for p in b.GetPads():
    bb = p.GetBoundingBox(); bb.Inflate(MM(0.2)); boxes.append(bb)
def inside(x, y): return any(bb.Contains(VECTOR2I(int(x), int(y))) for bb in boxes)
changed = 0
for f in b.GetFootprints():
    for g in list(f.GraphicalItems()):
        if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() != 'MGRAPHIC' or g.GetShapeStr() != 'Line': continue
        s, e = g.GetStart(), g.GetEnd(); n = max(2, int(((e.x - s.x) ** 2 + (e.y - s.y) ** 2) ** 0.5 / MM(0.05)))
        pts = [(s.x + (e.x - s.x) * k / n, s.y + (e.y - s.y) * k / n) for k in range(n + 1)]
        flags = [inside(*q) for q in pts]
        if not any(flags): continue
        runs, cur = [], []
        for q, fl in zip(pts, flags):
            if not fl: cur.append(q)
            elif cur: runs.append(cur); cur = []
        if cur: runs.append(cur)
        for r in runs:
            if len(r) < 4: continue          # drop slivers shorter than ~0.15 mm
            ng = g.Duplicate(); ng.SetStart(VECTOR2I(int(r[0][0]), int(r[0][1]))); ng.SetEnd(VECTOR2I(int(r[-1][0]), int(r[-1][1]))); f.Add(ng)
        f.Delete(g); changed += 1
pcbnew.SaveBoard(fn, b); print('silk lines trimmed', changed)
