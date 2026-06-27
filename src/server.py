"""
MCP Server - Copa do Mundo 2026
Usando FastMCP com dados do openfootball/worldcup.json (sem API key)
"""

from fastmcp import FastMCP
from datetime import datetime, timezone, timedelta
import httpx

mcp = FastMCP(
    name="copa-2026",
    instructions="""
    Servidor MCP para consultar dados em tempo real da Copa do Mundo FIFA 2026.
    Dados fornecidos pelo openfootball/worldcup.json (open source, sem API key).
    Use as ferramentas disponíveis para responder perguntas sobre a Copa 2026.
    """,
)

DATA_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
CACHE_TTL = 300  # 5 minutos

_cache: dict = {}


def _is_cache_valid() -> bool:
    if "data" not in _cache:
        return False
    return (datetime.now().timestamp() - _cache["data"][0]) < CACHE_TTL


async def _fetch_data() -> list[dict]:
    """Busca e cacheia todos os jogos do openfootball."""
    if _is_cache_valid():
        return _cache["data"][1]

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(DATA_URL)
        response.raise_for_status()
        matches = response.json()["matches"]

    _cache["data"] = (datetime.now().timestamp(), matches)
    return matches


def _parse_time_utc(date_str: str, time_str: str) -> datetime | None:
    """Converte 'YYYY-MM-DD' + 'HH:MM UTC-N' para datetime UTC."""
    try:
        # Extrai offset: "13:00 UTC-6" → offset=-6
        parts = time_str.split()
        hhmm = parts[0]
        offset_str = parts[1].replace("UTC", "")  # "-6" ou "+0"
        offset_h = int(offset_str)
        dt_local = datetime.strptime(f"{date_str} {hhmm}", "%Y-%m-%d %H:%M")
        dt_utc = dt_local - timedelta(hours=offset_h)
        return dt_utc.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _format_brt(date_str: str, time_str: str | None) -> str:
    """Retorna data/hora no fuso BRT (UTC-3)."""
    if not time_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            return d.strftime("%d/%m/%Y")
        except Exception:
            return date_str
    dt_utc = _parse_time_utc(date_str, time_str)
    if not dt_utc:
        return f"{date_str} {time_str}"
    dt_brt = dt_utc - timedelta(hours=3)
    return dt_brt.strftime("%d/%m/%Y %H:%M BRT")


def _placar(match: dict) -> str:
    score = match.get("score", {}).get("ft")
    if score:
        return f"{score[0]}-{score[1]}"
    return "x-x"


def _encerrado(match: dict) -> bool:
    return bool(match.get("score", {}).get("ft"))


def _build_resolver(matches: list[dict], standings: dict[str, list[dict]]) -> dict[str, str]:
    """
    Monta um mapa de placeholder → nome real do time.

    Tipos suportados:
      1X / 2X     — 1º/2º lugar do Grupo X
      3X/Y/Z      — melhor 3º lugar dentre os grupos listados
      WN          — vencedor da partida N (numeração openfootball: índice N-1)
      LN          — perdedor da partida N
    """
    resolver: dict[str, str] = {}

    # 1º e 2º de cada grupo
    for letra, times in standings.items():
        for t in times:
            if t["pos"] <= 2:
                resolver[f'{t["pos"]}{letra}'] = t["time"]

    # WN / LN — resolve iterativamente para propagar dependências encadeadas
    changed = True
    while changed:
        changed = False
        for idx, m in enumerate(matches):
            num = idx + 1
            t1 = resolver.get(m["team1"], m["team1"])
            t2 = resolver.get(m["team2"], m["team2"])
            score = m.get("score", {}).get("ft")
            if not score:
                continue
            winner = t1 if score[0] >= score[1] else t2
            loser  = t2 if score[0] >= score[1] else t1
            for key, val in [(f"W{num}", winner), (f"L{num}", loser)]:
                if resolver.get(key) != val:
                    resolver[key] = val
                    changed = True

    # 3X/Y/Z — melhor 3º lugar dentre os grupos listados (por pts, SG, GP)
    codigos_3 = {
        t for m in matches
        for t in (m["team1"], m["team2"])
        if t.startswith("3") and "/" in t
    }
    for codigo in codigos_3:
        grupos = codigo[1:].split("/")
        terceiros = [
            t for g in grupos if g in standings
            for t in standings[g] if t["pos"] == 3
        ]
        if terceiros:
            melhor = max(terceiros, key=lambda x: (x["pts"], x["gp"] - x["gc"], x["gp"]))
            resolver[codigo] = f'{melhor["time"]} (3º)'

    return resolver


