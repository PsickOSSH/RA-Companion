"""Internationalization: UI translations, language detection, sort-menu labels.

To add a UI language, add a block to I18N (copy the "en" block) and an entry to UI_LANGS and REFRESH_LABELS."""

import os


LANGS = {"Français": "fr", "English": "en", "Español": "es", "Deutsch": "de", "Italiano": "it",
         "Português": "pt", "Nederlands": "nl", "Polski": "pl", "Русский": "ru", "日本語": "ja", "中文": "zh-CN"}


UI_LANGS = {"Français": "fr", "English": "en", "Español": "es", "Deutsch": "de", "Italiano": "it", "Português": "pt"}


REFRESH_LABELS = {"fr": "Actualiser", "en": "Refresh", "es": "Actualizar", "de": "Aktualisieren",
                  "it": "Aggiorna", "pt": "Atualizar"}


SORT_IDS = ["unlocked_first", "disp_asc", "disp_desc", "awd_desc", "awd_asc", "pts_desc", "pts_asc",
            "title_asc", "title_desc", "type_asc", "type_desc"]


SORT_ICONS = {"unlocked_first": "🔓", "disp_asc": "↓1", "disp_desc": "↑1", "awd_desc": "👥", "awd_asc": "👥", "pts_desc": "🏅",
              "pts_asc": "🏅", "title_asc": "A↓", "title_desc": "Z↓", "type_asc": "🏷", "type_desc": "🏷"}


SORT_LABELS = {
 "fr": ["Ordre de tri", "Débloqué d'abord", "Ordre d'affichage (premier)", "Ordre d'affichage (dernier)", "Obtenu par (le plus)",
        "Obtenu par (le moins)", "Points (le plus)", "Points (le moins)", "Titre (A-Z)", "Titre (Z-A)",
        "Type (ascendant)", "Type (descendant)"],
 "en": ["Sort order", "Unlocked first", "Display order (first)", "Display order (last)", "Earned by (most)", "Earned by (least)",
        "Points (most)", "Points (least)", "Title (A-Z)", "Title (Z-A)", "Type (ascending)", "Type (descending)"],
 "es": ["Orden", "Desbloqueados primero", "Orden de visualización (primero)", "Orden de visualización (último)", "Obtenido por (más)",
        "Obtenido por (menos)", "Puntos (más)", "Puntos (menos)", "Título (A-Z)", "Título (Z-A)",
        "Tipo (ascendente)", "Tipo (descendente)"],
 "de": ["Sortierung", "Freigeschaltete zuerst", "Anzeigereihenfolge (erste zuerst)", "Anzeigereihenfolge (letzte zuerst)",
        "Erreicht von (meiste)", "Erreicht von (wenigste)", "Punkte (meiste)", "Punkte (wenigste)",
        "Titel (A-Z)", "Titel (Z-A)", "Typ (aufsteigend)", "Typ (absteigend)"],
 "it": ["Ordinamento", "Sbloccati prima", "Ordine di visualizzazione (primo)", "Ordine di visualizzazione (ultimo)",
        "Ottenuto da (più)", "Ottenuto da (meno)", "Punti (più)", "Punti (meno)", "Titolo (A-Z)",
        "Titolo (Z-A)", "Tipo (crescente)", "Tipo (decrescente)"],
 "pt": ["Ordenação", "Desbloqueadas primeiro", "Ordem de exibição (primeiro)", "Ordem de exibição (último)", "Obtida por (mais)",
        "Obtida por (menos)", "Pontos (mais)", "Pontos (menos)", "Título (A-Z)", "Título (Z-A)",
        "Tipo (ascendente)", "Tipo (descendente)"],
}


def sort_label(sid=None):
    """Return the localized label of a sort mode (or the menu title when `sid` is None)."""
    labels = SORT_LABELS.get(CUR, SORT_LABELS["en"])
    return labels[0] if sid is None else labels[1 + SORT_IDS.index(sid)]


COMMON = {"g_playing": "▶ {g}", "hcsc": "HC {h}  •  SC {s}"}


