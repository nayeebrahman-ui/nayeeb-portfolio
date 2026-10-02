"""Colour-grade the cafe's raw photos for the website.

Recipe (per image): partial grey-world white balance, percentile level stretch,
gentle S-curve, shadow lift, warm split-tone (amber highlights, cocoa shadows),
light saturation boost, unsharp mask, soft vignette. Exported as WebP.
"""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps

SRC = "assets"
OUT = "site/img"
os.makedirs(OUT, exist_ok=True)

# output name -> (source path, max long edge, exposure lift 0..1)
JOBS = {
    # interiors (dark, warm tungsten) - lift more
    "interior-brick": ("raw-photos/image16.jpeg", 1600, 0.28),
    "interior-gallery": ("raw-photos/image17.jpeg", 1600, 0.18),
    "interior-lounge": ("raw-photos/image19.jpeg", 1600, 0.30),
    "interior-window": ("raw-photos/image20.jpeg", 1600, 0.22),
    "interior-checker": ("raw-photos/image21.jpeg", 1600, 0.18),
    "interior-sign": ("raw-photos/image22.jpeg", 1600, 0.20),
    "interior-night": ("raw-photos/image18.jpeg", 1600, 0.32),
    # drinks, bakes, plates
    "cup-in-hand": ("raw-photos/image1.jpeg", 1400, 0.08),
    "latte": ("raw-photos/image2.jpeg", 1200, 0.06),
    "shakes": ("raw-photos/image9.jpeg", 1200, 0.10),
    "cake-iced": ("raw-photos/image10.jpeg", 1200, 0.10),
    "croissant": ("raw-photos/image13.jpeg", 1200, 0.10),
    "breakfast": ("raw-photos/image14.jpeg", 1200, 0.08),
    "schnitzel": ("pdfimg/p-001.jpg", 1000, 0.06),
    "cheese-blast": ("pdfimg/p-002.jpg", 1000, 0.12),
    "huns-kase": ("pdfimg/p-003.jpg", 1000, 0.06),
    "wrap": ("pdfimg/p-007.jpg", 1000, 0.08),
    "supreme": ("pdfimg/p-008.jpg", 1000, 0.08),
    "club": ("pdfimg/p-009.jpg", 1000, 0.06),
    "bruschetta": ("pdfimg/p-013.jpg", 1000, 0.08),
    "tenders": ("pdfimg/p-014.jpg", 1000, 0.08),
    "sauteed": ("pdfimg/p-015.jpg", 1000, 0.08),
    "fries": ("pdfimg/p-020.jpg", 1000, 0.08),
    "fish-chips": ("pdfimg/p-021.jpg", 1000, 0.08),
    "english-breakfast": ("pdfimg/p-027.jpg", 1000, 0.08),
}


def grade(img: Image.Image, lift: float) -> Image.Image:
    img = ImageOps.exif_transpose(img).convert("RGB")
    a = np.asarray(img).astype(np.float32) / 255.0

    # 1. partial grey-world white balance (kills heavy tungsten/green casts, keeps warmth)
    means = a.reshape(-1, 3).mean(0)
    gain = means.mean() / np.maximum(means, 1e-4)
    gain = 1 + (gain - 1) * 0.45
    a = a * gain

    # 2. percentile level stretch on luminance
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    lo, hi = np.percentile(lum, 0.6), np.percentile(lum, 99.9)
    a = (a - lo) / max(hi - lo, 1e-3)
    a = np.clip(a, 0, 1)

    # 3. exposure lift on shadows/mids (gamma), scaled per image
    a = a ** (1.0 / (1.0 + lift))

    # 4. gentle S-curve for contrast
    a = a - 0.035 * np.sin(2 * np.pi * a)  # soft S: deepen shadows, brighten highlights
    a = np.clip(0.5 + (a - 0.5) * 1.04, 0, 1)

    # 5. warm split-tone: amber into highlights, cocoa into shadows
    lum = (a @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    hi_t = np.array([1.035, 1.0, 0.95])
    sh_t = np.array([1.02, 0.99, 0.97])
    a = a * (sh_t + (hi_t - sh_t) * lum)

    # 6. saturation +10%
    lum = (a @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    a = lum + (a - lum) * 1.10

    # highlight roll-off so foam, plates and lamps keep detail
    k = 0.82
    over = np.clip(a - k, 0, None)
    a = np.where(a > k, k + (1 - k) * (1 - np.exp(-over / (1 - k) * 1.6)) / (1 - np.exp(-1.6)), a)
    a = np.clip(a, 0, 1)
    out = Image.fromarray((a * 255).astype(np.uint8))

    # 7. sharpen
    out = out.filter(ImageFilter.UnsharpMask(radius=1.4, percent=60, threshold=2))

    # 8. soft vignette
    w, h = out.size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    v = 1 - 0.18 * np.clip(d - 0.55, 0, 1) ** 1.5
    arr = np.asarray(out).astype(np.float32) * v[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


for name, (src, edge, lift) in JOBS.items():
    im = Image.open(os.path.join(SRC, src))
    im = grade(im, lift)
    im.thumbnail((edge, edge), Image.LANCZOS)
    im.save(os.path.join(OUT, f"{name}.webp"), "WEBP", quality=80, method=6)
    print(name, im.size)

# Berlin cup: already a transparent cut-out; grade colour only, keep alpha
cup = Image.open(os.path.join(SRC, "cup.png")).convert("RGBA")
bbox = cup.getbbox()
cup = cup.crop(bbox)
alpha = cup.getchannel("A")
rgb = grade(cup.convert("RGB"), 0.02)
# undo vignette darkening on the cut-out by re-grading without it is overkill; it is mild
cup = Image.merge("RGBA", (*rgb.split(), alpha))
cup.thumbnail((900, 900), Image.LANCZOS)
cup.save(os.path.join(OUT, "berlin-cup.webp"), "WEBP", quality=88, method=6)
print("berlin-cup", cup.size)

# Logo badge: cut the circle out of its black square
logo = Image.open(os.path.join(SRC, "logo.jpg")).convert("RGB")
w, h = logo.size
g = np.asarray(logo.convert("L"))
ys, xs = np.where(g > 200)  # the white outer ring
cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
r = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2 + 2
yy, xx = np.mgrid[0:h, 0:w]
dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
mask = np.clip((r - dist) * 1.5, 0, 255).astype(np.uint8)  # 1px soft edge
logo_rgba = logo.copy()
logo_rgba.putalpha(Image.fromarray(mask))
logo_rgba = logo_rgba.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))
for size in (480, 160):
    l2 = logo_rgba.copy()
    l2.thumbnail((size, size), Image.LANCZOS)
    l2.save(os.path.join(OUT, f"logo-{size}.webp"), "WEBP", quality=90, method=6)
print("logo done", logo_rgba.size)
