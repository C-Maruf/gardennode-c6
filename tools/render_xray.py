"""top render with bottom-layer copper traces overlaid in blue, to show where vias lead"""
import sys, numpy as np, cairosvg, pcbnew
from PIL import Image
from scipy import ndimage
pcb, d, out = sys.argv[1:4]; W = 2000
def m(L):
    cairosvg.svg2png(url=f'{d}/{L}.svg', write_to=f'{d}/{L}.png', output_width=W, background_color='white')
    return np.array(Image.open(f'{d}/{L}.png').convert('L')) < 128
base = np.array(Image.open(sys.argv[4]).convert('RGB')).astype(float)
edge = m('Edge.Cuts'); ys, xs = np.nonzero(edge); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
bcu = m('B.Cu')[max(0, y0 - 20):y1 + 20, max(0, x0 - 20):x1 + 20]
# B.Cu plot includes the bottom ground pour; keep only thin features (tracks), not the pour
pour = ndimage.binary_opening(bcu, structure=np.ones((25, 25)))
tracks = bcu & ~ndimage.binary_dilation(pour, iterations=2)
h = min(base.shape[0], tracks.shape[0]); w = min(base.shape[1], tracks.shape[1])
img = base[:h, :w]; t = tracks[:h, :w]
img[t] = img[t] * 0.35 + np.array([70, 140, 255]) * 0.65
Image.fromarray(img.astype(np.uint8)).save(out); print('saved', out)
