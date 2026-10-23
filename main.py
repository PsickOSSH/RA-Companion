"""RA Companion for Android (Kivy): profile, achievements, achievement page with notes, duel, group, game search, skins, notifications."""

import os
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor

import kivy
kivy.require("2.1.0")

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.image import AsyncImage

import androidutil
import iosutil
import appinfo
import updater
import features
import medians
import imgcache
import layoututil
import notify
import storage
import themes
import uitext
from config import MEDIA
from ra_api import call_api
import translator
from uitext import friendly_error, tr
from utils import date_of, fmt_date, fmt_int, is_any, is_hc, is_missable, norm

BASE = os.path.dirname(os.path.abspath(__file__))

# Kivy's default font has no symbols and shows crossed boxes instead. fonts/RASans*.ttf (DejaVu Sans + 4 drawn symbols)
# replaces the default font of the whole app. DejaVu alone is used as a fallback (the 4 drawn symbols are then missing).
for _regular, _bold in (("RASans.ttf", "RASans-Bold.ttf"), ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")):
    _f, _b = os.path.join(BASE, "fonts", _regular), os.path.join(BASE, "fonts", _bold)
    if os.path.exists(_f):
        LabelBase.register(name="Roboto", fn_regular=_f, fn_bold=_b if os.path.exists(_b) else _f)
        Logger.info("RA: font loaded: %s", _f)
        break
else:
    Logger.warning("RA: no font in fonts/: is 'ttf' in source.include_exts of buildozer.spec?")

# The soft keyboard must push the screen up so the text field being edited stays visible.
if kivy.utils.platform != "ios":
    Window.softinput_mode = "below_target"

CFG_DEFAULTS = {"friend": "", "group": [], "game_id": "", "auto": True, "hc_only": False, "interval": 30,
                "auto_refresh": True, "sort": "disp_asc", "miss_only": False, "notify": True, "translate": False,
                "ui_lang": "auto", "lang": "auto", "skin": "default", "filter": "all", "tab": "success"}


def _cfg():
    return App.get_running_app().cfg


def save_cfg(cfg=None):
    """Write the settings in the private folder of the app. Returns True when they were saved (the error is kept otherwise)."""
    app = App.get_running_app()
    ok, err = storage.save_json(app.settings_path, app.cfg if cfg is None else cfg)
    app.save_error = "" if ok else err
    if not ok:
        Logger.error("RA: cannot save the settings (%s): %s", app.settings_path, err)
    return ok


def _with_owned_by(rows, game, index):
    """Locked achievements show how many players earned them ('🔒 owned by 16% of players') instead of just 'locked'."""
    try:
        players = int((game or {}).get("NumDistinctPlayers") or (game or {}).get("NumDistinctPlayersCasual") or 0)
    except (TypeError, ValueError):
        return rows
    if not players:
        return rows
    locked = tr("f_todo")
    for r in rows:
        if r.get("status") == "locked" and r.get("date") == locked:
            a = index.get(str(r.get("ach_id")))
            try:
                pct = round(100 * int(a.get("NumAwarded", 0) or 0) / players)
            except Exception:
                continue
            r["date"] = f"{uitext.ICON_LOCK} {tr('owned_by', p=pct)}"
    return rows


def _labels():
    """Translated texts used by the pure functions of features.py."""
    return {"locked": tr("f_todo"), "sc_only": tr("sc_only"), "hc": tr("earned_hc"), "sc": tr("earned_sc")}


def _name_width(text):
    """Width in pixels of the player name (17 sp bold), so that the rank can be written right after it."""
    try:
        from kivy.core.text import Label as CoreLabel
        width = CoreLabel(font_size=sp(17), bold=True).get_extents(text)[0] + dp(8)
    except Exception:
        width = len(text) * dp(11)
    return min(width, dp(130))


# ---------------------------------------------------------------------------
# Translation of descriptions and comments (Google Translate through ra_api.translate, cached in memory)
# ---------------------------------------------------------------------------
TRANSLATOR = translator.Translator()      # its cache file is set in build() (private folder of the app)


class _Retry:
    """`_TRIED.clear()` lets the texts that failed be tried again (called when the user presses the translation button)."""

    def clear(self):
        TRANSLATOR.reset_failures()


_TRIED = _Retry()


def target_lang():
    return uitext.translation_language(_cfg().get("lang", "auto"))


def cached_translation(text):
    return TRANSLATOR.cached(target_lang(), text)


def translate_async(texts, done):
    """Translate the texts that are still pending in a background thread, then call `done()` on the UI thread.
    Returns False when there was nothing to do. Problems are kept in TRANSLATOR.last_error (the screens show it)."""
    lang = target_lang()
    todo = [t for t in dict.fromkeys(texts) if TRANSLATOR.pending(lang, t)]
    if not todo:
        return False

    def job():
        try:
            TRANSLATOR.translate_many(todo, lang)
        except Exception as e:                      # the callback must always be called
            TRANSLATOR.last_error = f"{e.__class__.__name__}: {e}"[:120]
            Logger.exception("RA: translation failed")
        Clock.schedule_once(lambda dt: done())
    threading.Thread(target=job, daemon=True).start()
    return True


# ---------------------------------------------------------------------------
# Small widgets styled in main.kv
# ---------------------------------------------------------------------------
class Card(BoxLayout):
    """Rounded panel."""

def _image_folder():
    return os.path.join(App.get_running_app().user_data_dir, "img_cache")


class Pic(AsyncImage):
    """Picture shown from `url` (not `source`): it is saved on the phone, so it is downloaded only once (imgcache.py)."""
    url = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        if hasattr(self, "fit_mode"):
            self.fit_mode = "contain"
        else:
            self.allow_stretch = True
        self.bind(url=self._on_url)
        if self.url:
            self._on_url(self, self.url)

    def _on_url(self, _widget, url):
        if not url:
            self.source = ""
            return
        if not url.startswith("http"):
            self.source = url
            return
        path = imgcache.cached_path(_image_folder(), url)
        if path:
            self.source = path
            return
        self.source = ""
        imgcache.fetch_async(_image_folder(), url, lambda p: Clock.schedule_once(lambda dt: self._loaded(url, p)))

    def _loaded(self, url, path):
        if self.url == url:
            self.source = path

class FlatButton(Button):
    """Flat button; `active` paints it with the accent color; `idle_color` (optional) is the text color when it is not active."""
    active = BooleanProperty(False)
    idle_color = ListProperty([])


class ChipButton(FlatButton):
    """Filter button: the font shrinks (never below 8 sp) so that the text always fits, whatever the language or the bold state."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self.fit, text=self.fit)

    @staticmethod
    def measure(text, size_sp):
        """Width in pixels of `text` written in bold at `size_sp` (the widest state of the button)."""
        try:
            from kivy.core.text import Label as CoreLabel
            return CoreLabel(font_size=sp(size_sp), bold=True).get_extents(text)[0]
        except Exception:
            return len(text) * sp(size_sp) * 0.62

    def need(self):
        """Width the text needs at the biggest size, with a little room on each side."""
        return self.measure(self.text, 12) + dp(18)

    def fit(self, *args):
        if self.width > 1 and self.text:
            self.font_size = sp(layoututil.fit_size(self.measure, self.text, self.width - dp(10), 12, 8))


class ChipRow(BoxLayout):
    """Row of ChipButton (+ fixed-width buttons): each chip gets a share of the width proportional to its text, so a long text
    such as 'Por desbloquear' is no longer cut."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(width=self.share, children=self.share)

    def share(self, *args):
        chips = [c for c in self.children if isinstance(c, ChipButton)]
        if chips:
            for chip, weight in zip(chips, layoututil.weights([c.need() for c in chips])):
                chip.size_hint_x = weight


class DarkInput(TextInput):
    """Single-line text field with its own long-press menu (Copy / Paste / Select all)."""

    def __init__(self, **kw):
        kw["use_bubble"] = True
        kw["use_handles"] = True
        super().__init__(**kw)


class SmallInput(DarkInput):
    """Narrow numeric field (refresh interval)."""


class NoteInput(DarkInput):
    """Multi-line field for the personal note of an achievement."""


class TextLabel(Label):
    """Left-aligned label that wraps its text and grows in height."""


class LinkLabel(TextLabel):
    """Label whose [ref=...] parts open a web link."""

    def on_ref_press(self, ref):
        App.get_running_app().open_url(ref)


class LinkLogo(ButtonBehavior, BoxLayout):
    """Logo + name that open a web link."""
    url = StringProperty("")
    logo_url = StringProperty("")
    caption = StringProperty("")
    logo_color = ListProperty([1, 1, 1, 1])

    def on_release(self):
        App.get_running_app().open_url(self.url)


class AchievementRow(ButtonBehavior, BoxLayout):
    ach_id = StringProperty("")
    title = StringProperty("")
    description = StringProperty("")
    points = StringProperty("")
    date = StringProperty("")
    status = StringProperty("locked")
    badge_url = StringProperty("")
    missable = BooleanProperty(False)
    has_note = BooleanProperty(False)

    def on_release(self):
        App.get_running_app().root.get_screen("profile").open_detail(self.ach_id)


class DuelRow(ButtonBehavior, BoxLayout):
    ach_id = StringProperty("")
    title = StringProperty("")
    description = StringProperty("")
    points = StringProperty("")
    badge_url = StringProperty("")
    me_line = StringProperty("")
    fr_line = StringProperty("")
    side = StringProperty("none")   # not `state`: ButtonBehavior already uses that name
    missable = BooleanProperty(False)
    has_note = BooleanProperty(False)

    def on_release(self):
        App.get_running_app().root.get_screen("profile").open_detail(self.ach_id)


class GroupRow(BoxLayout):
    member = StringProperty("")
    points_line = StringProperty("")
    play = StringProperty("")
    err = StringProperty("")
    progress = NumericProperty(0)
    progress_text = StringProperty("")
    pic_url = StringProperty("")
    me = BooleanProperty(False)
    removable = BooleanProperty(True)


class GameRow(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    subtitle = StringProperty("")
    game_id = StringProperty("")

    def on_release(self):
        App.get_running_app().root.get_screen("search").follow(self.game_id)


class CommentItem(BoxLayout):
    user_line = StringProperty("")
    body = StringProperty("")


# ---------------------------------------------------------------------------
# Main screen: profile, game card and the three tabs (achievements / duel / group)
# ---------------------------------------------------------------------------
class ProfileScreen(Screen):
    username = StringProperty("")
    name_width = NumericProperty(100)
    rank_line = StringProperty("")
    hc_line = StringProperty("")
    retro_line = StringProperty("")
    sc_line = StringProperty("")
    avatar_url = StringProperty("")
    game_icon_url = StringProperty("")
    rich_presence = StringProperty("")
    current_game = StringProperty("")
    game_console = StringProperty("")
    game_progress = StringProperty("")
    hcsc_line = StringProperty("")
    game_ratio = NumericProperty(0)
    status_text = StringProperty("")
    current_tab = StringProperty("success")
    current_filter = StringProperty("all")
    friend_name = StringProperty("")
    duel_title = StringProperty("")
    duel_detail = StringProperty("")
    group_hint = StringProperty("")
    interval_text = StringProperty("30")
    translate_on = BooleanProperty(False)
    hc_on = BooleanProperty(False)
    miss_on = BooleanProperty(False)
    auto_on = BooleanProperty(True)
    success_rows = ListProperty([])
    duel_rows = ListProperty([])
    group_rows = ListProperty([])

    def __init__(self, **kw):
        super().__init__(**kw)
        self._busy = False          # a network refresh is running
        self._gen = 0               # id of the last refresh; older results are ignored
        self._payload = None        # last data received from the API
        self._group_data = {}       # member.lower() -> API data, kept between refreshes
        self._rows_all = []         # all achievement rows (before the filters)
        self._ach_index = {}        # achievement ID -> API dict, for the detail page
        self._countdown = 0
        self._tick_ev = None
        self._from_detail = False   # coming back from the achievement page: no reload needed
        self._restored = False      # filter and tab restored from the saved settings

    # ---- lifecycle -------------------------------------------------------
    def on_enter(self):
        cfg = _cfg()
        if not self._restored:
            self._restored = True
            if cfg.get("filter") in ("all", "locked", "unlocked"):
                self.current_filter = cfg["filter"]
            if cfg.get("tab") in ("success", "duel", "group"):
                self.current_tab = cfg["tab"]
            self.ids.tabs.current = self.current_tab
        self.friend_name = str(cfg.get("friend", ""))
        self.translate_on = bool(cfg.get("translate"))
        self.hc_on = bool(cfg.get("hc_only"))
        self.miss_on = bool(cfg.get("miss_only"))
        self.auto_on = bool(cfg.get("auto_refresh", True))
        self.interval_text = str(self._interval())
        if self._tick_ev is None:
            self._tick_ev = Clock.schedule_interval(self._tick, 1)
        if self._from_detail:
            self._from_detail = False
            self.render_all()
            return
        self._countdown = 0
        self.refresh(force=True)

    def on_leave(self):
        if self._tick_ev is not None:
            self._tick_ev.cancel()
            self._tick_ev = None

    def reset_game_state(self):
        """Forget everything about the previous game / account."""
        self._gen += 1
        self._busy = False
        self._payload = None
        self._group_data = {}
        self._rows_all = []
        self._ach_index = {}
        self.success_rows = []
        self.duel_rows = []
        self.group_rows = []
        self.current_game = tr("loading")
        self.game_console = ""
        self.game_progress = ""
        self.hcsc_line = ""
        self.rich_presence = ""
        self.game_ratio = 0
        self.game_icon_url = ""
        App.get_running_app().tracker.reset()

    # ---- automatic refresh -----------------------------------------------
    def _interval(self):
        try:
            return max(10, min(3600, int(_cfg().get("interval", 30) or 30)))
        except (TypeError, ValueError):
            return 30

    def _tick(self, dt):
        if not _cfg().get("auto_refresh", True):
            return
        self._countdown -= 1
        if self._countdown <= 0 and not self._busy:
            self.refresh()

    def step_interval(self, delta):
        """Arrows of the footer: add or remove `delta` seconds between two automatic refreshes."""
        try:
            current = int(self.interval_text)
        except (TypeError, ValueError):
            current = self._interval()
        self.set_interval(current + delta)

    def toggle_auto(self):
        cfg = _cfg()
        cfg["auto_refresh"] = not cfg.get("auto_refresh", True)
        save_cfg(cfg)
        self.auto_on = bool(cfg["auto_refresh"])
        self._countdown = self._interval()

    def set_interval(self, text):
        """Seconds between two automatic refreshes (field of the footer)."""
        try:
            n = max(10, min(3600, int(text)))
        except (TypeError, ValueError):
            n = self._interval()
        cfg = _cfg()
        cfg["interval"] = n
        save_cfg(cfg)
        self.interval_text = str(n)
        self._countdown = n

    def interval_focus(self, widget, focused):
        if not focused:
            self.set_interval(widget.text)
            widget.text = self.interval_text

    # ---- network ---------------------------------------------------------
    def refresh(self, force=False):
        cfg = _cfg()
        user = str(cfg.get("user", "")).strip()
        key = str(cfg.get("key", "")).strip()
        if not user or not key:
            self.current_game = tr("need_cfg")
            self.status_text = ""
            return
        if self._busy and not force:
            return
        self._busy = True
        self._gen += 1
        forced = cfg.get("game_id") if (not cfg.get("auto", True) and cfg.get("game_id")) else None
        friend = str(cfg.get("friend", "")).strip()
        members = [m for m in cfg.get("group", []) if m]
        want_group = self.current_tab == "group"
        self.status_text = tr("updating")
        threading.Thread(target=self._worker, daemon=True,
                         args=(self._gen, user, key, forced, friend, members, want_group)).start()

    def _worker(self, gen, user, key, forced, friend, members, want_group):
        """Runs in a background thread: only API calls here, the UI is updated through Clock.schedule_once."""
        try:
            summary = call_api("API_GetUserSummary.php", key, u=user, g=1, a=0)
            if not isinstance(summary, dict):
                raise ValueError(tr("err_resp"))
            gid = forced or summary.get("LastGameID") or (summary.get("LastGame") or {}).get("ID")
            game = call_api("API_GetGameInfoAndUserProgress.php", key, u=user, g=gid) if gid else None
            if game:
                medians.apply(game, medians.fetch(call_api, key, gid, os.path.join(App.get_running_app().user_data_dir, "medians")))
            friend_game = None
            if friend and gid:
                try:
                    friend_game = call_api("API_GetGameInfoAndUserProgress.php", key, u=friend, g=gid)
                except Exception as e:
                    friend_game = {"error": friendly_error(e)}
            group = None
            if want_group and gid:
                def one(name):
                    try:
                        ss = call_api("API_GetUserSummary.php", key, u=name, g=1, a=0)
                        gg = call_api("API_GetGameInfoAndUserProgress.php", key, u=name, g=gid)
                        pic = ss.get("UserPic") or f"/UserPic/{name}.png"
                        return name.lower(), {"user": name, "s": ss, "game": gg, "pic": pic}
                    except Exception as e:
                        return name.lower(), {"user": name, "error": friendly_error(e)}
                with ThreadPoolExecutor(4) as ex:
                    group = dict(ex.map(one, members))
            payload = {"summary": summary, "game": game, "friend": friend_game, "group": group, "gid": gid}
            Clock.schedule_once(lambda dt: self._on_payload(gen, payload))
        except Exception as e:
            msg = friendly_error(e)
            Clock.schedule_once(lambda dt: self._on_error(gen, msg))

    def _on_payload(self, gen, payload):
        if gen != self._gen:
            return
        self._busy = False
        self._payload = payload
        if payload.get("group") is not None:
            self._group_data = payload["group"]
        app = App.get_running_app()
        friend = str(_cfg().get("friend", "")).strip()
        mine, theirs = app.tracker.check(payload.get("gid"), payload.get("game"), friend, payload.get("friend"))
        app.notify_unlocks(mine, None)
        app.notify_unlocks(theirs, friend)
        self._countdown = self._interval()
        self.status_text = tr("last_update", t=time.strftime("%H:%M:%S"))
        self.render_all()

    def _on_error(self, gen, msg):
        if gen != self._gen:
            return
        self._busy = False
        self._countdown = self._interval()
        self.status_text = tr("error", e=msg)

    # ---- rendering -------------------------------------------------------
    def render_all(self):
        p = self._payload
        if not p:
            return
        cfg = _cfg()
        hc = bool(cfg.get("hc_only"))
        s = p.get("summary") or {}
        game = p.get("game")
        noted = App.get_running_app().notes.ids()
        self.username = s.get("User") or str(cfg.get("user", ""))
        self.name_width = _name_width(self.username)
        pic = s.get("UserPic") or f"/UserPic/{self.username}.png"
        self.avatar_url = f"{MEDIA}{pic}"
        rank_txt = features.fmt_rank(s.get("Rank"), s.get("TotalRanked"), uitext.current_language())
        self.rank_line = ("#" + rank_txt) if rank_txt and rank_txt[0].isdigit() else rank_txt
        self.hc_line = f"{uitext.ICON_STAR} {fmt_int(s.get('TotalPoints', 0))} HardcorePoints"
        self.retro_line = f"{uitext.ICON_SPARK} {fmt_int(s.get('TotalTruePoints', 0))} RetroPoints"
        self.sc_line = f"{uitext.ICON_STAR_EMPTY} {fmt_int(s.get('TotalSoftcorePoints', 0))} SoftcorePoints"
        rp = s.get("RichPresenceMsg") or ""
        self.rich_presence = f"{uitext.ICON_PLAY} {rp}" if rp else ""
        desc_fn = cached_translation if cfg.get("translate") else None
        if game:
            self.current_game = game.get("Title") or "?"
            self.game_console = game.get("ConsoleName", "")
            icon = game.get("ImageIcon")
            self.game_icon_url = f"{MEDIA}{icon}" if icon else ""
            prog = features.progress_summary(game, hc)
            self.game_ratio = prog["ratio"]
            self.game_progress = tr("progress", d=prog["done"], t=prog["total"], gp=prog["got_pts"], tp=prog["tot_pts"], p=prog["pct"])
            self.hcsc_line = tr("hcsc", h=prog["n_hc"], s=prog["n_sc"])
            achs = features.achievements_of(game)
            self._ach_index = {str(a.get("ID")): a for a in achs}
            self._rows_all = features.achievement_rows(game, MEDIA, hc, cfg.get("sort", "disp_asc"), _labels(), desc_fn, noted)
            self._rows_all = _with_owned_by(self._rows_all, game, self._ach_index)
            if desc_fn:
                translate_async([a.get("Description", "") for a in achs], self._after_translation)
        else:
            self.current_game = tr("no_game")
            self.game_console = ""
            self.game_icon_url = ""
            self.game_progress = ""
            self.hcsc_line = ""
            self.game_ratio = 0
            self._rows_all = []
            self._ach_index = {}
        self.apply_filter()
        self.render_duel()
        self.render_group()

    def _after_translation(self):
        self.render_all()
        if TRANSLATOR.last_error:
            self.status_text = tr("tr_error", e=TRANSLATOR.last_error)

    def apply_filter(self):
        self.success_rows = features.filter_rows(self._rows_all, self.current_filter, bool(_cfg().get("miss_only")))

    def render_duel(self):
        p = self._payload
        if not p:
            return
        cfg = _cfg()
        friend = str(cfg.get("friend", "")).strip()
        user = (p.get("summary") or {}).get("User") or str(cfg.get("user", ""))
        game, fg = p.get("game"), p.get("friend")
        self.duel_detail = ""
        self.duel_rows = []
        if not friend:
            self.duel_title = tr("duel_empty")
        elif not game:
            self.duel_title = tr("no_game")
        elif fg is None:
            self.duel_title = tr("loading")
        elif fg.get("error"):
            self.duel_title = tr("error", e=fg["error"])
        else:
            desc_fn = cached_translation if cfg.get("translate") else None
            noted = App.get_running_app().notes.ids()
            d = features.compute_duel(game, fg, user, friend, MEDIA, bool(cfg.get("hc_only")), _labels(), desc_fn, noted)
            if d["x"] > d["y"]:
                self.duel_title = tr("duel_lead", n=user, d=d["x"] - d["y"])
            elif d["y"] > d["x"]:
                self.duel_title = tr("duel_lead", n=friend, d=d["y"] - d["x"])
            else:
                self.duel_title = tr("duel_tie", d=d["x"])
            self.duel_detail = f"{user} : {d['x']}/{d['tot']} • {d['pa']} pts      {friend} : {d['y']}/{d['tot']} • {d['pb']} pts"
            rows = d["rows"]
            for r in rows:
                r["side"] = r.pop("state")
            self.duel_rows = rows

    def render_group(self):
        p = self._payload
        cfg = _cfg()
        members = [m for m in cfg.get("group", []) if m]
        self.group_hint = "" if members else tr("g_empty")
        if not p:
            self.group_rows = []
            return
        s = p.get("summary") or {}
        user = s.get("User") or str(cfg.get("user", ""))
        my_pic = s.get("UserPic") or f"/UserPic/{user}.png"
        entries = features.group_entries(user, s, p.get("game"), my_pic, members, self._group_data, bool(cfg.get("hc_only")))
        self.group_rows = features.entry_rows(entries, MEDIA)

    # ---- actions from the UI --------------------------------------------
    def switch_tab(self, name):
        self.current_tab = name
        self.ids.tabs.current = name
        cfg = _cfg()
        cfg["tab"] = name
        save_cfg(cfg)
        if name == "group" and self._payload:
            members = [m for m in cfg.get("group", []) if m]
            if any(m.lower() not in self._group_data for m in members):
                self.refresh(force=True)
            else:
                self.render_group()

    def set_filter(self, name):
        self.current_filter = name
        cfg = _cfg()
        cfg["filter"] = name
        save_cfg(cfg)
        self.apply_filter()

    def toggle_miss(self):
        """'Missable' is an option that combines with the filters All / Locked / Unlocked."""
        cfg = _cfg()
        cfg["miss_only"] = not cfg.get("miss_only", False)
        save_cfg(cfg)
        self.miss_on = bool(cfg["miss_only"])
        self.apply_filter()

    def open_sort_menu(self):
        app = App.get_running_app()
        cur = _cfg().get("sort", "disp_asc")
        view = ModalView(size_hint=(0.9, None), height=min(dp(620), Window.height * 0.88), auto_dismiss=True,
                         background="", background_color=tuple(app.c_card))
        outer = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        outer.add_widget(TextLabel(text=f"{uitext.ICON_SORT}  {tr('sort_title')}", bold=True, color=tuple(app.c_accent)))
        scroll = ScrollView(do_scroll_x=False)
        box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        for sid in uitext.SORT_IDS:
            btn = FlatButton(text=tr("sort_" + sid), active=(sid == cur))
            btn.bind(on_release=lambda _b, s=sid: (view.dismiss(), self.set_sort(s)))
            box.add_widget(btn)
        scroll.add_widget(box)
        outer.add_widget(scroll)
        view.add_widget(outer)
        view.open()

    def set_sort(self, sid):
        cfg = _cfg()
        cfg["sort"] = sid
        save_cfg(cfg)
        self.render_all()

    def toggle_translate(self):
        cfg = _cfg()
        cfg["translate"] = not cfg.get("translate", False)
        save_cfg(cfg)
        self.translate_on = bool(cfg["translate"])
        if self.translate_on:
            _TRIED.clear()
        self.render_all()

    def toggle_hc(self):
        """Hardcore only / all unlocks counted (same switch as the one of the Windows version)."""
        cfg = _cfg()
        cfg["hc_only"] = not cfg.get("hc_only", False)
        save_cfg(cfg)
        self.hc_on = bool(cfg["hc_only"])
        self.render_all()
        self.status_text = tr("hc_on") if self.hc_on else tr("hc_off")

    def open_detail(self, ach_id):
        """Tap on an achievement: open its page (description, personal note, community comments)."""
        try:
            a = self._ach_index.get(str(ach_id))
            if not a:
                self.status_text = f"? {ach_id}"
                return
            self.manager.get_screen("detail").show(a, self.current_game)
            self._from_detail = True
            self.manager.current = "detail"
        except Exception as e:
            Logger.exception("RA: cannot open the achievement page")
            self.status_text = f"{e.__class__.__name__}: {e}"[:90]

    def set_friend(self, name):
        name = (name or "").strip()
        if not name:
            return
        cfg = _cfg()
        cfg["friend"] = name
        save_cfg(cfg)
        if self._payload:
            self._payload["friend"] = None
        self.render_duel()
        self.refresh(force=True)

    def clear_friend(self):
        cfg = _cfg()
        cfg["friend"] = ""
        save_cfg(cfg)
        self.friend_name = ""
        if self._payload:
            self._payload["friend"] = None
        self.render_duel()

    def add_member(self, name):
        name = (name or "").strip()
        cfg = _cfg()
        self.ids.member_input.text = ""
        low = [m.lower() for m in cfg.get("group", [])] + [str(cfg.get("user", "")).lower()]
        if not name or name.lower() in low:
            return
        cfg["group"].append(name)
        save_cfg(cfg)
        self.render_group()
        self.refresh(force=True)

    def remove_member(self, name):
        cfg = _cfg()
        cfg["group"] = [m for m in cfg.get("group", []) if m != name]
        save_cfg(cfg)
        self._group_data.pop(name.lower(), None)
        self.render_group()


# ---------------------------------------------------------------------------
# Achievement page: description, personal note and community comments
# ---------------------------------------------------------------------------
class DetailScreen(Screen):
    game_title = StringProperty("")
    badge_url = StringProperty("")
    ach_title = StringProperty("")
    ach_missable = StringProperty("")
    ach_desc = StringProperty("")
    ach_meta = StringProperty("")
    ach_earned = StringProperty("")
    earned = BooleanProperty(False)
    comments_title = StringProperty("")
    comments_info = StringProperty("")
    note_status = StringProperty("")
    translate_on = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self._gen = 0
        self._desc = ""
        self._items = []         # (CommentItem widget, original text)
        self._ach_id = ""
        self._note_loading = False
        self._note_ev = None

    def show(self, a, game_title=""):
        cfg = _cfg()
        self._gen += 1
        gen = self._gen
        self._items = []
        self.translate_on = bool(cfg.get("translate"))
        self.game_title = str(game_title or "")
        shown = not (cfg.get("hc_only") and not is_hc(a)) and is_any(a)
        name = a.get("BadgeName", "")
        self.badge_url = f"{MEDIA}/Badge/{name}{'' if shown else '_lock'}.png" if name else ""
        self.ach_title = str(a.get("Title", "") or "")
        self.ach_missable = f"{uitext.ICON_WARN} {tr('f_miss')}" if is_missable(a) else ""
        self._desc = str(a.get("Description", "") or "")
        self.ach_desc = self._desc
        self.ach_meta = tr("d_pts_line", p=a.get("Points", 0), r=a.get("TrueRatio", "?"))
        self.earned = bool(is_any(a))
        if self.earned:
            tag = tr("earned_hc") if is_hc(a) else tr("earned_sc")
            self.ach_earned = f"{uitext.ICON_CHECK} {fmt_date(date_of(a))} • {tag}"
        else:
            self.ach_earned = tr("d_not_earned")
        # personal note
        self._ach_id = str(a.get("ID", ""))
        self._note_loading = True
        self.note_status = ""
        if "note_input" in self.ids:
            self.ids.note_input.text = App.get_running_app().notes.get(self._ach_id)
        self._note_loading = False
        # community comments
        self.comments_title = uitext.ICON_CHAT + " " + tr("d_comments")
        self.comments_info = tr("d_loading")
        if "comments_box" in self.ids:
            self.ids.comments_box.clear_widgets()
        self._load_comments(gen, a.get("ID"))
        self._apply_translation(gen)
        if self.translate_on:
            translate_async([self._desc], lambda: self._apply_translation(gen))

    # ---- personal note: saved 0.9 s after the last key press, when the field loses focus and when leaving the page
    def note_changed(self):
        if self._note_loading:
            return
        self.note_status = ""
        if self._note_ev is not None:
            self._note_ev.cancel()
        self._note_ev = Clock.schedule_once(lambda dt: self.save_note(), 0.9)

    def note_focus(self, focused):
        if not focused:
            self.save_note()

    def save_note(self):
        if self._note_ev is not None:
            self._note_ev.cancel()
            self._note_ev = None
        if not self._ach_id or "note_input" not in self.ids:
            return
        store = App.get_running_app().notes
        if store.set(self._ach_id, self.ids.note_input.text):
            self.note_status = tr("d_note_saved") if not store.last_error else tr("err_save", e=store.last_error)

    # ---- comments
    def _load_comments(self, gen, ach_id):
        key = str(_cfg().get("key", "")).strip()

        def job():
            err = ""
            total, comments = 0, []
            try:
                total, comments = features.load_comments(call_api, key, ach_id)
            except Exception as e:
                err = friendly_error(e)
            Clock.schedule_once(lambda dt: self._show_comments(gen, total, comments, err))
        threading.Thread(target=job, daemon=True).start()

    def _show_comments(self, gen, total, comments, err):
        if gen != self._gen:
            return
        box = self.ids.comments_box
        box.clear_widgets()
        self._items = []
        if err:
            self.comments_info = tr("error", e=err)
            return
        if not comments:
            self.comments_info = tr("d_nocomments")
            return
        self.comments_info = tr("d_cinfo", n=len(comments), t=total)
        for c in comments:
            item = CommentItem(user_line=f"{c['user']}  •  {fmt_date(c['date'])}", body=c["text"])
            box.add_widget(item)
            self._items.append((item, c["text"]))
        if self.translate_on:
            self._translate_comments(gen)

    def _translate_comments(self, gen):
        self._apply_translation(gen)
        translate_async([t for _w, t in self._items], lambda: self._apply_translation(gen))

    def _apply_translation(self, gen):
        if gen != self._gen:
            return
        on = self.translate_on
        self.ach_desc = cached_translation(self._desc) if on else self._desc
        for w, orig in self._items:
            w.body = cached_translation(orig) if on else orig
        if on and TRANSLATOR.last_error:
            self.comments_info = tr("tr_error", e=TRANSLATOR.last_error)

    def toggle_translate(self):
        cfg = _cfg()
        cfg["translate"] = not cfg.get("translate", False)
        save_cfg(cfg)
        self.translate_on = bool(cfg["translate"])
        if self.translate_on:
            _TRIED.clear()
            translate_async([self._desc], lambda: self._apply_translation(self._gen))
            self._translate_comments(self._gen)
        else:
            self._apply_translation(self._gen)

    def go_back(self):
        self.save_note()
        self.manager.current = "profile"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
class SettingsScreen(Screen):
    username = StringProperty("")
    api_key = StringProperty("")
    notify_on = BooleanProperty(True)
    ui_lang_values = ListProperty([])
    tr_lang_values = ListProperty([])
    skin_values = ListProperty([])
    ui_lang_text = StringProperty("")
    tr_lang_text = StringProperty("")
    skin_text = StringProperty("")
    notes_msg = StringProperty("")
    update_msg = StringProperty("")
    update_url = StringProperty("")
    update_version = StringProperty("")
    data_info = StringProperty("")

    def on_enter(self):
        app = App.get_running_app()
        cfg = app.cfg
        auto = tr("s_auto")
        self.username = str(cfg.get("user", ""))
        self.api_key = str(cfg.get("key", ""))
        self.notify_on = bool(cfg.get("notify", True))
        self.ui_lang_values = [auto] + [n for _c, n in uitext.UI_LANGS]
        self.tr_lang_values = [auto] + [n for _c, n in uitext.TR_LANGS]
        self.skin_values = [s["name"] for s in app.skins]
        ui = cfg.get("ui_lang", "auto")
        lg = cfg.get("lang", "auto")
        self.ui_lang_text = auto if ui == "auto" else (uitext.lang_label(uitext.UI_LANGS, ui) or auto)
        self.tr_lang_text = auto if lg == "auto" else (uitext.lang_label(uitext.TR_LANGS, lg) or auto)
        self.skin_text = next((s["name"] for s in app.skins if s["id"] == cfg.get("skin", "default")), app.skins[0]["name"])
        self.notes_msg = ""
        self.data_info = f"{tr('s_data_dir')}: {app.user_data_dir}"

    # ---- update check: looks for an .apk in the GitHub releases of appinfo.UPDATE_REPO
    def check_update(self):
        if getattr(self, "_upd_busy", False):
            return
        self._upd_busy = True
        self.update_url = ""
        self.update_msg = tr("upd_checking")

        def job():
            url, version = "", ""
            try:
                ext = ".ipa" if kivy.utils.platform == "ios" else ".apk"
                res = updater.check(appinfo.UPDATE_REPO, appinfo.__version__, ext=ext)
                if res["status"] == "newer":
                    msg, url, version = tr("upd_available", v=res["version"]), res["url"], res["version"]
                elif res["status"] == "uptodate":
                    msg = tr("upd_uptodate", v=appinfo.__version__)
                else:
                    msg = tr("upd_noapk")
            except Exception as e:
                msg = tr("upd_error", e=updater.describe(e))
            Clock.schedule_once(lambda dt: self._update_done(msg, url, version))
        threading.Thread(target=job, daemon=True).start()

    def _update_done(self, msg, url, version):
        self._upd_busy = False
        self.update_msg, self.update_url, self.update_version = msg, url, version

    def download_update(self):
        """Opens the .apk address: the browser downloads it and Android offers to install it."""
        if self.update_url:
            App.get_running_app().open_url(self.update_url)

    def test_notification(self):
        notify.request_permission()
        if kivy.utils.platform == "ios":
            UnlockBanner(tr("toast"), tr("notif_test")).show()
        notify.send(tr("toast"), tr("notif_test"), 1, tr("notif_channel"), tr("notif_channel_desc"), delay=5)

    # ---- personal notes: export / import (same JSON format as the Windows version, so the file works on both)
    def export_notes(self):
        store = App.get_running_app().notes
        count = len(store.ids())
        if not count:
            self.notes_msg = tr("n_export_none")
            return
        androidutil.save_text("ra_companion_notes.json", store.export_text(), lambda status, info: self._after_export(status, info, count))

    def _after_export(self, status, info, count):
        if status == "ok":
            self.notes_msg = tr("n_export_ok", n=count)
        elif status == "error":
            self.notes_msg = tr("error", e=info)
        else:
            self.notes_msg = ""

    def import_notes(self):
        androidutil.read_text(self._after_import)

    def _after_import(self, status, text):
        if status == "cancel":
            return
        if status == "error":
            self.notes_msg = tr("error", e=text)
            return
        try:
            notes = features.parse_notes(text)
        except ValueError:
            self.notes_msg = tr("n_import_bad")
            return
        added, merged, unchanged = App.get_running_app().notes.merge(notes)
        self.notes_msg = tr("n_import_ok", a=added, m=merged, u=unchanged)
        self.manager.get_screen("profile").render_all()

    def save_settings(self, username, api_key, notify_on, ui_label, tr_label, skin_label):
        app = App.get_running_app()
        cfg = app.cfg
        old_account = (cfg.get("user"), cfg.get("key"))
        old_ui = cfg.get("ui_lang", "auto")
        cfg["user"] = username.strip()
        cfg["key"] = api_key.strip()
        cfg["notify"] = bool(notify_on)
        cfg["ui_lang"] = "auto" if ui_label == tr("s_auto") else uitext.lang_code(uitext.UI_LANGS, ui_label)
        cfg["lang"] = "auto" if tr_label == tr("s_auto") else uitext.lang_code(uitext.TR_LANGS, tr_label)
        app.set_skin(next((s["id"] for s in app.skins if s["name"] == skin_label), "default"))
        saved = save_cfg(cfg)
        if notify_on:
            notify.request_permission()
        account_changed = (cfg.get("user"), cfg.get("key")) != old_account
        if cfg["ui_lang"] != old_ui:
            app.apply_language()
            if account_changed:
                app.tracker.reset()
            app.rebuild_ui()
        else:
            if account_changed:
                self.manager.get_screen("profile").reset_game_state()
            self.manager.current = "profile"
        if not saved:
            app.root.get_screen("profile").status_text = tr("err_save", e=app.save_error)[:120]


# ---------------------------------------------------------------------------
# Game search
# ---------------------------------------------------------------------------
class SearchScreen(Screen):
    status = StringProperty("")
    results = ListProperty([])
    console_values = ListProperty([])
    all_label = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        self._search_ev = None
        self._indexing = False
        self._loading_consoles = False

    def _index(self):
        return App.get_running_app().games_index

    def on_enter(self):
        self.all_label = tr("se_all")
        self._fill_consoles()
        if not self._index().consoles_fresh():
            self._load_consoles()
        self.run_search()

    def _fill_consoles(self):
        self.console_values = [self.all_label] + [name for _cid, name in self._index().console_list()]

    def _load_consoles(self):
        key = str(_cfg().get("key", "")).strip()
        if self._loading_consoles or not key:
            return
        self._loading_consoles = True

        def job():
            msg = ""
            try:
                cons = call_api("API_GetConsoleIDs.php", key, a=1, g=1)
                if isinstance(cons, list):
                    self._index().set_consoles(cons)
            except Exception as e:
                msg = friendly_error(e)
            Clock.schedule_once(lambda dt: self._consoles_loaded(msg))
        threading.Thread(target=job, daemon=True).start()

    def _consoles_loaded(self, msg):
        self._loading_consoles = False
        if msg:
            self.status = msg
            return
        self._fill_consoles()
        self.run_search()

    def schedule_search(self):
        """Wait 0.3 s after the last key press before searching."""
        if self._search_ev is not None:
            self._search_ev.cancel()
        self._search_ev = Clock.schedule_once(lambda dt: self.run_search(), 0.3)

    def _selected_cids(self, label):
        consoles = self._index().console_list()
        for cid, name in consoles:
            if name == label:
                return [cid]
        return [cid for cid, _name in consoles]

    def run_search(self):
        if "query" not in self.ids:
            return
        query = self.ids.query.text
        cids = self._selected_cids(self.ids.console_spinner.text)
        idx = self._index()
        if len(norm(query.strip())) >= 2:
            missing = [c for c in cids if not idx.is_fresh(c)]
            if missing:
                self._index_missing(missing)
        self._show_results(idx.search(query, cids), query)

    def _show_results(self, found, query):
        self.results = [{
            "title": r["title"],
            "subtitle": (f"{r['console']} • " if r["console"] else "") + (tr("se_ach", n=r["count"]) if r["count"] else ""),
            "game_id": str(r["game_id"]),
        } for r in found]
        if self._indexing:
            return
        if found:
            self.status = tr("se_results", n=len(found))
        elif len(norm(query.strip())) >= 2:
            self.status = tr("se_none")
        else:
            self.status = ""

    def _index_missing(self, cids):
        key = str(_cfg().get("key", "")).strip()
        if self._indexing or not cids or not key:
            return
        self._indexing = True
        total = len(cids)

        def job():
            try:
                for i, cid in enumerate(cids, 1):
                    Clock.schedule_once(lambda dt, i=i: self._set_status(tr("se_index", i=i, n=total)))
                    try:
                        games = call_api("API_GetGameList.php", key, i=cid, f=1)
                        if isinstance(games, list):
                            self._index().set_games(cid, games)
                    except Exception:
                        pass
                    Clock.schedule_once(lambda dt: self._refresh_results())
                    time.sleep(0.25)
                self._index().save()
            finally:
                Clock.schedule_once(lambda dt: self._index_done())
        threading.Thread(target=job, daemon=True).start()

    def _set_status(self, text):
        self.status = text

    def _refresh_results(self):
        if "query" in self.ids:
            query = self.ids.query.text
            self._show_results(self._index().search(query, self._selected_cids(self.ids.console_spinner.text)), query)

    def _index_done(self):
        self._indexing = False
        self._refresh_results()

    def follow(self, game_id):
        cfg = _cfg()
        cfg["auto"] = False
        cfg["game_id"] = str(game_id)
        save_cfg(cfg)
        self.manager.get_screen("profile").reset_game_state()
        self.manager.current = "profile"

    def follow_auto(self):
        cfg = _cfg()
        cfg["auto"] = True
        cfg["game_id"] = ""
        save_cfg(cfg)
        self.manager.get_screen("profile").reset_game_state()
        self.manager.current = "profile"

    def go_back(self):
        self.manager.current = "profile"


Builder.load_file(os.path.join(BASE, "main.kv"))


class UnlockBanner(FloatLayout):
    """Small in-app banner shown at the top when an achievement unlocks while the app is open."""

    def __init__(self, title, text, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (Window.width - dp(24), dp(90))
        self.pos = (dp(12), Window.height - self.height - dp(60))
        with self.canvas.before:
            Color(0.05, 0.07, 0.12, 0.97)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._sync, size=self._sync)
        lbl = Label(markup=True,
                    text=f"[b]{title}[/b]\n{text}",
                    color=(0.96, 0.73, 0.26, 1),
                    font_size=sp(13),
                    halign="center",
                    valign="middle",
                    size_hint=(0.9, 0.8),
                    pos_hint={"center_x": 0.5, "center_y": 0.5})
        lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.add_widget(lbl)

    def _sync(self, *_args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def show(self, duration=4.0):
        Window.add_widget(self)
        Clock.schedule_once(lambda dt: self.dismiss(), duration)

    def dismiss(self, *_args):
        if self.parent:
            Window.remove_widget(self)

class RACompanionApp(App):
    title = "RA Companion"
    safe_left = NumericProperty(0)
    safe_top = NumericProperty(0)
    safe_right = NumericProperty(0)
    safe_bottom = NumericProperty(0)
    # Colors of the current skin (rgba). main.kv uses them as `app.c_card`... so a skin change is applied immediately everywhere.
    c_bg = ListProperty([0.059, 0.078, 0.125, 1])
    c_card = ListProperty([0.102, 0.129, 0.200, 1])
    c_alt = ListProperty([0.133, 0.173, 0.263, 1])
    c_locked = ListProperty([0.078, 0.102, 0.160, 1])
    c_press = ListProperty([0.220, 0.280, 0.420, 1])
    c_text = ListProperty([0.910, 0.925, 0.961, 1])
    c_muted = ListProperty([0.541, 0.580, 0.671, 1])
    c_accent = ListProperty([0.961, 0.725, 0.259, 1])
    c_on_accent = ListProperty([0.102, 0.075, 0, 1])
    c_success = ListProperty([0.239, 0.863, 0.592, 1])
    c_info = ListProperty([0.416, 0.690, 1, 1])
    c_warning = ListProperty([1, 0.624, 0.263, 1])
    c_danger = ListProperty([1, 0.420, 0.420, 1])
    info_hex = StringProperty("6ab0ff")
    github_color = ListProperty([1, 1, 1, 1])      # the GitHub logo is white: it is turned black on a light skin

    def build(self):
        self.settings_path = os.path.join(self.user_data_dir, "settings.json")
        self.save_error = ""
        self.cfg = self._load_settings()
        self.skins = themes.discover(os.path.join(BASE, "skins"))
        self.set_skin(self.cfg.get("skin", "default"))
        self.apply_language()
        self.tracker = features.UnlockTracker()
        self.games_index = features.GameIndex(os.path.join(self.user_data_dir, "games_index.json"))
        self.notes = features.NotesStore(os.path.join(self.user_data_dir, "notes.json"))
        TRANSLATOR.set_cache_file(os.path.join(self.user_data_dir, "translations.json"))
        self._bg_stop = None
        if os.path.exists(os.path.join(BASE, "icon.png")):
            self.icon = os.path.join(BASE, "icon.png")
        Logger.info("RA: data folder: %s", self.user_data_dir)
        cache_dir = os.path.join(self.user_data_dir, "img_cache")
        os.makedirs(cache_dir, exist_ok=True)
        try:
            files = os.listdir(cache_dir)
        except OSError as exc:
            files = []
            Logger.error("RA: cannot list cache dir: %r", exc)
        Logger.info("RA: img_cache=%s files=%d", cache_dir, len(files))
        sm = ScreenManager()
        for screen in self._make_screens():
            sm.add_widget(screen)
        Window.bind(on_keyboard=self._on_keyboard)
        def apply_safe_area(*_args):
            self.safe_left, self.safe_top, self.safe_right, self.safe_bottom = iosutil.safe_area()
            Logger.info("RA: safe area l=%s t=%s r=%s b=%s", self.safe_left, self.safe_top, self.safe_right, self.safe_bottom)
        Clock.schedule_once(apply_safe_area, 0)
        Window.bind(size=apply_safe_area)
        return sm

    def _load_settings(self):
        """Settings from the private folder. On the very first start, the old settings file of config.py is imported once."""
        data = storage.load_json(self.settings_path, None)
        first_start = not isinstance(data, dict)
        if first_start:
            data = {}
            try:
                from config import load_cfg as legacy_load
                legacy = legacy_load()
                if isinstance(legacy, dict):
                    data.update(legacy)
            except Exception:
                pass
        for k, v in CFG_DEFAULTS.items():
            data.setdefault(k, v if not isinstance(v, list) else list(v))
        if not isinstance(data["group"], list):
            data["group"] = []
        if first_start:
            storage.save_json(self.settings_path, data)
        return data

    def set_skin(self, skin_id):
        """Apply a skin (the same skin files as the Windows version). Colors are properties: the interface updates by itself."""
        entry = next((s for s in self.skins if s["id"] == skin_id), self.skins[0])
        pal = themes.palette(themes.read_skin(entry["path"]) if entry["path"] else {})
        for key, value in pal.items():
            if key == "info_hex":
                self.info_hex = value
            elif key != "muted_hex":
                setattr(self, "c_" + key, value)
        Window.clearcolor = pal["bg"]
        r, g, b = pal["bg"][:3]
        self.github_color = [0, 0, 0, 1] if 0.299 * r + 0.587 * g + 0.114 * b > 0.5 else [1, 1, 1, 1]
        self.cfg["skin"] = entry["id"]

    def _make_screens(self):
        return [ProfileScreen(name="profile"), DetailScreen(name="detail"),
                SettingsScreen(name="settings"), SearchScreen(name="search")]

    def apply_language(self):
        uitext.set_language(uitext.resolve_ui_language(self.cfg.get("ui_lang", "auto")))

    def rebuild_ui(self):
        """Recreate every screen so that all static texts (evaluated when a screen is created) use the new language."""
        sm = self.root
        if sm.has_screen("profile"):
            sm.get_screen("profile").on_leave()
        sm.clear_widgets()
        for screen in self._make_screens():
            sm.add_widget(screen)
        sm.current = "profile"

    def open_url(self, url):
        androidutil.open_url(url)

    def flush(self):
        """Write everything to disk (called whenever the app leaves the screen)."""
        try:
            self.root.get_screen("detail").save_note()
        except Exception:
            pass
        save_cfg(self.cfg)
        self.notes.save()

    def on_start(self):
        if self.cfg.get("notify", True):
            notify.request_permission()

    def on_stop(self):
        self.flush()

    # ---- notifications ---------------------------------------------------
    def notify_unlocks(self, items, who=None):
        """One notification per new achievement (at most 5, then a summary)."""
        if not items or not self.cfg.get("notify", True):
            return
        title = tr("f_toast", u=who) if who else tr("toast")
        channel = (tr("notif_channel"), tr("notif_channel_desc"))
        for a in items[:5]:
            text = f"{a.get('Title', '')} (+{a.get('Points', 0)})"
            if kivy.utils.platform == "ios":
                UnlockBanner(title, text).show()
            nid = zlib.crc32(f"{who}:{a.get('ID')}".encode()) & 0x7FFFFFFF
            notify.send(title, text, nid, *channel)
        if len(items) > 5:
            text = tr("more_unlocks", n=len(items) - 5)
            if kivy.utils.platform == "ios":
                UnlockBanner(title, text).show()
            nid = zlib.crc32(f"{who}:more".encode()) & 0x7FFFFFFF
            notify.send(title, text, nid, *channel)

    # ---- background polling while the app is paused -------------------------
    def _start_background_poll(self):
        if self._bg_stop is not None or not self.cfg.get("notify", True):
            return
        self._bg_stop = threading.Event()
        threading.Thread(target=self._bg_loop, args=(self._bg_stop,), daemon=True).start()

    def _stop_background_poll(self):
        if self._bg_stop is not None:
            self._bg_stop.set()
            self._bg_stop = None

    def _bg_loop(self, stop):
        """Best effort: Android may freeze the app after a while, then notifications arrive when it wakes up."""
        while not stop.wait(max(30, int(self.cfg.get("interval", 30) or 30))):
            try:
                self._bg_check()
            except Exception:
                pass

    def _bg_check(self):
        cfg = self.cfg
        user, key = str(cfg.get("user", "")).strip(), str(cfg.get("key", "")).strip()
        if not user or not key:
            return
        summary = call_api("API_GetUserSummary.php", key, u=user, g=1, a=0)
        forced = cfg.get("game_id") if (not cfg.get("auto", True) and cfg.get("game_id")) else None
        gid = forced or summary.get("LastGameID") or (summary.get("LastGame") or {}).get("ID")
        if not gid:
            return
        game = call_api("API_GetGameInfoAndUserProgress.php", key, u=user, g=gid)
        friend = str(cfg.get("friend", "")).strip()
        fgame = None
        if friend:
            try:
                fgame = call_api("API_GetGameInfoAndUserProgress.php", key, u=friend, g=gid)
            except Exception:
                fgame = None
        mine, theirs = self.tracker.check(gid, game, friend, fgame)
        self.notify_unlocks(mine, None)
        self.notify_unlocks(theirs, friend)

    # ---- Android lifecycle -----------------------------------------------
    def _on_keyboard(self, window, key, *args):
        """Android back button (key 27): go back to the main screen before leaving the app."""
        if key == 27 and self.root.current != "profile":
            if self.root.current == "detail":
                self.root.get_screen("detail").save_note()
            self.root.current = "profile"
            return True
        return False

    def on_pause(self):
        self.flush()
        self._start_background_poll()
        return True   # keep the app alive when it goes to the background

    def on_resume(self):
        self._stop_background_poll()
        if self.root.current == "profile":
            self.root.get_screen("profile").refresh()


if __name__ == "__main__":
    RACompanionApp().run()
