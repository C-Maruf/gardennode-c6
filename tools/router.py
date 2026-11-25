"""Small 2-layer grid A* autorouter for pcbnew boards (KiCad 7).
usage: /usr/bin/python3 router.py in.kicad_pcb out.kicad_pcb
GND is left to copper pours + stitching vias (added in finish step)."""
import sys, heapq, math, time
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
import pcbnew
from skimage.graph import MCP_Geometric
OFFS = [(0,-1,0),(0,1,0),(0,0,-1),(0,0,1),(0,-1,-1),(0,-1,1),(0,1,-1),(0,1,1),(1,0,0),(-1,0,0)]
from pcbnew import FromMM as MM, ToMM

RES = 0.05                # mm per cell
CLR = 0.20                # rule clearance
MARGIN = 0.06
NECK_W, NECK_R = 0.2, 0.9   # power traces neck to 0.2 mm within 0.9 mm of their own pads             # safety margin for raster error
EDGE_CLR = 0.35
VIA_D, VIA_DRILL = 0.6, 0.3
VIA_COST = 22.0
WIDTH = {'default': 0.2, 'power': 0.3, 'hc': 0.8}
CLASS = {**{n: 'power' for n in ['VBUS', 'VIN_CHG', 'SOLAR', 'VSYS', 'VBAT', 'VBAT_RAW', '+3V3', '3V3_SW']},
         **{n: 'hc' for n in ['VEXT', 'VALVE_D']}}
ORDER_FIRST = ['USB_DN', 'USB_DP', 'EN1', 'PGOOD_N', 'CHG_N', 'ILIM', 'ISET', 'TS', 'VBUS', 'CC1', 'CC2', 'VBAT', 'VSYS', 'VIN_CHG', '+3V3', 'VEXT', 'VALVE_D', 'SOLAR', '3V3_SW']
SKIP = {'GND'}
OX, OY = 50.0, 50.0

inp, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(inp)
import os
ONLY = [n for n in os.environ.get('ONLY', '').split(',') if n]
if ONLY:
    MARGIN_ESC = float(os.environ.get('ESC', '0.03'))
else:
    MARGIN_ESC = 0.01
bb = board.GetBoardEdgesBoundingBox()
X0, Y0 = ToMM(bb.GetLeft()), ToMM(bb.GetTop())
NX = int(round(ToMM(bb.GetWidth()) / RES)) + 1
NY = int(round(ToMM(bb.GetHeight()) / RES)) + 1
print('grid', NX, NY)

def to_px(xmm, ymm): return ((xmm - X0) / RES, (ymm - Y0) / RES)

# net id raster per layer: 0 = free, -1 = hard obstacle (holes/edge/keepout), >0 net code
net_names = {}
def nid(pad_or_item):
    n = pad_or_item.GetNetname(); c = pad_or_item.GetNetCode()
    if c: net_names[c] = n
    return c

cop = [Image.new('I', (NX, NY), 0), Image.new('I', (NX, NY), 0)]
hard = Image.new('L', (NX, NY), 0)
drw = [ImageDraw.Draw(cop[0]), ImageDraw.Draw(cop[1])]
hd = ImageDraw.Draw(hard)
pad_cells = {}   # pad -> (layers, mask indices)

def poly_pts(ps, i=0):
    o = ps.Outline(i)
    return [to_px(ToMM(o.CPoint(k).x), ToMM(o.CPoint(k).y)) for k in range(o.PointCount())]

pads = list(board.GetPads())
for p in pads:
    if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
        c = p.GetPosition(); r = ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2 + 0.25
        cx, cy = to_px(ToMM(c.x), ToMM(c.y)); rr = r / RES
        hd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
        continue
    code = nid(p)
    for li, layer in enumerate((pcbnew.F_Cu, pcbnew.B_Cu)):
        if not p.IsOnLayer(layer): continue
        ps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps, layer, 0, MM(0.005))
        for i in range(ps.OutlineCount()):
            drw[li].polygon(poly_pts(ps, i), fill=code if code else 999999)

