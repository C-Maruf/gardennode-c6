"""auto-place reference designators on F.SilkS without overlapping pads, silk or each other"""
import sys, pcbnew
from pcbnew import FromMM as MM, ToMM, VECTOR2I, EDA_ANGLE, DEGREES_T, BOX2I
fn = sys.argv[1]; b = pcbnew.LoadBoard(fn)
edge = b.GetBoardEdgesBoundingBox(); edge.Inflate(-MM(0.6))
pads = list(b.GetPads())
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
silk = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.F_SilkS]
for f in b.GetFootprints():
    silk += [g for g in f.GraphicalItems() if g.GetLayer() == pcbnew.F_SilkS]
placed = []
def ok(box):
    if not edge.Contains(box): return False
    bx = BOX2I(box.GetOrigin(), box.GetSize()); bx.Inflate(MM(0.15))
    if any(p.GetBoundingBox().Intersects(bx) for p in pads): return False
    if any(v.GetBoundingBox().Intersects(bx) for v in vias): return False
    if any(s.HitTest(bx, False, 0) for s in silk): return False
    if any(p.Intersects(bx) for p in placed): return False
    return True
fps = sorted(b.GetFootprints(), key=lambda f: -f.GetBoundingBox(False, False).GetArea())
miss = []
for f in fps:
    ref = f.Reference()
    if f.GetReference().startswith('H'): continue
    ref.SetLayer(pcbnew.F_SilkS); ref.SetVisible(True)
    ref.SetTextSize(VECTOR2I(MM(0.8), MM(0.8))); ref.SetTextThickness(MM(0.13))
    bb = f.GetBoundingBox(False, False)   # body without text
    cx, cy = bb.Centre().x, bb.Centre().y
    hw, hh = bb.GetWidth() // 2, bb.GetHeight() // 2
    cands = []
    for gap in (0.6, 1.0, 1.6, 2.4, 3.2):
        g = MM(gap)
        cands += [((cx, cy - hh - g), 0), ((cx, cy + hh + g), 0), ((cx - hw - g, cy), 90), ((cx + hw + g, cy), 90),
                  ((cx - hw - g, cy), 0), ((cx + hw + g, cy), 0)]
        for dx in (-1, 1):
            cands += [((cx + dx * hw, cy - hh - g), 0), ((cx + dx * hw, cy + hh + g), 0)]
    done = False
    for (x, y), rot in cands:
        ref.SetKeepUpright(True)
        ref.SetTextAngle(EDA_ANGLE(rot, DEGREES_T) - f.GetOrientation()); ref.SetPosition(VECTOR2I(int(x), int(y)))
        box = ref.GetBoundingBox()
        if ok(box):
            placed.append(box); done = True; break
    if not done:
        ref.SetLayer(pcbnew.F_Fab); ref.SetTextAngle(EDA_ANGLE(0, DEGREES_T)); ref.SetPosition(VECTOR2I(int(cx), int(cy))); miss.append(f.GetReference())
pcbnew.SaveBoard(fn, b)
print('placed', len(placed), 'left on assembly drawing only:', miss)