def _resolver_nome(nome: str, resolver: dict[str, str]) -> str:
    """Retorna o nome real se o código estiver resolvido, senão o original."""
    return resolver.get(nome, nome)


def _calcular_standings(matches: list[dict]) -> dict[str, list[dict]]:
    """Calcula classificação de todos os grupos a partir dos resultados."""
    grupos: dict[str, dict[str, dict]] = {}

    for m in matches:
        grupo = m.get("group")
        if not grupo:
            continue
        letra = grupo.replace("Group ", "").strip()
        if letra not in grupos:
            grupos[letra] = {}

        for time in (m["team1"], m["team2"]):
            if time not in grupos[letra]:
                grupos[letra][time] = {"pts": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0}

        if not _encerrado(m):
            continue

        g1, g2 = m["score"]["ft"]
        t1, t2 = m["team1"], m["team2"]

        grupos[letra][t1]["gp"] += g1
        grupos[letra][t1]["gc"] += g2
        grupos[letra][t2]["gp"] += g2
        grupos[letra][t2]["gc"] += g1

        if g1 > g2:
            grupos[letra][t1]["pts"] += 3
            grupos[letra][t1]["v"] += 1
            grupos[letra][t2]["d"] += 1
        elif g2 > g1:
            grupos[letra][t2]["pts"] += 3
            grupos[letra][t2]["v"] += 1
            grupos[letra][t1]["d"] += 1
        else:
            grupos[letra][t1]["pts"] += 1
            grupos[letra][t1]["e"] += 1
            grupos[letra][t2]["pts"] += 1
            grupos[letra][t2]["e"] += 1

    resultado: dict[str, list[dict]] = {}
    for letra, times in sorted(grupos.items()):
        classificados = sorted(
            [{"time": t, **s} for t, s in times.items()],
            key=lambda x: (x["pts"], x["gp"] - x["gc"], x["gp"]),
            reverse=True,
        )
        for i, t in enumerate(classificados, 1):
            t["pos"] = i
        resultado[letra] = classificados

    return resultado


# ─────────────────────────────────────────────
# MCP Tools
# ─────────────────────────────────────────────


@mcp.tool()
async def recent_matches(count: int = 5) -> str:
    """
    Returns the most recent FIFA World Cup 2026 match scores.

    Args:
        count: Number of matches to return (default: 5, max: 20)
    """
    count = min(count, 20)
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Error fetching data: {e}"

    standings = _calcular_standings(matches)
    resolver = _build_resolver(matches, standings)

    finished = [m for m in matches if _encerrado(m)]
    recent = finished[-count:][::-1]

    lines = ["🏆 RECENT MATCHES - World Cup 2026 [openfootball]\n"]
    for m in recent:
        date = _format_brt(m["date"], m.get("time"))
        context = f" | {m['group']}" if m.get("group") else f" | {m.get('round', '')}"
        t1 = _resolver_nome(m["team1"], resolver)
        t2 = _resolver_nome(m["team2"], resolver)
        lines.append(f"📅 {date}{context}")
        lines.append(f"   {t1} {_placar(m)} {t2}")
        if m.get("goals1") or m.get("goals2"):
            for g in m.get("goals1", []):
                lines.append(f"   ⚽ {t1}: {g['name']} {g.get('minute','')}′")
            for g in m.get("goals2", []):
                lines.append(f"   ⚽ {t2}: {g['name']} {g.get('minute','')}′")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def upcoming_matches(count: int = 5) -> str:
    """
    Returns the next scheduled FIFA World Cup 2026 matches.

    Args:
        count: Number of matches to return (default: 5, max: 20)
    """
    count = min(count, 20)
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Error fetching data: {e}"

    standings = _calcular_standings(matches)
    resolver = _build_resolver(matches, standings)

    upcoming = [m for m in matches if not _encerrado(m)][:count]

    lines = ["📅 UPCOMING MATCHES - World Cup 2026 [openfootball]\n"]
    for m in upcoming:
        date = _format_brt(m["date"], m.get("time"))
        context = m.get("group") or m.get("round", "")
        venue = m.get("ground", "")
        t1 = _resolver_nome(m["team1"], resolver)
        t2 = _resolver_nome(m["team2"], resolver)
        lines.append(f"⚽ {date} | {context}")
        lines.append(f"   {t1} vs {t2}{' | ' + venue if venue else ''}\n")

    return "\n".join(lines)


