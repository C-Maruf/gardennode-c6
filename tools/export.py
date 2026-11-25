"""Fab outputs: Gerbers, drill, pick-and-place, BOM, PDFs.  usage: python3 export.py board.kicad_pcb outdir"""
import sys, os, csv, subprocess, zipfile, glob
sys.path.insert(0, os.path.dirname(__file__))
from design import parts

pcb, out = sys.argv[1], sys.argv[2]
g = os.path.join(out, 'gerbers'); os.makedirs(g, exist_ok=True)
run = lambda *a: subprocess.run(a, check=True, capture_output=True, text=True)
layers = 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'
run('kicad-cli', 'pcb', 'export', 'gerbers', '--layers', layers, '--subtract-soldermask', '--no-x2', '-o', g + '/', pcb)
run('kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map', '--map-format', 'pdf',
    '--drill-origin', 'absolute', '--excellon-units', 'mm', '-o', g + '/', pcb)
with zipfile.ZipFile(os.path.join(out, 'gardennode-c6_revA_gerbers.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(glob.glob(g + '/*')):
        if not f.endswith('.pdf'): z.write(f, os.path.basename(f))

# pick and place (SMD only, top side)
run('kicad-cli', 'pcb', 'export', 'pos', '--side', 'front', '--format', 'csv', '--units', 'mm', '--smd-only',
    '--use-drill-file-origin', '-o', os.path.join(out, 'gardennode-c6_revA_cpl_top.csv'), pcb)

# BOM
DIST = {  # US distributors that stock each line (Digi-Key = DK, Mouser = MO); alt = drop-in second source
    'ESP32-C6-WROOM-1-N8': ('DK, MO', 'ESP32-C6-WROOM-1-N4 (4 MB flash)'),
    'BQ24074RGTR': ('DK, MO, TI.com', 'BQ24074RGTT (small reel)'),
    'TLV75733PDBVR': ('DK, MO, TI.com', 'TLV75733PDYDR, TLV75533PDBVR (0.5 A)'),
    'USB4105-GF-A': ('DK, MO', 'USB4105-GF-A-060'),
    'SP0503BAHTG': ('DK, MO', ''), 'B340A-13-F': ('DK, MO', 'B340A-E3/61T (Vishay)'),
    'SMAJ12A': ('DK, MO', 'SMAJ12A-13-F (Diodes)'), 'SMAJ26A': ('DK, MO', 'SMAJ26A-13-F (Diodes)'),
    'DMN3404L-7': ('DK, MO', 'DMG3404L-7'), 'DMG2305UX-7': ('DK, MO', 'DMG2307L-7'),
    '1042': ('DK, MO', '1042P (polarized)'), 'KMR221GLFS': ('DK, MO', ''),
    'NCP18XH103F03RB': ('DK, MO', 'NTCG163JF103FT1 (TDK)'), 'LTST-C191KGKT': ('DK, MO', ''),
    '1984617': ('DK, MO', ''), '1984633': ('DK, MO', ''),
    'B3B-PH-K-S(LF)(SN)': ('DK, MO', ''), 'SM04B-SRSS-TB(LF)(SN)': ('DK, MO', ''),
}
rows = {}
for p in parts:
    if p['grp'] == 'mech': continue
    key = (p['value'], p['fp'], p['mpn'])
    rows.setdefault(key, dict(refs=[], p=p))['refs'].append(p['ref'])
def refkey(r):
    import re; m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))
with open(os.path.join(out, 'gardennode-c6_revA_bom.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Item', 'Qty', 'References', 'Value', 'Footprint', 'Manufacturer', 'MPN', 'US distributors', 'Approved alternate', 'Populate'])
    items = sorted(rows.values(), key=lambda r: refkey(sorted(r['refs'], key=refkey)[0]))
    for i, r in enumerate(items, 1):
        p = r['p']; refs = sorted(r['refs'], key=refkey)
        dnp = p['mpn'] == 'DNP'
        mpn = p['mpn'] if not dnp else ('PRT-00116 (SparkFun) or any 0.1" header' if p['ref'].startswith('J') else '')
        dist, alt = DIST.get(p['mpn'], ('DK, MO', ''))
        if p['mfr'] in ('Yageo', 'Samsung Electro-Mechanics') and not alt:
            alt = 'any AEC/X7R-equivalent 0603/0805 part, same value/voltage/tolerance'
        w.writerow([i, len(refs), ' '.join(refs), p['value'], p['fp'].split(':')[1], p['mfr'] if not dnp else '-', mpn, dist if not dnp else '-', alt, 'DNP' if dnp else 'Yes'])

# drawings
run('kicad-cli', 'pcb', 'export', 'pdf', '--layers', 'F.Fab,F.SilkS,Edge.Cuts', '--black-and-white', '-o', os.path.join(out, 'assembly_top.pdf'), pcb)
print('exported to', out)