# board edge
edge = Image.new('L', (NX, NY), 255); ed = ImageDraw.Draw(edge)
outline = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(outline)
ed.polygon(poly_pts(outline, 0), fill=0)
# keepouts
for z in board.Zones():
    if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
        hd.polygon(poly_pts(z.Outline(), 0), fill=255)

COP = [np.array(c, dtype=np.int64) for c in cop]
PADCOP = [c.copy() for c in COP]
for t in board.GetTracks():
    if t.GetClass() != 'PCB_VIA':
        im_ = Image.new('I', (NX, NY), 0); d_ = ImageDraw.Draw(im_)
        a_ = to_px(ToMM(t.GetStart().x), ToMM(t.GetStart().y)); e_ = to_px(ToMM(t.GetEnd().x), ToMM(t.GetEnd().y))
        d_.line([a_, e_], fill=1, width=int(round(ToMM(t.GetWidth()) / RES)) + 1)
        r_ = ToMM(t.GetWidth()) / 2 / RES + 0.5
        for q_ in (a_, e_): d_.ellipse([q_[0] - r_, q_[1] - r_, q_[0] + r_, q_[1] + r_], fill=1)
        li = 0 if t.GetLayer() == pcbnew.F_Cu else 1
        m_ = np.array(im_) > 0; COP[li][m_ & (COP[li] == 0)] = t.GetNetCode()
    if t.GetClass() == 'PCB_VIA':
        c = t.GetPosition(); x_, y_ = to_px(ToMM(c.x), ToMM(c.y)); r_ = ToMM(t.GetWidth()) / 2 / RES + 0.5
        yy_, xx_ = np.ogrid[:NY, :NX]; m_ = (yy_ - y_) ** 2 + (xx_ - x_) ** 2 <= r_ * r_
        for li in (0, 1): COP[li][m_ & (COP[li] == 0)] = t.GetNetCode()
HARD = np.array(hard) > 0
EDGE = np.array(edge) > 0
edge_dist = ndimage.distance_transform_edt(~EDGE) * RES   # distance to outside-of-board
hard_dist = ndimage.distance_transform_edt(~HARD) * RES

tracks = []   # (net, layer, [(x,y)...] in grid coords, width)
vias = []     # (net, x, y)

def raster_track(code, li, pts, w):
    im = Image.fromarray(np.zeros((NY, NX), dtype=np.int32), 'I'); d = ImageDraw.Draw(im)
    rr = w / 2 / RES + 0.5
    for (a, b) in zip(pts, pts[1:]):
        d.line([a[1], a[0], b[1], b[0]], fill=1, width=int(round(w / RES)) + 1)
    for (y, x) in pts:
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=1)
    m = np.array(im) > 0
    COP[li][m & (COP[li] == 0)] = code

def raster_via(code, y, x):
    rr = VIA_D / 2 / RES
    yy, xx = np.ogrid[:NY, :NX]
    y0, y1, x0, x1 = max(0, int(y - rr - 1)), min(NY, int(y + rr + 2)), max(0, int(x - rr - 1)), min(NX, int(x + rr + 2))
    sub = (yy[y0:y1] - y) ** 2 + (xx[:, x0:x1] - x) ** 2 <= rr * rr + 1e-6
    for li in (0, 1):
        reg = COP[li][y0:y1, x0:x1]; reg[sub & (reg == 0)] = code

NB = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]