@mcp.tool()
async def group_standings(group: str) -> str:
    """
    Returns the standings for a specific World Cup 2026 group.

    Args:
        group: Group letter (A through L)
    """
    group = group.upper().strip()
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Error fetching data: {e}"

    standings = _calcular_standings(matches)

    if group not in standings:
        valid = ", ".join(sorted(standings.keys()))
        return f"❌ Group '{group}' not found. Valid groups: {valid}"

    teams = standings[group]
    lines = [f"📊 GROUP {group} - Standings [openfootball]\n"]
    lines.append(f"{'':4} {'Team':<25} {'Pts':<5} {'W':<4} {'D':<4} {'L':<4} {'GF':<4} {'GA':<4} {'GD'}")
    lines.append("-" * 58)
    for t in teams:
        qualified = "✅" if t["pos"] <= 2 else "  "
        gd = t["gp"] - t["gc"]
        lines.append(
            f"{qualified} {t['pos']:<2} {t['time']:<25} {t['pts']:<5} {t['v']:<4} {t['e']:<4} {t['d']:<4} {t['gp']:<4} {t['gc']:<4} {gd:+d}"
        )

    lines.append("\n✅ = Qualified for Round of 32")
    return "\n".join(lines)


@mcp.tool()
async def search_team(team_name: str) -> str:
    """
    Returns full information for a team: group, standings, and all matches.

    Args:
        team_name: Team name in English (e.g. Brazil, France, Argentina)
    """
    name_lower = team_name.lower().strip()
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Error fetching data: {e}"

    standings = _calcular_standings(matches)
    resolver = _build_resolver(matches, standings)

    reverso: dict[str, list[str]] = {}
    for code, name in resolver.items():
        reverso.setdefault(name.lower(), []).append(code)

    def _belongs(m: dict) -> bool:
        t1 = _resolver_nome(m["team1"], resolver).lower()
        t2 = _resolver_nome(m["team2"], resolver).lower()
        return name_lower in t1 or name_lower in t2

    team_matches = [m for m in matches if _belongs(m)]

    if not team_matches:
        return f"❌ Team '{team_name}' not found. Please use the English name."

    official_name = team_name
    for letter, teams in standings.items():
        for t in teams:
            if name_lower in t["time"].lower():
                official_name = t["time"]
                break

    group_found = None
    team_info = None
    for letter, teams in standings.items():
        for t in teams:
            if name_lower in t["time"].lower():
                group_found = letter
                team_info = t
                break
        if group_found:
            break

    lines = [f"🔍 {official_name} - World Cup 2026 [openfootball]\n"]

    if team_info and group_found:
        status = "✅ Qualified" if team_info["pos"] <= 2 else "❌ Eliminated"
        gd = team_info["gp"] - team_info["gc"]
        lines.append(f"📊 Group {group_found} | {team_info['pos']}{'st' if team_info['pos'] == 1 else 'nd' if team_info['pos'] == 2 else 'rd' if team_info['pos'] == 3 else 'th'} place")
        lines.append(f"🏅 Pts: {team_info['pts']} | W:{team_info['v']} D:{team_info['e']} L:{team_info['d']} | GF:{team_info['gp']} GA:{team_info['gc']} GD:{gd:+d}")
        lines.append(f"📌 Status: {status}\n")

    finished = [m for m in team_matches if _encerrado(m)]
    upcoming = [m for m in team_matches if not _encerrado(m)]

    if finished:
        lines.append("📅 Matches played:")
        for m in finished:
            date = _format_brt(m["date"], m.get("time"))
            context = m.get("group") or m.get("round", "")
            t1 = _resolver_nome(m["team1"], resolver)
            t2 = _resolver_nome(m["team2"], resolver)
            lines.append(f"  {date} | {context}")
            lines.append(f"  {t1} {_placar(m)} {t2}")
            for g in m.get("goals1", []):
                lines.append(f"    ⚽ {t1}: {g['name']} {g.get('minute','')}′")
            for g in m.get("goals2", []):
                lines.append(f"    ⚽ {t2}: {g['name']} {g.get('minute','')}′")

    if upcoming:
        lines.append("\n⏳ Upcoming matches:")
        for m in upcoming:
            date = _format_brt(m["date"], m.get("time"))
            context = m.get("group") or m.get("round", "")
            venue = m.get("ground", "")
            t1 = _resolver_nome(m["team1"], resolver)
            t2 = _resolver_nome(m["team2"], resolver)
            lines.append(f"  {date} | {context}")
            lines.append(f"  {t1} vs {t2}{' | ' + venue if venue else ''}")

    return "\n".join(lines)


