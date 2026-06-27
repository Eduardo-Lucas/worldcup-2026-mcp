"""
Streamlit Dashboard - FIFA World Cup 2026
"""

import asyncio
import sys
import os

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.server import (
    _fetch_data,
    _calcular_standings,
    _build_resolver,
    _resolver_nome,
    _format_brt,
    _encerrado,
    _placar,
    recent_matches,
    upcoming_matches,
    group_standings,
    search_team,
    all_groups,
    cup_statistics,
)

st.set_page_config(
    page_title="World Cup 2026",
    page_icon="⚽",
    layout="wide",
)

# ─────────────────────────────────────────────
# Translations
# ─────────────────────────────────────────────

TEAM_NAMES_PT = {
    "Algeria": "Argélia",
    "Argentina": "Argentina",
    "Australia": "Austrália",
    "Austria": "Áustria",
    "Belgium": "Bélgica",
    "Bosnia & Herzegovina": "Bósnia e Herzegovina",
    "Brazil": "Brasil",
    "Canada": "Canadá",
    "Cape Verde": "Cabo Verde",
    "Colombia": "Colômbia",
    "Croatia": "Croácia",
    "Curaçao": "Curaçao",
    "Czech Republic": "República Tcheca",
    "DR Congo": "Congo RD",
    "Ecuador": "Equador",
    "Egypt": "Egito",
    "England": "Inglaterra",
    "France": "França",
    "Germany": "Alemanha",
    "Ghana": "Gana",
    "Haiti": "Haiti",
    "Iran": "Irã",
    "Iraq": "Iraque",
    "Ivory Coast": "Costa do Marfim",
    "Japan": "Japão",
    "Jordan": "Jordânia",
    "Mexico": "México",
    "Morocco": "Marrocos",
    "Netherlands": "Países Baixos",
    "New Zealand": "Nova Zelândia",
    "Norway": "Noruega",
    "Panama": "Panamá",
    "Paraguay": "Paraguai",
    "Portugal": "Portugal",
    "Qatar": "Catar",
    "Saudi Arabia": "Arábia Saudita",
    "Scotland": "Escócia",
    "Senegal": "Senegal",
    "South Africa": "África do Sul",
    "South Korea": "Coreia do Sul",
    "Spain": "Espanha",
    "Sweden": "Suécia",
    "Switzerland": "Suíça",
    "Tunisia": "Tunísia",
    "Turkey": "Turquia",
    "USA": "EUA",
    "Uruguay": "Uruguai",
    "Uzbekistan": "Uzbequistão",
}


def localize_team(name: str) -> str:
    """Translates a team name to the current language (PT only; EN keeps original)."""
    if st.session_state.get("lang") != "pt":
        return name
    # Handle "TeamName (3º)" suffix from placeholder resolver
    suffix = ""
    base = name
    if " (" in name:
        base, rest = name.split(" (", 1)
        suffix = f" ({rest}"
    return TEAM_NAMES_PT.get(base, base) + suffix


