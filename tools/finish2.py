"""GND clean-up after finish.py: tie EPAD vias to pads, fix unconnected GND pads, drop orphan stitch vias."""
import sys, re, math
import pcbnew
from pcbnew import FromMM as MM, ToMM, VECTOR2I
src, out = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src); GND = b.GetNetcodeFromNetname('GND')
def trk(a, c, w=0.3, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNetCode(GND); b.Add(t)
fp = {f.GetReference(): f for f in b.GetFootprints()}
ep = [p.GetPosition() for p in fp['U4'].Pads() if p.GetNumber() == '29']
for v in [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetCode() == GND]:
    near = [p for p in ep if (p - v.GetPosition()).EuclideanNorm() < MM(0.95)]
    if len(near) == 4:
        for p in near: trk(v.GetPosition(), p)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(out, b)
for it in range(3):
    b = pcbnew.LoadBoard(out); rep = out.replace('.kicad_pcb', '_drc.rpt')
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rep).read()
    blocks = re.split(r'\n(?=\[)', txt)
    bad_vias, bad_pads = set(), set()
    for bl in blocks:
        if not (bl.startswith('[unconnected_items]') or bl.startswith('[via_dangling]')): continue
        for m in re.finditer(r'@\(([\d.]+) mm, ([\d.]+) mm\): (Via \[GND\]|Pad (\S+) \[GND\] of (\S+))', bl):
            x, y = float(m.group(1)), float(m.group(2))
            if m.group(3).startswith('Via'): bad_vias.add((x, y))
            else: bad_pads.add((m.group(5), m.group(4)))
    print('iter', it, 'orphan vias', len(bad_vias), 'pads', bad_pads)
    if not bad_vias and not bad_pads: break
    epv = [(ToMM(p.x), ToMM(p.y)) for p in ep]
    for t in list(b.GetTracks()):
        if t.GetClass() == 'PCB_VIA' and t.GetNetCode() == GND:
            q = (round(ToMM(t.GetPosition().x), 4), round(ToMM(t.GetPosition().y), 4))
            if any(abs(q[0] - x) < 0.01 and abs(q[1] - y) < 0.01 for x, y in bad_vias):
                if min(math.hypot(q[0] - a, q[1] - c) for a, c in epv) > 1.0: b.Delete(t)
    # for unconnected GND pads: bridge to nearest GND via on F.Cu if a straight line is clear
    for ref, num in bad_pads:
        pad = [p for p in fp_ref(b, ref).Pads() if p.GetNumber() == num][0] if False else None
    for ref, num in bad_pads:
        f = [f for f in b.GetFootprints() if f.GetReference() == ref][0]
        pad = [p for p in f.Pads() if p.GetNumber() == num][0]
        best = None
        for t in b.GetTracks():
            if t.GetClass() != 'PCB_VIA' or t.GetNetCode() != GND: continue
            d = (t.GetPosition() - pad.GetPosition()).EuclideanNorm()
            if d > MM(5): continue
            seg = pcbnew.PCB_TRACK(b); seg.SetStart(pad.GetPosition()); seg.SetEnd(t.GetPosition()); seg.SetWidth(MM(0.25)); seg.SetLayer(pcbnew.F_Cu)
            ok = True
            for o in b.GetTracks():
                if o.GetNetCode() == GND or not o.IsOnLayer(pcbnew.F_Cu): continue
                sh = o.GetEffectiveShape(pcbnew.F_Cu)
                if seg.GetEffectiveShape(pcbnew.F_Cu).Collide(sh, MM(0.21)): ok = False; break
            if ok:
                for p2 in b.GetPads():
                    if p2.GetNetCode() == GND or not p2.IsOnLayer(pcbnew.F_Cu): continue
                    if seg.GetEffectiveShape(pcbnew.F_Cu).Collide(p2.GetEffectiveShape(pcbnew.F_Cu), MM(0.21)): ok = False; break
            if ok and (best is None or d < best[0]): best = (d, t.GetPosition())
        if best: trk(pad.GetPosition(), best[1], 0.25); print('bridged', ref, num)
        else: print('NO BRIDGE', ref, num)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(out, b)
b = pcbnew.LoadBoard(out); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(out, b)
pcbnew.WriteDRCReport(b, out.replace('.kicad_pcb', '_drc.rpt'), pcbnew.EDA_UNITS_MILLIMETRES, True)
