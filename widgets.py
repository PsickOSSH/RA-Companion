"""Reusable Tk widgets (rounded cards and buttons, tooltips, mixed-font labels, progress bar).

Every color, font and radius comes from the active skin (see the `skins` package)."""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from skins import active as skin


class Tip:
    """Tooltip shown when the mouse rests on a widget; `fn` returns the (possibly dynamic) text."""

    def __init__(self, w, fn):
        self.w, self.fn, self.tw, self.job = (w, fn, None, None)
        w.bind("<Enter>", self.enter, add="+")
        w.bind("<Leave>", self.leave, add="+")
        w.bind("<ButtonPress>", self.leave, add="+")

    def enter(self, _):
        """Schedule the tooltip to appear shortly after the pointer enters the widget."""
        self.leave()
        self.job = self.w.after(400, self.show)

    def leave(self, _=None):
        """Cancel a pending tooltip and hide the visible one."""
        if self.job:
            try:
                self.w.after_cancel(self.job)
            except Exception:
                pass
            self.job = None
        if self.tw:
            try:
                self.tw.destroy()
            except Exception:
                pass
            self.tw = None

    def show(self):
        """Create the tooltip window just below the widget (rounded, drawn with the skin colors)."""
        try:
            self.tw = tw = tk.Toplevel(self.w)
            tw.overrideredirect(True)
            tw.attributes("-topmost", True)
            tw.configure(bg=TRANSPARENT_KEY)
            try:
                tw.attributes("-transparentcolor", TRANSPARENT_KEY)
            except Exception:
                pass
            card = Card(tw, fill=skin.TOOLTIP_BG, radius=skin.RADIUS_BUTTON, pad=4, outline=skin.TOOLTIP_BORDER)
            card.pack()
            tk.Label(card.body, text=self.fn(), bg=skin.TOOLTIP_BG, fg=skin.TOOLTIP_TEXT,
                     font=(skin.FONT, 9), padx=6, pady=2, justify="left").pack()
            x = self.w.winfo_rootx()
            y = self.w.winfo_rooty() + self.w.winfo_height() + 6
            tw.update_idletasks()
            x = max(0, min(x, self.w.winfo_screenwidth() - tw.winfo_width() - 4))
            tw.geometry(f"+{x}+{y}")
        except Exception:
            self.tw = None


# Color made transparent on Windows, so that rounded notification windows have real round corners.
TRANSPARENT_KEY = "#010203"


def rrect(cv, x1, y1, x2, y2, r, **kw):
    """Draw a rounded rectangle on a canvas (smoothed polygon)."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1]
    return cv.create_polygon(pts, smooth=True, **kw)


def blend(c1, c2, t):
    """Linearly mix two '#rrggbb' colors; `t` = 0 gives `c1`, `t` = 1 gives `c2`."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple((round(x + (y - x) * t) for x, y in zip(a, b)))