@mcp.tool()
async def all_groups() -> str:
    """
    Returns a summary of all 12 group standings in the World Cup 2026.
    """
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Error fetching data: {e}"

    standings = _calcular_standings(matches)
    lines = ["🏆 FIFA WORLD CUP 2026 - All Groups [openfootball]\n"]

    for letter in sorted(standings.keys()):
        teams = standings[letter]
        lines.append(f"GROUP {letter}:")
        for t in teams:
            icon = "✅" if t["pos"] <= 2 else "❌"
            gd = t["gp"] - t["gc"]
            lines.append(f"  {t['pos']}. {icon} {t['time']:<25} {t['pts']}pts  GD:{gd:+d}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def cup_statistics() -> str:
    """
    Returns overall FIFA World Cup 2026 statistics: goals, averages, and top scorers.
    """
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Error fetching data: {e}"

    finished = [m for m in matches if _encerrado(m)]
    total_matches = len(finished)
    total_goals = sum(m["score"]["ft"][0] + m["score"]["ft"][1] for m in finished)
    avg_goals = round(total_goals / total_matches, 2) if total_matches else 0

    biggest_win = max(
        finished,
        key=lambda m: abs(m["score"]["ft"][0] - m["score"]["ft"][1]),
        default=None,
    )

    scorers: dict[str, int] = {}
    for m in finished:
        for g in m.get("goals1", []) + m.get("goals2", []):
            scorers[g["name"]] = scorers.get(g["name"], 0) + 1

    top_scorers = sorted(scorers.items(), key=lambda x: x[1], reverse=True)[:5]

    lines = ["📈 STATISTICS - World Cup 2026 [openfootball]\n"]
    lines.append(f"⚽ Matches played: {total_matches} of {len(matches)}")
    lines.append(f"🥅 Total goals: {total_goals}")
    lines.append(f"📊 Average goals per match: {avg_goals}")

    if biggest_win:
        g1, g2 = biggest_win["score"]["ft"]
        lines.append(
            f"\n💥 Biggest win: {biggest_win['team1']} {g1}-{g2} {biggest_win['team2']} ({biggest_win['date']})"
        )

    if top_scorers:
        lines.append("\n🏅 Top Scorers:")
        for name, goals in top_scorers:
            lines.append(f"  {goals}⚽ {name}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
