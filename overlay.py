"""Overlay for OBS (Windows / Linux): a small web page, served only to this computer, that shows the progress on the current
game, the last achievement unlocked in it (at the bottom) and, in its place, a banner at every new achievement. In OBS it
is added as a "Browser" source with the address of the page.

The server listens on 127.0.0.1 only, so nothing is reachable from the network. It never sends the account key: only the
game, the counters and the unlocked achievements."""

import base64
import io
import json
import os
import socketserver
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from config import MEDIA
from skins import active as skin
from symbols import _font_path
from utils import api_time, is_counted

DEFAULT_PORT = 8765

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>RA Companion overlay</title>
<style>
  html, body { margin: 0; background: transparent; overflow: hidden; font-family: "Segoe UI", "DejaVu Sans", sans-serif; }
  .box { box-sizing: border-box; width: 440px; margin: 8px; padding: 12px; display: flex; gap: 12px; align-items: center;
         background: __CARD__; color: __TEXT__; border-radius: 16px; box-shadow: 0 2px 8px rgba(0, 0, 0, .45); }
  .box.hidden { display: none; }
  img { width: 56px; height: 56px; border-radius: 8px; flex: none; }
  .info { flex: 1; min-width: 0; }
  .title { font-weight: 700; font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .line { font-size: 13px; color: __MUTED__; margin-top: 2px; }
  .bar { height: 10px; border-radius: 5px; background: __TRACK__; margin-top: 6px; overflow: hidden; }
  .bar div { height: 100%; width: 0; border-radius: 5px; background: __ACCENT__; transition: width .6s; }
  #banner { border: 2px solid __ACCENT__; animation: enter .5s ease-out; }
  .head { font-size: 13px; font-weight: 700; color: __ACCENT__; }
  .head img { width: 17px; height: 17px; border-radius: 0; margin-right: 5px; vertical-align: -3px; }
  #last .head { color: __MUTED__; }
  #last .line { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .points { font-size: 13px; font-weight: 700; color: __SUCCESS__; margin-top: 2px; }
  @keyframes enter { from { transform: translateX(-110%); } to { transform: translateX(0); } }
</style></head>
<body>
<div id="game" class="box hidden"><img id="icon" alt=""><div class="info">
  <div class="title" id="name"></div><div class="line" id="progress"></div><div class="bar"><div id="fill"></div></div>
</div></div>
<div id="last" class="box hidden"><img id="lbadge" alt=""><div class="info">
  <div class="head" id="lhead"></div><div class="title" id="lwhat"></div><div class="line" id="ldesc"></div><div class="points" id="lpts"></div>
</div></div>
<div id="banner" class="box hidden"><img id="badge" alt=""><div class="info">
  <div class="head"><img id="hicon" alt=""><span id="head"></span></div><div class="title" id="what"></div><div class="line" id="desc"></div><div class="points" id="pts"></div>
</div></div>
<script>
  var BANNER_MS = 8000, run = null, last = 0, queue = [], busy = false, banner = false, latest = null;
  function el(id) { return document.getElementById(id); }
  function text(id, value) { el(id).textContent = value; }
  function picture(id, url) {
    var img = el(id);
    img.style.display = url ? "" : "none";
    if (url && img.getAttribute("src") !== url) img.setAttribute("src", url);
  }
  function paintLast() {                                     // hidden while the banner of a new unlock takes its place
    el("last").classList.toggle("hidden", !latest || banner);
    if (!latest) return;
    picture("lbadge", latest.badge);
    text("lhead", latest.head);
    text("lwhat", latest.title);
    text("ldesc", latest.description);
    text("lpts", latest.points);
  }
  function show(state) {
    var g = state.game;
    el("game").classList.toggle("hidden", !g);
    latest = g ? g.last : null;
    paintLast();
    if (!g) return;
    picture("icon", g.icon);
    text("name", g.title);
    text("progress", g.progress);
    el("fill").style.width = g.percent + "%";
  }
  function next() {
    if (busy || !queue.length) return;
    busy = true;
    var e = queue.shift();
    picture("badge", e.badge);
    picture("hicon", e.icon);
    text("head", e.head);
    text("what", e.title);
    text("desc", e.description);
    text("pts", e.points);
    el("banner").classList.remove("hidden");
    banner = true;
    paintLast();
    setTimeout(function () {
      el("banner").classList.add("hidden");
      banner = false;
      paintLast();
      setTimeout(function () { busy = false; next(); }, 400);
    }, BANNER_MS);
  }
  function poll() {
    fetch("/state", { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (s) {
      if (s.run !== run) { run = s.run; last = s.seq; }        // page just opened: old unlocks are not shown again
      s.events.forEach(function (e) { if (e.seq > last) queue.push(e); });
      last = Math.max(last, s.seq);
      show(s);
      next();
    }).catch(function () {}).then(function () { setTimeout(poll, 2000); });
  }
  poll();
</script>
</body></html>
"""


def page():
    """The HTML page, in the colors of the active skin."""
    html = PAGE
    for mark, color in (("__CARD__", skin.CARD), ("__TEXT__", skin.TEXT), ("__MUTED__", skin.TEXT_MUTED),
                        ("__TRACK__", skin.BAR_TRACK_ALT), ("__ACCENT__", skin.ACCENT), ("__SUCCESS__", skin.SUCCESS)):
        html = html.replace(mark, color)
    return html


def split_icon(head):
    """'(trophy) Achievement unlocked!' -> (trophy, 'Achievement unlocked!'): the symbol is shown as a picture."""
    first, _, rest = str(head).partition(" ")
    if rest and not any(c.isalnum() for c in first):
        return first.replace("\ufe0f", ""), rest
    return "", str(head)


_PICTURES = {}


def symbol_picture(symbol):
    """The symbol drawn like in the app (its symbol font, accent color) as a "data:" address of a PNG picture. A browser
    would otherwise show a colour emoji. Empty (no symbol at all) without Pillow or without the font."""
    if symbol not in _PICTURES:
        try:
            from PIL import Image, ImageDraw, ImageFont
            path = (os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "seguisym.ttf") if os.name == "nt"
                    else _font_path())
            font = ImageFont.truetype(path, 52)
            im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(im)
            left, top, right, bottom = draw.textbbox((0, 0), symbol, font=font)
            draw.text(((64 - left - right) / 2, (64 - top - bottom) / 2), symbol, font=font, fill=skin.ACCENT)
            out = io.BytesIO()
            im.save(out, "PNG")
            _PICTURES[symbol] = "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")
        except Exception:
            _PICTURES[symbol] = ""
    return _PICTURES[symbol]


def _entry(head, title, description, points, hardcore, badge):
    """One achievement, as the page shows it."""
    icon, head = split_icon(head)
    return {"icon": symbol_picture(icon) if icon else "", "head": head, "title": str(title or ""), "description": str(description or ""),
            "points": f"+{points or 0} pts" + (" • HARDCORE" if hardcore else ""),
            "badge": f"{MEDIA}/Badge/{badge}.png" if badge else ""}


def last_unlock(achievements, hc_only=False):
    """The achievement unlocked the most recently (only hardcore unlocks with `hc_only`), or None."""
    def when(a):
        hc = api_time(a.get("DateEarnedHardcore")) or 0
        return hc if hc_only else max(hc, api_time(a.get("DateEarned")) or 0)
    best = max(achievements, key=when, default=None)
    return best if best is not None and when(best) else None


class _Handler(BaseHTTPRequestHandler):
    timeout = 10

    def do_GET(self):
        port = self.server.server_address[1]
        # another web site must not be able to read the page through a domain name that points to 127.0.0.1
        if (self.headers.get("Host") or "").lower() not in (f"127.0.0.1:{port}", f"localhost:{port}"):
            return self.send_error(403)
        path = self.path.split("?")[0]
        if path == "/":
            self._reply(page().encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/state":
            self._reply(json.dumps(self.server.overlay.state()).encode("utf-8"), "application/json")
        else:
            self.send_error(404)

    def _reply(self, body, kind):
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):          # the .exe has no console: nothing must be printed
        pass


class _Server(ThreadingHTTPServer):
    # On Windows "reuse address" would let two programs listen on the same port: the second one must fail instead
    allow_reuse_address = os.name != "nt"

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)      # (the standard method also looks up the computer name: slow)
        self.server_name, self.server_port = self.server_address[:2]

    def handle_error(self, request, client_address):  # OBS closing a connection is not an error to report
        pass


class Overlay:
    """The web server and the data it shows. All methods can be called from the interface thread."""

    def __init__(self):
        self._lock = threading.Lock()
        self._server = None
        self._game = None
        self._events = deque(maxlen=20)
        self._seq = 0
        self._run = str(time.time())

    @property
    def running(self):
        return self._server is not None

    @property
    def port(self):
        return self._server.server_address[1] if self._server else None

    @property
    def url(self):
        return address(self.port or DEFAULT_PORT)

    def start(self, port=DEFAULT_PORT):
        """Start the server (or keep it if it already uses this port). False when the port cannot be used."""
        if self._server and self.port == port:
            return True
        self.stop()
        try:
            server = _Server(("127.0.0.1", port), _Handler)
        except (OSError, OverflowError):
            return False
        server.overlay = self
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self._server = server
        return True

    def stop(self):
        server, self._server = self._server, None
        if server:
            server.shutdown()
            server.server_close()

    def set_game(self, game, hc_only=False, progress="", last_head=""):
        """Current game (answer of API_GetGameInfoAndUserProgress, or None), its progress line and the title line of its
        last unlocked achievement, both already translated."""
        data = None
        if game:
            ach = list((game.get("Achievements") or {}).values())
            done = sum(1 for a in ach if is_counted(a, hc_only))
            icon = game.get("ImageIcon")
            data = {"title": str(game.get("Title") or "?"), "icon": MEDIA + icon if icon else "", "progress": progress,
                    "percent": round(100 * done / len(ach)) if ach else 0, "last": None}
            a = last_unlock(ach, hc_only)
            if a:
                data["last"] = _entry(last_head, a.get("Title"), a.get("Description"), a.get("Points"),
                                      a.get("DateEarnedHardcore"), a.get("BadgeName"))
        with self._lock:
            self._game = data

    def push(self, item, head):
        """Show the banner of a new unlock (an item of utils.Session) with the title line `head`."""
        entry = _entry(head, item.get("title"), item.get("description"), item.get("points"), item.get("hc"), item.get("badge"))
        with self._lock:
            self._seq += 1
            self._events.append(dict(entry, seq=self._seq))

    def state(self):
        with self._lock:
            return {"run": self._run, "seq": self._seq, "game": self._game, "events": list(self._events)}


def address(port):
    return f"http://127.0.0.1:{port}"
