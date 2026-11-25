"""widen power tracks where clearance allows, add per-pin silk labels"""
import sys, pcbnew
from pcbnew import FromMM as MM, ToMM, VECTOR2I
fn = sys.argv[1]; b = pcbnew.LoadBoard(fn); OX = OY = 50.0
# ---- 1) widen power tracks segment by segment (keeps 0.2 mm to every other-net item)
POWER = {'VBAT', 'VBAT_RAW', 'SOLAR', 'VIN_CHG', 'VSYS', 'VBUS', '+3V3', '3V3_SW', 'VEXT', 'VALVE_D'}
others = list(b.GetPads()) + [t for t in b.GetTracks()]
holes = [p for p in b.GetPads() if p.GetDrillSize().x > 0]
edge = b.GetBoardEdgesBoundingBox(); edge.Inflate(-MM(0.4))
count = {}
for t in list(b.GetTracks()):
    if t.GetClass() == 'PCB_VIA' or t.GetNetname() not in POWER: continue
    L = t.GetLayer(); w0 = t.GetWidth()
    for w in (1.0, 0.8, 0.6, 0.5, 0.4):
        if MM(w) <= w0: break
        t.SetWidth(MM(w)); sh = t.GetEffectiveShape(L); bad = False
        if not (edge.Contains(t.GetStart()) and edge.Contains(t.GetEnd())): bad = True
        for o in others:
            if bad: break
            if o is t or o.GetNetCode() == t.GetNetCode() or not o.IsOnLayer(L): continue
            if sh.Collide(o.GetEffectiveShape(L), MM(0.2)): bad = True
        for h in holes:
            if bad: break
            if h.GetNetCode() != t.GetNetCode() and sh.Collide(h.GetEffectiveHoleShape(), MM(0.3)): bad = True
        if not bad:
            count[t.GetNetname()] = count.get(t.GetNetname(), 0) + 1; break
        t.SetWidth(w0)
print('widened segments', count)
# ---- 2) silk labels
for d in [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == '3V3 TX RX GND']: b.Delete(d)
def text(t, x, y, sz=0.8, rot=0):
    tx = pcbnew.PCB_TEXT(b); tx.SetText(t); tx.SetPosition(VECTOR2I(MM(OX + x), MM(OY + y))); tx.SetLayer(pcbnew.F_SilkS)
    tx.SetTextSize(VECTOR2I(MM(sz), MM(sz))); tx.SetTextThickness(MM(sz * 0.16)); tx.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T)); b.Add(tx)
for x, t in zip((47.0, 49.54, 52.08, 54.62), ('3V3', 'TX', 'RX', 'GND')): text(t, x, 6.75)
for x0, names in ((52.0, 'VSG'), (61.0, 'VSG'), (70.0, 'VDG')):
    for k, ch in enumerate(names): text(ch, x0 + 2 * k, 73.55)
for y, t in zip((15.0, 17.54, 20.08, 22.62, 25.16, 27.7), ('3V3', 'IO20', 'IO21', 'IO22', 'IO23', 'GND')):
    text(t, 92.3, y, 0.8)
pcbnew.SaveBoard(fn, b)
