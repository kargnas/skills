"""Images and checks for a work report page (standard library only; needs Chrome or Chromium).

Run with:  uv run --no-project --no-config python report.py <command> ...

  shot      <transcript> <out.png> --title T        command transcript -> terminal-style PNG
  check     <page.html> [--out DIR]                 render at 375, 800, 1280px in light and dark; report problems; write page images
  capture   <page.html> <out.png> [--select CSS]    one PNG of the page, or of the selected elements only
  single    <page.html> <out.html>                  one HTML file with every image inside
  selftest                                          run every command against generated sample pages
"""
import argparse
import base64
import html
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

# Virtual time Chrome gives a page to finish (scripts, images, fonts) before it reads or captures it.
BUDGET_MS = 5000
# Device pixels per CSS pixel in every PNG, so text stays sharp when a chat app scales the image down.
SCALE = 2
# Chrome captures at most 16,384 device pixels in one image: 8,000 CSS px at SCALE 2 leaves a margin.
MAX_CAPTURE_HEIGHT = 8000
# Height of one page image written by check. At SCALE 2 a tile is 2,800px, which an image viewer still shows readable.
TILE = 1400
# Chat apps shrink taller images until the text is hard to read.
MAX_SHARE_HEIGHT = 2200
WIDTHS = (375, 800, 1280)
SCHEME = {"dark": 0, "light": 1}  # Blink's preferredColorScheme values
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif", ".svg": "image/svg+xml"}
# Shapes that are a credential with high confidence, so that normal command output does not trip the check.
SECRETS = [
    ("private key block", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("AWS access key id", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("GitHub token", r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    ("Slack token", r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    ("API key", r"\b(?:sk|pk|rk|phc|phx)[-_][A-Za-z0-9_-]{24,}"),
    ("JSON web token", r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\."),
    ("bearer token", r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{20,}"),
    ("password inside a URL", r"://[^/\s:@]+:[^/\s:@]{6,}@"),
]
# Runs inside the page. __KEEP__ is a CSS selector list or null: everything outside those elements is hidden before measuring.
# With __TEST__, every selectable element is clicked twice after the measurement, and the ones that change nothing are listed.
PROBE = r"""<script>(function(){var errs=[];window.addEventListener('error',function(e){errs.push(String(e.message||e));});
window.addEventListener('load',function(){var d=document.documentElement,sel=__KEEP__,kept=null;
 if(sel){var keep=[].slice.call(document.querySelectorAll(sel));kept=keep.length;
  if(kept)[].forEach.call(document.body.querySelectorAll('*'),function(e){
   if(!keep.some(function(k){return k===e||k.contains(e)||e.contains(k);}))e.style.setProperty('display','none','important');});}
 var imgs=[].slice.call(document.images);imgs.forEach(function(i){i.loading='eager';});
 Promise.all(imgs.map(function(i){return i.complete?0:new Promise(function(r){i.onload=i.onerror=r;});})).then(function(){setTimeout(function(){
  var broken=[],stretched=[],dead=[];
  imgs.forEach(function(i){var n=(i.getAttribute('src')||'').slice(0,80);
   if(!i.naturalWidth){broken.push(n);return;}
   var w=i.clientWidth,h=i.clientHeight,r=i.naturalWidth/i.naturalHeight;
   if(w&&h&&getComputedStyle(i).objectFit==='fill'&&Math.abs(w/h-r)/r>0.02)stretched.push(n+' (shown '+w+'x'+h+', its own shape is '+i.naturalWidth+'x'+i.naturalHeight+')');});
  [].forEach.call(document.querySelectorAll('a[href^="#"]'),function(a){var id=decodeURIComponent(a.getAttribute('href').slice(1));if(id&&!document.getElementById(id))dead.push('#'+id);});
  var cs=getComputedStyle(document.body),win=document.querySelector('.wr-win'),wr=win&&win.getBoundingClientRect(),cut=0;
  [].forEach.call(document.querySelectorAll('svg'),function(g){if(g.getBoundingClientRect().width<200)return;
   for(var e=g.parentElement;e&&e!==document.body;e=e.parentElement){if(getComputedStyle(e).overflowX!=='visible'&&e.scrollWidth-e.clientWidth>4){cut=Math.max(cut,e.scrollWidth-e.clientWidth);break;}}});
  var out={over:d.scrollWidth-d.clientWidth,h:d.scrollHeight,broken:broken,stretched:stretched,dead:dead,kept:kept,
   look:cs.backgroundColor+cs.color,win:wr?[Math.ceil(wr.width),Math.ceil(wr.height)]:null,picks:null,inert:[],cut:cut};
  if(__TEST__){var picks=[].filter.call(document.querySelectorAll('[role="button"],button,summary,[tabindex]'),function(e){
    return e.tabIndex>=0&&!e.closest('a[href]')&&e.getBoundingClientRect().width>0;}),obs=new MutationObserver(function(){});
   obs.observe(d,{subtree:true,childList:true,attributes:true,characterData:true});out.picks=picks.length;
   for(var pass=0;pass<2;pass++)picks.forEach(function(e){obs.takeRecords();e.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
    if(pass&&!obs.takeRecords().length)out.inert.push((e.getAttribute('aria-label')||e.textContent||e.tagName).trim().replace(/\s+/g,' ').slice(0,50));});
   obs.disconnect();}
  out.errors=errs;d.setAttribute('data-wr-probe',JSON.stringify(out));},100);});});})();</script>"""


def die(message):
    sys.exit("report.py: " + message)


def read(path):
    path = pathlib.Path(path).expanduser().resolve()
    if not path.is_file():
        die(f"{path} does not exist.")
    return path, path.read_text(encoding="utf-8")


def find_chrome(explicit):
    names = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
    for cand in [explicit, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium", *(shutil.which(n) for n in names)]:
        if cand and pathlib.Path(cand).is_file():
            return cand
    die("Chrome or Chromium was not found. Install one, or pass --chrome <path to the binary>.")


def chrome(binary, folder, text, theme, *args):
    """Open `text` as a page saved in `folder` (so its relative images load) and return Chrome's standard output."""
    page = folder / f".wr-{os.getpid()}.html"
    page.write_text(text, encoding="utf-8")
    cmd = [binary, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           f"--virtual-time-budget={BUDGET_MS}", f"--blink-settings=preferredColorScheme={SCHEME[theme]}", *args, page.as_uri()]
    try:
        # Chrome's exit status says little: callers confirm the result through the page probe or the written image.
        return subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False).stdout
    except subprocess.TimeoutExpired:
        die("headless Chrome did not answer within 180 seconds. Close stuck Chrome processes and run the command again.")
    finally:
        page.unlink(missing_ok=True)


def inject(text, keep=None, css="", test=False):
    """Add the measuring script (and CSS) to a page. With `keep`, only those elements stay visible. With `test`, selectable elements are clicked."""
    if "<head>" not in text:
        die("the page has no plain <head> tag, so it cannot be measured.")
    probe = PROBE.replace("__KEEP__", json.dumps(keep)).replace("__TEST__", json.dumps(test))
    return text.replace("<head>", f"<head>{probe}<style>{css}</style>", 1)


def probe(binary, folder, text, theme, width):
    # A 100px window makes scrollHeight the height of the content, not of the window.
    dom = chrome(binary, folder, text, theme, f"--window-size={width},100", "--dump-dom")
    m = re.search(r'data-wr-probe="([^"]*)"', dom)
    if not m:
        die("the page did not finish loading in headless Chrome, so it could not be measured. Open it in a browser and read the console.")
    return json.loads(html.unescape(m.group(1)))


def capture(binary, folder, text, theme, width, height, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    chrome(binary, folder, text, theme, f"--force-device-scale-factor={SCALE}", f"--window-size={width},{height}", f"--screenshot={out}")
    if not out.is_file() or out.stat().st_size == 0:
        die(f"Chrome wrote no image for {out}.")


# ---------- shot ----------

def cmd_shot(a):
    src, body = read(a.transcript)
    lines = body.rstrip("\n").split("\n")
    if not a.no_secret_check:
        hits = [f"line {n}: {name}" for n, line in enumerate(lines, 1) for name, rx in SECRETS if re.search(rx, line)]
        if hits:
            die("the transcript may show a credential:\n  " + "\n  ".join(hits[:12]) +
                "\nMask it in a copy of the transcript and render the copy. If it is not a credential, pass --no-secret-check.")
    total = len(lines)
    if total > a.max_lines:
        head = a.max_lines * 2 // 3
        lines = lines[:head] + [f"## … {total - a.max_lines} lines left out here; the full text is in {src.name}"] + lines[total - (a.max_lines - head):]

    def paint(line):
        text = html.escape(line[:a.max_cols]) + ('<span class="cut"> …</span>' if len(line) > a.max_cols else "")
        if line.startswith("$ "):
            return f'<span class="cmd">{text}</span>'
        if line.startswith("## "):
            return f'<span class="sec">{text}</span>'
        if line.startswith("#"):
            return f'<span class="hdr">{text}</span>'
        if re.search(r" deleted|NotFound|REFUSED|ABORT", line):
            return f'<span class="del">{text}</span>'
        return text

    note = a.note or f"Saved at run time: {src.name}, {total} lines"
    css = ("html,body{margin:0;background:#0d1117}.wr-win{display:inline-block;vertical-align:top;min-width:520px;"
           "font:13px/19px Menlo,Consolas,'DejaVu Sans Mono',monospace;color:#c9d1d9;padding:0 0 18px}"
           ".bar{background:#161b22;border-bottom:1px solid #30363d;padding:10px 18px;font:600 13px/20px -apple-system,'Apple SD Gothic Neo','Noto Sans KR',sans-serif;color:#e6edf3}"
           ".bar small{display:block;font-weight:400;color:#8b949e}pre{margin:14px 18px 0;white-space:pre;font:inherit}"
           ".cmd{color:#7ee787;font-weight:700}.sec{color:#e3b341;font-weight:700}.hdr{color:#79c0ff}.del{color:#ff7b72}.cut{color:#6e7681}")
    page = (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div class="wr-win">'
            f'<div class="bar">{html.escape(a.title)}<small>{html.escape(note)}</small></div><pre>'
            + "\n".join(paint(line) for line in lines) + "</pre></div></body></html>")
    binary = find_chrome(a.chrome)
    out = pathlib.Path(a.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    # A 3000px window lets the widest line set the width of the image.
    width, height = probe(binary, out.parent, inject(page), "dark", 3000)["win"]
    capture(binary, out.parent, page, "dark", width, height, out)
    print(f"{out}  {width}x{height} CSS px")
    print(f"Keep these proportions on the page, for example: <img src=\"{out.name}\" width=\"{width}\" height=\"{height}\" alt=\"...\">")
    return width, height


# ---------- check ----------

def analyze(binary, path, text):
    """Probe the page at every width and scheme. Return {problem: [where, ...]}, the 800px dark height, whether the schemes differ, and the elements that change nothing when clicked."""
    found, looks, tall, inert = {}, {}, 0, []
    for theme in SCHEME:
        for width in WIDTHS:
            p = probe(binary, path.parent, inject(text, test=True), theme, width)
            issues = [f"the page scrolls sideways by {p['over']}px"] if p["over"] > 0 else []
            issues += [f"script error: {e}" for e in p["errors"]]
            issues += [f"image does not load: {s}" for s in p["broken"]]
            issues += [f"image is stretched: {s}" for s in p["stretched"]]
            issues += [f"link to an anchor that does not exist: {s}" for s in sorted(set(p["dead"]))]
            # A phone may scroll a graph inside its box. From 800px, the width of the images made for a chat channel, the whole graph must show.
            if p["cut"] and width >= 800:
                issues.append(f"a graph is cut off: {p['cut']}px of it are outside its box. Make it fit at 800px")
            if p["picks"] == 0:
                issues.append("nothing on the page can be selected by click or keyboard (no button, no element with tabindex): the node graphs need selectable nodes")
            inert += [s for s in p["inert"] if s not in inert]
            for issue in issues:
                # A stretched image reports its shown size, which differs per width: group by the part before it.
                found.setdefault(issue.split(" (shown ")[0], []).append(f"{width}px {theme}")
            print(f"{width:>5}px {theme:<5} height {p['h']:>6}px  {len(issues)} problem(s)")
            looks[theme] = p["look"]
            if (theme, width) == ("dark", 800):
                tall = p["h"]
    return found, tall, looks["dark"] != looks["light"], inert


def cmd_check(a):
    path, text = read(a.page)
    binary = find_chrome(a.chrome)
    out = pathlib.Path(a.out).expanduser().resolve() if a.out else path.parent.parent / "check"
    if out.is_dir():
        shutil.rmtree(out)
    found, tall, two_schemes, inert = analyze(binary, path, text)
    print("\nPage images (800px wide, dark, top to bottom). Open and look at every one:")
    for n in range(-(-tall // TILE)):
        top = n * TILE
        shift = f"html{{overflow:hidden!important}}body{{transform:translateY(-{top}px)!important}}"
        capture(binary, path.parent, inject(text, css=shift), "dark", 800, min(TILE, tall - top), out / f"page-{n + 1:02d}.png")
        print(f"  {out / f'page-{n + 1:02d}.png'}")
    if inert:
        print("Note: a click on these changes nothing on the page. Confirm that each one is meant to do nothing:\n  " + "\n  ".join(inert))
    if not two_schemes:
        print("Note: the page looks the same in light and dark. Confirm that this is intended.")
    if found:
        print(f"\n{len(found)} problem(s):")
        for issue, where in found.items():
            print(f"- {issue}  [{', '.join(where)}]")
        sys.exit(1)
    print("No problem found at 375, 800 and 1280px in light and dark.")


# ---------- capture ----------

def cmd_capture(a):
    path, text = read(a.page)
    binary = find_chrome(a.chrome)
    out = pathlib.Path(a.out).expanduser().resolve()
    page = inject(text, keep=a.select)
    p = probe(binary, path.parent, page, a.theme, a.width)
    if a.select and not p["kept"]:
        die(f'--select "{a.select}" matches no element on the page.')
    if p["h"] > MAX_CAPTURE_HEIGHT:
        die(f"the capture would be {p['h']}px tall; one image holds {MAX_CAPTURE_HEIGHT}px. Pick fewer elements with --select.")
    capture(binary, path.parent, page, a.theme, a.width, p["h"], out)
    print(f"{out}  {a.width}x{p['h']} CSS px")
    if p["h"] > MAX_SHARE_HEIGHT:
        print(f"Warning: taller than {MAX_SHARE_HEIGHT}px. A chat app shrinks it until the text is hard to read. Split it into two images.")


# ---------- single ----------

def cmd_single(a):
    path, text = read(a.page)
    count = 0

    def embed(m):
        nonlocal count
        f = path.parent / m.group(1)
        if not f.is_file() or f.suffix.lower() not in MIME:
            die(f"cannot put {m.group(1)} inside the file: it is missing or not an image. Move CSS and scripts into the page itself.")
        count += 1
        return f'src="data:{MIME[f.suffix.lower()]};base64,{base64.b64encode(f.read_bytes()).decode()}"'

    text = re.sub(r'\bsrc="(?!data:|https?:|//)([^"]+)"', embed, text)
    # Only plain paths count: a link that a script builds from parts is not a file reference.
    outside = sorted(set(re.findall(r'\bhref="(?!https?:|mailto:|#|data:)([\w./%-]+)"', text)))
    if outside:
        die("these links point at files next to the page, which the single file does not carry: " + ", ".join(outside) +
            "\nMake each image open larger in place (a toggle) instead of linking to its file, then run single again.")
    out = pathlib.Path(a.out).expanduser().resolve()
    out.write_text(text, encoding="utf-8")
    print(f"{out}  {out.stat().st_size} bytes, {count} images inside")


# ---------- selftest ----------

def cmd_selftest(a):
    transcript = "\n".join([
        "################ Delete the scratch volume", "# started 2026-01-15 02:05:11 UTC on host-1, project demo", "",
        "## BEFORE", "", "$ ls -l /tmp/scratch", "-rw-r--r--  1 demo  demo  0 Jan 15 02:04 volume.img", "OK: owner of /tmp/scratch is demo", "",
        "## ACTION", "", "$ rm -v /tmp/scratch/volume.img", "volume.img deleted", "", "# finished 2026-01-15 02:05:13 UTC", ""])
    good = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            "<style>body{margin:16px;font:14px sans-serif;background:#fff;color:#111}@media (prefers-color-scheme:dark){body{background:#111;color:#eee}}"
            "img{max-width:100%;height:auto}</style></head><body><h1>Sample</h1><section id=\"a\"><a href=\"#b\">to b</a><p>first block</p></section>"
            '<section id="b"><img loading="lazy" src="shots/01.png" width="WIDTH" height="HEIGHT" alt="record"></section>'
            '<button type="button" id="t">select</button><p id="o"></p>'
            "<script>document.getElementById('a').appendChild(document.createElement('p')).textContent='made by a script';"
            "document.getElementById('t').addEventListener('click',function(){document.getElementById('o').textContent+='x';});</script></body></html>")
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "public/shots").mkdir(parents=True)
        (root / "record.txt").write_text(transcript, encoding="utf-8")
        ns = argparse.Namespace
        size = cmd_shot(ns(transcript=str(root / "record.txt"), out=str(root / "public/shots/01.png"), title="Destructive: scratch volume deleted",
                           note=None, max_lines=380, max_cols=190, no_secret_check=False, chrome=a.chrome))
        page = root / "public/index.html"
        page.write_text(good.replace("WIDTH", str(size[0])).replace("HEIGHT", str(size[1])), encoding="utf-8")
        cmd_check(ns(page=str(page), out=None, chrome=a.chrome))
        cmd_capture(ns(page=str(page), out=str(root / "public/share/a.png"), select="#a", theme="dark", width=776, chrome=a.chrome))
        cmd_single(ns(page=str(page), out=str(root / "public/one.html")))
        assert (root / "check/page-01.png").stat().st_size > 0 and (root / "public/share/a.png").stat().st_size > 0
        assert 'src="shots/' not in (root / "public/one.html").read_text(encoding="utf-8"), "the single file kept a file reference"
        # A page with the defects that check exists for: each one must be reported.
        bad = good.replace("WIDTH", str(size[0])).replace("HEIGHT", str(size[1] * 3)).replace("img{max-width:100%;height:auto}", "").replace('href="#b"', 'href="#nowhere"')
        bad = bad.replace("<h1>Sample</h1>", '<h1>Sample</h1><div style="width:2000px">wide</div><img src="shots/missing.png" alt="">'
                          '<div style="overflow-x:auto;width:300px"><svg width="900" height="40"></svg></div>')
        bad = bad.replace('<button type="button" id="t">select</button>', '<span id="t">select</span>')
        bad_page = root / "public/bad.html"
        bad_page.write_text(bad, encoding="utf-8")
        found = " | ".join(analyze(find_chrome(a.chrome), bad_page, bad)[0])
        for want in ("scrolls sideways", "image does not load: shots/missing.png", "image is stretched: shots/01.png", "#nowhere", "nothing on the page can be selected", "a graph is cut off"):
            assert want in found, f"check did not report: {want}\nreported: {found}"
        if a.keep:
            shutil.copytree(root, pathlib.Path(a.keep).expanduser(), dirs_exist_ok=True)
    print("selftest passed")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    def add(name, fn, chrome_flag=True):
        p = sub.add_parser(name)
        p.set_defaults(fn=fn)
        if chrome_flag:
            p.add_argument("--chrome", help="path to a Chrome or Chromium binary (found automatically when omitted)")
        return p

    p = add("shot", cmd_shot)
    p.add_argument("transcript")
    p.add_argument("out", help="PNG to write, for example <report>/public/shots/01-old-vm-delete.png")
    p.add_argument("--title", required=True, help="bar text: what was destroyed and when")
    p.add_argument("--note", help="second bar line (default: the transcript's file name and length)")
    # 380 lines of 19px are about 7,300px, below MAX_CAPTURE_HEIGHT.
    p.add_argument("--max-lines", type=int, default=380)
    # Longer lines are cut so that the image stays readable at its own size.
    p.add_argument("--max-cols", type=int, default=190)
    p.add_argument("--no-secret-check", action="store_true")

    p = add("check", cmd_check)
    p.add_argument("page")
    p.add_argument("--out", help="folder for the page images (default: check/ next to the page's folder)")

    p = add("capture", cmd_capture)
    p.add_argument("page")
    p.add_argument("out", help="PNG to write")
    p.add_argument("--select", help='CSS selector list of the elements to keep, for example "header, #outcome, #before-after"')
    p.add_argument("--theme", choices=tuple(SCHEME), default="dark")
    p.add_argument("--width", type=int, default=800)

    p = add("single", cmd_single, chrome_flag=False)
    p.add_argument("page")
    p.add_argument("out", help="HTML file to write")

    p = add("selftest", cmd_selftest)
    p.add_argument("--keep", help="copy the generated files here")

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
