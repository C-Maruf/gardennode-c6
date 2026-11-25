"""Generate a label-style KiCad 7 schematic from design.py"""
import sys, uuid, os, copy
sys.path.insert(0, os.path.dirname(__file__))
from sexp import *
from design import parts, POWER_NETS, SYM

U = lambda: str(uuid.uuid4())
ROOT = U()
G = 2.54
def snap(v): return round(v / G) * G

LIBNICK = lambda p: os.path.basename(p['lib']).replace('.kicad_sym', '')

GROUPS = [
    ('usb', 'USB-C input + ESD', 20, 30, 170),
    ('pwr', 'Solar input / power OR-ing', 20, 140, 170),
    ('chg', 'Li-ion charger + power path (BQ24074, USB500 mode, 0.59 A)', 20, 230, 170),
    ('ldo', '3.3 V LDO', 20, 350, 170),
    ('mcu', 'ESP32-C6 (Wi-Fi 6 / BLE 5 / 802.15.4 Zigbee+Thread)', 205, 30, 190),
    ('meas', 'Battery + solar voltage sense', 205, 260, 190),
    ('sens', 'Switched 3V3 sensor rail, soil probes, 1-Wire, Qwiic', 410, 30, 170),
    ('valve', 'Valve / pump low-side driver (5-24 V)', 410, 250, 170),
    ('mech', 'Mechanical', 410, 360, 170),
]

lib_syms = {}
out_syms, labels, ncs, texts = [], [], [], []

def lbl(net, x, y, ang):
    just = {0: 'left', 180: 'right', 90: 'left', 270: 'right'}[ang]
    labels.append([Sym('label'), net, [Sym('at'), x, y, ang],
                   [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], [Sym('justify'), Sym(just), Sym('bottom')]],
                   [Sym('uuid'), Sym(U())]])

def add_symbol(libpath, name, nick, ref, value, fp, x, y, pinnets, extra_props=(), in_bom=True):
    s = get_symbol(libpath, name)
    lid = f'{nick}:{name}'
    if lid not in lib_syms:
        e = copy.deepcopy(s); e[1] = lid; lib_syms[lid] = e
    ps = pins(s)
    ys = [p['y'] for p in ps] or [0]
    top, bot = -max(ys) if ps else -5, -min(ys) if ps else 5
    props = [('Reference', ref, x, y + top - 3.0, False), ('Value', value, x, y + bot + 3.0, False),
             ('Footprint', fp, x, y, True), ('Datasheet', '', x, y, True)] + [(k, v, x, y, True) for k, v in extra_props]
    inst = [Sym('symbol'), [Sym('lib_id'), lid], [Sym('at'), x, y, 0], [Sym('unit'), 1],
            [Sym('in_bom'), Sym('yes' if in_bom else 'no')], [Sym('on_board'), Sym('yes')], [Sym('dnp'), Sym('no')], [Sym('uuid'), Sym(U())]]
    for k, v, px, py, hide in props:
        eff = [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]]]
        if hide: eff.append(Sym('hide'))
        inst.append([Sym('property'), k, v, [Sym('at'), px, py, 0], eff])
    seen = set()
    for p in ps:
        if p['num'] in seen: continue
        seen.add(p['num'])
        inst.append([Sym('pin'), p['num'], [Sym('uuid'), Sym(U())]])
    inst.append([Sym('instances'), [Sym('project'), 'gardennode', [Sym('path'), '/' + ROOT, [Sym('reference'), ref], [Sym('unit'), 1]]]])
    out_syms.append(inst)
    for p in ps:
        wx, wy = x + p['x'], y - p['y']
        if p['num'] not in pinnets:
            continue
        net = pinnets[p['num']]
        if net is None:
            if p['type'] != 'no_connect':
                ncs.append([Sym('no_connect'), [Sym('at'), wx, wy], [Sym('uuid'), Sym(U())]])
            continue
        ang = {0: 180, 180: 0, 90: 270, 270: 90}[int(p['rot']) % 360]
        lbl(net, wx, wy, ang)

def text(t, x, y, size=2.0):
    texts.append([Sym('text'), t, [Sym('at'), x, y, 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), size, size], Sym('bold')], [Sym('justify'), Sym('left'), Sym('bottom')]],
                  [Sym('uuid'), Sym(U())]])

def extent(p):
    s = get_symbol(p['lib'], p['sym']); ps = pins(s)
    if not ps: return (-3, 3, -3, 3), 0
    xs = [q['x'] for q in ps]; ys = [q['y'] for q in ps]
    maxlab = max((len(n or '') for n in p['pins'].values()), default=0)
    return (min(xs), max(xs), min(ys), max(ys)), maxlab * 1.1 + 3

for key, title, gx, gy, gw in GROUPS:
    text(title, gx, gy - 6)
    cx, cy, rowh = gx, gy + 5, 0
    for p in [q for q in parts if q['grp'] == key]:
        (x0, x1, y0, y1), lab = extent(p)
        lx = lab if x0 < -0.1 or (x1 - x0) < 0.1 else 2
        rx = lab if x1 > 0.1 or (x1 - x0) < 0.1 else 2
        w = (x1 - x0) + lx + rx + 6
        h = (y1 - y0) + 14
        if cx + w > gx + gw and cx > gx:
            cx, cy, rowh = gx, cy + rowh, 0
        X = snap(cx + lx - x0); Y = snap(cy + 6 + y1)
        extra = [('Manufacturer', p['mfr']), ('MPN', p['mpn'])]
        add_symbol(p['lib'], p['sym'], LIBNICK(p), p['ref'], p['value'], p['fp'], X, Y, p['pins'], extra,
                   in_bom=p['grp'] != 'mech')
        cx += w; rowh = max(rowh, h)

# power flags
fx = 205
text('Power flags (ERC)', fx, 372)
for i, net in enumerate(POWER_NETS):
    X, Y = snap(fx + 5 + i * 20), snap(382)
    add_symbol(SYM + 'power.kicad_sym', 'PWR_FLAG', 'power', f'#FLG{i+1:02d}', 'PWR_FLAG', '', X, Y, {'1': net}, in_bom=False)

sch = [Sym('kicad_sch'), [Sym('version'), 20230121], [Sym('generator'), Sym('eeschema')], [Sym('uuid'), Sym(ROOT)],
       [Sym('paper'), 'A2'],
       [Sym('title_block'), [Sym('title'), 'GardenNode-C6 solar garden/greenhouse sensor node'], [Sym('date'), '2026-11-24'],
        [Sym('rev'), 'A'], [Sym('company'), 'Open hardware'], [Sym('comment'), 1, 'Generated from tools/design.py - edit there and regenerate']],
       [Sym('lib_symbols')] + list(lib_syms.values())]
sch += labels + ncs + texts + out_syms
sch.append([Sym('sheet_instances'), [Sym('path'), '/', [Sym('page'), '1']]])
os.makedirs(sys.argv[1], exist_ok=True)
open(os.path.join(sys.argv[1], 'gardennode.kicad_sch'), 'w').write(dump(sch) + '\n')
print('symbols', len(out_syms), 'labels', len(labels), 'nc', len(ncs))
