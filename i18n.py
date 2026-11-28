"""Internationalization: UI translations, language detection, sort-menu labels.

To add a UI language, add a block to I18N (copy the "en" block) and an entry to UI_LANGS and REFRESH_LABELS."""

import os

from symbols import sym


LANGS = {"Français": "fr", "English": "en", "Español": "es", "Deutsch": "de", "Italiano": "it",
         "Português": "pt", "Nederlands": "nl", "Polski": "pl", "Русский": "ru", "日本語": "ja", "中文": "zh-CN"}


UI_LANGS = {"Français": "fr", "English": "en", "Español": "es", "Deutsch": "de", "Italiano": "it", "Português": "pt"}


REFRESH_LABELS = {"fr": "Actualiser", "en": "Refresh", "es": "Actualizar", "de": "Aktualisieren",
                  "it": "Aggiorna", "pt": "Atualizar"}


SORT_IDS = ["unlocked_first", "disp_asc", "disp_desc", "awd_desc", "awd_asc", "pts_desc", "pts_asc",
            "title_asc", "title_desc", "type_asc", "type_desc", "med_asc", "med_desc"]


SORT_ICONS = {"unlocked_first": "🔓", "disp_asc": "↓1", "disp_desc": "↑1", "awd_desc": "👥", "awd_asc": "👥", "pts_desc": "🏅",
              "pts_asc": "🏅", "title_asc": "A↓", "title_desc": "Z↓", "type_asc": "🏷", "type_desc": "🏷",
              "med_asc": "⏱", "med_desc": "⏱"}
SORT_ICONS = {k: sym(v) for k, v in SORT_ICONS.items()}


