"""stitch F.Cu GND pour fragments that contain no GND via"""
import sys, pcbnew, numpy as np
from pcbnew import FromMM as MM, ToMM, VECTOR2I
fn = sys.argv[1]
b = pcbnew.LoadBoard(fn); GND = b.GetNetcodeFromNetname('GND')
vias = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetCode() == GND]
others = [t for t in b.GetTracks() if t.GetNetCode() != GND] + [p for p in b.GetPads() if p.GetNetCode() != GND]
holes = [p for p in b.GetPads() if p.GetDrillSize().x > 0] + [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
added = 0
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetLayer() != pcbnew.F_Cu: continue
    fp_ = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(fp_.OutlineCount()):
        poly = pcbnew.SHAPE_POLY_SET(); poly.AddOutline(fp_.Outline(i))
        chains = [fp_.Outline(i)] + [fp_.CHole(i, h) for h in range(fp_.HoleCount(i))]
        for h in range(fp_.HoleCount(i)): poly.AddHole(fp_.CHole(i, h))
        import math
        def touching(v):
            return any(poly.Contains(VECTOR2I(int(v.x + MM(0.75) * math.cos(a)), int(v.y + MM(0.75) * math.sin(a)))) for a in np.linspace(0, 6.28, 16))
        if any(touching(v) for v in vias): continue
        bb = fp_.Outline(i).BBox()
        done = False
        for yy in np.arange(bb.GetTop(), bb.GetBottom(), MM(0.1)):
            for xx in np.arange(bb.GetLeft(), bb.GetRight(), MM(0.1)):
                c = VECTOR2I(int(xx), int(yy))
                if not poly.Contains(c): continue
                if min(ch.SquaredDistance(c, True) for ch in chains) < MM(0.32) ** 2: continue
                v = pcbnew.PCB_VIA(b); v.SetPosition(c); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNetCode(GND); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                vs = v.GetEffectiveShape(pcbnew.B_Cu)
                if any(o.IsOnLayer(pcbnew.B_Cu) and vs.Collide(o.GetEffectiveShape(pcbnew.B_Cu), MM(0.21)) for o in others): continue
                if any((h.GetPosition() - c).EuclideanNorm() < MM(0.85) for h in holes): continue
                if any(p2.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p2.GetEffectiveShape(pcbnew.F_Cu).Collide(v.GetEffectiveShape(pcbnew.F_Cu), MM(0.15)) for p2 in b.GetPads()): continue
                b.Add(v); added += 1; done = True; break
            if done: break
        print('fragment', i, 'area', round(fp_.Outline(i).Area() / 1e12, 3), 'mm2 ->', 'via added' if done else 'NO SPOT')
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(fn, b)
b = pcbnew.LoadBoard(fn); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(fn, b)
pcbnew.WriteDRCReport(b, fn.replace('.kicad_pcb', '_drc.rpt'), pcbnew.EDA_UNITS_MILLIMETRES, True)
print('added', added)
