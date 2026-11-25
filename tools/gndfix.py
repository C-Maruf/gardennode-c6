"""refill pours, then give any unconnected GND SMD pad a short F.Cu link to a new or existing GND via"""
import sys, re, math, pcbnew
from pcbnew import FromMM as MM, ToMM, VECTOR2I
fn = sys.argv[1]
def drc(b):
    rep = fn.replace('.kicad_pcb', '_drc.rpt'); pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True); return open(rep).read()
b = pcbnew.LoadBoard(fn); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(fn, b)
b = pcbnew.LoadBoard(fn); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
txt = drc(b); GND = b.GetNetcodeFromNetname('GND')
bad = set(re.findall(r'Pad (\S+) \[GND\] of (\S+)', '\n'.join(x for x in re.split(r'\n(?=\[)', txt) if x.startswith('[unconnected_items]'))))
print('unconnected GND pads', bad)
def clear(shape_item, layers):
    for o in list(b.GetTracks()) + list(b.GetPads()):
        if o.GetNetCode() == GND or o is shape_item: continue
        for L in layers:
            if o.IsOnLayer(L) and shape_item.GetEffectiveShape(L).Collide(o.GetEffectiveShape(L), MM(0.22)): return False
    for o in list(b.GetTracks()) + list(b.GetPads()):
        h = o.GetDrillValue() if o.GetClass() == 'PCB_VIA' else (o.GetDrillSize().x if o.GetClass() == 'PAD' else 0)
        if h and (o.GetPosition() - shape_item.GetPosition()).EuclideanNorm() < MM(0.3 + h / 1e6 / 2 + 0.3) and shape_item.GetClass() == 'PCB_VIA': return False
    return True
for num, ref in bad:
    pad = [p for f in b.GetFootprints() if f.GetReference() == ref for p in f.Pads() if p.GetNumber() == num][0]
    c = pad.GetPosition(); done = False
    for r in [1.0 + 0.2 * k for k in range(15)]:
        for a in range(0, 360, 15):
            pos = VECTOR2I(int(c.x + MM(r) * math.cos(math.radians(a))), int(c.y + MM(r) * math.sin(math.radians(a))))
            v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNetCode(GND); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            t = pcbnew.PCB_TRACK(b); t.SetStart(c); t.SetEnd(pos); t.SetWidth(MM(0.3)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(GND)
            if any(p2.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p2.GetEffectiveShape(pcbnew.F_Cu).Collide(v.GetEffectiveShape(pcbnew.F_Cu), MM(0.15)) for p2 in b.GetPads()): continue
            if clear(v, [pcbnew.F_Cu, pcbnew.B_Cu]) and clear(t, [pcbnew.F_Cu]):
                b.Add(v); b.Add(t); done = True; break
        if done: break
    print(ref, num, 'linked' if done else 'FAILED')
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(fn, b)
b = pcbnew.LoadBoard(fn); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(fn, b)
txt = drc(b); print([l for l in txt.splitlines() if l.startswith('** Found')])
