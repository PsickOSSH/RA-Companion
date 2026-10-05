"""Main window of RA Companion."""

import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from tkinter import ttk

from skins import active as skin
import i18n
import skins
from config import API_KEY_URL, GAMES_FILE, GAMES_TTL, HOME, LOGO_URLS, MEDIA, NOTES_FILE, REPO_URL, SITE_URL, load_cfg, read_json, save_cfg, write_json
from i18n import LANGS, REFRESH_LABELS, SORT_ICONS, SORT_IDS, T, UI_LANGS, resolve_ui, sort_label, tr_lang
from ra_api import TRANSLATION_CACHE, call_api, http_get, translate
from utils import date_of, fmt_date, fmt_int, is_any, is_counted, is_hc, is_missable, norm, sort_achievements
from widgets import Bar, Card, RoundBtn, SLabel, SYMF, TRANSPARENT_KEY, Tip, has_sym, is_sym, setup_ttk_styles


class App(tk.Tk):
    """Main window: profile header, game card, achievement list, duel / group views, settings and notifications."""

    def __init__(self):
        """Load the settings, create the window and start the background polling loops."""
        if os.name == "nt":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RACompanion.App")
            except Exception:
                pass
        super().__init__()
        self.cfg = load_cfg()
        i18n.set_language(resolve_ui(self.cfg["ui_lang"]))
        self.notes = read_json(NOTES_FILE, {})
        self.title("RA Companion")
        try:
            base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            self.iconbitmap(default=os.path.join(base, "logo.ico"))
        except Exception:
            pass
        self.configure(bg=skin.BACKGROUND)
        self.geometry("580x760")
        self.minsize(500, 297)
        # Messages from worker threads to the UI thread (Tk widgets must only be touched from the main thread).
        self.q = queue.Queue()
        self.imgs = {}
        self.raw = {}
        # State used to detect new unlocks between two refreshes, and to skip redundant re-renders.
        self.known = None
        self.sig = None
        self.game = None
        self.payload = None
        self.fgame = None
        self.f_known = None
        self.f_key = None
        self.group_data = {}
        self.filter = tk.StringVar(value="all")
        self.view = "ach"
        self.countdown = 0
        self.busy = False
        self.last_game_id = None
        self.desc_labels = []
        self.desc_items = []
        self.duel_items = []
        self.sigs = {"duel": None, "group": None}
        self.search_win = None
        self.gdb = None
        setup_ttk_styles(self)
        self.build()
        self.apply_window()
        self.bind("<F5>", lambda e: self.refresh())
        self.after(150, self.pump)
        self.after(1000, self.tick)
        if self.cfg["key"] and self.cfg["user"]:
            self.refresh()
        else:
            self.after(300, self.settings)

    # ----------------------------------------------------------------------
    # Application lifecycle
    # ----------------------------------------------------------------------
    def restart(self):
        """Relaunch the program (required to apply a new skin)."""
        env = dict(os.environ)
        if getattr(sys, "frozen", False):
            # PyInstaller onefile: the child must unpack its own temp folder instead of reusing ours
            env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
            args = [sys.executable]
        else:
            args = [sys.executable, os.path.abspath(sys.argv[0])]
        subprocess.Popen(args + sys.argv[1:], env=env, close_fds=True)
        self.destroy()

    def rebuild_ui(self):
        """Destroy and rebuild every widget (used after a language change) and re-render the last data."""
        for w in self.winfo_children():
            w.destroy()
        self.sig = None
        self.sigs = {"duel": None, "group": None}
        self.desc_labels = []
        self.desc_items = []
        self.duel_items = []
        self.build()
        self.apply_window()
        if self.payload:
            self.on_data(self.payload)

    # ----------------------------------------------------------------------
    # UI building blocks
    # ----------------------------------------------------------------------
    def lbl(self, parent, text="", size=10, color=skin.TEXT, bold=False, bg=None, sym=False, **kw):
        """Create a label; text containing symbols/emoji automatically becomes an SLabel (mixed fonts)."""
        if sym or has_sym(text):
            return SLabel(parent, text, size, color, bold, bg or parent["bg"], **kw)
        return tk.Label(parent, text=text, bg=bg or parent["bg"], fg=color,
            font=(skin.FONT, size, "bold" if bold else "normal"), **kw)

    def link(self, parent, text, url, size=9, bg=None):
        """Clickable link opening `url` in the browser, underlined on hover."""
        l = self.lbl(parent, text, size, skin.INFO, bg=bg, cursor="hand2")
        l.bind("<Button-1>", lambda e: webbrowser.open(url))
        l.bind("<Enter>", lambda e: l.config(font=(skin.FONT, size, "underline")))
        l.bind("<Leave>", lambda e: l.config(font=(skin.FONT, size)))
        return l

    def logo_link(self, parent, key, url, fallback):
        """Clickable logo (downloaded once, then cached on disk); falls back to a text link until it is available."""
        lab = self.link(parent, fallback, url, 9)
        Tip(lab, lambda: url)
        lab.bind("<Enter>", lambda e: lab.config(bg=skin.CARD_ALT), add="+")
        lab.bind("<Leave>", lambda e: lab.config(bg=skin.BACKGROUND), add="+")
        cache = os.path.join(HOME, ".ra_companion_cache")
        os.makedirs(cache, exist_ok=True)
        f = os.path.join(cache, f"logo_{key}.png")

        def show(data):
            try:
                im = tk.PhotoImage(data=data)
                if im.width() > 36:
                    im = im.subsample(max(1, round(im.width() / 36)))
                elif im.width() < 24:
                    im = im.zoom(max(1, round(32 / im.width())))
            except Exception:
                return
            if lab.winfo_exists():
                lab.config(image=im, text="", padx=6, pady=6)
                lab.image = im

        def job():
            try:
                if os.path.exists(f):
                    with open(f, "rb") as fh:
                        data = fh.read()
                else:
                    data = http_get(LOGO_URLS[key], binary=True)
                    with open(f, "wb") as fh:
                        fh.write(data)
            except Exception:
                return
            self.q.put(("call", lambda: show(data)))
        threading.Thread(target=job, daemon=True).start()
        return lab

    def icon_btn(self, parent, icon, text, cmd):
        """Rounded button with an icon (symbol font) followed by a text."""
        b = RoundBtn(parent, text=text, icon=icon, bg=skin.CARD_ALT, padx=12, pady=5)
        b.bind("<Button-1>", lambda e: cmd())
        return b

    def row_hover(self, row):
        """Lighten a whole card (shape + texts) while the pointer is over it."""
        card = getattr(row, "_card", None)
        hov = {skin.CARD: skin.CARD_ALT, skin.CARD_LOCKED: skin.CARD_LOCKED_HOVER}
        rev = {v: k for k, v in hov.items()}

        def walk(w):
            yield w
            for c in w.winfo_children():
                yield from walk(c)

        def paint(m):
            if card is not None:
                new = m.get(card.fill)
                if new:
                    card.set_fill(new)
            for w in walk(row):
                try:
                    new = m.get(w.cget("bg"))
                    if new:
                        w.config(bg=new)
                except Exception:
                    pass

        def leave(e):
            try:
                x, y = e.widget.winfo_pointerxy()
                p = e.widget.winfo_containing(x, y)
            except Exception:
                p = None
            while p is not None:
                if p is row or p is card:
                    return
                p = getattr(p, "master", None)
            paint(rev)
        for w in list(walk(row)) + ([card, card.cv] if card is not None else []):
            w.bind("<Enter>", lambda e: paint(hov), add="+")
            w.bind("<Leave>", leave, add="+")

    def btn(self, parent, text, cmd, tip=None, bg=skin.CARD_ALT, font=None, **kw):
        """Rounded button. Symbol-only texts automatically use the symbol font; `tip` is an optional tooltip callable."""
        chars = kw.pop("width", None)
        if font is None and text and all((is_sym(c) or c == " " for c in text)):
            font = SYMF
            chars = chars or 3
        b = RoundBtn(parent, text=text, bg=bg, font=font, chars=chars, **kw)
        b.bind("<Button-1>", lambda e: cmd())
        if tip:
            Tip(b, tip)
        return b

    def entry(self, parent, var, **kw):
        """Single-line text entry styled with the skin (gold focus ring)."""
        return tk.Entry(parent, textvariable=var, bg=skin.CARD, fg=skin.TEXT, insertbackground=skin.TEXT, relief="flat",
            font=(skin.FONT, 11), highlightthickness=1, highlightbackground=skin.CARD_ALT, highlightcolor=skin.ACCENT,
            **kw)

    def make_scroll(self, parent, name):
        """Create a scrollable area. Layout updates are debounced and hidden while resizing, which keeps long lists smooth."""
        wrap = tk.Frame(parent, bg=skin.BACKGROUND)
        cv = tk.Canvas(wrap, bg=skin.BACKGROUND, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=cv.yview, style="App.Vertical.TScrollbar")
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(8, 0))
        cv.pack(side="left", fill="both", expand=True)
        sb.update_idletasks()
        self.sbw = sb.winfo_reqwidth() + 8
        inner = tk.Frame(cv, bg=skin.BACKGROUND)
        win = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        # While the window is being resized the list is hidden, then laid out once at the final width
        # (re-laying out hundreds of rounded cards on every pixel makes the window lag).
        job = {"id": None, "w": 0}

        def apply_width():
            job["id"] = None
            cv.itemconfig(win, width=job["w"], state="normal")
            self.rewrap(job["w"])

        def on_cfg(e):
            if e.width == job["w"] and job["id"] is None:
                return
            job["w"] = e.width
            cv.itemconfig(win, state="hidden")
            if job["id"]:
                cv.after_cancel(job["id"])
            job["id"] = cv.after(120, apply_width)
        cv.bind("<Configure>", on_cfg)
        self.cvs[name] = cv
        self.inners[name] = inner
        return wrap

    # ----------------------------------------------------------------------
    # Window layout and view switching
    # ----------------------------------------------------------------------
    def build(self):
        """Build the whole window: header, game card, tabs, the three views and the footer."""
        self.cvs = {}
        self.inners = {}
        self._hcard = Card(self, radius=skin.RADIUS_PANEL, pad=4)
        self._hcard.pack(fill="x", padx=10, pady=(10, 6))
        self.header = self._hcard.body
        self.avatar = tk.Label(self.header, bg=skin.CARD)
        self.avatar.pack(side="left", padx=10, pady=10)
        info = tk.Frame(self.header, bg=skin.CARD)
        info.pack(side="left", fill="x", expand=True)
        name_row = tk.Frame(info, bg=skin.CARD)
        name_row.pack(fill="x")
        self.l_user = self.lbl(name_row, "", 14, bold=True, anchor="w")
        self.l_user.pack(side="left", anchor="s")
        self.l_rank = self.lbl(name_row, "", 8, skin.TEXT_MUTED, anchor="w")
        self.l_rank.pack(side="left", anchor="s", padx=(4, 0), pady=(0, 5))
        stats = tk.Frame(info, bg=skin.CARD)
        stats.pack(fill="x")

        def stat_row(r, icon, color, bold=False, size=10):
            tk.Label(stats, text=icon, bg=skin.CARD, fg=color, font=(skin.SYMBOL_FONT, 10), width=2, anchor="center").grid(row=r,
                column=0, sticky="w")
            tx = tk.Label(stats, text="", bg=skin.CARD, fg=color, font=(skin.FONT, size, "bold" if bold else "normal"),
                anchor="w")
            tx.grid(row=r, column=1, sticky="w")
            return tx
        self.l_hp = stat_row(0, "★", skin.INFO)
        self.l_true = stat_row(1, "✦", skin.TEXT)
        self.l_sp = stat_row(2, "☆", skin.TEXT_MUTED)
        tools = tk.Frame(self.header, bg=skin.CARD)
        tools.pack(side="right", padx=8)
        self.b_pin = self.btn(tools, "📌", self.toggle_top, lambda: T("tip_pin"))
        self.b_pin.grid(row=0, column=0, padx=2)
        self.b_tr = self.btn(tools, "🌐", self.toggle_translate, lambda: T("tip_tr"))
        self.b_tr.grid(row=0, column=1, padx=2)
        self.btn(tools, "⚙", self.settings, lambda: T("tip_settings")).grid(row=0, column=2, padx=2)
        self._gcard = Card(self, radius=skin.RADIUS_PANEL, pad=4)
        self._gcard.pack(fill="x", padx=10, pady=6)
        self.gcard = self._gcard.body
        top = tk.Frame(self.gcard, bg=skin.CARD)
        top.pack(fill="x", padx=10, pady=(10, 4))
        self.gicon = tk.Label(top, bg=skin.CARD)
        self.gicon.pack(side="left")
        self.btn(top, "🔍", self.open_search, lambda: T("tip_search"), font=(skin.SYMBOL_FONT, 13), width=3).pack(side="right",
            anchor="n")
        self.b_hc = self.btn(top, "🔥", self.toggle_hc,
            lambda: T("tip_hc_on") if self.cfg["hc_only"] else T("tip_hc_off"), font=(skin.SYMBOL_FONT, 13), width=3)
        self.b_hc.pack(side="right", anchor="n", padx=(0, 6))
        gi = tk.Frame(top, bg=skin.CARD)
        gi.pack(side="left", fill="x", expand=True, padx=10)
        self.l_game = self.lbl(gi, T("no_game"), 12, bold=True, anchor="w", wraplength=320, justify="left")
        self.l_game.pack(fill="x")
        self.l_console = self.lbl(gi, "", 9, skin.TEXT_MUTED, anchor="w")
        self.l_console.pack(fill="x")
        self.l_rp = self.lbl(gi, "", 9, skin.SUCCESS, sym=True, anchor="w", wraplength=320, justify="left")
        self.l_rp.pack(fill="x")
        self.bar = Bar(self.gcard)
        self.bar.pack(fill="x", padx=10, pady=(4, 2))
        self.l_prog = self.lbl(self.gcard, "", 10, anchor="w")
        self.l_prog.pack(fill="x", padx=10)
        self.l_prog2 = self.lbl(self.gcard, "", 9, skin.TEXT_MUTED, anchor="w")
        self.l_prog2.pack(fill="x", padx=10, pady=(0, 10))
        tabs = tk.Frame(self, bg=skin.BACKGROUND)
        tabs.pack(fill="x", padx=10, pady=(2, 0))
        self.tabs = {}
        for key, name in (("ach", "tab_ach"), ("duel", "tab_duel"), ("group", "tab_group")):
            c = RoundBtn(tabs, text=T(name), font=(skin.FONT, 10, "bold"), padx=14, pady=6,
                radius=skin.RADIUS_BUTTON_LARGE)
            c.pack(side="left", padx=(0, 6))
            c.bind("<Button-1>", lambda e, k=key: self.show_view(k))
            self.tabs[key] = c
        self.footer = tk.Frame(self, bg=skin.BACKGROUND)
        self.footer.pack(side="bottom", fill="x", padx=10, pady=6)
        self.l_status = self.lbl(self.footer, "", 8, skin.TEXT_MUTED, anchor="w")
        self.l_status.pack(side="left")
        rb = self.icon_btn(self.footer, "↻", REFRESH_LABELS.get(i18n.CUR, REFRESH_LABELS["en"]), self.refresh)
        rb.pack(side="right")
        self.auto_var = tk.BooleanVar(value=self.cfg.get("auto_refresh", True))
        self.int_var = tk.StringVar(value=str(self.cfg["interval"]))
        af = tk.Frame(self.footer, bg=skin.BACKGROUND)
        af.pack(side="right", padx=(0, 8))
        tk.Checkbutton(af, text="Auto", variable=self.auto_var, command=self.on_auto, bg=skin.BACKGROUND, fg=skin.TEXT,
            selectcolor=skin.CARD, activebackground=skin.BACKGROUND, activeforeground=skin.TEXT, font=(skin.FONT, 10),
            bd=0, highlightthickness=0, cursor="hand2").pack(side="left")
        sp = tk.Spinbox(af, from_=10, to=3600, increment=5, width=4, textvariable=self.int_var, command=self.on_interval,
            bg=skin.CARD, fg=skin.TEXT, insertbackground=skin.TEXT, buttonbackground=skin.CARD_ALT, relief="flat",
            font=(skin.FONT, 10), justify="center", highlightthickness=0)
        sp.pack(side="left", padx=(4, 2), ipady=3)
        sp.bind("<Return>", self.on_interval)
        sp.bind("<FocusOut>", self.on_interval)
        tk.Label(af, text="s", bg=skin.BACKGROUND, fg=skin.TEXT_MUTED, font=(skin.FONT, 10)).pack(side="left")
        self.content = tk.Frame(self, bg=skin.BACKGROUND)
        self.content.pack(fill="both", expand=True, padx=10, pady=(6, 0))
        self.views = {k: tk.Frame(self.content, bg=skin.BACKGROUND) for k in ("ach", "duel", "group")}
        v = self.views["ach"]
        self.fbar = tk.Frame(v, bg=skin.BACKGROUND)
        self.fbar.pack(fill="x")
        self.chips = {}
        for key, txt in (("all", T("f_all")), ("todo", T("f_todo")), ("done", T("f_done"))):
            c = RoundBtn(self.fbar, text=txt, font=(skin.FONT, 9, "bold"), padx=10, pady=4, radius=skin.RADIUS_BUTTON)
            c.pack(side="left", padx=(0, 6), pady=4)
            c.bind("<Button-1>", lambda e, k=key: self.set_filter(k))
            self.chips[key] = c
        self.miss_chip = RoundBtn(self.fbar, text=T("f_miss"), font=(skin.FONT, 9, "bold"), padx=10, pady=4,
            radius=skin.RADIUS_BUTTON)
        self.miss_chip.pack(side="left", padx=(10, 0), pady=4)
        self.miss_chip.bind("<Button-1>", lambda e: self.toggle_miss())
        self.paint_miss()
        self.b_sort = self.btn(self.fbar, "⇅", self.open_sort_menu, font=(skin.SYMBOL_FONT, 13), width=3)
        self.b_sort.pack(side="right", pady=4)
        self.set_filter(self.filter.get(), rebuild=False)
        self.make_scroll(v, "ach").pack(fill="both", expand=True)
        self.fbar.pack_configure(padx=(0, self.sbw))
        rb.pack_configure(padx=(0, self.sbw))
        v = self.views["duel"]
        bar = tk.Frame(v, bg=skin.BACKGROUND)
        bar.pack(fill="x", pady=(4, 2))
        self.friend_var = tk.StringVar(value=self.cfg["friend"])
        e = self.entry(bar, self.friend_var)
        e.pack(side="left", fill="x", expand=True, ipady=4)
        e.bind("<Return>", lambda ev: self.set_friend())
        self.btn(bar, T("duel_go"), self.set_friend).pack(side="left", padx=4)
        self.btn(bar, T("duel_stop"), self.clear_friend).pack(side="left")
        self.l_duel = self.lbl(v, "", 10, skin.ACCENT, bold=True, sym=True, anchor="w")
        self.l_duel.pack(fill="x", pady=(6, 0))
        self.l_duel2 = self.lbl(v, "", 9, skin.TEXT_MUTED, anchor="w", wraplength=440, justify="left")
        self.l_duel2.pack(fill="x", pady=(0, 4))
        self.make_scroll(v, "duel").pack(fill="both", expand=True)
        v = self.views["group"]
        bar = tk.Frame(v, bg=skin.BACKGROUND)
        bar.pack(fill="x", pady=(4, 2))
        self.member_var = tk.StringVar()
        e = self.entry(bar, self.member_var)
        e.pack(side="left", fill="x", expand=True, ipady=4)
        e.bind("<Return>", lambda ev: self.add_member())
        self.btn(bar, T("g_add"), self.add_member).pack(side="left", padx=4)
        self.make_scroll(v, "group").pack(fill="both", expand=True)
        self.bind_all("<MouseWheel>", self.wheel)
        self.show_view(self.view, fetch=False)

    def show_view(self, v, fetch=True):
        """Switch between the 'ach' (achievements), 'duel' and 'group' views."""
        self.view = v
        for f in self.views.values():
            f.pack_forget()
        self.views[v].pack(fill="both", expand=True)
        for k, c in self.tabs.items():
            c.config(bg=skin.ACCENT if k == v else skin.CARD_ALT, fg=skin.TEXT_ON_ACCENT if k == v else skin.TEXT)
        if self.payload:
            self.render_views(force=True)
        if v == "group" and fetch and self.cfg["group"]:
            self.refresh()

    def wheel(self, e):
        """Mouse-wheel scrolling for the visible list (text boxes scroll themselves)."""
        n = int(-e.delta / 120) * 2
        try:
            if isinstance(e.widget, (tk.Text, tk.Listbox)):
                e.widget.yview_scroll(n, "units")
            elif e.widget.winfo_toplevel() is self:
                self.cvs[self.view].yview_scroll(n, "units")
        except Exception:
            pass

    def rewrap(self, w):
        """Update the wrap length of the description labels after a width change."""
        for r in self.desc_labels + [l for l, _ in self.duel_items]:
            try:
                r.config(wraplength=max(120, w - 165))
            except Exception:
                pass

    # ----------------------------------------------------------------------
    # Filters, toggles and window options
    # ----------------------------------------------------------------------
    def paint_miss(self):
        """Color the 'Missable' toggle according to its state."""
        on = bool(self.cfg.get("miss_only", False))
        self.miss_chip.config(bg=skin.WARNING if on else skin.CARD_ALT, fg=skin.TEXT_ON_ACCENT if on else skin.WARNING)

    def toggle_miss(self):
        """Toggle the 'Missable only' filter (combinable with the All / Locked / Unlocked filters)."""
        self.cfg["miss_only"] = not self.cfg.get("miss_only", False)
        save_cfg(self.cfg)
        self.paint_miss()
        self.render_list(force=True)

    def set_filter(self, k, rebuild=True):
        """Select the All / Locked / Unlocked filter chip and refresh the list."""
        self.filter.set(k)
        for key, c in self.chips.items():
            c.config(bg=skin.ACCENT if key == k else skin.CARD_ALT, fg=skin.TEXT_ON_ACCENT if key == k else skin.TEXT)
        if rebuild:
            self.render_list(force=True)

    def apply_window(self):
        """Apply window options (always-on-top, opacity) and the on/off look of the toggle buttons."""
        self.attributes("-topmost", bool(self.cfg["ontop"]))
        self.attributes("-alpha", max(0.3, self.cfg["alpha"] / 100))
        for b, on in ((self.b_pin, self.cfg["ontop"]), (self.b_tr, self.cfg["translate"]),
            (self.b_hc, self.cfg["hc_only"])):
            b.config(bg=skin.ACCENT if on else skin.CARD_ALT, fg=skin.TEXT_ON_ACCENT if on else skin.TEXT)

    def toggle_top(self):
        """Toggle 'always on top'."""
        self.cfg["ontop"] = not self.cfg["ontop"]
        save_cfg(self.cfg)
        self.apply_window()

    def toggle_hc(self):
        """Toggle 'hardcore only' counting and re-render."""
        self.cfg["hc_only"] = not self.cfg["hc_only"]
        save_cfg(self.cfg)
        self.apply_window()
        self.sig = None
        self.sigs = {"duel": None, "group": None}
        if self.payload:
            self.on_data(self.payload)

    def toggle_translate(self):
        """Toggle the automatic translation of descriptions and comments."""
        self.cfg["translate"] = not self.cfg["translate"]
        save_cfg(self.cfg)
        self.apply_window()
        if self.cfg["translate"]:
            self.translate_labels()
        else:
            for lab, orig in self.desc_items + self.duel_items:
                if lab.winfo_exists():
                    lab.config(text=orig)

    def translate_labels(self):
        """Translate every visible description in background threads and update the labels when done."""
        items = list(self.desc_items) + list(self.duel_items)
        lang = tr_lang(self.cfg)

        def one(it):
            lab, orig = it
            try:
                t = translate(orig, lang)
            except Exception:
                return
            self.q.put(("call", lambda: lab.winfo_exists() and self.cfg["translate"] and lab.config(text=t)))

        def job():
            with ThreadPoolExecutor(6) as ex:
                list(ex.map(one, items))
        threading.Thread(target=job, daemon=True).start()

    # ----------------------------------------------------------------------
    # Settings window, duel and group configuration
    # ----------------------------------------------------------------------
    def settings(self):
        """Open the settings window (language, skin, account, API key, opacity, translation)."""
        w = tk.Toplevel(self)
        w.title(T("s_title"))
        w.configure(bg=skin.BACKGROUND)
        w.transient(self)
        w.grab_set()
        w.geometry("430x500")

        def row(text, hint=""):
            self.lbl(w, text, 10, bold=True, anchor="w").pack(fill="x", padx=18, pady=(10, 0))
            if hint:
                self.lbl(w, hint, 8, skin.TEXT_MUTED, anchor="w").pack(fill="x", padx=18)

        sys_label = T("s_uisys")
        row(T("s_uilang"))
        ui = tk.StringVar(value=next((n for n, c in UI_LANGS.items() if c == self.cfg["ui_lang"]), sys_label))
        ttk.Combobox(w, textvariable=ui, values=[sys_label] + list(UI_LANGS), state="readonly").pack(fill="x", padx=18)
        row(T("s_skin"))
        skin_names = skins.available()
        sk = tk.StringVar(value=next((n for n, m in skin_names.items() if m == self.cfg.get("skin", "default")),
                skin.NAME))
        ttk.Combobox(w, textvariable=sk, values=list(skin_names), state="readonly").pack(fill="x", padx=18)
        row(T("s_user"))
        u = tk.StringVar(value=self.cfg["user"])
        self.entry(w, u).pack(fill="x", padx=18, ipady=5)
        row(T("s_key"))
        self.link(w, API_KEY_URL, API_KEY_URL, 8).pack(anchor="w", padx=18)
        k = tk.StringVar(value=self.cfg["key"])
        self.entry(w, k, show="•").pack(fill="x", padx=18, ipady=5)
        row(T("s_opacity"))
        al = tk.IntVar(value=self.cfg["alpha"])
        tk.Scale(w, from_=30, to=100, orient="horizontal", variable=al, bg=skin.BACKGROUND, fg=skin.TEXT,
            highlightthickness=0, troughcolor=skin.CARD).pack(fill="x", padx=18)
        row(T("s_trlang"))
        lg = tk.StringVar(value=next((n for n, c in LANGS.items() if c == self.cfg["lang"]), sys_label))
        ttk.Combobox(w, textvariable=lg, values=[sys_label] + list(LANGS), state="readonly").pack(fill="x", padx=18)

        def ok():
            old = i18n.CUR
            new_skin = skin_names.get(sk.get(), "default")
            skin_changed = new_skin != self.cfg.get("skin", "default")
            self.cfg.update(user=u.get().strip(), key=k.get().strip(), alpha=al.get(), skin=new_skin,
                lang=LANGS.get(lg.get(), "auto"), ui_lang=UI_LANGS.get(ui.get(), "auto"))
            save_cfg(self.cfg)
            i18n.set_language(resolve_ui(self.cfg["ui_lang"]))
            if skin_changed:
                w.destroy()
                self.restart()
                return
            self.known = None
            self.f_known = None
            self.sig = None
            w.destroy()
            if i18n.CUR != old:
                self.rebuild_ui()
            else:
                self.apply_window()
            self.refresh()
        b = RoundBtn(w, text=T("save"), bg=skin.ACCENT, fg=skin.TEXT_ON_ACCENT, font=(skin.FONT, 11, "bold"), pady=9,
            radius=skin.RADIUS_BUTTON_LARGE)
        b.pack(fill="x", padx=18, pady=(14, 8))
        b.bind("<Button-1>", lambda e: ok())
        links = tk.Frame(w, bg=skin.BACKGROUND)
        links.pack(pady=(0, 12))
        self.logo_link(links, "github", REPO_URL, "GitHub").pack(side="left", padx=10)
        self.logo_link(links, "ra", SITE_URL, "retroachievements.org").pack(side="left", padx=10)

    def set_friend(self):
        """Start comparing with the friend typed in the Duel tab."""
        name = self.friend_var.get().strip()
        if not name:
            return
        self.cfg["friend"] = name
        save_cfg(self.cfg)
        self.f_known = None
        self.fgame = None
        self.sigs["duel"] = None
        self.render_duel(force=True)
        self.refresh()

    def clear_friend(self):
        """Stop the duel."""
        self.cfg["friend"] = ""
        save_cfg(self.cfg)
        self.friend_var.set("")
        self.fgame = None
        self.f_known = None
        self.sigs["duel"] = None
        self.render_duel(force=True)

    def add_member(self):
        """Add a player to the group dashboard."""
        name = self.member_var.get().strip()
        low = [m.lower() for m in self.cfg["group"]] + [self.cfg["user"].lower()]
        if name and name.lower() not in low:
            self.cfg["group"].append(name)
            save_cfg(self.cfg)
        self.member_var.set("")
        self.sigs["group"] = None
        self.render_group(force=True)
        self.refresh()

    def remove_member(self, name):
        """Remove a player from the group dashboard."""
        self.cfg["group"] = [m for m in self.cfg["group"] if m != name]
        save_cfg(self.cfg)
        self.sigs["group"] = None
        self.render_group(force=True)

    # ----------------------------------------------------------------------
    # Networking: background thread -> UI queue
    # ----------------------------------------------------------------------
    def refresh(self):
        """Start a background update (ignored if one is already running or no account is configured)."""
        if self.busy or not (self.cfg["key"] and self.cfg["user"]):
            return
        self.busy = True
        self.l_status.config(text=T("updating"), fg=skin.TEXT_MUTED)
        threading.Thread(target=self.worker, daemon=True).start()

    def img(self, path):
        """Download an image from the RetroAchievements media server (cached in memory)."""
        if path not in self.raw:
            try:
                self.raw[path] = http_get(MEDIA + path, binary=True)
            except Exception:
                self.raw[path] = None
        return self.raw[path]

    def worker(self):
        """Background thread: fetch the profile, the current game, the friend's progress and the group data, then post the result to the UI queue."""
        try:
            key, user, view = (self.cfg["key"], self.cfg["user"], self.view)
            friend = self.cfg["friend"]
            members = list(self.cfg["group"])
            s = call_api("API_GetUserSummary.php", key, u=user, g=1, a=0)
            gid = self.cfg["game_id"] if not self.cfg["auto"] and self.cfg["game_id"] else s.get("LastGameID") or (s.get("LastGame") or {}).get("ID")
            game = fgame = group = None
            if gid:
                game = call_api("API_GetGameInfoAndUserProgress.php", key, u=user, g=gid)
                self.img(game.get("ImageIcon", ""))
                paths = []
                for a in (game.get("Achievements") or {}).values():
                    paths += [f"/Badge/{a['BadgeName']}.png", f"/Badge/{a['BadgeName']}_lock.png"]
                with ThreadPoolExecutor(8) as ex:
                    list(ex.map(self.img, paths))
                if friend:
                    try:
                        fgame = call_api("API_GetGameInfoAndUserProgress.php", key, u=friend, g=gid)
                    except Exception as ex:
                        fgame = {"error": str(ex)}
            if view == "group":

                def one(name):
                    try:
                        ss = call_api("API_GetUserSummary.php", key, u=name, g=1, a=0)
                        gg = call_api("API_GetGameInfoAndUserProgress.php", key, u=name, g=gid) if gid else None
                        pic = ss.get("UserPic") or f"/UserPic/{name}.png"
                        self.img(pic)
                        return (name.lower(), {"user": name, "s": ss, "game": gg, "pic": pic})
                    except Exception as ex:
                        return (name.lower(), {"user": name, "error": str(ex)})
                with ThreadPoolExecutor(4) as ex:
                    group = dict(ex.map(one, members))
            pic = s.get("UserPic") or f"/UserPic/{user}.png"
            self.img(pic)
            self.q.put(("ok", {"s": s, "game": game, "pic": pic, "friend": fgame, "group": group}))
        except Exception as e:
            self.q.put(("err", str(e)))

    def pump(self):
        """Run on the UI thread every 150 ms: process messages posted by the worker threads."""
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == "call":
                    try:
                        m[1]()
                    except Exception:
                        pass
                    continue
                self.busy = False
                if m[0] == "err":
                    self.l_status.config(text=T("error", e=m[1]), fg=skin.DANGER)
                else:
                    self.on_data(m[1], fresh=True)
        except queue.Empty:
            pass
        self.after(150, self.pump)

    def tick(self):
        """Run every second: trigger an automatic refresh when the countdown reaches zero."""
        if self.cfg.get("auto_refresh", True):
            self.countdown -= 1
            if self.countdown <= 0 and (not self.busy):
                self.countdown = int(self.cfg["interval"])
                self.refresh()
        self.after(1000, self.tick)

    def on_auto(self):
        """Enable / disable the automatic refresh."""
        self.cfg["auto_refresh"] = bool(self.auto_var.get())
        save_cfg(self.cfg)
        self.countdown = int(self.cfg["interval"])

    def on_interval(self, _=None):
        """Validate and store the refresh interval typed in the footer (10 to 3600 seconds)."""
        try:
            n = int(float(self.int_var.get()))
        except Exception:
            n = int(self.cfg["interval"])
        n = max(10, min(3600, n))
        self.int_var.set(str(n))
        self.cfg["interval"] = n
        save_cfg(self.cfg)
        self.countdown = n

    # ----------------------------------------------------------------------
    # Images
    # ----------------------------------------------------------------------
    def photo(self, path, size=None):
        """Return a Tk image for a downloaded picture, scaled down to about `size` pixels."""
        b = self.raw.get(path)
        if not b:
            return None
        key = (path, size)
        if key not in self.imgs:
            try:
                im = tk.PhotoImage(data=b)
                if size and im.width() > size:
                    im = im.subsample(max(1, round(im.width() / size)))
                self.imgs[key] = im
            except Exception:
                try:
                    from PIL import Image, ImageTk
                    import io
                    pi = Image.open(io.BytesIO(b)).convert("RGBA")
                    if size:
                        pi = pi.resize((size, size))
                    self.imgs[key] = ImageTk.PhotoImage(pi)
                except Exception:
                    self.imgs[key] = None
        return self.imgs[key]

    def badge(self, parent, a, shown, size, bg):
        """Label showing an achievement badge (colored when unlocked, grey lock version otherwise)."""
        im = self.photo(f"/Badge/{a['BadgeName']}{('' if shown else '_lock')}.png", size)
        l = tk.Label(parent, bg=bg, image=im if im else "")
        l.image = im
        return l

    # ----------------------------------------------------------------------
    # Rendering (header, game card, achievement list, duel, group)
    # ----------------------------------------------------------------------
    def on_data(self, p, fresh=False):
        """Update the header and the game card with fresh data, send unlock notifications and re-render the active view."""
        self.payload = p
        s, game, pic = (p["s"], p["game"], p["pic"])
        hc_only = self.cfg["hc_only"]
        if fresh:
            self.countdown = int(self.cfg["interval"])
            self.l_status.config(text=T("last_update",
                    t=datetime.now().strftime("%I:%M:%S %p" if i18n.CUR == "en" else "%H:%M:%S")), fg=skin.TEXT_MUTED)
            if p.get("group") is not None:
                self.group_data = p["group"]
            self.fgame = p.get("friend") if self.cfg["friend"] else None
        self.l_user.config(text=s.get("User", self.cfg["user"]))
        hcp = s.get("TotalPoints", 0)
        scp = s.get("TotalSoftcorePoints", 0)
        tpts = s.get("TotalTruePoints", 0)
        self.l_hp.config(text=f"{fmt_int(hcp)} HardcorePoints")
        self.l_sp.config(text=f"{fmt_int(scp)} SoftcorePoints")
        self.l_true.config(text=f"{fmt_int(tpts)} RetroPoints")
        rank = s.get("Rank")
        total = s.get("TotalRanked")
        rtxt = ""
        if rank:
            rtxt = f"#{fmt_int(rank)}"
            try:
                pct = f"{100 * int(rank) / int(total):.1f}"
                if i18n.CUR in ("fr", "es", "de", "it", "pt"):
                    pct = pct.replace(".", ",")
                rtxt += f" ({pct} %)"
            except Exception:
                pass
        self.l_rank.config(text=rtxt)
        im = self.photo(pic, 56)
        if im:
            self.avatar.config(image=im)
            self.avatar.image = im
        rp = s.get("RichPresenceMsg") or ""
        self.l_rp.config(text="▶ " + rp if rp else "")
        if not game:
            self.game = None
            self.l_game.config(text=T("no_game"))
            self.render_views()
            return
        self.game = game
        self.l_game.config(text=game.get("Title", "?"))
        self.l_console.config(text=game.get("ConsoleName", ""))
        gi = self.photo(game.get("ImageIcon", ""), 56)
        if gi:
            self.gicon.config(image=gi)
            self.gicon.image = gi
        ach = list((game.get("Achievements") or {}).values())
        counted = [a for a in ach if is_counted(a, hc_only)]
        n_hc = sum((1 for a in ach if is_hc(a)))
        n_sc = sum((1 for a in ach if is_any(a) and (not is_hc(a))))
        tot_pts = sum((int(a.get("Points", 0)) for a in ach))
        got_pts = sum((int(a.get("Points", 0)) for a in counted))
        self.bar.set(len(counted) / len(ach) if ach else 0)
        self.l_prog.config(text=T("progress", d=len(counted), t=len(ach), gp=got_pts, tp=tot_pts,
                p=round(100 * len(counted) / len(ach)) if ach else 0))
        self.l_prog2.config(text=T("hcsc", h=n_hc, s=n_sc))
        gid = game.get("ID")
        if fresh:
            ids = {a["ID"] for a in ach if is_any(a)}
            if self.known is not None and gid == self.last_game_id:
                for a in ach:
                    if is_any(a) and a["ID"] not in self.known:
                        self.toast(a)
            self.known = ids
            self.last_game_id = gid
            fg = self.fgame
            if fg and (not fg.get("error")):
                fach = list((fg.get("Achievements") or {}).values())
                fids = {a["ID"] for a in fach if is_any(a)}
                fkey = (gid, self.cfg["friend"].lower())
                if self.f_known is not None and self.f_key == fkey:
                    for a in fach:
                        if is_any(a) and a["ID"] not in self.f_known:
                            self.toast(a, who=self.cfg["friend"])
                self.f_known = fids
                self.f_key = fkey
            else:
                self.f_known = None
        self.render_views()
        if fresh and self.view == "group" and (p.get("group") is None) and self.cfg["group"]:
            self.refresh()

    def render_views(self, force=False):
        """Render the currently visible view."""
        if self.view == "ach":
            self.render_list(force)
        elif self.view == "duel":
            self.render_duel(force)
        else:
            self.render_group(force)

    def note_of(self, a):
        """Return the personal note stored for an achievement (empty string if none)."""
        return (self.notes.get(str(a["ID"])) or "").strip()

    def bind_click(self, w, fn):
        """Bind a click handler on a widget, all its descendants and its rounded card background."""
        w.bind("<Button-1>", lambda e: fn())
        for c in w.winfo_children():
            self.bind_click(c, fn)
        card = getattr(w, "_card", None)
        if card is not None:
            for x in (card, card.cv):
                x.bind("<Button-1>", lambda e: fn())
            card.config(cursor="hand2")

    def open_sort_menu(self):
        """Pop up the sort menu below the sort button."""
        m = tk.Menu(self, tearoff=0, bg=skin.CARD, fg=skin.TEXT, activebackground=skin.ACCENT,
            activeforeground=skin.TEXT_ON_ACCENT, font=(skin.FONT, 10), bd=0)
        m.add_command(label=sort_label(), state="disabled")
        m.add_separator()
        cur = self.cfg.get("sort", "disp_asc")
        self._sortvars = []
        for sid in SORT_IDS:
            v = tk.BooleanVar(value=sid == cur)
            self._sortvars.append(v)
            m.add_checkbutton(label=f"{SORT_ICONS[sid]}   {sort_label(sid)}", variable=v, onvalue=True, offvalue=False,
                command=lambda s=sid: self.set_sort(s))
        b = self.b_sort
        try:
            m.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())
        finally:
            m.grab_release()

    def set_sort(self, sid):
        """Store the chosen sort mode and re-render the list."""
        self.cfg["sort"] = sid
        save_cfg(self.cfg)
        self.render_list(force=True)

    def render_list(self, force=False):
        """Render the achievement list (filters, sort order, notes, missable markers). Skipped when nothing changed."""
        if not self.game:
            return
        inner = self.inners["ach"]
        hc_only = self.cfg["hc_only"]
        ach = list((self.game.get("Achievements") or {}).values())
        f = self.filter.get()
        E = lambda a: is_counted(a, hc_only)
        if f == "todo":
            ach = [a for a in ach if not E(a)]
        elif f == "done":
            ach = [a for a in ach if E(a)]
        if self.cfg.get("miss_only"):
            ach = [a for a in ach if is_missable(a)]
        ach = sort_achievements(ach, self.cfg.get("sort", "disp_asc"), hc_only)
        sig = (self.game.get("ID"), f, i18n.CUR, hc_only, bool(self.cfg.get("miss_only")),
            tuple(((a["ID"], E(a), is_any(a), bool(self.note_of(a)), is_missable(a)) for a in ach)))
        if sig == self.sig and (not force):
            return
        self.sig = sig
        for w in inner.winfo_children():
            w.destroy()
        self.desc_labels = []
        self.desc_items = []
        if not ach:
            self.lbl(inner, T("nothing"), 11, skin.TEXT_MUTED).pack(pady=30)
        players = int(self.game.get("NumDistinctPlayers") or self.game.get("NumDistinctPlayersCasual") or 0)
        lang = tr_lang(self.cfg)
        for a in ach:
            e = E(a)
            card = Card(inner, fill=skin.CARD if e else skin.CARD_LOCKED, radius=skin.RADIUS_CARD, pad=4)
            card.pack(fill="x", pady=3)
            row = card.body
            self.badge(row, a, e, 52, row["bg"]).pack(side="left", padx=8, pady=8)
            mid = tk.Frame(row, bg=row["bg"])
            mid.pack(side="left", fill="x", expand=True)
            trow = tk.Frame(mid, bg=row["bg"])
            trow.pack(fill="x")
            self.lbl(trow, a.get("Title", ""), 10, skin.TEXT if e else skin.TEXT_MUTED, bold=True, bg=row["bg"],
                anchor="w").pack(side="left")
            if self.note_of(a):
                self.lbl(trow, "📝", 9, skin.TEXT_MUTED, bg=row["bg"]).pack(side="left", padx=(6, 0))
            if is_missable(a):
                self.lbl(trow, "⚠ " + T("f_miss"), 8, skin.WARNING, bold=True, bg=row["bg"]).pack(side="left",
                    padx=(8, 0))
            orig = a.get("Description", "")
            shown = TRANSLATION_CACHE.get((lang, orig), orig) if self.cfg["translate"] else orig
            d = self.lbl(mid, shown, 9, skin.TEXT_MUTED, bg=row["bg"], anchor="w", justify="left", wraplength=280)
            d.pack(fill="x")
            self.desc_labels.append(d)
            self.desc_items.append((d, orig))
            if e:
                tag = T("earned_hc") if is_hc(a) else T("earned_sc")
                self.lbl(mid, f"✔ {fmt_date(date_of(a))} • {tag}", 8, skin.INFO if is_hc(a) else skin.SUCCESS,
                    bg=row["bg"], anchor="w").pack(fill="x")
            elif is_any(a):
                self.lbl(mid, f"🔒 {T('sc_only')}", 8, skin.TEXT_MUTED, bg=row["bg"], anchor="w").pack(fill="x")
            else:
                pct = ""
                if players and a.get("NumAwarded"):
                    pct = T("owned_by", p=round(100 * int(a["NumAwarded"]) / players))
                self.lbl(mid, f"🔒{pct}", 8, skin.TEXT_MUTED, bg=row["bg"], anchor="w").pack(fill="x")
            self.lbl(row, str(a.get("Points", 0)), 13, skin.ACCENT if e else skin.TEXT_MUTED, bold=True, bg=row["bg"]).pack(side="right",
                padx=12)
            row.config(cursor="hand2")
            self.bind_click(row, lambda a=a: self.open_detail(a))
            self.row_hover(row)
        self.rewrap(self.cvs["ach"].winfo_width())
        if self.cfg["translate"]:
            self.translate_labels()

    def render_duel(self, force=False):
        """Render the duel view: who unlocked what, who is ahead, with dates and modes."""
        inner = self.inners["duel"]
        fr = self.cfg["friend"]
        fg = self.fgame
        me = self.game
        hc_only = self.cfg["hc_only"]
        user = self.cfg["user"]
        msg = None
        if not fr:
            msg = T("duel_empty")
        elif not me:
            msg = T("no_game")
        elif fg is None:
            msg = T("loading")
        elif fg.get("error"):
            msg = T("error", e=fg["error"])
        if msg:
            sig = ("msg", msg, i18n.CUR)
            if sig == self.sigs["duel"] and (not force):
                return
            self.sigs["duel"] = sig
            for w in inner.winfo_children():
                w.destroy()
            self.duel_items = []
            self.l_duel.config(text="")
            self.l_duel2.config(text="")
            self.lbl(inner, msg, 10, skin.TEXT_MUTED, wraplength=400, justify="left").pack(pady=20, padx=6, anchor="w")
            return
        mine = list((me.get("Achievements") or {}).values())
        theirs = {str(a["ID"]): a for a in (fg.get("Achievements") or {}).values()}
        data = []
        for a in mine:
            b = theirs.get(str(a["ID"]))
            data.append((a, b, is_counted(a, hc_only), bool(b) and is_counted(b, hc_only)))
        sig = (fr, me.get("ID"), i18n.CUR, hc_only, self.cfg["translate"],
            tuple(((a["ID"], x, y) for a, b, x, y in data)))
        if sig == self.sigs["duel"] and (not force):
            return
        self.sigs["duel"] = sig
        x = sum((1 for d in data if d[2]))
        y = sum((1 for d in data if d[3]))
        tot = len(data)
        pa = sum((int(d[0].get("Points", 0)) for d in data if d[2]))
        pb = sum((int(d[0].get("Points", 0)) for d in data if d[3]))
        if x > y:
            lead = T("duel_lead", n=user, d=x - y)
        elif y > x:
            lead = T("duel_lead", n=fr, d=y - x)
        else:
            lead = T("duel_tie", d=x)
        self.l_duel.config(text=lead)
        self.l_duel2.config(text=f"{user}: {x}/{tot} • {pa} pts     |     {fr}: {y}/{tot} • {pb} pts")
        for w in inner.winfo_children():
            w.destroy()
        self.duel_items = []

        def order(d):
            a, b, me_e, fr_e = d
            grp = 0 if fr_e and (not me_e) else 1 if me_e and (not fr_e) else 2 if not (me_e or fr_e) else 3
            return (grp, int(a.get("DisplayOrder", 0)))
        lang = tr_lang(self.cfg)
        for a, b, me_e, fr_e in sorted(data, key=order):
            any_e = me_e or fr_e
            card = Card(inner, fill=skin.CARD if any_e else skin.CARD_LOCKED, radius=skin.RADIUS_CARD, pad=4)
            card.pack(fill="x", pady=3)
            row = card.body
            self.badge(row, a, any_e, 48, row["bg"]).pack(side="left", padx=8, pady=8)
            mid = tk.Frame(row, bg=row["bg"])
            mid.pack(side="left", fill="x", expand=True)
            trow = tk.Frame(mid, bg=row["bg"])
            trow.pack(fill="x")
            self.lbl(trow, a.get("Title", ""), 10, skin.TEXT if any_e else skin.TEXT_MUTED, bold=True, bg=row["bg"],
                anchor="w").pack(side="left")
            if is_missable(a):
                self.lbl(trow, "⚠ " + T("f_miss"), 8, skin.WARNING, bold=True, bg=row["bg"]).pack(side="left",
                    padx=(8, 0))
            orig = a.get("Description", "")
            shown = TRANSLATION_CACHE.get((lang, orig), orig) if self.cfg["translate"] else orig
            d = self.lbl(mid, shown, 9, skin.TEXT_MUTED, bg=row["bg"], anchor="w", justify="left", wraplength=280)
            d.pack(fill="x")
            self.duel_items.append((d, orig))
            da = fmt_date(date_of(a))
            db = fmt_date(date_of(b)) if b else ""
            tag_a = T("earned_hc") if is_hc(a) else T("earned_sc")
            tag_b = T("earned_hc") if b and is_hc(b) else T("earned_sc")
            col_a = skin.INFO if is_hc(a) else skin.SUCCESS
            col_b = skin.WARNING if b and is_hc(b) else skin.SUCCESS
            self.lbl(mid, f"{user}: " + (f"✔ {da} • {tag_a}" if me_e else "—"), 8, col_a if me_e else skin.TEXT_MUTED,
                bg=row["bg"], anchor="w").pack(fill="x")
            self.lbl(mid, f"{fr}: " + (f"✔ {db} • {tag_b}" if fr_e else "—"), 8, col_b if fr_e else skin.TEXT_MUTED,
                bg=row["bg"], anchor="w").pack(fill="x")
            self.lbl(row, str(a.get("Points", 0)), 13, skin.ACCENT if any_e else skin.TEXT_MUTED, bold=True,
                bg=row["bg"]).pack(side="right", padx=12)
            row.config(cursor="hand2")
            self.bind_click(row, lambda a=a: self.open_detail(a))
            self.row_hover(row)
        self.rewrap(self.cvs["duel"].winfo_width())
        if self.cfg["translate"]:
            self.translate_labels()

    def render_group(self, force=False):
        """Render the group dashboard: every player ranked by progress on the tracked game."""
        inner = self.inners["group"]
        hc_only = self.cfg["hc_only"]

        def build(name, s, game, pic, err, me=False):
            ach = list(((game or {}).get("Achievements") or {}).values())
            cnt = sum((1 for a in ach if is_counted(a, hc_only)))
            s = s or {}
            lg = s.get("LastGame") or {}
            rp = s.get("RichPresenceMsg") or lg.get("Title") or ""
            return {"name": name, "pic": pic, "pts": s.get("TotalPoints", 0), "play": rp, "cnt": cnt, "tot": len(ach),
                "err": err, "me": me}
        entries = []
        if self.payload and self.payload.get("s"):
            entries.append(build(self.cfg["user"], self.payload["s"], self.game, self.payload["pic"], None, True))
        for m in self.cfg["group"]:
            d = self.group_data.get(m.lower())
            if d is None:
                entries.append({"name": m, "pic": None, "pts": 0, "play": "", "cnt": 0, "tot": 0, "err": None,
                        "me": False, "wait": True})
            elif d.get("error"):
                entries.append({"name": m, "pic": None, "pts": 0, "play": "", "cnt": 0, "tot": 0, "err": d["error"],
                        "me": False})
            else:
                entries.append(build(m, d["s"], d.get("game"), d["pic"], None))
        entries.sort(key=lambda e: (-(e["cnt"] / e["tot"] if e["tot"] else 0), -e["cnt"], e["name"].lower()))
        sig = (i18n.CUR, hc_only,
            tuple(((e["name"], e["cnt"], e["tot"], e["pts"], e["play"], e["err"], e.get("wait")) for e in entries)))
        if sig == self.sigs["group"] and (not force):
            return
        self.sigs["group"] = sig
        for w in inner.winfo_children():
            w.destroy()
        if self.game:
            self.lbl(inner, self.game.get("Title", ""), 10, skin.ACCENT, bold=True, anchor="w").pack(fill="x",
                pady=(4, 4))
        for e in entries:
            card = Card(inner, fill=skin.CARD, radius=skin.RADIUS_CARD, pad=4)
            card.pack(fill="x", pady=3)
            row = card.body
            im = self.photo(e["pic"], 44) if e["pic"] else None
            av = tk.Label(row, bg=skin.CARD, image=im if im else "", width=44 if not im else 0)
            av.image = im
            av.pack(side="left", padx=8, pady=8)
            mid = tk.Frame(row, bg=skin.CARD)
            mid.pack(side="left", fill="x", expand=True, padx=(0, 8))
            head = tk.Frame(mid, bg=skin.CARD)
            head.pack(fill="x")
            self.lbl(head, e["name"], 11, skin.ACCENT if e["me"] else skin.TEXT, bold=True, bg=skin.CARD).pack(side="left")
            self.lbl(head, f"   ★ {fmt_int(e['pts'])}", 9, skin.TEXT_MUTED, bg=skin.CARD).pack(side="left")
            if not e["me"]:
                x = self.lbl(head, "✕", 10, skin.TEXT_MUTED, bg=skin.CARD, cursor="hand2")
                x.pack(side="right")
                x.bind("<Button-1>", lambda ev, n=e["name"]: self.remove_member(n))
                x.bind("<Enter>", lambda ev, w_=x: w_.config(fg=skin.DANGER))
                x.bind("<Leave>", lambda ev, w_=x: w_.config(fg=skin.TEXT_MUTED))
            if e["err"]:
                self.lbl(mid, T("error", e=e["err"]), 8, skin.DANGER, bg=skin.CARD, anchor="w", wraplength=300,
                    justify="left").pack(fill="x")
                continue
            if e["play"]:
                self.lbl(mid, T("g_playing", g=e["play"]), 8, skin.SUCCESS, bg=skin.CARD, anchor="w", wraplength=300,
                    justify="left").pack(fill="x")
            if e["tot"]:
                b = Bar(mid, bg=skin.CARD, h=12)
                b.pack(fill="x", pady=(3, 0))
                b.set(e["cnt"] / e["tot"])
                self.lbl(mid, T("g_on_game", d=e["cnt"], t=e["tot"]), 8, skin.TEXT, bg=skin.CARD, anchor="w").pack(fill="x")
        if not self.cfg["group"]:
            self.lbl(inner, T("g_empty"), 10, skin.TEXT_MUTED, wraplength=400, justify="left").pack(pady=16, padx=6,
                anchor="w")

    # ----------------------------------------------------------------------
    # Game search
    # ----------------------------------------------------------------------
    def open_search(self):
        """Open the game search window (indexes each console once, then searches locally)."""
        if self.search_win is not None and self.search_win.winfo_exists():
            self.search_win.lift()
            return
        key = self.cfg["key"]
        if not key:
            return self.settings()
        if self.gdb is None:
            self.gdb = read_json(GAMES_FILE, {"consoles": [], "ct": 0, "games": {}})
        gdb = self.gdb
        w = tk.Toplevel(self)
        self.search_win = w
        w.title(T("se_title"))
        w.configure(bg=skin.BACKGROUND)
        w.geometry("540x600")
        w.transient(self)
        self.lbl(w, T("se_console"), 10, bold=True, anchor="w").pack(fill="x", padx=14, pady=(12, 0))
        all_label = T("se_all")
        con_var = tk.StringVar(value=all_label)
        csel = {"name": all_label}
        pop = {"w": None, "lb": None, "items": []}
        ce = self.entry(w, con_var)
        ce.pack(fill="x", padx=14, ipady=5)
        self.lbl(w, T("se_name"), 10, bold=True, anchor="w").pack(fill="x", padx=14, pady=(10, 0))
        q_var = tk.StringVar()
        ent = self.entry(w, q_var)
        ent.pack(fill="x", padx=14, ipady=5)
        ent.focus_set()
        status = self.lbl(w, "", 9, skin.TEXT_MUTED, anchor="w")
        status.pack(fill="x", padx=14, pady=4)
        lb = tk.Listbox(w, bg=skin.CARD, fg=skin.TEXT, selectbackground=skin.ACCENT,
            selectforeground=skin.TEXT_ON_ACCENT, relief="flat", font=(skin.FONT, 10), activestyle="none",
            highlightthickness=0)
        lb.pack(fill="both", expand=True, padx=14)
        st = {"results": [], "job": None, "indexing": False}

        def selected_cids():
            n = csel["name"]
            if n == all_label:
                return [c[0] for c in gdb["consoles"]]
            return [c[0] for c in gdb["consoles"] if c[1] == n]

        def fresh(cid):
            g = gdb["games"].get(str(cid))
            return bool(g) and time.time() - g["t"] < GAMES_TTL

        def filter_now():
            if not w.winfo_exists():
                return
            q = norm(q_var.get().strip())
            res = []
            if q.isdigit():
                res.append((int(q), f"→ ID {q}", "", 0))
            if len(q) >= 2:
                words = q.split()
                found = []
                for cid in selected_cids():
                    g = gdb["games"].get(str(cid))
                    if not g:
                        continue
                    for gid, title, cname, n in g["g"]:
                        nt = norm(title)
                        if all((wd in nt for wd in words)):
                            found.append((not nt.startswith(words[0]), nt, gid, title, cname, n))
                found.sort()
                res += [(f[2], f[3], f[4], f[5]) for f in found[:200]]
            st["results"] = res
            lb.delete(0, "end")
            for gid, title, cname, n in res:
                lb.insert("end", title if not cname else f"{title} — {cname} ({T('se_ach', n=n)})")
            if st["indexing"]:
                return
            status.config(text=T("se_results", n=len(res)) if res else T("se_none") if len(q) >= 2 else "")

        def index_missing():
            cids = [c for c in selected_cids() if not fresh(c)]
            if not cids or st["indexing"]:
                return
            st["indexing"] = True

            def job():
                for i, cid in enumerate(cids, 1):
                    self.q.put(("call",
                            lambda i=i: w.winfo_exists() and (status.config(text=T("se_index", i=i, n=len(cids))),
                                filter_now())))
                    try:
                        games = call_api("API_GetGameList.php", key, i=cid, f=1)
                        if isinstance(games, list):
                            gdb["games"][str(cid)] = {"t": time.time(),
                                "g": [[g.get("ID"), g.get("Title", ""), g.get("ConsoleName", ""),
                                        g.get("NumAchievements", 0)] for g in games]}
                    except Exception:
                        pass
                    time.sleep(0.25)
                write_json(GAMES_FILE, gdb)
                st["indexing"] = False
                self.q.put(("call", lambda: w.winfo_exists() and filter_now()))
            threading.Thread(target=job, daemon=True).start()

        def load_consoles():

            def job():
                try:
                    cons = call_api("API_GetConsoleIDs.php", key, a=1, g=1)
                    gdb["consoles"] = sorted([[c["ID"], c["Name"]] for c in cons], key=lambda c: c[1])
                    gdb["ct"] = time.time()
                    write_json(GAMES_FILE, gdb)
                except Exception as ex:
                    msg = str(ex)
                    self.q.put(("call",
                            lambda: w.winfo_exists() and status.config(text=T("error", e=msg), fg=skin.DANGER)))
                    return

                def upd():
                    if w.winfo_exists():
                        changed()
                self.q.put(("call", upd))
            threading.Thread(target=job, daemon=True).start()

        def changed(*_):
            if st["job"]:
                w.after_cancel(st["job"])

            def go():
                if not w.winfo_exists():
                    return
                if len(norm(q_var.get().strip())) >= 2:
                    index_missing()
                filter_now()
            st["job"] = w.after(280, go)
        q_var.trace_add("write", changed)

        def con_names():
            return [all_label] + [c[1] for c in gdb["consoles"]]

        def close_pop(_=None):
            if pop["w"] is not None:
                try:
                    pop["w"].destroy()
                except Exception:
                    pass
                pop["w"] = None
            if con_var.get() not in con_names():
                con_var.set(csel["name"])

        def pick(i):
            if not 0 <= i < len(pop["items"]):
                return
            name = pop["items"][i]
            csel["name"] = name
            con_var.set(name)
            close_pop()
            changed()
            ent.focus_set()

        def open_pop(text=""):
            if pop["w"] is None:
                pw = tk.Toplevel(w)
                pw.overrideredirect(True)
                pw.attributes("-topmost", True)
                pw.configure(bg=skin.SCROLL_THUMB)
                inner = tk.Frame(pw, bg=skin.CARD)
                inner.pack(fill="both", expand=True, padx=1, pady=1)
                lb2 = tk.Listbox(inner, bg=skin.CARD, fg=skin.TEXT, selectbackground=skin.ACCENT,
                    selectforeground=skin.TEXT_ON_ACCENT, relief="flat", font=(skin.FONT, 10), activestyle="none",
                    highlightthickness=0, exportselection=False, width=10)
                sbp = ttk.Scrollbar(inner, command=lb2.yview, style="App.Vertical.TScrollbar")
                lb2.configure(yscrollcommand=sbp.set)
                lb2.pack(side="left", fill="both", expand=True)
                sbp.pack(side="right", fill="y", padx=(0, 2))
                lb2.bind("<Motion>", lambda e: (lb2.selection_clear(0, "end"), lb2.selection_set(lb2.nearest(e.y))))
                lb2.bind("<ButtonRelease-1>", lambda e: pick(lb2.nearest(e.y)))
                pop["w"], pop["lb"] = (pw, lb2)
            ft = norm(text.strip())
            lb2 = pop["lb"]
            pop["items"] = [n for n in con_names() if not ft or ft in norm(n)]
            lb2.delete(0, "end")
            for n in pop["items"]:
                lb2.insert("end", n)
            lb2.config(height=max(1, min(9, len(pop["items"]))))
            if pop["items"]:
                lb2.selection_set(0)
            pop["w"].update_idletasks()
            pop["w"].geometry(f"{ce.winfo_width()}x{pop['w'].winfo_reqheight()}+{ce.winfo_rootx()}+{ce.winfo_rooty() + ce.winfo_height()}")

        def on_key(e):
            if e.keysym == "Escape":
                close_pop()
                return
            if e.keysym in ("Return", "KP_Enter"):
                if pop["w"] is not None and pop["items"]:
                    cur = pop["lb"].curselection()
                    pick(cur[0] if cur else 0)
                return
            if e.keysym in ("Down", "Up") and pop["w"] is not None and pop["items"]:
                cur = pop["lb"].curselection()
                i = cur[0] if cur else -1
                i = max(0, min(len(pop["items"]) - 1, i + (1 if e.keysym == "Down" else -1)))
                pop["lb"].selection_clear(0, "end")
                pop["lb"].selection_set(i)
                pop["lb"].see(i)
                return
            if e.keysym in ("Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Left", "Right", "Home", "End"):
                return
            open_pop(con_var.get())
        ce.bind("<KeyRelease>", on_key)
        ce.bind("<FocusIn>", lambda e: (ce.after(10, lambda: ce.selection_range(0, "end")), open_pop("")))
        ce.bind("<Button-1>", lambda e: open_pop("") if pop["w"] is None else None, add="+")
        ce.bind("<FocusOut>", lambda e: w.after(180, close_pop))
        if not gdb["consoles"] or time.time() - gdb.get("ct", 0) > GAMES_TTL:
            load_consoles()

        def follow(_=None):
            sel = lb.curselection()
            if not sel:
                return
            gid = st["results"][sel[0]][0]
            self.cfg["auto"] = False
            self.cfg["game_id"] = str(gid)
            save_cfg(self.cfg)
            self.reset_game_state()
            w.destroy()
            self.refresh()

        def auto():
            self.cfg["auto"] = True
            self.cfg["game_id"] = ""
            save_cfg(self.cfg)
            self.reset_game_state()
            w.destroy()
            self.refresh()
        lb.bind("<Double-Button-1>", follow)
        lb.bind("<Return>", follow)
        bf = tk.Frame(w, bg=skin.BACKGROUND)
        bf.pack(fill="x", padx=14, pady=12)
        b1 = RoundBtn(bf, text=T("se_follow"), bg=skin.ACCENT, fg=skin.TEXT_ON_ACCENT, font=(skin.FONT, 11, "bold"),
            pady=8, radius=skin.RADIUS_BUTTON_LARGE)
        b1.pack(side="left", fill="x", expand=True)
        b1.bind("<Button-1>", follow)
        self.icon_btn(bf, "↺", T("se_auto").replace("↺ ", ""), auto).pack(side="left", padx=(8, 0), fill="y")

    def reset_game_state(self):
        """Forget everything tied to the previously tracked game."""
        self.known = None
        self.f_known = None
        self.last_game_id = None
        self.sig = None
        self.sigs = {"duel": None, "group": None}
        self.fgame = None
        self.group_data = {}

    # ----------------------------------------------------------------------
    # Achievement detail window (notes + comments)
    # ----------------------------------------------------------------------
    def open_detail(self, a):
        """Open the detail window of an achievement: badge, description, personal note and community comments."""
        w = tk.Toplevel(self)
        w.title(a.get("Title", T("ach_default")))
        w.configure(bg=skin.BACKGROUND)
        w.geometry("520x760")
        w.attributes("-topmost", bool(self.cfg["ontop"]))
        e = is_counted(a, self.cfg["hc_only"]) or is_any(a)
        _hc = Card(w, radius=skin.RADIUS_PANEL, pad=4)
        _hc.pack(fill="x", padx=10, pady=10)
        head = _hc.body
        self.badge(head, a, e, 64, skin.CARD).pack(side="left", padx=10, pady=10)
        c = tk.Frame(head, bg=skin.CARD)
        c.pack(side="left", fill="x", expand=True)
        self.lbl(c, a.get("Title", ""), 13, bold=True, bg=skin.CARD, anchor="w", wraplength=340, justify="left").pack(fill="x")
        if is_missable(a):
            self.lbl(c, "⚠ " + T("f_miss"), 9, skin.WARNING, bold=True, bg=skin.CARD, anchor="w").pack(fill="x")
        orig = a.get("Description", "")
        desc = self.lbl(c, orig, 10, skin.TEXT_MUTED, bg=skin.CARD, anchor="w", wraplength=340, justify="left")
        desc.pack(fill="x")
        self.lbl(c, T("pts_line", p=a.get("Points", 0), r=a.get("TrueRatio", "?")), 9, skin.ACCENT, bg=skin.CARD,
            anchor="w").pack(fill="x")
        if is_any(a):
            tag = T("earned_hc") if is_hc(a) else T("earned_sc")
            self.lbl(c, f"✔ {fmt_date(date_of(a))} • {tag}", 9, skin.INFO if is_hc(a) else skin.SUCCESS, bg=skin.CARD,
                anchor="w").pack(fill="x")
        nid = str(a["ID"])
        nbar = tk.Frame(w, bg=skin.BACKGROUND)
        nbar.pack(fill="x", padx=10)
        self.lbl(nbar, T("note_title"), 11, bold=True, anchor="w").pack(side="left")
        nstat = self.lbl(nbar, "", 9, skin.SUCCESS)
        nstat.pack(side="right")
        nt = tk.Text(w, bg=skin.CARD, fg=skin.TEXT, insertbackground=skin.TEXT, wrap="word", relief="flat",
            font=(skin.FONT, 10), padx=8, pady=6, height=4)
        nt.pack(fill="x", padx=10, pady=(4, 8))
        nt.insert("1.0", self.notes.get(nid, ""))
        nst = {"job": None}

        def save_note(_=None):
            if not nt.winfo_exists():
                return
            txt_ = nt.get("1.0", "end").strip()
            had = bool(self.note_of(a))
            if txt_:
                self.notes[nid] = txt_
            else:
                self.notes.pop(nid, None)
            write_json(NOTES_FILE, self.notes)
            nstat.config(text=T("note_saved"))
            if had != bool(txt_):
                self.sig = None
                self.render_views(force=True)

        def sched(_=None):
            nstat.config(text="")
            if nst["job"]:
                w.after_cancel(nst["job"])
            nst["job"] = w.after(900, save_note)
        nt.bind("<KeyRelease>", sched)
        nt.bind("<FocusOut>", save_note)
        w.protocol("WM_DELETE_WINDOW", lambda: (save_note(), w.destroy()))
        bar = tk.Frame(w, bg=skin.BACKGROUND)
        bar.pack(fill="x", padx=10)
        self.lbl(bar, T("comments"), 11, bold=True, anchor="w").pack(side="left")
        lang = tr_lang(self.cfg)
        st = {"tr": bool(self.cfg["translate"]), "comments": None, "info": ""}
        info = self.lbl(w, T("loading"), 9, skin.TEXT_MUTED, anchor="w")
        info.pack(fill="x", padx=10)
        box = tk.Frame(w, bg=skin.BACKGROUND)
        box.pack(fill="both", expand=True, padx=10, pady=8)
        txt = tk.Text(box, bg=skin.CARD, fg=skin.TEXT, wrap="word", relief="flat", font=(skin.FONT, 10), padx=10, pady=8,
            spacing3=6, state="disabled")
        sb = ttk.Scrollbar(box, command=txt.yview, style="App.Vertical.TScrollbar")
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(8, 0))
        txt.pack(side="left", fill="both", expand=True)
        txt.tag_config("u", foreground=skin.ACCENT, font=(skin.FONT, 10, "bold"))
        txt.tag_config("d", foreground=skin.TEXT_MUTED, font=(skin.FONT, 8))

        def render():
            if not w.winfo_exists():
                return
            cm = st["comments"]
            txt.config(state="normal")
            txt.delete("1.0", "end")
            if cm is not None and (not cm):
                txt.insert("end", T("no_comments"))
            for r in cm or []:
                body = r.get("CommentText", "")
                if st["tr"]:
                    body = TRANSLATION_CACHE.get((lang, body), body)
                txt.insert("end", r.get("User", "?"), "u")
                txt.insert("end", "  " + fmt_date(r.get("Submitted", "")) + '\n', "d")
                txt.insert("end", body.strip() + '\n\n')
            txt.config(state="disabled")
            desc.config(text=TRANSLATION_CACHE.get((lang, orig), orig) if st["tr"] else orig)

        def one(t):
            try:
                translate(t, lang)
            except Exception:
                pass

        def run_tr():

            def job():
                texts = [orig] + [r.get("CommentText", "") for r in st["comments"] or []]
                with ThreadPoolExecutor(6) as ex:
                    list(ex.map(one, texts))
                self.q.put(("call", lambda: (w.winfo_exists() and info.config(text=st["info"]), render())))
            threading.Thread(target=job, daemon=True).start()

        def set_btn():
            bt.config(text=T("orig") if st["tr"] else T("tr_btn", l=lang), bg=skin.ACCENT if st["tr"] else skin.CARD_ALT,
                fg=skin.TEXT_ON_ACCENT if st["tr"] else skin.TEXT)

        def toggle():
            st["tr"] = not st["tr"]
            set_btn()
            if st["tr"]:
                info.config(text=T("translating"))
                run_tr()
            else:
                render()
        bt = self.btn(bar, "", toggle)
        bt.pack(side="right")
        set_btn()

        def load():
            try:
                key = self.cfg["key"]
                r = call_api("API_GetComments.php", key, t=2, i=a["ID"], c=100, o=0)
                total = int(r.get("Total", 0))
                res = r.get("Results", []) or []
                if total > 100:
                    res = call_api("API_GetComments.php", key, t=2, i=a["ID"], c=100, o=total - 100).get("Results", []) or []
                res = sorted(res, key=lambda x: x.get("Submitted", ""), reverse=True)

                def done():
                    if not w.winfo_exists():
                        return
                    st["comments"] = res
                    st["info"] = T("c_info", n=len(res), t=total)
                    info.config(text=st["info"])
                    render()
                    if st["tr"]:
                        info.config(text=T("translating"))
                        run_tr()
                self.q.put(("call", done))
            except Exception as ex:
                msg = str(ex)
                self.q.put(("call", lambda: w.winfo_exists() and info.config(text=T("error", e=msg), fg=skin.DANGER)))
        threading.Thread(target=load, daemon=True).start()

    # ----------------------------------------------------------------------
    # Unlock notifications
    # ----------------------------------------------------------------------
    TOAST_MAX = 4        # notifications shown at the same time, the others wait in a queue
    TOAST_GAP = 8        # pixels between two stacked notifications
    TOAST_MS = 7000      # display duration of one notification

    def toast(self, a, who=None):
        """Queue an unlock notification; several of them are stacked in the bottom-right corner."""
        if not hasattr(self, "_toasts"):
            self._toasts = []
            self._toast_queue = []
        self._toast_queue.append((a, who))
        self._pump_toasts()

    def _pump_toasts(self):
        """Display queued notifications while there is room on screen."""
        while self._toast_queue and len(self._toasts) < self.TOAST_MAX:
            a, who = self._toast_queue.pop(0)
            self._show_toast(a, who)

    def _place_toasts(self):
        """Stack the visible notifications from the bottom of the screen upwards (oldest at the bottom)."""
        sw, sh = (self.winfo_screenwidth(), self.winfo_screenheight())
        y = sh - 70
        for t in self._toasts:
            try:
                w, h = (t.winfo_reqwidth(), t.winfo_reqheight())
                y -= h
                t.geometry(f"+{sw - w - 20}+{max(0, y)}")
                y -= self.TOAST_GAP
            except Exception:
                pass

    def _close_toast(self, t):
        """Remove one notification, move the others down and show the next waiting one."""
        try:
            t.destroy()
        except Exception:
            pass
        if t in self._toasts:
            self._toasts.remove(t)
        self._place_toasts()
        self._pump_toasts()

    def _show_toast(self, a, who=None):
        """Show an unlock notification (yours, or a friend's)."""
        t = tk.Toplevel(self)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        t.configure(bg=TRANSPARENT_KEY)
        try:
            t.attributes("-transparentcolor", TRANSPARENT_KEY)
        except Exception:
            pass
        tcard = Card(t, fill=skin.CARD, radius=skin.RADIUS_TOAST, pad=6, outline=skin.INFO if who else skin.ACCENT)
        tcard.pack()
        inner = tcard.body
        l = self.badge(inner, a, True, 52, skin.CARD)
        l.pack(side="left", padx=10, pady=10)
        c = tk.Frame(inner, bg=skin.CARD)
        c.pack(side="left", padx=(0, 16))
        self.lbl(c, T("f_toast", u=who) if who else T("toast"), 9, skin.INFO if who else skin.ACCENT, bold=True,
            bg=skin.CARD, anchor="w").pack(fill="x")
        self.lbl(c, a.get("Title", ""), 12, bold=True, bg=skin.CARD, anchor="w").pack(fill="x")
        d = a.get("Description", "")
        if self.cfg["translate"]:
            d = TRANSLATION_CACHE.get((tr_lang(self.cfg), d), d)
        self.lbl(c, d, 9, skin.TEXT_MUTED, bg=skin.CARD, anchor="w", wraplength=260, justify="left").pack(fill="x")
        self.lbl(c, T("plus_pts", n=a.get("Points", 0)), 10, skin.SUCCESS, bold=True, bg=skin.CARD, anchor="w").pack(fill="x")
        t.update_idletasks()
        self._toasts.append(t)
        self._place_toasts()
        t.after(self.TOAST_MS, lambda t=t: self._close_toast(t))
