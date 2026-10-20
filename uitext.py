"""Language, symbols and text helpers shared by main.py and main.kv (translations come from mobile_i18n.py)."""

import locale
import os
import urllib.error

import i18n
from mobile_i18n import MOBILE

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Symbols of the buttons. They are plain text characters drawn by fonts/RASans.ttf (a copy of DejaVu Sans in which
# the 4 symbols that DejaVu lacks - globe, magnifier, trophy, group - were drawn; they live in the private-use area).
# ---------------------------------------------------------------------------
ICON_GLOBE = "\ue000"      # translation
ICON_SEARCH = "\ue001"     # game search
ICON_TROPHY = "\ue002"     # achievements tab
ICON_GROUP = "\ue003"      # group tab
ICON_SWORDS = "\u2694"     # duel tab
ICON_BOLT = "\u26a1"       # hardcore only
ICON_GEAR = "\u2699"       # settings
ICON_SORT = "\u21c5"       # sort order
ICON_WARN = "\u26a0"       # missable
ICON_NOTE = "\u270e"       # personal note
ICON_LOCK = "\ue005"      # locked achievement (drawn in fonts/RASans*.ttf)
ICON_CHECK = "\u2714"     # unlocked
ICON_CHAT = "\ue004"      # comments
ICON_REFRESH = "\u21bb"    # refresh
ICON_PLAY = "\u25b6"       # rich presence
ICON_STAR = "\u2605"       # hardcore points
ICON_SPARK = "\u2726"      # retro points
ICON_STAR_EMPTY = "\u2606"  # softcore points

# ---------------------------------------------------------------------------
# Texts added after mobile_i18n.py was written (same 6 languages).
# ---------------------------------------------------------------------------
SORT_IDS = ["unlocked_first", "disp_asc", "disp_desc", "awd_desc", "awd_asc", "pts_desc", "pts_asc",
            "title_asc", "title_desc", "type_asc", "type_desc"]
_SORT = {
    "en": ["Sort order", "Unlocked first", "Display order: first", "Display order: last", "Earned by most players", "Earned by fewest players",
           "Most points", "Fewest points", "Title A-Z", "Title Z-A", "Type ascending", "Type descending"],
    "fr": ["Ordre de tri", "Débloqués d'abord", "Ordre d'affichage (début)", "Ordre d'affichage (fin)", "Obtenu par le plus de joueurs", "Obtenu par le moins de joueurs",
           "Plus de points", "Moins de points", "Titre A-Z", "Titre Z-A", "Type croissant", "Type décroissant"],
    "es": ["Orden", "Desbloqueados primero", "Orden de visualización (inicio)", "Orden de visualización (final)", "Obtenido por más jugadores", "Obtenido por menos jugadores",
           "Más puntos", "Menos puntos", "Título A-Z", "Título Z-A", "Tipo ascendente", "Tipo descendente"],
    "de": ["Sortierung", "Freigeschaltete zuerst", "Anzeigereihenfolge (Anfang)", "Anzeigereihenfolge (Ende)", "Von den meisten erreicht", "Von den wenigsten erreicht",
           "Meiste Punkte", "Wenigste Punkte", "Titel A-Z", "Titel Z-A", "Typ aufsteigend", "Typ absteigend"],
    "it": ["Ordinamento", "Sbloccati prima", "Ordine di visualizzazione (inizio)", "Ordine di visualizzazione (fine)", "Ottenuto da più giocatori", "Ottenuto da meno giocatori",
           "Più punti", "Meno punti", "Titolo A-Z", "Titolo Z-A", "Tipo crescente", "Tipo decrescente"],
    "pt": ["Ordenação", "Desbloqueadas primeiro", "Ordem de exibição (início)", "Ordem de exibição (fim)", "Obtida por mais jogadores", "Obtida por menos jogadores",
           "Mais pontos", "Menos pontos", "Título A-Z", "Título Z-A", "Tipo ascendente", "Tipo descendente"],
}

_EXTRA_KEYS = ["hc_on", "hc_off", "hcsc", "d_note_title", "d_note_hint", "d_note_saved", "s_skin", "s_notes", "s_notes_export",
               "s_notes_import", "n_export_ok", "n_export_none", "n_import_ok", "n_import_bad", "err_save", "s_data_dir"]
_EXTRA = {
    "en": ["Hardcore only counted", "All achievements counted", "HC {h} • SC {s}", "My notes", "Write a note about this achievement…", "Saved ✓",
           "Skin", "Personal notes", "Export notes", "Import notes", "{n} notes exported ✓", "No notes to export.",
           "Imported: {a} added, {m} merged, {u} unchanged", "This file is not a notes file.", "Cannot save the data: {e}", "Data folder"],
    "fr": ["Hardcore uniquement", "Tous les succès comptés", "HC {h} • SC {s}", "Mes notes", "Écrivez une note sur ce succès…", "Enregistré ✓",
           "Skin (thème)", "Notes personnelles", "Exporter les notes", "Importer les notes", "{n} notes exportées ✓", "Aucune note à exporter.",
           "Importé : {a} ajoutées, {m} fusionnées, {u} inchangées", "Ce fichier n'est pas un fichier de notes.", "Impossible d'enregistrer les données : {e}", "Dossier des données"],
    "es": ["Solo hardcore", "Todos los logros cuentan", "HC {h} • SC {s}", "Mis notas", "Escribe una nota sobre este logro…", "Guardado ✓",
           "Skin (tema)", "Notas personales", "Exportar notas", "Importar notas", "{n} notas exportadas ✓", "No hay notas para exportar.",
           "Importado: {a} añadidas, {m} combinadas, {u} sin cambios", "Este archivo no es un archivo de notas.", "No se pueden guardar los datos: {e}", "Carpeta de datos"],
    "de": ["Nur Hardcore zählt", "Alle Erfolge zählen", "HC {h} • SC {s}", "Meine Notizen", "Schreibe eine Notiz zu diesem Erfolg…", "Gespeichert ✓",
           "Skin (Design)", "Persönliche Notizen", "Notizen exportieren", "Notizen importieren", "{n} Notizen exportiert ✓", "Keine Notizen zum Exportieren.",
           "Importiert: {a} neu, {m} zusammengeführt, {u} unverändert", "Diese Datei ist keine Notizdatei.", "Daten konnten nicht gespeichert werden: {e}", "Datenordner"],
    "it": ["Solo hardcore", "Tutti gli obiettivi contano", "HC {h} • SC {s}", "Le mie note", "Scrivi una nota su questo obiettivo…", "Salvato ✓",
           "Skin (tema)", "Note personali", "Esporta note", "Importa note", "{n} note esportate ✓", "Nessuna nota da esportare.",
           "Importato: {a} aggiunte, {m} unite, {u} invariate", "Questo file non è un file di note.", "Impossibile salvare i dati: {e}", "Cartella dei dati"],
    "pt": ["Apenas hardcore", "Todas as conquistas contam", "HC {h} • SC {s}", "As minhas notas", "Escreva uma nota sobre esta conquista…", "Guardado ✓",
           "Skin (tema)", "Notas pessoais", "Exportar notas", "Importar notas", "{n} notas exportadas ✓", "Nenhuma nota para exportar.",
           "Importado: {a} adicionadas, {m} combinadas, {u} inalteradas", "Este ficheiro não é um ficheiro de notas.", "Não foi possível guardar os dados: {e}", "Pasta de dados"],
}
_TR_ERR = {
    "en": "Translation unavailable ({e})", "fr": "Traduction indisponible ({e})", "es": "Traducción no disponible ({e})",
    "de": "Übersetzung nicht verfügbar ({e})", "it": "Traduzione non disponibile ({e})", "pt": "Tradução indisponível ({e})",
}
_UPD_KEYS = ['s_version', 's_update_check', 's_update_get', 'upd_checking', 'upd_uptodate', 'upd_available', 'upd_noapk', 'upd_error']
_UPD = {'en': ['Version {v}', 'Check for updates', 'Download version {v}', 'Checking…', 'You are up to date (version {v})', 'Version {v} is available', 'No APK found in the GitHub releases', 'Update check failed ({e})'], 'fr': ['Version {v}', 'Rechercher une mise à jour', 'Télécharger la version {v}', 'Recherche en cours…', 'Vous êtes à jour (version {v})', 'La version {v} est disponible', 'Aucun APK trouvé dans les releases GitHub', 'Échec de la recherche ({e})'], 'es': ['Versión {v}', 'Buscar actualizaciones', 'Descargar la versión {v}', 'Buscando…', 'Estás al día (versión {v})', 'La versión {v} está disponible', 'No se encontró ningún APK en las releases de GitHub', 'Error al buscar actualizaciones ({e})'], 'de': ['Version {v}', 'Nach Updates suchen', 'Version {v} herunterladen', 'Suche läuft…', 'Du bist auf dem neuesten Stand (Version {v})', 'Version {v} ist verfügbar', 'Kein APK in den GitHub-Releases gefunden', 'Update-Suche fehlgeschlagen ({e})'], 'it': ['Versione {v}', 'Cerca aggiornamenti', 'Scarica la versione {v}', 'Ricerca in corso…', 'Sei aggiornato (versione {v})', 'La versione {v} è disponibile', 'Nessun APK trovato nelle release di GitHub', 'Ricerca non riuscita ({e})'], 'pt': ['Versão {v}', 'Procurar atualizações', 'Transferir a versão {v}', 'A procurar…', 'Está atualizado (versão {v})', 'A versão {v} está disponível', 'Nenhum APK encontrado nas releases do GitHub', 'Falha ao procurar atualizações ({e})']}
_OWN = {'en': 'owned by {p}% of players', 'fr': 'obtenu par {p}% des joueurs', 'es': 'conseguido por el {p}% de los jugadores', 'de': 'von {p}% der Spieler erreicht', 'it': 'ottenuto dal {p}% dei giocatori', 'pt': 'obtida por {p}% dos jogadores'}
for _lang, _values in _EXTRA.items():
    MOBILE[_lang].update(dict(zip(_EXTRA_KEYS, _values)))
    MOBILE[_lang]["sort_title"] = _SORT[_lang][0]
    MOBILE[_lang]["owned_by"] = _OWN[_lang]
    MOBILE[_lang].update(dict(zip(_UPD_KEYS, _UPD[_lang])))
    MOBILE[_lang]["tr_error"] = _TR_ERR[_lang]
    for _sid, _label in zip(SORT_IDS, _SORT[_lang][1:]):
        MOBILE[_lang]["sort_" + _sid] = _label

# Links of the settings page (config.py can override them with the same names as the desktop version)
try:
    import config as _config
except Exception:
    _config = None
SITE_URL = getattr(_config, "SITE_URL", "https://retroachievements.org")
REPO_URL = getattr(_config, "REPO_URL", "https://github.com/PsickOSSH/RA-Companion")
LOGO_URLS = getattr(_config, "LOGO_URLS", {
    "github": "https://github.githubassets.com/favicons/favicon-dark.png",
    "ra": "https://commons.wikimedia.org/wiki/Special:FilePath/RetroAchievements_logo_square_color.png?width=64",
})
API_KEY_URL = "https://retroachievements.org/settings?tab=applications"
LOGO_GITHUB = LOGO_URLS.get("github", "")
LOGO_RA = LOGO_URLS.get("ra", "")

UI_LANGS = [("fr", "Français"), ("en", "English"), ("es", "Español"), ("de", "Deutsch"), ("it", "Italiano"), ("pt", "Português")]
# Languages offered for the translation of descriptions and comments (Latin and Cyrillic scripts only: the app font has no CJK glyphs)
TR_LANGS = UI_LANGS + [("nl", "Nederlands"), ("pl", "Polski"), ("ru", "Русский")]

_current = "en"


def system_language():
    """Two-letter language code of the device (Android locale through pyjnius, system locale on a PC)."""
    try:
        from jnius import autoclass
        return str(autoclass("java.util.Locale").getDefault().getLanguage()).lower()[:2]
    except Exception:
        pass
    name = None
    try:
        if os.name == "nt":
            import ctypes
            name = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage())
        else:
            name = locale.getlocale()[0] or os.environ.get("LC_ALL") or os.environ.get("LANG")
    except Exception:
        pass
    return (name or "en")[:2].lower()


