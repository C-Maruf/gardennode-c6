"""photo-style top render from per-layer SVG plots: green mask, gold pads, white silk"""
import sys, numpy as np, cairosvg, pcbnew
from PIL import Image, ImageDraw
from scipy import ndimage
pcb, d, out = sys.argv[1], sys.argv[2], sys.argv[3]
W = 2000
def m(L):
    cairosvg.svg2png(url=f'{d}/{L}.svg', write_to=f'{d}/{L}.png', output_width=W, background_color='white')
    return np.array(Image.open(f'{d}/{L}.png').convert('L')) < 128
cu, mask, silk, edge = m('F.Cu'), m('F.Mask'), m('F.SilkS'), m('Edge.Cuts')
H = cu.shape[0]
inside = ndimage.binary_fill_holes(ndimage.binary_dilation(edge, iterations=2))
inside = ndimage.binary_erosion(inside, iterations=2)
b = pcbnew.LoadBoard(pcb); bb = b.GetBoardEdgesBoundingBox()
ys_, xs_ = np.nonzero(edge)
ex0, ex1, ey0, ey1 = xs_.min(), xs_.max(), ys_.min(), ys_.max()
sx = (ex1 - ex0) / pcbnew.ToMM(bb.GetWidth()); sy = (ey1 - ey0) / pcbnew.ToMM(bb.GetHeight())
def px(v): return (ex0 + (pcbnew.ToMM(v.x) - pcbnew.ToMM(bb.GetLeft())) * sx, ey0 + (pcbnew.ToMM(v.y) - pcbnew.ToMM(bb.GetTop())) * sy)
holes = Image.new('L', (W, H), 0); hd = ImageDraw.Draw(holes)
for p in b.GetPads():
    if p.GetDrillSize().x > 0:
        x, y = px(p.GetPosition()); r = pcbnew.ToMM(p.GetDrillSize().x) / 2 * sx; ry = pcbnew.ToMM(p.GetDrillSize().y) / 2 * sy
        hd.ellipse([x - r, y - ry, x + r, y + ry], fill=255)
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        x, y = px(t.GetPosition()); r = pcbnew.ToMM(t.GetDrillValue()) / 2 * sx; hd.ellipse([x - r, y - r, x + r, y + r], fill=255)
holes = np.array(holes) > 0
img = np.zeros((H, W, 3), np.uint8); img[:] = (245, 245, 245)
img[inside] = (22, 84, 44)                       # FR-4 under solder mask
img[inside & cu] = (38, 120, 62)                 # copper under mask
img[inside & mask & ~cu] = (190, 175, 130)       # bare FR-4 opening
img[inside & mask & cu] = (212, 172, 72)         # ENIG pads
img[inside & silk & ~(mask & cu)] = (250, 250, 250)
img[holes] = (30, 30, 30)
Image.fromarray(img[max(0,ey0-20):ey1+20, max(0,ex0-20):ex1+20]).save(out)
print('saved', out, img.shape)
