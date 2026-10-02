"""PNG render frames -> site/img/hero/fNNN.webp (1280x800)."""
import glob, os
from PIL import Image
src = sorted(glob.glob("/home/claude/berlin-cafe/render/frames/desk_*.png"))
out = "/home/claude/berlin-cafe/site/img/hero"
os.makedirs(out, exist_ok=True)
tot = 0
for p in src:
    n = int(os.path.basename(p)[5:8])
    im = Image.open(p).convert("RGB")
    dst = f"{out}/f{n:03d}.webp"
    im.save(dst, "WEBP", quality=74, method=6)
    tot += os.path.getsize(dst)
print(len(src), "frames", round(tot / 1e6, 2), "MB")