def route_conn(code, w, src_cells, dst_mask, dst_center, neck=None):
    """multi-source A*. src_cells: list of (l,y,x). dst_mask: bool array [2,NY,NX]"""
    need = CLR + w / 2 + MARGIN
    vneed = CLR + VIA_D / 2 + MARGIN
    free = []; vfit = (edge_dist >= EDGE_CLR + VIA_D / 2) & (hard_dist >= VIA_D / 2 + 0.1)
    for li in (0, 1):
        other = (COP[li] != 0) & (COP[li] != code)
        dist = ndimage.distance_transform_edt(~other) * RES
        f = (dist >= need) & (edge_dist >= EDGE_CLR + w / 2) & (hard_dist >= w / 2 + 0.05)
        if neck is not None:
            # pad escape: rasterised pads are ~1 px fat, so near our own pads relax the raster margin
            f |= neck & (dist >= CLR + NECK_W / 2 + MARGIN_ESC) & (edge_dist >= EDGE_CLR + NECK_W / 2)
        f |= (PADCOP[li] == code)
        f |= ONTRACK[li] == code
        if li == 0: f &= ~HARDF | (PADCOP[0] == code)
        free.append(f); vfit &= dist >= vneed
    vfit &= ~HARDV & ~SMDV
    cost = np.full((3, NY, NX), np.inf)
    cost[0][free[0]] = 1.0
    cost[2][free[1]] = 1.0
    cost[1][vfit & free[0] & free[1]] = VIA_COST
    starts = [(0 if l == 0 else 2, y, x) for (l, y, x) in src_cells if free[l][y, x]]
    ends = [(0 if l == 0 else 2, y, x) for (l, y, x) in np.argwhere(dst_mask)]
    if not starts or not ends: return None
    m = MCP_Geometric(cost, offsets=OFFS)
    cum, _ = m.find_costs(starts, ends, find_all_ends=False)
    ec = [cum[e] for e in ends]
    k = int(np.argmin(ec))
    if not np.isfinite(ec[k]): return None
    tb = m.traceback(ends[k])
    for a_, b_ in zip(tb, tb[1:]):
        if a_[0] == 1 and b_[0] == 1: print('    WARN via-plane move', a_, b_)
    path = []
    for (l, y, x) in tb:
        if l == 1: continue
        path.append((0 if l == 0 else 1, int(y), int(x)))
    return path

STUB = {}
ONTRACK = [np.zeros((NY, NX), np.int64), np.zeros((NY, NX), np.int64)]
_tr = [t for t in board.GetTracks() if t.GetClass() != 'PCB_VIA']
for t in _tr:   # centreline cells of existing tracks are usable by their own net
    a_ = to_px(ToMM(t.GetStart().x), ToMM(t.GetStart().y)); e_ = to_px(ToMM(t.GetEnd().x), ToMM(t.GetEnd().y))
    n_ = int(max(abs(e_[0] - a_[0]), abs(e_[1] - a_[1]))) + 1
    li = 0 if t.GetLayer() == pcbnew.F_Cu else 1
    for k in range(n_ + 1):
        xx = int(round(a_[0] + (e_[0] - a_[0]) * k / n_)); yy = int(round(a_[1] + (e_[1] - a_[1]) * k / n_))
        ONTRACK[li][yy, xx] = t.GetNetCode()
for p in pads:
    c = p.GetPosition(); cur = (c.x, c.y); used = set()
    while True:
        nxt = None
        for t in _tr:
            if id(t) in used or t.GetNetCode() != p.GetNetCode() or p.GetNetCode() == 0: continue
            if (t.GetStart().x, t.GetStart().y) == cur: nxt = (t.GetEnd().x, t.GetEnd().y)
            elif (t.GetEnd().x, t.GetEnd().y) == cur: nxt = (t.GetStart().x, t.GetStart().y)
            if nxt: used.add(id(t)); break
        if not nxt: break
        cur = nxt
    if used: STUB[(p.GetParent().GetReference(), p.GetNumber())] = (ToMM(cur[0]), ToMM(cur[1]))

def pad_mask(p, code):
    m = np.zeros((2, NY, NX), bool)
    k_ = (p.GetParent().GetReference(), p.GetNumber())
    if k_ in STUB:
        x_, y_ = to_px(*STUB[k_]); yy_, xx_ = np.ogrid[:NY, :NX]
        m[0] = (yy_ - y_) ** 2 + (xx_ - x_) ** 2 <= 2.1 ** 2
        return m
    for li, layer in enumerate((pcbnew.F_Cu, pcbnew.B_Cu)):
        if not p.IsOnLayer(layer): continue
        im = Image.new('L', (NX, NY), 0); d = ImageDraw.Draw(im)
        ps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps, layer, 0, MM(0.005))
        for i in range(ps.OutlineCount()): d.polygon(poly_pts(ps, i), fill=1)
        m[li] = np.array(im) > 0
    return m