I18N = {
"en": {
 "no_game": "No game detected", "f_all": "All", "f_todo": "Locked", "f_done": "Unlocked", "f_miss": "Missable", "updating": "Updating…",
 "last_update": "Last update {t}", "error": "Error: {e}",
 "progress": "{d}/{t} achievements  •  {gp}/{tp} pts  •  {p} %", "nothing": "Nothing to show here",
 "earned_hc": "HARDCORE", "earned_sc": "SOFTCORE", "owned_by": " • earned by {p} % of players",
 "sc_only": "softcore only (not counted)",
 "toast": "🏆 Achievement unlocked!", "plus_pts": "+{n} points", "f_toast": "👤 {u} unlocked an achievement!",
 "s_title": "Settings", "s_user": "RetroAchievements username", "s_key": "API key",
 "s_opacity": "Window opacity (%)",
 "s_trlang": "Translation language",
 "s_uilang": "Software language", "s_skin": "Skin (theme)",
 "s_uisys": "Auto (system)", "save": "Save",
 "comments": "💬 Comments", "loading": "Loading…", "no_comments": "No comments for this achievement.",
 "c_info": "{n} comment(s) shown out of {t} • newest first", "translating": "Translating…",
 "tr_btn": "🌐 Translate ({l})", "orig": "Show original", "pts_line": "{p} pts • {r} RetroPoints",
 "ach_default": "Achievement",
 "tab_ach": "🏆 Achievements", "tab_duel": "⚔ Duel", "tab_group": "👥 Group",
 "tip_settings": "Settings", "tip_search": "Find a game by name", "tip_pin": "Keep the window on top of other windows",
 "tip_tr": "Translate descriptions and comments", "tip_hc_off": "Shows only achievements earned in hardcore",
 "tip_hc_on": "Shows achievements earned in both hardcore and softcore",
 "duel_user": "Friend's username", "duel_go": "Compare", "duel_stop": "✕ Stop",
 "duel_empty": "Enter a friend's username to compare progress on this game.",
 "duel_lead": "{n} leads by {d} achievement(s)", "duel_tie": "Tied at {d} achievement(s)", "duel_me": "You",
 "g_user": "Add a player", "g_add": "Add", "g_empty": "No players yet. Add usernames above to follow them together.",
 "g_on_game": "{d}/{t} on this game",
 "note_title": "📝 My notes", "note_saved": "Saved ✔",
 "se_title": "Find a game", "se_console": "Console", "se_all": "All consoles", "se_name": "Game name or ID",
 "se_follow": "Track this game", "se_auto": "↺ Last played game", "se_index": "Indexing {i}/{n}…",
 "se_results": "{n} result(s)", "se_none": "No game found.", "se_ach": "{n} achievements"},
"fr": {
 "no_game": "Aucun jeu détecté", "f_all": "Tous", "f_todo": "À débloquer", "f_done": "Débloqués", "f_miss": "Manquable", "updating": "Mise à jour…",
 "last_update": "Dernière MAJ {t}", "error": "Erreur : {e}",
 "progress": "{d}/{t} succès  •  {gp}/{tp} pts  •  {p} %", "nothing": "Rien à afficher ici",
 "earned_hc": "HARDCORE", "earned_sc": "SOFTCORE", "owned_by": " • obtenu par {p} % des joueurs",
 "sc_only": "softcore uniquement (non compté)",
 "toast": "🏆 Succès débloqué !", "plus_pts": "+{n} points", "f_toast": "👤 {u} a débloqué un succès !",
 "s_title": "Réglages", "s_user": "Pseudo RetroAchievements", "s_key": "Clé API",
 "s_opacity": "Opacité de la fenêtre (%)",
 "s_trlang": "Langue de traduction",
 "s_uilang": "Langue du logiciel", "s_skin": "Skin (thème)",
 "s_uisys": "Auto (système)", "save": "Enregistrer",
 "comments": "💬 Commentaires", "loading": "Chargement…", "no_comments": "Aucun commentaire pour ce succès.",
 "c_info": "{n} commentaire(s) affiché(s) sur {t} • plus récents d'abord", "translating": "Traduction en cours…",
 "tr_btn": "🌐 Traduire ({l})", "orig": "Voir l'original", "pts_line": "{p} pts • {r} RetroPoints",
 "ach_default": "Succès",
 "tab_ach": "🏆 Succès", "tab_duel": "⚔ Duel", "tab_group": "👥 Groupe",
 "tip_settings": "Réglages", "tip_search": "Chercher un jeu par son nom", "tip_pin": "Garder la fenêtre au-dessus des autres",
 "tip_tr": "Traduire les descriptions et les commentaires", "tip_hc_off": "Affiche uniquement les succès fait en hardcore",
 "tip_hc_on": "Affiche les succès fait en hardcore et en softcore",
 "duel_user": "Pseudo de l'ami", "duel_go": "Comparer", "duel_stop": "✕ Arrêter",
 "duel_empty": "Saisissez le pseudo d'un ami pour comparer vos progrès sur ce jeu.",
 "duel_lead": "{n} est en avance de {d} succès", "duel_tie": "Égalité à {d} succès", "duel_me": "Vous",
 "g_user": "Ajouter un joueur", "g_add": "Ajouter", "g_empty": "Aucun joueur pour l'instant. Ajoutez des pseudos pour les suivre ensemble.",
 "g_on_game": "{d}/{t} sur ce jeu",
 "note_title": "📝 Mes notes", "note_saved": "Enregistré ✔",
 "se_title": "Rechercher un jeu", "se_console": "Console", "se_all": "Toutes les consoles", "se_name": "Nom ou ID du jeu",
 "se_follow": "Suivre ce jeu", "se_auto": "↺ Dernier jeu joué", "se_index": "Indexation {i}/{n}…",
 "se_results": "{n} résultat(s)", "se_none": "Aucun jeu trouvé.", "se_ach": "{n} succès"},
"es": {
 "no_game": "Ningún juego detectado", "f_all": "Todos", "f_todo": "Por desbloquear", "f_done": "Desbloqueados", "f_miss": "Perdible", "updating": "Actualizando…",
 "last_update": "Última act. {t}", "error": "Error: {e}",
 "progress": "{d}/{t} logros  •  {gp}/{tp} pts  •  {p} %", "nothing": "Nada que mostrar aquí",
 "earned_hc": "HARDCORE", "earned_sc": "SOFTCORE", "owned_by": " • conseguido por el {p} % de los jugadores",
 "sc_only": "solo softcore (no cuenta)",
 "toast": "🏆 ¡Logro desbloqueado!", "plus_pts": "+{n} puntos", "f_toast": "👤 ¡{u} ha desbloqueado un logro!",
 "s_title": "Ajustes", "s_user": "Usuario de RetroAchievements", "s_key": "Clave API",
 "s_opacity": "Opacidad de la ventana (%)",
 "s_trlang": "Idioma de traducción",
 "s_uilang": "Idioma del programa", "s_skin": "Skin (tema)",
 "s_uisys": "Auto (sistema)", "save": "Guardar",
 "comments": "💬 Comentarios", "loading": "Cargando…", "no_comments": "Sin comentarios para este logro.",
 "c_info": "{n} comentario(s) mostrado(s) de {t} • más recientes primero", "translating": "Traduciendo…",
 "tr_btn": "🌐 Traducir ({l})", "orig": "Ver original", "pts_line": "{p} pts • {r} RetroPoints",
 "ach_default": "Logro",
 "tab_ach": "🏆 Logros", "tab_duel": "⚔ Duelo", "tab_group": "👥 Grupo",
 "tip_settings": "Ajustes", "tip_search": "Buscar un juego por nombre", "tip_pin": "Mantener la ventana encima de las demás",
 "tip_tr": "Traducir descripciones y comentarios", "tip_hc_off": "Muestra solo los logros obtenidos en hardcore",
 "tip_hc_on": "Muestra los logros obtenidos en hardcore y en softcore",
 "duel_user": "Usuario del amigo", "duel_go": "Comparar", "duel_stop": "✕ Detener",
 "duel_empty": "Introduce el usuario de un amigo para comparar vuestro progreso en este juego.",
 "duel_lead": "{n} va por delante por {d} logro(s)", "duel_tie": "Empate a {d} logro(s)", "duel_me": "Tú",
 "g_user": "Añadir un jugador", "g_add": "Añadir", "g_empty": "Aún no hay jugadores. Añade usuarios para seguirlos juntos.",
 "g_on_game": "{d}/{t} en este juego",
 "note_title": "📝 Mis notas", "note_saved": "Guardado ✔",
 "se_title": "Buscar un juego", "se_console": "Consola", "se_all": "Todas las consolas", "se_name": "Nombre o ID del juego",
 "se_follow": "Seguir este juego", "se_auto": "↺ Último juego jugado", "se_index": "Indexando {i}/{n}…",
 "se_results": "{n} resultado(s)", "se_none": "Ningún juego encontrado.", "se_ach": "{n} logros"},
"de": {
 "no_game": "Kein Spiel erkannt", "f_all": "Alle", "f_todo": "Gesperrt", "f_done": "Freigeschaltet", "f_miss": "Verpassbar", "updating": "Aktualisiere…",
 "last_update": "Zuletzt {t}", "error": "Fehler: {e}",
 "progress": "{d}/{t} Erfolge  •  {gp}/{tp} Pkt.  •  {p} %", "nothing": "Hier gibt es nichts anzuzeigen",
 "earned_hc": "HARDCORE", "earned_sc": "SOFTCORE", "owned_by": " • von {p} % der Spieler erreicht",
 "sc_only": "nur Softcore (zählt nicht)",
 "toast": "🏆 Erfolg freigeschaltet!", "plus_pts": "+{n} Punkte", "f_toast": "👤 {u} hat einen Erfolg freigeschaltet!",
 "s_title": "Einstellungen", "s_user": "RetroAchievements-Benutzername", "s_key": "API-Schlüssel",
 "s_opacity": "Fenstertransparenz (%)",
 "s_trlang": "Übersetzungssprache",
 "s_uilang": "Sprache der Software", "s_skin": "Skin (Design)",
 "s_uisys": "Auto (System)", "save": "Speichern",
 "comments": "💬 Kommentare", "loading": "Lädt…", "no_comments": "Keine Kommentare zu diesem Erfolg.",
 "c_info": "{n} Kommentar(e) von {t} angezeigt • neueste zuerst", "translating": "Übersetze…",
 "tr_btn": "🌐 Übersetzen ({l})", "orig": "Original anzeigen", "pts_line": "{p} Pkt. • {r} RetroPoints",
 "ach_default": "Erfolg",
 "tab_ach": "🏆 Erfolge", "tab_duel": "⚔ Duell", "tab_group": "👥 Gruppe",
 "tip_settings": "Einstellungen", "tip_search": "Spiel nach Namen suchen", "tip_pin": "Fenster immer im Vordergrund halten",
 "tip_tr": "Beschreibungen und Kommentare übersetzen", "tip_hc_off": "Zeigt nur die im Hardcore-Modus erreichten Erfolge",
 "tip_hc_on": "Zeigt die im Hardcore- und im Softcore-Modus erreichten Erfolge",
 "duel_user": "Benutzername des Freundes", "duel_go": "Vergleichen", "duel_stop": "✕ Beenden",
 "duel_empty": "Gib den Benutzernamen eines Freundes ein, um den Fortschritt in diesem Spiel zu vergleichen.",
 "duel_lead": "{n} führt mit {d} Erfolg(en)", "duel_tie": "Gleichstand bei {d} Erfolg(en)", "duel_me": "Du",
 "g_user": "Spieler hinzufügen", "g_add": "Hinzufügen", "g_empty": "Noch keine Spieler. Füge Benutzernamen hinzu, um sie gemeinsam zu verfolgen.",
 "g_on_game": "{d}/{t} in diesem Spiel",
 "note_title": "📝 Meine Notizen", "note_saved": "Gespeichert ✔",
 "se_title": "Spiel suchen", "se_console": "Konsole", "se_all": "Alle Konsolen", "se_name": "Spielname oder ID",
 "se_follow": "Dieses Spiel verfolgen", "se_auto": "↺ Zuletzt gespieltes Spiel", "se_index": "Indexiere {i}/{n}…",
 "se_results": "{n} Ergebnis(se)", "se_none": "Kein Spiel gefunden.", "se_ach": "{n} Erfolge"},
"it": {
 "no_game": "Nessun gioco rilevato", "f_all": "Tutti", "f_todo": "Da sbloccare", "f_done": "Sbloccati", "f_miss": "Mancabile", "updating": "Aggiornamento…",
 "last_update": "Ultimo agg. {t}", "error": "Errore: {e}",
 "progress": "{d}/{t} obiettivi  •  {gp}/{tp} pt  •  {p} %", "nothing": "Niente da mostrare qui",
 "earned_hc": "HARDCORE", "earned_sc": "SOFTCORE", "owned_by": " • ottenuto dal {p} % dei giocatori",
 "sc_only": "solo softcore (non conta)",
 "toast": "🏆 Obiettivo sbloccato!", "plus_pts": "+{n} punti", "f_toast": "👤 {u} ha sbloccato un obiettivo!",
 "s_title": "Impostazioni", "s_user": "Nome utente RetroAchievements", "s_key": "Chiave API",
 "s_opacity": "Opacità della finestra (%)",
 "s_trlang": "Lingua di traduzione",
 "s_uilang": "Lingua del software", "s_skin": "Skin (tema)",
 "s_uisys": "Auto (sistema)", "save": "Salva",
 "comments": "💬 Commenti", "loading": "Caricamento…", "no_comments": "Nessun commento per questo obiettivo.",
 "c_info": "{n} commento/i mostrato/i su {t} • più recenti prima", "translating": "Traduzione in corso…",
 "tr_btn": "🌐 Traduci ({l})", "orig": "Mostra originale", "pts_line": "{p} pt • {r} RetroPoints",
 "ach_default": "Obiettivo",
 "tab_ach": "🏆 Obiettivi", "tab_duel": "⚔ Sfida", "tab_group": "👥 Gruppo",
 "tip_settings": "Impostazioni", "tip_search": "Cerca un gioco per nome", "tip_pin": "Mantieni la finestra sopra le altre",
 "tip_tr": "Traduci descrizioni e commenti", "tip_hc_off": "Mostra solo gli obiettivi ottenuti in hardcore",
 "tip_hc_on": "Mostra gli obiettivi ottenuti in hardcore e in softcore",
 "duel_user": "Nome utente dell'amico", "duel_go": "Confronta", "duel_stop": "✕ Interrompi",
 "duel_empty": "Inserisci il nome utente di un amico per confrontare i progressi in questo gioco.",
 "duel_lead": "{n} è avanti di {d} obiettivo/i", "duel_tie": "Parità a {d} obiettivo/i", "duel_me": "Tu",
 "g_user": "Aggiungi un giocatore", "g_add": "Aggiungi", "g_empty": "Ancora nessun giocatore. Aggiungi nomi utente per seguirli insieme.",
 "g_on_game": "{d}/{t} in questo gioco",
 "note_title": "📝 Le mie note", "note_saved": "Salvato ✔",
 "se_title": "Cerca un gioco", "se_console": "Console", "se_all": "Tutte le console", "se_name": "Nome o ID del gioco",
 "se_follow": "Segui questo gioco", "se_auto": "↺ Ultimo gioco giocato", "se_index": "Indicizzazione {i}/{n}…",
 "se_results": "{n} risultato/i", "se_none": "Nessun gioco trovato.", "se_ach": "{n} obiettivi"},
"pt": {
 "no_game": "Nenhum jogo detectado", "f_all": "Todas", "f_todo": "Por desbloquear", "f_done": "Desbloqueadas", "f_miss": "Perdível", "updating": "A atualizar…",
 "last_update": "Última atualização {t}", "error": "Erro: {e}",
 "progress": "{d}/{t} conquistas  •  {gp}/{tp} pts  •  {p} %", "nothing": "Nada para mostrar aqui",
 "earned_hc": "HARDCORE", "earned_sc": "SOFTCORE", "owned_by": " • obtida por {p} % dos jogadores",
 "sc_only": "apenas softcore (não conta)",
 "toast": "🏆 Conquista desbloqueada!", "plus_pts": "+{n} pontos", "f_toast": "👤 {u} desbloqueou uma conquista!",
 "s_title": "Definições", "s_user": "Utilizador RetroAchievements", "s_key": "Chave API",
 "s_opacity": "Opacidade da janela (%)",
 "s_trlang": "Idioma de tradução",
 "s_uilang": "Idioma do programa", "s_skin": "Skin (tema)",
 "s_uisys": "Auto (sistema)", "save": "Guardar",
 "comments": "💬 Comentários", "loading": "A carregar…", "no_comments": "Sem comentários nesta conquista.",
 "c_info": "{n} comentário(s) mostrado(s) de {t} • mais recentes primeiro", "translating": "A traduzir…",
 "tr_btn": "🌐 Traduzir ({l})", "orig": "Ver original", "pts_line": "{p} pts • {r} RetroPoints",
 "ach_default": "Conquista",
 "tab_ach": "🏆 Conquistas", "tab_duel": "⚔ Duelo", "tab_group": "👥 Grupo",
 "tip_settings": "Definições", "tip_search": "Procurar um jogo pelo nome", "tip_pin": "Manter a janela por cima das outras",
 "tip_tr": "Traduzir descrições e comentários", "tip_hc_off": "Mostra apenas as conquistas obtidas em hardcore",
 "tip_hc_on": "Mostra as conquistas obtidas em hardcore e em softcore",
 "duel_user": "Utilizador do amigo", "duel_go": "Comparar", "duel_stop": "✕ Parar",
 "duel_empty": "Introduza o utilizador de um amigo para comparar o progresso neste jogo.",
 "duel_lead": "{n} está à frente por {d} conquista(s)", "duel_tie": "Empate a {d} conquista(s)", "duel_me": "Tu",
 "g_user": "Adicionar um jogador", "g_add": "Adicionar", "g_empty": "Ainda sem jogadores. Adicione utilizadores para os acompanhar em conjunto.",
 "g_on_game": "{d}/{t} neste jogo",
 "note_title": "📝 As minhas notas", "note_saved": "Guardado ✔",
 "se_title": "Procurar um jogo", "se_console": "Consola", "se_all": "Todas as consolas", "se_name": "Nome ou ID do jogo",
 "se_follow": "Acompanhar este jogo", "se_auto": "↺ Último jogo jogado", "se_index": "A indexar {i}/{n}…",
 "se_results": "{n} resultado(s)", "se_none": "Nenhum jogo encontrado.", "se_ach": "{n} conquistas"},
}


