import sys, pcbnew
from pcbnew import FromMM as MM, VECTOR2I, EDA_ANGLE, DEGREES_T
b = pcbnew.LoadBoard(sys.argv[1]); OX = OY = 50.0
def net(n):
    f_ = b.FindNet(n)
    if f_ is None:
        f_ = pcbnew.NETINFO_ITEM(b, n); b.Add(f_)
    return f_
fp = {f.GetReference(): f for f in b.GetFootprints()}
[p for p in fp['BT1'].Pads() if p.GetNumber() == '1'][0].SetNet(net('VBAT_RAW'))
def add(ref, lib, name, val, x, y, rot, pins):
    f = pcbnew.FootprintLoad(f'/usr/share/kicad/footprints/{lib}.pretty', name)
    f.SetReference(ref); f.SetValue(val); f.SetPosition(VECTOR2I(MM(OX + x), MM(OY + y))); f.SetOrientation(EDA_ANGLE(rot, DEGREES_T))
    f.Reference().SetLayer(pcbnew.F_Fab)
    for p in f.Pads():
        if p.GetNumber() in pins: p.SetNet(net(pins[p.GetNumber()]))
    b.Add(f)
add('Q3', 'Package_TO_SOT_SMD', 'SOT-23', 'DMG2305UX', 10.5, 30.5, 0, {'1': 'BAT_G', '2': 'VBAT', '3': 'VBAT_RAW'})
add('R25', 'Resistor_SMD', 'R_0603_1608Metric', '10k', 6.5, 30.5, 90, {'1': 'BAT_G', '2': 'GND'})
# drop the duplicate +/- I had added (the holder footprint already has its own)
for d in list(b.GetDrawings()):
    if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() in ('+', '-'): b.Delete(d)
pcbnew.SaveBoard(sys.argv[2], b); print('ok')