SORT_LABELS = {
 "fr": ["Ordre de tri", "Débloqué d'abord", "Ordre d'affichage (premier)", "Ordre d'affichage (dernier)", "Obtenu par (le plus)",
        "Obtenu par (le moins)", "Points (le plus)", "Points (le moins)", "Titre (A-Z)", "Titre (Z-A)",
        "Type (ascendant)", "Type (descendant)",
        "Médiane hardcore (la plus courte)", "Médiane hardcore (la plus longue)"],
 "en": ["Sort order", "Unlocked first", "Display order (first)", "Display order (last)", "Earned by (most)", "Earned by (least)",
        "Points (most)", "Points (least)", "Title (A-Z)", "Title (Z-A)", "Type (ascending)", "Type (descending)",
        "Hardcore median (shortest)", "Hardcore median (longest)"],
 "es": ["Orden", "Desbloqueados primero", "Orden de visualización (primero)", "Orden de visualización (último)", "Obtenido por (más)",
        "Obtenido por (menos)", "Puntos (más)", "Puntos (menos)", "Título (A-Z)", "Título (Z-A)",
        "Tipo (ascendente)", "Tipo (descendente)",
        "Mediana hardcore (la más corta)", "Mediana hardcore (la más larga)"],
 "de": ["Sortierung", "Freigeschaltete zuerst", "Anzeigereihenfolge (erste zuerst)", "Anzeigereihenfolge (letzte zuerst)",
        "Erreicht von (meiste)", "Erreicht von (wenigste)", "Punkte (meiste)", "Punkte (wenigste)",
        "Titel (A-Z)", "Titel (Z-A)", "Typ (aufsteigend)", "Typ (absteigend)",
        "Hardcore-Median (kürzester)", "Hardcore-Median (längster)"],
 "it": ["Ordinamento", "Sbloccati prima", "Ordine di visualizzazione (primo)", "Ordine di visualizzazione (ultimo)",
        "Ottenuto da (più)", "Ottenuto da (meno)", "Punti (più)", "Punti (meno)", "Titolo (A-Z)",
        "Titolo (Z-A)", "Tipo (crescente)", "Tipo (decrescente)",
        "Mediana hardcore (la più breve)", "Mediana hardcore (la più lunga)"],
 "pt": ["Ordenação", "Desbloqueadas primeiro", "Ordem de exibição (primeiro)", "Ordem de exibição (último)", "Obtida por (mais)",
        "Obtida por (menos)", "Pontos (mais)", "Pontos (menos)", "Título (A-Z)", "Título (Z-A)",
        "Tipo (ascendente)", "Tipo (descendente)",
        "Mediana hardcore (a mais curta)", "Mediana hardcore (a mais longa)"],
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


# Texts shared with the mobile app (uitext.py copies them): time to 100 %, search tabs, session summary
SHARED_KEYS = ["t100", "se_tab_search", "se_tab_recent", "se_tab_want", "se_loading", "se_recent_none", "se_want_none",
               "se_progress", "session", "session_title", "se_filter", "s_skin_import", "s_skin_ok", "s_skin_bad", "s_skin_hint",
               "s_skin_custom", "btn_import", "btn_export", "btn_delete", "btn_cancel", "s_skin_export_btn", "s_skin_delete_btn",
               "s_skin_pick_export", "s_skin_pick_delete", "s_skin_all", "s_skin_none", "s_skin_confirm_n", "s_skins_imported",
               "s_skins_exported", "s_skins_copied", "s_skins_deleted", "s_params", "s_params_warn", "s_params_replace",
               "s_params_exported", "s_params_copied", "s_params_imported", "s_params_bad", "s_params_hint",
               "n_delete_pick", "n_delete_confirm", "n_deleted", "n_none", "s_params_reset", "s_params_all", "s_params_keep",
               "s_params_reset_done", "s_all_warn", "s_all_replace", "s_all_exported", "s_all_copied",
               "s_all_imported", "s_all_bad", "s_all_reset", "s_all_deleted", "n_copied"]
_SHARED = {
    "en": ["Average time to 100%: ≈ {t}", "Search", "Recent", "Want to play", "Loading…", "No recently played game.",
           "Your \"Want to Play\" list is empty.", "{d}/{t} achievements", "Session: {n} unlocked • +{p} pts • {t}",
           "Unlocked this session", "Search in this list", "Import a skin…",
           "Skin \"{n}\" imported. Save to apply it.", "This is not a skin file (no valid color found).",
           "Android: choose a skin file (.py). iPhone: copy the content of the file first, then tap the button.", "My skin",
           "Import", "Export", "Delete", "Cancel", "Export skins…", "Delete skins…",
           "Choose the skins to export", "Choose the skins to delete", "Select all", "No imported skin.",
           "Delete {n} skin(s)?\n{names}", "{n} skins imported. Choose one and save.",
           "{n} skin(s) exported.", "{n} skin(s) copied to the clipboard.", "{n} skin(s) deleted.",
           "Settings", "The file contains your RetroAchievements API key and your translation keys, in plain text. Do not share it.",
           "Replace your settings with the ones of this file? Your skins and notes do not change.", "Settings exported.",
           "Settings copied to the clipboard.", "Settings imported.", "This is not a settings file.",
           "Android: choose the settings file (.json). iPhone: export copies to the clipboard; to import, copy the content of the file first.",
           "Choose the notes to delete", "Delete {n} note(s)?", "{n} note(s) deleted.", "No personal note.",
           "Reset the settings to their default values?\n\n• Everything: as after a first installation, account and API key included.\n• Keep account: only your username and API key stay; friend, group, translation keys and options are reset.\n\nYour skins, theme and notes do not change.",
           "Everything", "Keep account", "Settings reset.",
           "The file contains everything: settings (with your RetroAchievements API key and translation keys in plain text), theme, imported skins and notes. Do not share it.",
           "Import this backup?\n\n• Your settings and theme are replaced.\n• Its skins are added (a skin with the same name is replaced).\n• Its notes are merged with yours: nothing is lost.",
           "Everything exported.", "Everything copied to the clipboard.", "Imported: settings, {s} skin(s), notes: {a} added, {m} merged.",
           "This is not a complete backup file.",
           "Delete everything?\n\nAll your settings (account and API key included) and your theme go back to default, and your imported skins and personal notes are deleted for good. Export everything first if you want to keep them.",
           "Everything has been deleted.", "{n} notes copied to the clipboard."],
    "fr": ["Temps moyen pour le 100\u00a0%\u00a0: ≈\u00a0{t}", "Rechercher", "Récents", "À jouer", "Chargement…", "Aucun jeu joué récemment.",
           "Votre liste « Want to Play » est vide.", "{d}/{t} succès", "Session : {n} succès • +{p} pts • {t}",
           "Succès de la session", "Rechercher dans la liste", "Importer un skin…",
           "Skin « {n} » importé. Enregistrez pour l'appliquer.", "Ce n'est pas un fichier de skin (aucune couleur valide).",
           "Android : choisissez un fichier de skin (.py). iPhone : copiez d'abord le contenu du fichier, puis touchez le bouton.",
           "Mon skin", "Importer", "Exporter", "Supprimer", "Annuler", "Exporter des skins…", "Supprimer des skins…",
           "Choisissez les skins à exporter", "Choisissez les skins à supprimer", "Tout sélectionner", "Aucun skin importé.",
           "Supprimer {n} skin(s) ?\n{names}", "{n} skins importés. Choisissez-en un et enregistrez.",
           "{n} skin(s) exporté(s).", "{n} skin(s) copié(s) dans le presse-papiers.", "{n} skin(s) supprimé(s).",
           "Paramètres", "Le fichier contient votre clé API RetroAchievements et vos clés de traduction, en clair. Ne le partagez pas.",
           "Remplacer vos paramètres par ceux de ce fichier ? Vos skins et vos notes ne changent pas.", "Paramètres exportés.",
           "Paramètres copiés dans le presse-papiers.", "Paramètres importés.", "Ce n'est pas un fichier de paramètres.",
           "Android : choisissez le fichier de paramètres (.json). iPhone : l'export copie dans le presse-papiers ; pour importer, copiez d'abord le contenu du fichier.",
           "Choisissez les notes à supprimer", "Supprimer {n} note(s) ?", "{n} note(s) supprimée(s).", "Aucune note personnelle.",
           "Remettre les paramètres à leurs valeurs par défaut ?\n\n• Tout : comme après une première installation, compte et clé API compris.\n• Garder le compte : seuls votre pseudo et votre clé API restent ; ami, groupe, clés de traduction et options sont réinitialisés.\n\nVos skins, votre thème et vos notes ne changent pas.",
           "Tout", "Garder le compte", "Paramètres réinitialisés.",
           "Le fichier contient tout : les paramètres (dont votre clé API RetroAchievements et vos clés de traduction en clair), le thème, les skins importés et les notes. Ne le partagez pas.",
           "Importer cette sauvegarde ?\n\n• Vos paramètres et votre thème sont remplacés.\n• Ses skins sont ajoutés (un skin du même nom est remplacé).\n• Ses notes sont fusionnées avec les vôtres : rien n'est perdu.",
           "Tout a été exporté.", "Tout a été copié dans le presse-papiers.", "Importé : paramètres, {s} skin(s), notes : {a} ajoutées, {m} fusionnées.",
           "Ce n'est pas un fichier de sauvegarde complète.",
           "Tout supprimer ?\n\nTous vos paramètres (compte et clé API compris) et votre thème reviennent par défaut, et vos skins importés et vos notes sont supprimés définitivement. Exportez tout d'abord si vous voulez les garder.",
           "Tout a été supprimé.", "{n} notes copiées dans le presse-papiers."],
    "es": ["Tiempo medio para el 100 %: ≈ {t}", "Buscar", "Recientes", "Por jugar", "Cargando…", "Ningún juego jugado recientemente.",
           "Tu lista «Want to Play» está vacía.", "{d}/{t} logros", "Sesión: {n} logros • +{p} pts • {t}",
           "Logros de la sesión", "Buscar en la lista", "Importar un skin…",
           "Skin «{n}» importado. Guarda para aplicarlo.", "No es un archivo de skin (ningún color válido).",
           "Android: elige un archivo de skin (.py). iPhone: copia primero el contenido del archivo y toca el botón.", "Mi skin",
           "Importar", "Exportar", "Eliminar", "Cancelar", "Exportar skins…", "Eliminar skins…",
           "Elige los skins que exportar", "Elige los skins que eliminar", "Seleccionar todo", "Ningún skin importado.",
           "¿Eliminar {n} skin(s)?\n{names}", "{n} skins importados. Elige uno y guarda.",
           "{n} skin(s) exportado(s).", "{n} skin(s) copiado(s) al portapapeles.", "{n} skin(s) eliminado(s).",
           "Ajustes", "El archivo contiene tu clave API de RetroAchievements y tus claves de traducción, en texto sin cifrar. No lo compartas.",
           "¿Reemplazar tus ajustes por los de este archivo? Tus skins y notas no cambian.", "Ajustes exportados.",
           "Ajustes copiados al portapapeles.", "Ajustes importados.", "No es un archivo de ajustes.",
           "Android: elige el archivo de ajustes (.json). iPhone: exportar copia al portapapeles; para importar, copia primero el contenido del archivo.",
           "Elige las notas que eliminar", "¿Eliminar {n} nota(s)?", "{n} nota(s) eliminada(s).", "Ninguna nota personal.",
           "¿Restablecer los ajustes a sus valores por defecto?\n\n• Todo: como tras una primera instalación, cuenta y clave API incluidas.\n• Conservar la cuenta: solo se mantienen tu usuario y tu clave API; amigo, grupo, claves de traducción y opciones se restablecen.\n\nTus skins, tu tema y tus notas no cambian.",
           "Todo", "Conservar la cuenta", "Ajustes restablecidos.",
           "El archivo lo contiene todo: los ajustes (con tu clave API de RetroAchievements y tus claves de traducción sin cifrar), el tema, los skins importados y las notas. No lo compartas.",
           "¿Importar esta copia de seguridad?\n\n• Tus ajustes y tu tema se reemplazan.\n• Sus skins se añaden (un skin con el mismo nombre se reemplaza).\n• Sus notas se combinan con las tuyas: no se pierde nada.",
           "Todo exportado.", "Todo copiado al portapapeles.", "Importado: ajustes, {s} skin(s), notas: {a} añadidas, {m} combinadas.",
           "No es un archivo de copia de seguridad completa.",
           "¿Eliminar todo?\n\nTodos tus ajustes (cuenta y clave API incluidas) y tu tema vuelven a los valores por defecto, y tus skins importados y tus notas se eliminan definitivamente. Exporta todo antes si quieres conservarlos.",
           "Todo se ha eliminado.", "{n} notas copiadas al portapapeles."],
    "de": ["Durchschnittliche Zeit bis 100 %: ≈ {t}", "Suchen", "Zuletzt", "Wunschliste", "Wird geladen…",
           "Kein zuletzt gespieltes Spiel.", "Deine „Want to Play“-Liste ist leer.", "{d}/{t} Erfolge",
           "Sitzung: {n} Erfolge • +{p} Pkt • {t}", "In dieser Sitzung freigeschaltet", "In der Liste suchen",
           "Skin importieren…", "Skin „{n}“ importiert. Zum Anwenden speichern.", "Keine Skin-Datei (keine gültige Farbe gefunden).",
           "Android: wähle eine Skin-Datei (.py). iPhone: kopiere zuerst den Inhalt der Datei und tippe dann auf die Schaltfläche.",
           "Mein Skin", "Importieren", "Exportieren", "Löschen", "Abbrechen", "Skins exportieren…", "Skins löschen…",
           "Skins zum Exportieren wählen", "Skins zum Löschen wählen", "Alle auswählen", "Kein importierter Skin.",
           "{n} Skin(s) löschen?\n{names}", "{n} Skins importiert. Wähle einen aus und speichere.",
           "{n} Skin(s) exportiert.", "{n} Skin(s) in die Zwischenablage kopiert.", "{n} Skin(s) gelöscht.",
           "Einstellungen", "Die Datei enthält deinen RetroAchievements-API-Schlüssel und deine Übersetzungsschlüssel im Klartext. Teile sie nicht.",
           "Deine Einstellungen durch die dieser Datei ersetzen? Skins und Notizen bleiben unverändert.", "Einstellungen exportiert.",
           "Einstellungen in die Zwischenablage kopiert.", "Einstellungen importiert.", "Das ist keine Einstellungsdatei.",
           "Android: wähle die Einstellungsdatei (.json). iPhone: Export kopiert in die Zwischenablage; zum Importieren zuerst den Dateiinhalt kopieren.",
           "Notizen zum Löschen wählen", "{n} Notiz(en) löschen?", "{n} Notiz(en) gelöscht.", "Keine persönliche Notiz.",
           "Einstellungen auf die Standardwerte zurücksetzen?\n\n• Alles: wie nach der ersten Installation, Konto und API-Schlüssel eingeschlossen.\n• Konto behalten: nur Benutzername und API-Schlüssel bleiben; Freund, Gruppe, Übersetzungsschlüssel und Optionen werden zurückgesetzt.\n\nSkins, Design und Notizen bleiben unverändert.",
           "Alles", "Konto behalten", "Einstellungen zurückgesetzt.",
           "Die Datei enthält alles: Einstellungen (mit deinem RetroAchievements-API-Schlüssel und den Übersetzungsschlüsseln im Klartext), Design, importierte Skins und Notizen. Teile sie nicht.",
           "Diese Sicherung importieren?\n\n• Einstellungen und Design werden ersetzt.\n• Ihre Skins werden hinzugefügt (ein Skin mit gleichem Namen wird ersetzt).\n• Ihre Notizen werden mit deinen zusammengeführt: nichts geht verloren.",
           "Alles exportiert.", "Alles in die Zwischenablage kopiert.", "Importiert: Einstellungen, {s} Skin(s), Notizen: {a} neu, {m} zusammengeführt.",
           "Das ist keine vollständige Sicherungsdatei.",
           "Alles löschen?\n\nAlle Einstellungen (Konto und API-Schlüssel eingeschlossen) und das Design werden zurückgesetzt, importierte Skins und Notizen werden endgültig gelöscht. Exportiere zuerst alles, wenn du sie behalten willst.",
           "Alles wurde gelöscht.", "{n} Notizen in die Zwischenablage kopiert."],
    "it": ["Tempo medio per il 100%: ≈ {t}", "Cerca", "Recenti", "Da giocare", "Caricamento…", "Nessun gioco giocato di recente.",
           "La tua lista «Want to Play» è vuota.", "{d}/{t} obiettivi", "Sessione: {n} obiettivi • +{p} pt • {t}",
           "Obiettivi della sessione", "Cerca nell'elenco", "Importa uno skin…",
           "Skin «{n}» importato. Salva per applicarlo.", "Non è un file di skin (nessun colore valido).",
           "Android: scegli un file di skin (.py). iPhone: copia prima il contenuto del file, poi tocca il pulsante.", "Il mio skin",
           "Importa", "Esporta", "Elimina", "Annulla", "Esporta skin…", "Elimina skin…",
           "Scegli gli skin da esportare", "Scegli gli skin da eliminare", "Seleziona tutto", "Nessuno skin importato.",
           "Eliminare {n} skin?\n{names}", "{n} skin importati. Scegline uno e salva.",
           "{n} skin esportati.", "{n} skin copiati negli appunti.", "{n} skin eliminati.",
           "Impostazioni", "Il file contiene la tua chiave API di RetroAchievements e le chiavi di traduzione, in chiaro. Non condividerlo.",
           "Sostituire le tue impostazioni con quelle di questo file? Skin e note non cambiano.", "Impostazioni esportate.",
           "Impostazioni copiate negli appunti.", "Impostazioni importate.", "Non è un file di impostazioni.",
           "Android: scegli il file delle impostazioni (.json). iPhone: l'esportazione copia negli appunti; per importare, copia prima il contenuto del file.",
           "Scegli le note da eliminare", "Eliminare {n} note?", "{n} note eliminate.", "Nessuna nota personale.",
           "Ripristinare le impostazioni predefinite?\n\n• Tutto: come dopo la prima installazione, account e chiave API compresi.\n• Mantieni l'account: restano solo nome utente e chiave API; amico, gruppo, chiavi di traduzione e opzioni vengono ripristinati.\n\nSkin, tema e note non cambiano.",
           "Tutto", "Mantieni l'account", "Impostazioni ripristinate.",
           "Il file contiene tutto: le impostazioni (con la tua chiave API di RetroAchievements e le chiavi di traduzione in chiaro), il tema, gli skin importati e le note. Non condividerlo.",
           "Importare questo backup?\n\n• Impostazioni e tema vengono sostituiti.\n• I suoi skin vengono aggiunti (uno skin con lo stesso nome viene sostituito).\n• Le sue note vengono unite alle tue: nulla va perso.",
           "Tutto esportato.", "Tutto copiato negli appunti.", "Importato: impostazioni, {s} skin, note: {a} aggiunte, {m} unite.",
           "Non è un file di backup completo.",
           "Eliminare tutto?\n\nTutte le impostazioni (account e chiave API compresi) e il tema tornano predefiniti, gli skin importati e le note vengono eliminati definitivamente. Esporta prima tutto se vuoi conservarli.",
           "È stato eliminato tutto.", "{n} note copiate negli appunti."],
    "pt": ["Tempo médio para os 100%: ≈ {t}", "Procurar", "Recentes", "Por jogar", "A carregar…", "Nenhum jogo jogado recentemente.",
           "A sua lista «Want to Play» está vazia.", "{d}/{t} conquistas", "Sessão: {n} conquistas • +{p} pts • {t}",
           "Conquistas da sessão", "Procurar na lista", "Importar um skin…",
           "Skin «{n}» importado. Guarde para o aplicar.", "Não é um ficheiro de skin (nenhuma cor válida).",
           "Android: escolha um ficheiro de skin (.py). iPhone: copie primeiro o conteúdo do ficheiro e toque no botão.",
           "O meu skin", "Importar", "Exportar", "Eliminar", "Cancelar", "Exportar skins…", "Eliminar skins…",
           "Escolha os skins a exportar", "Escolha os skins a eliminar", "Selecionar tudo", "Nenhum skin importado.",
           "Eliminar {n} skin(s)?\n{names}", "{n} skins importados. Escolha um e guarde.",
           "{n} skin(s) exportado(s).", "{n} skin(s) copiado(s) para a área de transferência.", "{n} skin(s) eliminado(s).",
           "Definições", "O ficheiro contém a sua chave API do RetroAchievements e as chaves de tradução, em texto simples. Não o partilhe.",
           "Substituir as suas definições pelas deste ficheiro? Os skins e as notas não mudam.", "Definições exportadas.",
           "Definições copiadas para a área de transferência.", "Definições importadas.", "Não é um ficheiro de definições.",
           "Android: escolha o ficheiro de definições (.json). iPhone: a exportação copia para a área de transferência; para importar, copie primeiro o conteúdo.",
           "Escolha as notas a eliminar", "Eliminar {n} nota(s)?", "{n} nota(s) eliminada(s).", "Nenhuma nota pessoal.",
           "Repor as definições para os valores predefinidos?\n\n• Tudo: como após a primeira instalação, conta e chave API incluídas.\n• Manter a conta: só o utilizador e a chave API se mantêm; amigo, grupo, chaves de tradução e opções são repostos.\n\nOs skins, o tema e as notas não mudam.",
           "Tudo", "Manter a conta", "Definições repostas.",
           "O ficheiro contém tudo: as definições (com a sua chave API do RetroAchievements e as chaves de tradução em texto simples), o tema, os skins importados e as notas. Não o partilhe.",
           "Importar esta cópia de segurança?\n\n• As definições e o tema são substituídos.\n• Os skins são adicionados (um skin com o mesmo nome é substituído).\n• As notas são combinadas com as suas: nada se perde.",
           "Tudo exportado.", "Tudo copiado para a área de transferência.", "Importado: definições, {s} skin(s), notas: {a} adicionadas, {m} combinadas.",
           "Não é um ficheiro de cópia de segurança completa.",
           "Eliminar tudo?\n\nTodas as definições (conta e chave API incluídas) e o tema voltam ao predefinido, e os skins importados e as notas são eliminados definitivamente. Exporte tudo primeiro se os quiser guardar.",
           "Tudo foi eliminado.", "{n} notas copiadas para a área de transferência."],
}
for _l, _values in _SHARED.items():
    I18N[_l].update(zip(SHARED_KEYS, _values))


# Current UI language code; read it as `i18n.CUR` from other modules and change it with set_language().
CUR = "en"


def set_language(code):
    """Set the language used by T() and by the date/sort helpers."""
    global CUR
    CUR = code


def T(key, **kw):
    """Translate a UI string key into the current language, formatting it with `kw` when given."""
    s = I18N.get(CUR, {}).get(key) or I18N["en"].get(key, key)
    return sym(s.format(**kw) if kw else s)             # (Linux: the emoji are replaced by plain symbols)


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