def simplify(path, neck=None):
    """split into per-layer runs, drop collinear points; returns segments & via positions"""
    runs, vias_ = [], []
    cur = [path[0]]
    for a, b in zip(path, path[1:]):
        if a[0] != b[0]:
            runs.append(cur); vias_.append((a[1], a[2])); cur = [b]
        else: cur.append(b)
    runs.append(cur)
    out_runs = []
    for r0 in runs:
        # split into sub-runs of constant neck membership (sharing the boundary cell)
        subs = [[r0[0]]]
        nk = lambda c: bool(neck[c[1], c[2]]) if neck is not None else False
        for c in r0[1:]:
            if nk(c) != nk(subs[-1][-1]) and len(subs[-1]) > 1:
                subs.append([subs[-1][-1]])
            subs[-1].append(c)
        for r in subs:
            pts = [(r[0][1], r[0][2])]
            for i in range(1, len(r) - 1):
                d1 = (r[i][1] - r[i - 1][1], r[i][2] - r[i - 1][2]); d2 = (r[i + 1][1] - r[i][1], r[i + 1][2] - r[i][2])
                if d1 != d2: pts.append((r[i][1], r[i][2]))
            if len(r) > 1: pts.append((r[-1][1], r[-1][2]))
            isneck = neck is not None and any(nk(c) for c in r[1:-1] or r)
            out_runs.append((r[0][0], pts, isneck))
    return out_runs, vias_

