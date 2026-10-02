import asyncio, sys, os, threading, http.server, functools, socketserver
from playwright.async_api import async_playwright

SITE = "/home/claude/berlin-cafe/site"
OUT = "/tmp/claude-0/-home-claude/97a0f72b-3143-5fba-89fb-48e38feffc7b/scratchpad/shots"
V = "/tmp/vendor"
os.makedirs(OUT, exist_ok=True)

FONT_CSS = """
@font-face{font-family:'Gloock';font-weight:400;src:url(https://fonts.gstatic.com/l/gloock.woff2) format('woff2')}
@font-face{font-family:'Hanken Grotesk';font-weight:300 700;src:url(https://fonts.gstatic.com/l/hanken.woff2) format('woff2')}
@font-face{font-family:'Cinzel';font-weight:500;src:url(https://fonts.gstatic.com/l/cinzel500.woff2) format('woff2')}
@font-face{font-family:'Cinzel';font-weight:600;src:url(https://fonts.gstatic.com/l/cinzel600.woff2) format('woff2')}
"""
FONTS = {
    "gloock.woff2": f"{V}/fontsource-gloock-5.3.0/package/files/gloock-latin-400-normal.woff2",
    "hanken.woff2": f"{V}/fontsource-variable-hanken-grotesk-5.3.0/package/files/hanken-grotesk-latin-wght-normal.woff2",
    "cinzel500.woff2": f"{V}/fontsource-cinzel-5.3.0/package/files/cinzel-latin-500-normal.woff2",
    "cinzel600.woff2": f"{V}/fontsource-cinzel-5.3.0/package/files/cinzel-latin-600-normal.woff2",
}

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def serve():
    h = functools.partial(Q, directory=SITE)
    socketserver.TCPServer.allow_reuse_address = True
    s = socketserver.TCPServer(("127.0.0.1", 8765), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

async def route(r):
    u = r.request.url
    if "cdnjs.cloudflare.com" in u:
        f = "gsap.min.js" if u.endswith("gsap.min.js") else "ScrollTrigger.min.js"
        return await r.fulfill(path=f"{V}/gsap-3.12.5/package/dist/{f}", content_type="application/javascript")
    if "fonts.googleapis.com" in u:
        return await r.fulfill(body=FONT_CSS, content_type="text/css")
    if "fonts.gstatic.com/l/" in u:
        return await r.fulfill(path=FONTS[u.rsplit("/", 1)[1]], content_type="font/woff2")
    return await r.continue_()

async def scroll_to(page, y, wait=1600):
    await page.evaluate(f"window.scrollTo(0,{y})")
    await page.wait_for_timeout(wait)

async def main(which):
    srv = serve()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        errs = []
        for name, vw, vh, mobile in (("d", 1440, 900, False), ("m", 390, 844, True)):
            ctx = await b.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile)
            page = await ctx.new_page()
            page.on("console", lambda m: errs.append(f"{name} {m.type}: {m.text}") if m.type in ("error", "warning") else None)
            page.on("pageerror", lambda e: errs.append(f"{name} pageerror: {e}"))
            await page.route("**/*", route)
            if which in ("home", "all"):
                await page.goto("http://127.0.0.1:8765/preview.html", wait_until="networkidle")
                await page.wait_for_timeout(1200)
                hero_h = await page.evaluate("document.getElementById('brew-section').offsetHeight - innerHeight")
                for i, pr in enumerate([0, 0.15, 0.4, 0.63, 0.8, 0.9, 1.0]):
                    await scroll_to(page, int(hero_h * pr))
                    await page.screenshot(path=f"{OUT}/{name}-hero-{i}.png")
                for sel in ("#story", "#signatures", ".chapters", "#gallery", "#visit", ".footer"):
                    y = await page.evaluate(f"document.querySelector('{sel}').getBoundingClientRect().top + scrollY")
                    await scroll_to(page, int(y) + (0 if sel != "#signatures" else 300), 1200)
                    await page.screenshot(path=f"{OUT}/{name}-sec-{sel.strip('#.')}.png")
                ow = await page.evaluate("document.documentElement.scrollWidth > innerWidth")
                if ow: errs.append(f"{name} HOME HORIZONTAL OVERFLOW")
            if which in ("menu", "all"):
                await page.goto("http://127.0.0.1:8765/menu.html", wait_until="networkidle")
                await page.wait_for_timeout(1200)
                await page.screenshot(path=f"{OUT}/{name}-menu-0.png")
                for i, sel in enumerate(("#picks", "#coffee", "#teas", "#bakery", "#appetizers", "#breakfast")):
                    y = await page.evaluate(f"document.querySelector('{sel}').getBoundingClientRect().top + scrollY - 140")
                    await scroll_to(page, int(y), 900)
                    await page.screenshot(path=f"{OUT}/{name}-menu-{i+1}.png")
                ow = await page.evaluate("document.documentElement.scrollWidth > innerWidth")
                if ow: errs.append(f"{name} MENU HORIZONTAL OVERFLOW")
            await ctx.close()
        await b.close()
    srv.shutdown()
    print("\n".join(errs) or "no console errors")

asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