def resolve_ui_language(setting):
    """Settings value ('auto' or a code) -> a supported interface language code."""
    code = system_language() if setting in (None, "", "auto") else setting
    return code if code in MOBILE else "en"


def translation_language(setting):
    """Settings value ('auto' or a code) -> target language code of the translation."""
    codes = [c for c, _n in TR_LANGS]
    code = system_language() if setting in (None, "", "auto") else setting
    return code if code in codes else "en"


def set_language(code):
    global _current
    _current = code if code in MOBILE else "en"
    try:
        i18n.set_language(_current)   # keeps the date formats of utils.fmt_date in the same language
    except Exception:
        pass
    return _current


def current_language():
    return _current


def tr(key, **kw):
    """Text of `key` in the current language (falls back to English, then to the desktop translations, then to the key)."""
    text = MOBILE.get(_current, {}).get(key) or MOBILE["en"].get(key)
    if text is None:
        try:
            text = i18n.T(key)
        except Exception:
            text = key
    try:
        return text.format(**kw) if kw else text
    except (KeyError, IndexError, ValueError):
        return text


def miss_tag():
    """Orange tag shown on missable achievements."""
    return f"{ICON_WARN} {tr('f_miss')}"


def lang_label(langs, code):
    for c, name in langs:
        if c == code:
            return name
    return ""


def lang_code(langs, label, default="auto"):
    for c, name in langs:
        if name == label:
            return c
    return default


def friendly_error(e):
    """Short, readable message for a network / API error."""
    if isinstance(e, urllib.error.HTTPError):
        if e.code in (401, 403):
            return tr("err_key")
        if e.code == 429:
            return tr("err_rate")
        return tr("err_server", c=e.code)
    if isinstance(e, (urllib.error.URLError, TimeoutError, OSError)):
        return tr("err_net")
    return str(e)[:80] or e.__class__.__name__
