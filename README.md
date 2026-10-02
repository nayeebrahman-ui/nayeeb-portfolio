# Berlin Café & Bistro website

Website for Berlin Café & Bistro, Mirpur, Dhaka. It has two pages:

- **Home** (`site/index.html`): a hero that plays as you scroll, going from green beans through the roast to the Berlin cup, then the story, signature dishes, menu sections, gallery and a visit card.
- **Menu** (`site/menu.html`): a parchment-style menu with framed dish photos.

## Structure

| Path | What it is |
|---|---|
| `src/` | Page templates, shared CSS, scripts and menu data |
| `build.py` | Assembles `src/` into `site/` |
| `site/` | Built site, ready to host (static files) |
| `site/img/hero/` | 90 rendered hero frames (WebP) |
| `render/scene.py` | Blender (bpy) scene for the hero: beans, roast, cup |
| `render/convert.py` | Converts rendered PNG frames to WebP |
| `grade.py` | Colour grading for the raw cafe photos |
| `shot.py` | Playwright screenshots for desktop and mobile checks |
| `assets/` | Source brand assets, menu PDF and raw photos |

## Build

```sh
python3 build.py
```

The built `site/index.html` has no `<!doctype>`/`<head>` wrapper, because it was written for an artifact host that adds one. To host it anywhere else, wrap it in a standard HTML document first (`site/preview.html` is generated the same way by the build).

## Re-render the hero

```sh
pip install bpy==5.2.2
python3 render/scene.py --res 1280 800 --samples 16   # writes render/frames/desk_NNN.png
python3 render/convert.py                              # -> site/img/hero/fNNN.webp
```