class Card(tk.Frame):
    """Frame with rounded corners. Put the content in `card.body`; the shape is drawn on a canvas behind it."""

    def __init__(self, parent, fill=skin.CARD, radius=skin.RADIUS_PANEL, pad=6, outline=None):
        super().__init__(parent, bg=parent["bg"])
        self.fill, self.radius, self.outline = (fill, radius, outline)
        self.cv = tk.Canvas(self, width=1, height=1, bg=parent["bg"], highlightthickness=0, bd=0)
        self.cv.grid(row=0, column=0, sticky="nsew")
        self.body = tk.Frame(self, bg=fill)
        self.body._card = self
        self.body.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._job = None
        self.cv.bind("<Configure>", self._on_cfg)

    def _on_cfg(self, e):
        """Debounce redraws while the window is being resized."""
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(40, self.redraw)

    def redraw(self):
        """Redraw the rounded background (cheap rectangles + circles; polygon only when an outline is needed)."""
        self._job = None
        self.cv.delete("all")
        w, h = (self.cv.winfo_width(), self.cv.winfo_height())
        if w < 4 or h < 4:
            return
        if self.outline:
            rrect(self.cv, 1, 1, w - 1, h - 1, self.radius, fill=self.fill, outline=self.outline, width=2)
        else:
            r = max(0, min(self.radius, w // 2, h // 2))
            d = 2 * r
            f = dict(fill=self.fill, outline="")
            self.cv.create_rectangle(r, 0, w - r, h, **f)
            self.cv.create_rectangle(0, r, w, h - r, **f)
            for x0, y0 in ((0, 0), (w - d, 0), (0, h - d), (w - d, h - d)):
                self.cv.create_oval(x0, y0, x0 + d, y0 + d, **f)

    def set_fill(self, color):
        """Change the fill color (used by the hover effect)."""
        self.fill = color
        self.body.config(bg=color)
        self.redraw()


# Font used for every emoji / symbol (the regular UI font renders them inconsistently).
SYMF = (skin.SYMBOL_FONT, 13)


def is_sym(ch):
    """True for characters that must be rendered with the symbol font (arrows, dingbats, emoji...)."""
    o = ord(ch)
    return 8592 <= o <= 11263 or 126976 <= o <= 129791 or o in (65039, 8205)


def has_sym(text):
    """True if the text contains at least one symbol character."""
    return isinstance(text, str) and any((is_sym(c) for c in text))


def split_lead(text):
    """Split a leading symbol from its label: '⚔ Duel' -> ('⚔', 'Duel'); otherwise (None, text)."""
    i = 0
    while i < len(text) and is_sym(text[i]):
        i += 1
    if i and i < len(text) and (text[i] == " "):
        return (text[:i], text[i:].strip())
    return (None, text)


def setup_ttk_styles(root):
    """Configure the ttk widgets (scrollbar, combobox) with the colors of the active skin."""
    st = ttk.Style(root)
    st.theme_use("clam")
    st.layout("App.Vertical.TScrollbar",
        [("Vertical.Scrollbar.trough",
                {"sticky": "ns", "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
    st.configure("App.Vertical.TScrollbar", troughcolor=skin.BACKGROUND, background=skin.SCROLL_THUMB,
        bordercolor=skin.BACKGROUND, lightcolor=skin.SCROLL_THUMB, darkcolor=skin.SCROLL_THUMB, gripcount=0, width=8)
    st.map("App.Vertical.TScrollbar", background=[("active", skin.ACCENT), ("pressed", skin.ACCENT)],
        lightcolor=[("active", skin.ACCENT), ("pressed", skin.ACCENT)],
        darkcolor=[("active", skin.ACCENT), ("pressed", skin.ACCENT)])
    st.configure("TCombobox", fieldbackground=skin.CARD, background=skin.CARD_ALT, foreground=skin.TEXT,
        arrowcolor=skin.TEXT, bordercolor=skin.CARD_ALT, lightcolor=skin.CARD_ALT, darkcolor=skin.CARD_ALT,
        selectbackground=skin.CARD, selectforeground=skin.TEXT)
    st.map("TCombobox", fieldbackground=[("readonly", skin.CARD)], foreground=[("readonly", skin.TEXT)],
        selectbackground=[("readonly", skin.CARD)], selectforeground=[("readonly", skin.TEXT)],
        background=[("active", skin.CONTROL_HOVER)])
    root.option_add("*TCombobox*Listbox.background", skin.CARD)
    root.option_add("*TCombobox*Listbox.foreground", skin.TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", skin.ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", skin.TEXT_ON_ACCENT)
    root.option_add("*TCombobox*Listbox.font", (skin.FONT, 10))


class SLabel(tk.Frame):
    """Label that renders symbols/emoji with the symbol font and the rest with the normal font. Accepts the usual Label options (text, fg, bg, wraplength...)."""

    def __init__(self, parent, text="", size=10, color=skin.TEXT, bold=False, bg=None, anchor="w", justify="left",
        wraplength=0, cursor="", **_):
        super().__init__(parent, bg=bg or parent["bg"])
        self.size, self.fg_, self.bold, self.wrap, self.just = (size, color, bold, wraplength, justify)
        self.text = ""
        self._binds = []
        self.cursor_ = cursor
        if cursor:
            tk.Frame.configure(self, cursor=cursor)
        self._build(text)

    @staticmethod
    def _runs(text):
        """Group the text into runs of symbol / non-symbol characters."""
        runs = []
        for ch in text:
            sym = is_sym(ch)
            if ch == " " and runs:
                sym = runs[-1][0]
            if runs and runs[-1][0] == sym:
                runs[-1][1] += ch
            else:
                runs.append([sym, ch])
        return runs

    def _build(self, text):
        """(Re)create the child widgets for `text`."""
        for c in self.winfo_children():
            c.destroy()
        self.text = text
        bg = tk.Frame.cget(self, "bg")
        runs = self._runs(text)
        if not runs:
            return
        if self.wrap:
            return self._build_wrapped(runs, bg)
        for sym, t in runs:
            font = (skin.SYMBOL_FONT, self.size) if sym else (skin.FONT, self.size, "bold" if self.bold else "normal")
            lab = tk.Label(self, text=t, bg=bg, fg=self.fg_, font=font, bd=0, padx=0, pady=0, anchor="w")
            if self.cursor_:
                lab.config(cursor=self.cursor_)
            lab.pack(side="left", anchor="w")
            for seq, fn, add in self._binds:
                lab.bind(seq, fn, add)

    def _build_wrapped(self, runs, bg):
        """Draw the text word by word on a canvas so that mixed fonts can still wrap on the available width."""
        fonts = {False: tkfont.Font(font=(skin.FONT, self.size, "bold" if self.bold else "normal")),
            True: tkfont.Font(font=(skin.SYMBOL_FONT, self.size))}
        tokens = []
        for sym, chunk in runs:
            part = ""
            for ch in chunk:
                part += ch
                if ch == " ":
                    tokens.append((sym, part))
                    part = ""
            if part:
                tokens.append((sym, part))
        asc = max((f.metrics("ascent") for f in fonts.values()))
        desc = max((f.metrics("descent") for f in fonts.values()))
        lh = asc + desc
        cv = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0, width=1, height=lh, cursor=self.cursor_ or "arrow")
        cv.pack(fill="x", expand=True)
        state = {"w": 0, "h": 0}

        def layout(width):
            width = max(60, width)
            cv.delete("all")
            x = y = 0
            for sym, part in tokens:
                f = fonts[sym]
                shown = part.rstrip()
                if x > 0 and x + f.measure(shown) > width:
                    x = 0
                    y += lh
                if shown:
                    cv.create_text(x, y + asc - f.metrics("ascent"), text=shown, font=f, fill=self.fg_, anchor="nw")
                x += f.measure(part)
            if state["h"] != y + lh:
                state["h"] = y + lh
                cv.config(height=y + lh)

        def on_cfg(e):
            if e.width != state["w"]:
                state["w"] = e.width
                layout(e.width)
        cv.bind("<Configure>", on_cfg)
        layout(self.wrap)
        for seq, fn, add in self._binds:
            cv.bind(seq, fn, add)

    def configure(self, cnf=None, **kw):
        """Label-like configure(): text, fg, bg and wraplength are handled here."""
        if "text" in kw:
            self._build(kw.pop("text"))
        for k in ("fg", "foreground"):
            if k in kw:
                self.fg_ = kw.pop(k)
                for c in self.winfo_children():
                    if isinstance(c, tk.Canvas):
                        c.itemconfig("all", fill=self.fg_)
                    else:
                        c.config(fg=self.fg_)
        if "wraplength" in kw:
            new = kw.pop("wraplength")
            changed = bool(new) != bool(self.wrap)
            self.wrap = new
            if changed:
                self._build(self.text)
        for k in ("bg", "background"):
            if k in kw:
                bg = kw.pop(k)
                tk.Frame.configure(self, bg=bg)
                for c in self.winfo_children():
                    c.config(bg=bg)
        for k in ("font", "justify", "anchor", "width", "image"):
            kw.pop(k, None)
        if kw:
            tk.Frame.configure(self, **kw)
    config = configure

    def cget(self, key):
        """Label-like cget() for `text` and `fg`."""
        if key == "text":
            return self.text
        if key in ("fg", "foreground"):
            return self.fg_
        return tk.Frame.cget(self, key)

    def bind(self, seq=None, func=None, add=None):
        """Bind an event on the frame and on every child widget (and remember it for rebuilds)."""
        self._binds.append((seq, func, add))
        tk.Frame.bind(self, seq, func, add)
        for c in self.winfo_children():
            c.bind(seq, func, add)


class RoundBtn(tk.Canvas):
    """Rounded button (icon + text) with an animated hover color. Mimics tk.Label (bg, fg, text) so it can be recolored easily."""

    def __init__(self, parent, text="", icon=None, bg=skin.CARD_ALT, fg=skin.TEXT, font=None, icon_font=None, padx=10,
        pady=5, radius=skin.RADIUS_BUTTON, chars=None):
        self._tkfont = tkfont
        self._icon_font = icon_font
        self._icon_given = icon is not None
        self._f = tkfont.Font(font=font or (skin.FONT, 10))
        self._if = None
        if icon is None and text:
            lead, rest = split_lead(text)
            if lead:
                icon, text = (lead, rest)
        self.text, self.icon, self.fg_, self.base, self.cur = (text, icon, fg, bg, bg)
        self._mkicon()
        self.px, self.py, self.radius, self.chars = (padx, pady, radius, chars)
        self.hov = False
        self._job = None
        super().__init__(parent, width=10, height=10, bg=parent["bg"], highlightthickness=0, bd=0, cursor="hand2")
        self._resize()
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))

    def _mkicon(self):
        """Create the icon font lazily (symbol font, slightly larger than the text)."""
        if self.icon and self._if is None:
            size = abs(int(self._f.actual("size"))) + 3
            self._if = self._tkfont.Font(font=self._icon_font or (skin.SYMBOL_FONT, size))

    def _widths(self):
        """Return the pixel widths of the text, the icon and the gap between them."""
        tw = self._f.measure(self.text) if self.text else 0
        iw = self._if.measure(self.icon) if self.icon else 0
        return (tw, iw, 5 if tw and iw else 0)

    def _resize(self):
        """Compute the requested size from the content."""
        tw, iw, gap = self._widths()
        base_w = max(tw, self._f.measure("0") * self.chars) if self.chars else tw
        h = max(self._f.metrics("linespace"), self._if.metrics("linespace") if self._if else 0) + self.py * 2
        tk.Canvas.configure(self, width=self.px * 2 + iw + gap + base_w, height=h)

    def draw(self):
        """Draw the rounded background, the icon and the text."""
        self.delete("all")
        w, h = (self.winfo_width(), self.winfo_height())
        if w < 4:
            w, h = (int(float(self.cget("width"))), int(float(self.cget("height"))))
        rrect(self, 0, 0, w, h, self.radius, fill=self.cur, outline="")
        tw, iw, gap = self._widths()
        x = (w - (iw + gap + tw)) / 2
        if self.icon:
            self.create_text(x, h / 2, text=self.icon, font=self._if, fill=self.fg_, anchor="w")
        if self.text:
            self.create_text(x + iw + gap, h / 2, text=self.text, font=self._f, fill=self.fg_, anchor="w")

    def _target(self):
        """Color the button should currently have (base color, lightened while hovered)."""
        return blend(self.base, skin.HOVER_TINT, skin.HOVER_STRENGTH) if self.hov else self.base

    def _hover(self, on):
        """Animate the color change when the pointer enters or leaves the button."""
        self.hov = on
        if self._job:
            self.after_cancel(self._job)
        start, tgt, n = (self.cur, self._target(), [0])

        def step():
            n[0] += 1
            self.cur = blend(start, tgt, n[0] / 6)
            self.draw()
            self._job = self.after(18, step) if n[0] < 6 else None
        step()

    def configure(self, **kw):
        """tk.Label-like configure(): bg, fg and text are handled here."""
        for k in ("bg", "background"):
            if k in kw:
                self.base = kw.pop(k)
                self.cur = self._target()
        if "fg" in kw:
            self.fg_ = kw.pop("fg")
        if "foreground" in kw:
            self.fg_ = kw.pop("foreground")
        if "text" in kw:
            t = kw.pop("text")
            if self._icon_given:
                self.text = t
            else:
                lead, rest = split_lead(t) if t else (None, t)
                self.icon, self.text = (lead, rest) if lead else (None, t)
                self._mkicon()
            self._resize()
        if kw:
            tk.Canvas.configure(self, **kw)
        self.draw()
    config = configure

    def cget(self, key):
        """tk.Label-like cget() for `bg` and `text`."""
        if key in ("bg", "background"):
            return self.base
        if key == "text":
            return self.text
        return tk.Canvas.cget(self, key)


class Bar(tk.Canvas):
    """Slim rounded progress bar; call set(fraction) with a value between 0 and 1."""

    def __init__(self, master, bg=skin.CARD, h=14, **kw):
        super().__init__(master, height=h, bg=bg, highlightthickness=0, **kw)
        self.v = 0.0
        self.h = h
        self.track = skin.CARD_ALT if bg == skin.CARD else skin.BAR_TRACK_ALT
        self.bind("<Configure>", lambda e: self.draw())

    def set(self, v):
        """Set the progress (0..1) and redraw."""
        self.v = max(0, min(1, v))
        self.draw()

    def draw(self):
        """Draw the track and the filled part (gold while in progress, green when complete)."""
        self.delete("all")
        w = self.winfo_width()
        t = (self.h - 10) // 2 + 2
        rrect(self, 0, t, w, t + 10, 5, fill=self.track, outline="")
        if self.v > 0:
            rrect(self, 0, t, max(10, int(w * self.v)), t + 10, 5, fill=skin.ACCENT if self.v < 1 else skin.SUCCESS,
                outline="")