TRANSLATIONS = {
    "en": {
        "title": "World Cup 2026",
        "data_source": "Data: openfootball/worldcup.json",
        "refresh": "🔄 Refresh data",
        "pages": ["🏆 Recent Matches", "📅 Upcoming Matches", "📊 Standings", "🔍 Team Search", "📈 Statistics", "💬 Chat"],
        "loading": "Loading World Cup 2026 data...",
        "error_loading": "Error loading data: {}",
        "no_upcoming": "No upcoming matches found.",

        # Recent Matches
        "recent_title": "🏆 Recent Matches",
        "num_matches": "Number of matches",

        # Upcoming
        "upcoming_title": "📅 Upcoming Matches",

        # Standings
        "standings_title": "📊 Standings",
        "group_label": "Group",
        "all_groups": "All groups",
        "group_prefix": "Group ",
        "col_team": "Team",
        "col_w": "W",
        "col_d": "D",
        "col_l": "L",
        "col_gf": "GF",
        "col_ga": "GA",
        "col_gd": "GD",
        "col_pts": "Pts",
        "qualified_note": "✅ = Qualified for Round of 32",

        # Team Search
        "search_title": "🔍 Team Search",
        "select_team": "Select a team",
        "metric_group": "Group",
        "metric_pts": "Points",
        "metric_gd": "Goal Difference",
        "metric_status": "Status",
        "qualified": "✅ Qualified",
        "eliminated": "❌ Eliminated",
        "place": lambda n: f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'} place",
        "matches_played": "📅 Matches played",
        "upcoming_matches": "⏳ Upcoming matches",

        # Statistics
        "stats_title": "📈 World Cup 2026 Statistics",
        "stat_played": "Matches played",
        "stat_goals": "Total goals",
        "stat_avg": "Avg goals/match",
        "stat_biggest": "Biggest win",
        "top_scorers": "🏅 Top Scorers",
        "top_teams": "🏆 Top Teams by Points",

        # Chat
        "chat_title": "💬 Chat",
        "chat_placeholder": "Ask anything about the World Cup 2026...",
        "chat_welcome": "Hello! Ask me anything about the World Cup 2026. Examples:\n- *What are Brazil's results?*\n- *Show Group C standings*\n- *Who are the top scorers?*\n- *Upcoming matches for France*",
        "chat_thinking": "Thinking...",
        "chat_clear": "🗑️ Clear chat",
    },
    "pt": {
        "title": "Copa do Mundo 2026",
        "data_source": "Dados: openfootball/worldcup.json",
        "refresh": "🔄 Atualizar dados",
        "pages": ["🏆 Jogos Recentes", "📅 Próximos Jogos", "📊 Classificação", "🔍 Buscar Time", "📈 Estatísticas", "💬 Chat"],
        "loading": "Carregando dados da Copa 2026...",
        "error_loading": "Erro ao carregar dados: {}",
        "no_upcoming": "Nenhum jogo futuro encontrado.",

        # Jogos Recentes
        "recent_title": "🏆 Jogos Recentes",
        "num_matches": "Quantidade de jogos",

        # Próximos
        "upcoming_title": "📅 Próximos Jogos",

        # Classificação
        "standings_title": "📊 Classificação",
        "group_label": "Grupo",
        "all_groups": "Todos os grupos",
        "group_prefix": "Grupo ",
        "col_team": "Time",
        "col_w": "V",
        "col_d": "E",
        "col_l": "D",
        "col_gf": "GP",
        "col_ga": "GC",
        "col_gd": "SG",
        "col_pts": "Pts",
        "qualified_note": "✅ = Classificado para as oitavas",

        # Buscar Time
        "search_title": "🔍 Buscar Time",
        "select_team": "Selecione um time",
        "metric_group": "Grupo",
        "metric_pts": "Pontos",
        "metric_gd": "Saldo de Gols",
        "metric_status": "Status",
        "qualified": "✅ Classificado",
        "eliminated": "❌ Eliminado",
        "place": lambda n: f"{n}º lugar",
        "matches_played": "📅 Jogos realizados",
        "upcoming_matches": "⏳ Próximos jogos",

        # Estatísticas
        "stats_title": "📈 Estatísticas da Copa 2026",
        "stat_played": "Jogos realizados",
        "stat_goals": "Total de gols",
        "stat_avg": "Média por jogo",
        "stat_biggest": "Maior goleada",
        "top_scorers": "🏅 Artilheiros",
        "top_teams": "🏆 Times com mais pontos",

        # Chat
        "chat_title": "💬 Chat",
        "chat_placeholder": "Pergunte qualquer coisa sobre a Copa 2026...",
        "chat_welcome": "Olá! Pergunte qualquer coisa sobre a Copa do Mundo 2026. Exemplos:\n- *Quais os resultados do Brasil?*\n- *Classificação do Grupo C*\n- *Quem são os artilheiros?*\n- *Próximos jogos da França*",
        "chat_thinking": "Pensando...",
        "chat_clear": "🗑️ Limpar conversa",
    },
}

# ─────────────────────────────────────────────
# Language state
# ─────────────────────────────────────────────

if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(key: str):
    return TRANSLATIONS[st.session_state.lang][key]


# ─────────────────────────────────────────────
# Cached data
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_data():
    matches = asyncio.run(_fetch_data())
    standings = _calcular_standings(matches)
    resolver = _build_resolver(matches, standings)
    return matches, standings, resolver


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

