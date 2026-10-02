"""photographic finish: highlight bloom, gentle vignette, warm split-tone, slight sharpening"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter

def finish(src, dst, bloom=0.12, vig=0.18, warm=0.03, eve=False):
    im = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255
    h, w, _ = im.shape
    # bloom from bright areas
    lum = im.mean(axis=2)
    thr = 0.78 if not eve else 0.62
    hi = np.clip((lum - thr) / (1 - thr), 0, 1)[..., None] * im
    s = max(h, w) / 1600
    bl = sum(gaussian_filter(hi, (r * s, r * s, 0)) * wgt for r, wgt in ((6, 0.5), (24, 0.35), (70, 0.25)))
    im = 1 - (1 - im) * (1 - np.clip(bl * (bloom * (1.6 if eve else 1.0)), 0, 1))
    # warm grade: lift shadows slightly warm, keep highlights neutral
    sh = (1 - lum)[..., None] ** 2
    im = im + sh * np.array([warm, warm * 0.45, -warm * 0.4]) * 0.6
    # gentle global warmth + saturation for day shots (renders read slightly cool)
    if not eve:
        im = im * np.array([1.025, 1.0, 0.955])
        g = im.mean(axis=2, keepdims=True)
        im = g + (im - g) * 1.08
    # vignette
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    im = im * (1 - vig * r[..., None] ** 2.2)
    out = Image.fromarray((np.clip(im, 0, 1) * 255).astype(np.uint8))
    out = out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=35, threshold=2))
    out.save(dst, quality=93) if dst.lower().endswith('.jpg') else out.save(dst)

if __name__ == '__main__':
    finish(sys.argv[1], sys.argv[2], eve=('eve' in sys.argv[1] or 'dusk' in sys.argv[1]))