for _l in I18N: I18N[_l].update(COMMON)


# Current UI language code; read it as `i18n.CUR` from other modules and change it with set_language().
CUR = "en"


def set_language(code):
    """Set the language used by T() and by the date/sort helpers."""
    global CUR
    CUR = code


def T(key, **kw):
    """Translate a UI string key into the current language, formatting it with `kw` when given."""
    s = I18N.get(CUR, {}).get(key) or I18N["en"].get(key, key)
    return s.format(**kw) if kw else s


def system_lang():
    """Return the two-letter language code of the operating system (falls back to 'en')."""
    name = ""
    try:
        import locale
        if os.name == "nt":
            import ctypes
            name = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "")
        else:
            name = locale.getlocale()[0] or os.environ.get("LANG", "")
    except Exception:
        pass
    return (name or "en")[:2].lower()


def resolve_ui(code):
    """Turn a configured UI language ('auto' or a code) into a language that actually has translations."""
    if code == "auto":
        code = system_lang()
    return code if code in I18N else "en"


def tr_lang(cfg):
    """Return the target language for content translation ('auto' follows the system language)."""
    if cfg.get("lang", "auto") != "auto":
        return cfg["lang"]
    sl = system_lang()
    return "zh-CN" if sl == "zh" else sl if sl in LANGS.values() else "en"