def route_all(order):
    fails = []
    for name in order:
        code = board.GetNetcodeFromNetname(name)
        w = WIDTH[CLASS.get(name, 'default')]
        npads = [p for p in pads if p.GetNetCode() == code and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
        if len(npads) < 2: continue
        masks = [pad_mask(p, code) for p in npads]
        allpads = np.zeros((NY, NX), bool)
        for p_, m_ in zip(npads, masks):
            if (p_.GetParent().GetReference(), p_.GetNumber()) not in STUB: allpads |= m_[0] | m_[1]
        neck = ndimage.distance_transform_edt(~allpads) * RES <= NECK_R
        tree = masks[0].copy(); connected = [0]
        todo = list(range(1, len(npads)))
        while todo:
            # nearest pad to tree (by center distance to any connected pad)
            def dmin(i):
                pi = npads[i].GetPosition()
                return min((pi - npads[j].GetPosition()).EuclideanNorm() for j in connected)
            todo.sort(key=dmin); i = todo.pop(0)
            if (tree & masks[i]).any():
                connected.append(i); tree |= masks[i]; continue
            c = npads[i].GetPosition(); cy, cx = to_px(ToMM(c.x), ToMM(c.y))[::-1]
            src = [tuple(v) for v in np.argwhere(tree)]
            # limit sources to a manageable number: those closest to target
            if len(src) > 30000:
                src.sort(key=lambda s: (s[1] - cy) ** 2 + (s[2] - cx) ** 2); src = src[:30000]
            path = route_conn(code, w, src, masks[i], (int(round(cy)), int(round(cx))), neck)
            if path is None:
                fails.append((name, npads[i].GetParent().GetReference() + '.' + npads[i].GetNumber())); continue
            runs, vs = simplify(path, neck if w > NECK_W else None)
            # snap ends into pad centres so KiCad sees the connection
            def pc(pd):
                k_ = (pd.GetParent().GetReference(), pd.GetNumber())
                if k_ in STUB:
                    xx_, yy_ = to_px(*STUB[k_]); return (yy_, xx_)
                c_ = pd.GetPosition(); xx_, yy_ = to_px(ToMM(c_.x), ToMM(c_.y)); return (yy_, xx_)
            lst = runs[-1]
            if lst[1] and masks[i][lst[0], lst[1][-1][0], lst[1][-1][1]]:
                lst[1].append(pc(npads[i]))
            fst = runs[0]
            for j in connected:
                if fst[1] and masks[j][fst[0], fst[1][0][0], fst[1][0][1]]:
                    fst[1].insert(0, pc(npads[j])); break
            for li, pts, nk in runs:
                if len(pts) >= 2:
                    ww = NECK_W if nk else w
                    tracks.append((code, li, pts, ww)); raster_track(code, li, pts, ww)
                    for (y, x) in pts:
                        if float(y).is_integer() and float(x).is_integer(): tree[li, int(y), int(x)] = True
                # mark the whole run as tree for later connections
            for (y, x) in vs:
                vias.append((code, y, x)); raster_via(code, y, x); tree[:, y, x] = True
            for (l, y, x) in path: tree[l, y, x] = True; ONTRACK[l][y, x] = code
            connected.append(i); tree |= masks[i]
        print('  net', name, 'done', len(tracks), flush=True)
    return fails

all_nets = sorted({p.GetNetname() for p in pads if p.GetNetCode()} - SKIP)
rest = [n for n in all_nets if n not in ORDER_FIRST]
rest.sort(key=lambda n: sum(1 for p in pads if p.GetNetname() == n))
order = [n for n in ORDER_FIRST if n in all_nets] + rest
if ONLY: order = ONLY
t = time.time()
# no F.Cu routing / vias under the radio module body (board coords, mm)
KEEP_F = [(74.0, -0.5, 86.0, 28.0)]
HARDF = np.zeros((NY, NX), bool)
for (a0, b0, a1, b1) in KEEP_F:
    xa, ya = to_px(OX + a0, OY + b0); xb, yb = to_px(OX + a1, OY + b1)
    HARDF[max(0, int(ya)):int(yb) + 1, max(0, int(xa)):int(xb) + 1] = True
HARDV = np.zeros((NY, NX), bool)   # tented vias are fine under the module body, not under its antenna
# no via may touch any SMD pad (solder would wick down it); exposed thermal pads are handled separately
_sm = Image.new('L', (NX, NY), 0); _sd = ImageDraw.Draw(_sm)
for p in pads:
    if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
    if (p.GetParent().GetReference(), p.GetNumber()) in (('U1', '17'), ('U4', '29')): continue
    _ps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(_ps, pcbnew.F_Cu, 0, MM(0.005))
    for i in range(_ps.OutlineCount()): _sd.polygon(poly_pts(_ps, i), fill=1)
SMDV = ndimage.distance_transform_edt(np.array(_sm) == 0) * RES < VIA_D / 2 + 0.15
xa, ya = to_px(OX + 71.9, OY - 0.5); xb, yb = to_px(OX + 88.1, OY + 7.5)
HARDV[max(0, int(ya)):int(yb) + 1, max(0, int(xa)):int(xb) + 1] = True
COP0 = [c.copy() for c in COP]
ONTRACK0 = [c.copy() for c in ONTRACK]
for attempt in range(6):
    tracks.clear(); vias.clear(); COP = [c.copy() for c in COP0]; ONTRACK = [c.copy() for c in ONTRACK0]
    fails = route_all(order)
    print(f'attempt {attempt}: {len(tracks)} tracks {len(vias)} vias fails={fails} ({time.time()-t:.0f}s)', flush=True)
    if not fails: break
    fn = [f[0] for f in fails]
    order = list(dict.fromkeys(fn + order))

import pickle; pickle.dump((tracks, vias, fails), open(out + '.route.pkl', 'wb'))
def gp(y, x): return pcbnew.VECTOR2I(MM(float(X0 + float(x) * RES)), MM(float(Y0 + float(y) * RES)))
for code, li, pts, w in tracks:
    for a, b in zip(pts, pts[1:]):
        t_ = pcbnew.PCB_TRACK(board); t_.SetStart(gp(*a)); t_.SetEnd(gp(*b)); t_.SetWidth(MM(float(w)))
        t_.SetLayer(pcbnew.F_Cu if li == 0 else pcbnew.B_Cu); t_.SetNetCode(int(code)); board.Add(t_)
for code, y, x in vias:
    v = pcbnew.PCB_VIA(board); v.SetPosition(gp(y, x)); v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_DRILL)); v.SetNetCode(int(code))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); board.Add(v)
pcbnew.SaveBoard(out, board)
print('saved', out, 'unrouted:', fails)