with st.sidebar:
    # Language switcher
    flag_col1, flag_col2 = st.columns(2)
    with flag_col1:
        if st.button("🇺🇸 English", use_container_width=True,
                     type="primary" if st.session_state.lang == "en" else "secondary"):
            st.session_state.lang = "en"
            st.rerun()
    with flag_col2:
        if st.button("🇧🇷 Português", use_container_width=True,
                     type="primary" if st.session_state.lang == "pt" else "secondary"):
            st.session_state.lang = "pt"
            st.rerun()

    st.divider()
    st.title(f"⚽ {t('title')}")
    st.caption(t("data_source"))
    st.divider()

    page = st.radio(
        "nav",
        t("pages"),
        label_visibility="collapsed",
    )

    st.divider()
    if st.button(t("refresh")):
        st.cache_data.clear()
        st.rerun()


# ─────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────

try:
    with st.spinner(t("loading")):
        matches, standings, resolver = get_data()
except Exception as e:
    st.error(t("error_loading").format(e))
    st.stop()


# ─────────────────────────────────────────────
# Render helpers
# ─────────────────────────────────────────────

def qualified_badge(pos: int) -> str:
    return "✅" if pos <= 2 else "❌"


def render_match(m: dict, show_scorers: bool = True):
    t1 = localize_team(_resolver_nome(m["team1"], resolver))
    t2 = localize_team(_resolver_nome(m["team2"], resolver))
    date = _format_brt(m["date"], m.get("time"))
    context = m.get("group") or m.get("round", "")
    venue = m.get("ground", "")

    if _encerrado(m):
        col1, col2, col3 = st.columns([3, 1, 3])
        with col1:
            st.markdown(f"### {t1}")
        with col2:
            st.markdown(f"<h2 style='text-align:center'>{_placar(m)}</h2>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"### {t2}")
        st.caption(f"📅 {date}  |  {context}  |  📍 {venue}")
        if show_scorers and (m.get("goals1") or m.get("goals2")):
            g1 = [f"⚽ {g['name']} {g.get('minute','')}′" for g in m.get("goals1", [])]
            g2 = [f"⚽ {g['name']} {g.get('minute','')}′" for g in m.get("goals2", [])]
            col1, _, col3 = st.columns([3, 1, 3])
            with col1:
                for g in g1:
                    st.caption(g)
            with col3:
                for g in g2:
                    st.caption(g)
    else:
        col1, col2, col3 = st.columns([3, 1, 3])
        with col1:
            st.markdown(f"### {t1}")
        with col2:
            st.markdown("<h2 style='text-align:center'>vs</h2>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"### {t2}")
        st.caption(f"📅 {date}  |  {context}  |  📍 {venue}")


# ─────────────────────────────────────────────
# Chat — intent detection + answer
# ─────────────────────────────────────────────

import re
import unicodedata


def _strip_accents(text: str) -> str:
    return unicodedata.normalize("NFD", text.lower()).encode("ascii", "ignore").decode("ascii")


# Build accent-normalized lookup maps at module load time
_PT_TO_EN_NORM = {_strip_accents(v): k for k, v in TEAM_NAMES_PT.items()}
_EN_NORM = {_strip_accents(k): k for k in TEAM_NAMES_PT.keys()}


def _detect_team(q: str) -> str | None:
    """Return the English team name if any team name (EN or PT, with or without accents) appears in the query."""
    q_norm = _strip_accents(q)
    # PT names first (longer/more specific → e.g. "paises baixos" before "paises")
    for pt_norm, en in sorted(_PT_TO_EN_NORM.items(), key=lambda x: -len(x[0])):
        if pt_norm in q_norm:
            return en
    for en_norm, en in sorted(_EN_NORM.items(), key=lambda x: -len(x[0])):
        if en_norm in q_norm:
            return en
    return None


def _detect_group(q: str) -> str | None:
    """Return group letter if query mentions a specific group."""
    m = re.search(r'\b(?:group|grupo)\s+([A-La-l])\b', q, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


async def _answer(question: str) -> str:
    q_norm = _strip_accents(question)

    # 1. Specific group standings
    group = _detect_group(question)
    if group:
        return await group_standings(group)

    # 2. Team-specific query
    team = _detect_team(question)
    if team:
        return await search_team(team)

    # 3. All groups / standings overview
    standings_kw = [
        "all groups", "todos os grupos", "overview", "visao geral",
        "classificacao", "tabela", "standings", "classificados",
        "quem passou", "quem classificou", "quem se classificou",
        "todos os times", "all teams",
    ]
    if any(kw in q_norm for kw in standings_kw):
        return await all_groups()

    # 4. Statistics / top scorers
    stats_kw = [
        "statistic", "stats", "artilheiro", "artilharia", "scorer",
        "top scorer", "gols", "goals", "media", "average",
        "biggest win", "maior goleada", "goleada", "hat-trick",
        "quantos gols", "how many goals", "quem marcou mais",
    ]
    if any(kw in q_norm for kw in stats_kw):
        return await cup_statistics()

    # 5. Upcoming matches
    upcoming_kw = [
        "upcoming", "next match", "proximo", "proxima", "schedule",
        "agenda", "quando joga", "when does", "vai jogar",
        "jogos que faltam", "falta jogar", "futuro", "proximos jogos",
    ]
    if any(kw in q_norm for kw in upcoming_kw):
        return await upcoming_matches(count=8)

    # 6. Recent / results (default fallback)
    return await recent_matches(count=8)


# ─────────────────────────────────────────────
# Pages — resolve by checking against current language pages list
# ─────────────────────────────────────────────

pages = t("pages")

if page == pages[0]:  # Recent / Jogos Recentes
    st.title(t("recent_title"))
    count = st.slider(t("num_matches"), 1, 20, 5)
    finished = [m for m in matches if _encerrado(m)]
    for m in finished[-count:][::-1]:
        with st.container(border=True):
            render_match(m)
        st.write("")


elif page == pages[1]:  # Upcoming / Próximos Jogos
    st.title(t("upcoming_title"))
    count = st.slider(t("num_matches"), 1, 20, 8)
    upcoming = [m for m in matches if not _encerrado(m)][:count]
    if not upcoming:
        st.info(t("no_upcoming"))
    else:
        for m in upcoming:
            with st.container(border=True):
                render_match(m, show_scorers=False)
            st.write("")


elif page == pages[2]:  # Standings / Classificação
    st.title(t("standings_title"))
    option = st.selectbox(
        t("group_label"),
        [t("all_groups")] + [f"{t('group_prefix')}{l}" for l in sorted(standings.keys())],
    )
    groups_to_show = (
        sorted(standings.keys())
        if option == t("all_groups")
        else [option.replace(t("group_prefix"), "")]
    )
    cols = st.columns(2) if len(groups_to_show) > 1 else st.columns(1)
    for i, letter in enumerate(groups_to_show):
        teams = standings[letter]
        col = cols[i % len(cols)]
        with col:
            st.subheader(f"{t('group_prefix')}{letter}")
            rows = []
            for tm in teams:
                gd = tm["gp"] - tm["gc"]
                rows.append({
                    "": qualified_badge(tm["pos"]),
                    t("col_team"): localize_team(tm["time"]),
                    t("col_pts"): tm["pts"],
                    t("col_w"): tm["v"],
                    t("col_d"): tm["e"],
                    t("col_l"): tm["d"],
                    t("col_gf"): tm["gp"],
                    t("col_ga"): tm["gc"],
                    t("col_gd"): f"{gd:+d}",
                })
            st.dataframe(rows, hide_index=True, use_container_width=True)
    st.caption(t("qualified_note"))


elif page == pages[3]:  # Team Search / Buscar Time
    st.title(t("search_title"))
    all_teams_en = sorted({tm["time"] for teams in standings.values() for tm in teams})
    all_teams_display = [localize_team(n) for n in all_teams_en]
    default_display = localize_team("Brazil") if "Brazil" in all_teams_en else all_teams_display[0]
    col1, _ = st.columns([3, 1])
    with col1:
        name_display = st.selectbox(
            t("select_team"),
            all_teams_display,
            index=all_teams_display.index(default_display),
        )
    # Map display name back to English for lookup
    name = all_teams_en[all_teams_display.index(name_display)]

    name_lower = name.lower()
    group_found = None
    team_info = None
    for letter, teams in standings.items():
        for tm in teams:
            if tm["time"].lower() == name_lower:
                group_found = letter
                team_info = tm
                break
        if group_found:
            break

    if team_info:
        gd = team_info["gp"] - team_info["gc"]
        qualified = team_info["pos"] <= 2
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(t("metric_group"), f"{group_found} — {t('place')(team_info['pos'])}")
        col2.metric(t("metric_pts"), team_info["pts"])
        col3.metric(t("metric_gd"), f"{gd:+d}")
        col4.metric(t("metric_status"), t("qualified") if qualified else t("eliminated"))
        st.divider()

    def _belongs(m: dict) -> bool:
        r1 = _resolver_nome(m["team1"], resolver).lower()
        r2 = _resolver_nome(m["team2"], resolver).lower()
        return name_lower in r1 or name_lower in r2

    team_matches = [m for m in matches if _belongs(m)]
    finished = [m for m in team_matches if _encerrado(m)]
    upcoming = [m for m in team_matches if not _encerrado(m)]

    if finished:
        st.subheader(t("matches_played"))
        for m in finished:
            with st.container(border=True):
                render_match(m)
            st.write("")

    if upcoming:
        st.subheader(t("upcoming_matches"))
        for m in upcoming:
            with st.container(border=True):
                render_match(m, show_scorers=False)
            st.write("")


elif page == pages[4]:  # Statistics / Estatísticas
    st.title(t("stats_title"))
    finished = [m for m in matches if _encerrado(m)]
    total_matches = len(finished)
    total_goals = sum(m["score"]["ft"][0] + m["score"]["ft"][1] for m in finished)
    avg_goals = round(total_goals / total_matches, 2) if total_matches else 0
    biggest_win = max(
        finished,
        key=lambda m: abs(m["score"]["ft"][0] - m["score"]["ft"][1]),
        default=None,
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("stat_played"), f"{total_matches} / {len(matches)}")
    col2.metric(t("stat_goals"), total_goals)
    col3.metric(t("stat_avg"), avg_goals)
    if biggest_win:
        g1, g2 = biggest_win["score"]["ft"]
        col4.metric(t("stat_biggest"), f"{g1}-{g2}", f"{biggest_win['team1']} vs {biggest_win['team2']}")

    st.divider()

    scorers: dict[str, int] = {}
    for m in finished:
        for g in m.get("goals1", []) + m.get("goals2", []):
            scorers[g["name"]] = scorers.get(g["name"], 0) + 1

    top_scorers = sorted(scorers.items(), key=lambda x: x[1], reverse=True)[:10]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t("top_scorers"))
        for i, (name, goals) in enumerate(top_scorers, 1):
            medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
            st.markdown(f"{medal} **{name}** — {goals} ⚽")

    with col2:
        st.subheader(t("top_teams"))
        top_teams = sorted(
            [
                {"team": tm["time"], "group": letter, "pts": tm["pts"], "gd": tm["gp"] - tm["gc"]}
                for letter, teams in standings.items()
                for tm in teams
            ],
            key=lambda x: (x["pts"], x["gd"]),
            reverse=True,
        )[:10]
        for i, tm in enumerate(top_teams, 1):
            medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
            st.markdown(f"{medal} **{localize_team(tm['team'])}** ({t('group_prefix')}{tm['group']}) — {tm['pts']} pts  {t('col_gd')}:{tm['gd']:+d}")


elif page == pages[5]:  # Chat
    st.title(t("chat_title"))

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.button(t("chat_clear")):
        st.session_state.chat_history = []
        st.rerun()

    # Show welcome message when chat is empty
    if not st.session_state.chat_history:
        with st.chat_message("assistant"):
            st.markdown(t("chat_welcome"))

    # Replay history
    for role, content in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(content)

    # Chat input
    if question := st.chat_input(t("chat_placeholder")):
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner(t("chat_thinking")):
                answer = asyncio.run(_answer(question))
            st.markdown(f"```\n{answer}\n```")
            st.session_state.chat_history.append(("assistant", f"```\n{answer}\n```"))
