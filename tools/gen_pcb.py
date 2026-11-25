"""Build the GardenNode-C6 PCB with pcbnew (KiCad 7). Usage: gen_pcb.py out.kicad_pcb [routed.ses]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from pcbnew import VECTOR2I, FromMM as MM, EDA_ANGLE, DEGREES_T
from design import parts

FPLIBS = {'Espressif': '/home/claude/dl/esp/footprints/Espressif.pretty'}
def fplib(nick): return FPLIBS.get(nick, f'/usr/share/kicad/footprints/{nick}.pretty')

W, H = 100.0, 82.0          # board size, mm
OX, OY = 50.0, 50.0         # sheet offset
def P(x, y): return VECTOR2I(MM(OX + x), MM(OY + y))

# (x, y, rotation_deg, side)  coordinates in board frame, origin = top-left corner
PLACE = {
    # USB / power entry (top-left)
    'J1': (3.2, 14, 270, 'F'), 'U3': (14.0, 12.0, 0, 'F'), 'R1': (10.5, 20.5, 90, 'F'), 'R2': (12.5, 20.5, 90, 'F'),
    'D1': (18.5, 6.0, 0, 'F'),
    # charger
    'U1': (27.0, 13.0, 0, 'F'), 'C1': (27.0, 7.5, 0, 'F'), 'C2': (32.8, 10.5, 90, 'F'), 'C3': (21.5, 14.0, 90, 'F'),
    'R3': (23.0, 8.5, 90, 'F'), 'R4': (32.8, 15.5, 90, 'F'), 'TH1': (17.0, 29.0, 0, 'F'), 'R5': (28.5, 19.5, 90, 'F'),
    'R6': (34.8, 15.5, 90, 'F'), 'R24': (26.0, 19.5, 90, 'F'),
    # LDO
    'U2': (40.0, 12.0, 0, 'F'), 'C4': (40.0, 8.0, 0, 'F'), 'C5': (40.0, 16.0, 0, 'F'),
    # MCU support
    'C6': (66.5, 8.0, 90, 'F'), 'C7': (64.5, 8.0, 90, 'F'), 'R7': (64.0, 13.5, 0, 'F'), 'C8': (64.0, 15.5, 0, 'F'),
    'R8': (64.0, 20.0, 0, 'F'), 'R9': (64.0, 22.0, 0, 'F'), 'SW1': (50.0, 27.0, 0, 'F'), 'SW2': (57.0, 27.0, 0, 'F'),
    'D4': (44.0, 27.5, 0, 'F'), 'R10': (44.0, 25.5, 0, 'F'),
    'U4': (80.0, 15.2, 0, 'F'),
    'J8': (47.0, 4.5, 90, 'F'), 'J9': (95.5, 15.0, 0, 'F'),
    # measurement
    'R11': (56.0, 17.0, 90, 'F'), 'R12': (58.0, 17.0, 90, 'F'), 'C9': (60.0, 17.0, 90, 'F'),
    'R13': (52.0, 17.0, 90, 'F'), 'R14': (50.0, 17.0, 90, 'F'), 'C10': (48.0, 17.0, 90, 'F'),
    # battery
    'BT1': (50.0, 45.0, 0, 'F'),
    # bottom connector row
    'J2': (10.0, 74.5, 0, 'F'), 'D2': (11.0, 63.0, 90, 'F'), 'D5': (6.5, 63.0, 90, 'F'),
    'J7': (21.5, 74.5, 0, 'F'), 'Q2': (30.0, 64.0, 0, 'F'), 'D3': (24.5, 63.0, 90, 'F'), 'D6': (19.5, 63.0, 90, 'F'),
    'C14': (15.5, 63.0, 90, 'F'), 'R22': (34.0, 62.0, 0, 'F'), 'R23': (34.0, 66.0, 0, 'F'),
    'Q1': (44.0, 63.0, 0, 'F'), 'R15': (44.0, 59.5, 0, 'F'), 'C11': (48.5, 63.0, 90, 'F'),
    'J3': (52.0, 76.0, 0, 'F'), 'R16': (54.0, 68.0, 90, 'F'), 'C12': (56.0, 68.0, 90, 'F'),
    'J4': (61.0, 76.0, 0, 'F'), 'R17': (63.0, 68.0, 90, 'F'), 'C13': (65.0, 68.0, 90, 'F'),
    'J5': (70.0, 76.0, 0, 'F'), 'R18': (72.0, 68.0, 90, 'F'), 'R19': (74.0, 68.0, 90, 'F'),
    'J6': (86.0, 75.0, 0, 'F'), 'R20': (84.0, 68.0, 90, 'F'), 'R21': (86.0, 68.0, 90, 'F'),
    # mounting
    'H1': (4.0, 4.0, 0, 'F'), 'H2': (96.0, 4.0, 0, 'F'), 'H3': (4.0, 78.0, 0, 'F'), 'H4': (96.0, 78.0, 0, 'F'),
}

def build(out, ses=None):
    b = pcbnew.BOARD()
    ds = b.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = MM(0.15); ds.m_MinClearance = MM(0.15); ds.m_ViasMinSize = MM(0.5); ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.3); ds.m_HoleClearance = MM(0.25); ds.m_HoleToHoleMin = MM(0.25)
    ds.SetBoardThickness(MM(1.6))
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetTrackWidth(MM(0.25)); nc.SetClearance(MM(0.2)); nc.SetViaDiameter(MM(0.6)); nc.SetViaDrill(MM(0.3))
    netobj = {}
    def net(name):
        if name not in netobj:
            ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); netobj[name] = ni
        return netobj[name]

    for p in parts:
        nick, name = p['fp'].split(':')
        f = pcbnew.FootprintLoad(fplib(nick), name)
        f.SetReference(p['ref']); f.SetValue(p['value'])
        x, y, rot, side = PLACE[p['ref']]
        f.SetPosition(P(x, y))
        f.SetOrientation(EDA_ANGLE(rot, DEGREES_T))
        if p['mpn'] == 'DNP' or p['grp'] == 'mech':
            pass
        for pad in f.Pads():
            n = p['pins'].get(pad.GetNumber())
            if n: pad.SetNet(net(n))
        f.Reference().SetTextSize(VECTOR2I(MM(0.8), MM(0.8))); f.Reference().SetTextThickness(MM(0.12))
        # reference designators live on the assembly (Fab) layer; silkscreen keeps outlines, polarity and labels
        f.Reference().SetLayer(pcbnew.F_Fab)
        b.Add(f)

    # outline with 3 mm corner radius
    r = 3.0
    def seg(a, c):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(P(*a)); s.SetEnd(P(*c)); s.SetWidth(MM(0.1)); b.Add(s)
    def arc(cx, cy, sx, sy):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(P(cx, cy)); s.SetStart(P(sx, sy)); s.SetArcAngleAndEnd(EDA_ANGLE(90, DEGREES_T)); s.SetWidth(MM(0.1)); b.Add(s)
    seg((r, 0), (W - r, 0)); seg((W, r), (W, H - r)); seg((W - r, H), (r, H)); seg((0, H - r), (0, r))
    arc(W - r, r, W - r, 0); arc(W - r, H - r, W, H - r); arc(r, H - r, r, H); arc(r, r, 0, r)

    # antenna keepout (all copper, both layers) above/right of module antenna
    def keepout(x0, y0, x1, y1):
        z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
        o = z.Outline(); o.NewOutline()
        for xx, yy in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]: o.Append(MM(OX + xx), MM(OY + yy))
        b.Add(z)
    keepout(69.5, -0.5, 100.5, 6.2)

    # GND vias in exposed pads (placed before routing so the router keeps clear)
    gnd = net('GND')
    def via(x, y):
        v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(MM(x), MM(y))); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
        v.SetNet(gnd); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    c = [p for p in fps['U1'].Pads() if p.GetNumber() == '17'][0].GetPosition(); via(pcbnew.ToMM(c.x), pcbnew.ToMM(c.y))
    ep = [p.GetPosition() for p in fps['U4'].Pads() if p.GetNumber() == '29']
    xs = sorted({pcbnew.ToMM(p.x) for p in ep}); ys = sorted({pcbnew.ToMM(p.y) for p in ep})
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1): via((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2)

    # U1 (0.5 mm QFN) escape stubs so every signal pin keeps a clear exit
    u1pads = {p.GetNumber(): p for p in fps['U1'].Pads()}
    def stub(num, dx, dy):
        p = u1pads[num]; c = p.GetPosition()
        t = pcbnew.PCB_TRACK(b); t.SetStart(c); t.SetEnd(VECTOR2I(c.x + MM(dx), c.y + MM(dy)))
        t.SetWidth(MM(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(p.GetNet()); b.Add(t)
    for n in ('1', '2', '3'): stub(n, -1.3, 0)
    for n in ('6', '7'): stub(n, 0, 1.3)
    for n in ('9', '10', '11', '12'): stub(n, 1.3, 0)
    for n in ('13', '16'): stub(n, 0, -1.3)

    # J1 (USB-C, 0.5 mm pitch) fan-out to a 1 mm pitch so D+/D-/CC can escape cleanly
    def trk(netobj_, pts, w=0.2):
        for a_, c_ in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(MM(a_[0]), MM(a_[1]))); t.SetEnd(VECTOR2I(MM(c_[0]), MM(c_[1])))
            t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(netobj_); b.Add(t)
    jp = {p.GetNumber(): p for p in fps['J1'].Pads()}
    for n_, ty in {'A5': 11.9, 'B7': 12.9, 'A6': 13.9, 'A7': 14.9, 'B6': 15.9, 'B5': 16.9}.items():
        c_ = jp[n_].GetPosition(); x0_, y0_ = pcbnew.ToMM(c_.x), pcbnew.ToMM(c_.y)
        trk(jp[n_].GetNet(), [(x0_, y0_), (OX + 7.9, y0_), (OX + 9.4, OY + ty), (OX + 9.9, OY + ty)])

    # GND pours on both layers
    if ses is not None:
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net('GND'))
            z.SetMinThickness(MM(0.2)); z.SetLocalClearance(MM(0.3)); z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            o = z.Outline(); o.NewOutline()
            for xx, yy in [(0.2, 0.2), (W - 0.2, 0.2), (W - 0.2, H - 0.2), (0.2, H - 0.2)]: o.Append(MM(OX + xx), MM(OY + yy))
            b.Add(z)

    # silkscreen labels
    def silk(t, x, y, sz=1.0, layer=pcbnew.F_SilkS, rot=0):
        tx = pcbnew.PCB_TEXT(b); tx.SetText(t); tx.SetPosition(P(x, y)); tx.SetLayer(layer)
        tx.SetTextSize(VECTOR2I(MM(sz), MM(sz))); tx.SetTextThickness(MM(sz * 0.15)); tx.SetTextAngle(EDA_ANGLE(rot, DEGREES_T)); b.Add(tx)
    silk('GardenNode-C6 rev A', 50, 33.0, 1.2)
    silk('SOL+  -', 11.8, 80.6, 0.8); silk('VEXT GND V+ V-', 26.8, 80.6, 0.8)
    silk('SOIL1', 54, 80.3, 0.8); silk('SOIL2', 63, 80.3, 0.8); silk('1-WIRE', 72, 80.3, 0.8); silk('QWIIC', 86, 79.8, 0.8)
    silk('+', 5.5, 38.5, 2.0); silk('-', 94.5, 38.5, 2.0)
    silk('RST', 50, 30.0, 0.8); silk('BOOT', 57, 30.0, 0.8)
    silk('GardenNode-C6 rev A  2026-11  open hardware', 50, 45, 1.2, pcbnew.B_SilkS)
    silk('3V3 TX RX GND', 47, 8.2, 0.8)

    if ses:
        b.SetFileName(out)
        pcbnew.SaveBoard(out, b)
        b = pcbnew.LoadBoard(out)
        ok = pcbnew.ImportSpecctraSES(b, ses)
        print('SES import', ok)
        filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
    pcbnew.SaveBoard(out, b)
    return b

if __name__ == '__main__':
    b = build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    if len(sys.argv) <= 2:
        pcbnew.ExportSpecctraDSN(b, sys.argv[1].replace('.kicad_pcb', '.dsn'))
        print('DSN written')
