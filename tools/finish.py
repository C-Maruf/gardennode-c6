"""Add GND pours + stitching, fill, DRC.  usage: /usr/bin/python3 finish.py routed.kicad_pcb final.kicad_pcb"""
import sys, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
import pcbnew
from pcbnew import FromMM as MM, ToMM, VECTOR2I

RES = 0.05
inp, out = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(inp)
GND = b.GetNetcodeFromNetname('GND')
bb = b.GetBoardEdgesBoundingBox()
X0, Y0 = ToMM(bb.GetLeft()), ToMM(bb.GetTop())
NX = int(round(ToMM(bb.GetWidth()) / RES)) + 1; NY = int(round(ToMM(bb.GetHeight()) / RES)) + 1
OX, OY = 50.0, 50.0

def px(x, y): return ((x - X0) / RES, (y - Y0) / RES)
def poly_pts(ps, i=0):
    o = ps.Outline(i); return [px(ToMM(o.CPoint(k).x), ToMM(o.CPoint(k).y)) for k in range(o.PointCount())]

def rasters():
    """per-layer boolean map of non-GND copper (+ NPTH/keepout as hard)"""
    ims = [Image.new('L', (NX, NY), 0) for _ in range(2)]; ds = [ImageDraw.Draw(i) for i in ims]
    hard = Image.new('L', (NX, NY), 0); hd = ImageDraw.Draw(hard)
    for li, layer in enumerate((pcbnew.F_Cu, pcbnew.B_Cu)):
        for p in b.GetPads():
            if p.GetDrillSize().x > 0:
                c = p.GetPosition(); r = (ToMM(p.GetDrillSize().x) / 2 + 0.25) / RES; x, y = px(ToMM(c.x), ToMM(c.y))
                hd.ellipse([x - r, y - r, x + r, y + r], fill=1)
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                c = p.GetPosition(); r = ToMM(p.GetDrillSize().x) / 2 / RES; x, y = px(ToMM(c.x), ToMM(c.y))
                hd.ellipse([x - r, y - r, x + r, y + r], fill=1); continue
            if p.GetNetCode() == GND or not p.IsOnLayer(layer): continue
            ps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps, layer, 0, MM(0.005))
            for i in range(ps.OutlineCount()): ds[li].polygon(poly_pts(ps, i), fill=1)
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA':
                c = t.GetPosition(); r = (ToMM(t.GetDrillValue()) / 2 + 0.25) / RES; x, y = px(ToMM(c.x), ToMM(c.y))
                hd.ellipse([x - r, y - r, x + r, y + r], fill=1)
            if t.GetNetCode() == GND: continue
            if t.GetClass() == 'PCB_VIA':
                c = t.GetPosition(); r = ToMM(t.GetWidth()) / 2 / RES; x, y = px(ToMM(c.x), ToMM(c.y))
                ds[li].ellipse([x - r, y - r, x + r, y + r], fill=1)
            elif t.GetLayer() == layer:
                a = px(ToMM(t.GetStart().x), ToMM(t.GetStart().y)); e = px(ToMM(t.GetEnd().x), ToMM(t.GetEnd().y))
                w = ToMM(t.GetWidth()) / RES
                ds[li].line([a, e], fill=1, width=max(1, int(round(w))))
                for q in (a, e): ds[li].ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], fill=1)
    for z in b.Zones():
        if z.GetIsRuleArea(): hd.polygon(poly_pts(z.Outline(), 0), fill=1)
    edge = Image.new('L', (NX, NY), 1); ImageDraw.Draw(edge).polygon(poly_pts(outline, 0), fill=0)
    return [np.array(i) > 0 for i in ims], np.array(hard) > 0, np.array(edge) > 0

outline = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(outline)

def add_via(x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(MM(float(x)), MM(float(y)))); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
    v.SetNetCode(GND); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)

def add_track(a, c, layer=pcbnew.F_Cu, w=0.3):
    t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(MM(float(a[0])), MM(float(a[1])))); t.SetEnd(VECTOR2I(MM(float(c[0])), MM(float(c[1]))))
    t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNetCode(GND); b.Add(t)

def clear_map(need, stub=0.42):
    global cop_ok
    cop, hard, edge = rasters()
    cop_ok = ndimage.distance_transform_edt(~cop[0]) * RES >= stub
    ok = np.ones((NY, NX), bool)
    for li in (0, 1): ok &= ndimage.distance_transform_edt(~cop[li]) * RES >= need
    ok &= ndimage.distance_transform_edt(~hard) * RES >= 0.45
    ok &= ndimage.distance_transform_edt(~edge) * RES >= 1.0
    return ok

# 2) pours
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(GND)
    z.SetMinThickness(MM(0.25)); z.SetLocalClearance(MM(0.3)); z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for xx, yy in [(0.2, 0.2), (99.8, 0.2), (99.8, 81.8), (0.2, 81.8)]: o.Append(MM(OX + xx), MM(OY + yy))
    b.Add(z)

# 3) stitching grid (avoid module body except EPAD, and the USB connector)
ok = clear_map(0.3 + 0.3 + 0.05)
def in_rect(x, y, r):
    return r[0] <= x <= r[2] and r[1] <= y <= r[3]
avoid = [(OX + 70.5, OY + 0, OX + 89.5, OY + 26.0), (OX + 0, OY + 8, OX + 8, OY + 20)]
n = 0
for gy in np.arange(Y0 + 2.0, Y0 + 80.5, 3.0):
    for gx in np.arange(X0 + 2.0, X0 + 98.5, 3.0):
        if any(in_rect(gx, gy, r) for r in avoid): continue
        i, j = int(round((gy - Y0) / RES)), int(round((gx - X0) / RES))
        if ok[i, j]:
            add_via(gx, gy); n += 1
print('stitch vias', n)

# 4) GND fan-out via next to every SMD GND pad (F pour alone may not reach some)
ok = clear_map(0.3 + 0.3 + 0.05)
fan = 0
for p in b.GetPads():
    if p.GetNetCode() != GND or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
    if p.GetParent().GetReference() in ('U4',) and p.GetNumber() == '29': continue
    if p.GetParent().GetReference() == 'U1' and p.GetNumber() == '17': continue
    c = p.GetPosition(); cx, cy = ToMM(c.x), ToMM(c.y)
    best = None
    for r in np.arange(0.9, 2.6, 0.2):
        for ang in range(0, 360, 20):
            x, y = cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang))
            i, j = int(round((y - Y0) / RES)), int(round((x - X0) / RES))
            if 0 <= i < NY and 0 <= j < NX and ok[i, j]:
                # the short F.Cu stub must also stay clear: sample along it
                good = True
                for t in np.linspace(0, 1, 12):
                    xx, yy = cx + (x - cx) * t, cy + (y - cy) * t
                    ii, jj = int(round((yy - Y0) / RES)), int(round((xx - X0) / RES))
                    if not cop_ok[ii, jj]: good = False; break
                if good: best = (x, y); break
        if best: break
    if best:
        add_via(*best); add_track((cx, cy), best); fan += 1
        ok = clear_map(0.65)
print('fanout vias', fan)

filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
pcbnew.SaveBoard(out, b)
b2 = pcbnew.LoadBoard(out)
pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
pcbnew.SaveBoard(out, b2)
rep = out.replace('.kicad_pcb', '_drc.rpt')
pcbnew.WriteDRCReport(b2, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
print(open(rep).read()[-1500:])
