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
# Ferramentas MCP (Tools)
# ─────────────────────────────────────────────


@mcp.tool()
async def jogos_recentes(quantidade: int = 5) -> str:
    """
    Retorna os jogos mais recentes da Copa do Mundo 2026 com placares.

    Args:
        quantidade: Número de jogos a retornar (padrão: 5, máximo: 20)
    """
    quantidade = min(quantidade, 20)
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Erro ao buscar dados: {e}"

    standings = _calcular_standings(matches)
    resolver = _build_resolver(matches, standings)

    encerrados = [m for m in matches if _encerrado(m)]
    recentes = encerrados[-quantidade:][::-1]

    linhas = ["🏆 JOGOS RECENTES - Copa 2026 [openfootball]\n"]
    for m in recentes:
        data = _format_brt(m["date"], m.get("time"))
        grupo = f" | {m['group']}" if m.get("group") else f" | {m.get('round', '')}"
        t1 = _resolver_nome(m["team1"], resolver)
        t2 = _resolver_nome(m["team2"], resolver)
        linhas.append(f"📅 {data}{grupo}")
        linhas.append(f"   {t1} {_placar(m)} {t2}")
        if m.get("goals1") or m.get("goals2"):
            for g in m.get("goals1", []):
                linhas.append(f"   ⚽ {t1}: {g['name']} {g.get('minute','')}′")
            for g in m.get("goals2", []):
                linhas.append(f"   ⚽ {t2}: {g['name']} {g.get('minute','')}′")
        linhas.append("")

    return "\n".join(linhas)


@mcp.tool()
async def proximos_jogos(quantidade: int = 5) -> str:
    """
    Retorna os próximos jogos agendados da Copa do Mundo 2026.

    Args:
        quantidade: Número de jogos a retornar (padrão: 5)
    """
    quantidade = min(quantidade, 20)
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Erro ao buscar dados: {e}"

    standings = _calcular_standings(matches)
    resolver = _build_resolver(matches, standings)

    futuros = [m for m in matches if not _encerrado(m)][:quantidade]

    linhas = ["📅 PRÓXIMOS JOGOS - Copa 2026 [openfootball]\n"]
    for m in futuros:
        data = _format_brt(m["date"], m.get("time"))
        contexto = m.get("group") or m.get("round", "")
        local = m.get("ground", "")
        t1 = _resolver_nome(m["team1"], resolver)
        t2 = _resolver_nome(m["team2"], resolver)
        linhas.append(f"⚽ {data} | {contexto}")
        linhas.append(f"   {t1} vs {t2}{' | ' + local if local else ''}\n")

    return "\n".join(linhas)


@mcp.tool()
async def classificacao_grupo(grupo: str) -> str:
    """
    Retorna a classificação de um grupo específico da Copa 2026.

    Args:
        grupo: Letra do grupo (A até L)
    """
    grupo = grupo.upper().strip()
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Erro ao buscar dados: {e}"

    standings = _calcular_standings(matches)

    if grupo not in standings:
        grupos_validos = ", ".join(sorted(standings.keys()))
        return f"❌ Grupo '{grupo}' não encontrado. Grupos válidos: {grupos_validos}"

    times = standings[grupo]
    linhas = [f"📊 GRUPO {grupo} - Classificação [openfootball]\n"]
    linhas.append(f"{'':4} {'Time':<25} {'Pts':<5} {'V':<4} {'E':<4} {'D':<4} {'GP':<4} {'GC':<4} {'SG'}")
    linhas.append("-" * 58)
    for t in times:
        qualificado = "✅" if t["pos"] <= 2 else "  "
        sg = t["gp"] - t["gc"]
        linhas.append(
            f"{qualificado} {t['pos']:<2} {t['time']:<25} {t['pts']:<5} {t['v']:<4} {t['e']:<4} {t['d']:<4} {t['gp']:<4} {t['gc']:<4} {sg:+d}"
        )

    linhas.append("\n✅ = Classificado para as oitavas")
    return "\n".join(linhas)


@mcp.tool()
async def buscar_time(nome_time: str) -> str:
    """
    Busca informações completas de um time: grupo, classificação e todos os jogos.

    Args:
        nome_time: Nome do time em inglês (ex: Brazil, France, Argentina)
    """
    nome_lower = nome_time.lower().strip()
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Erro ao buscar dados: {e}"

    standings = _calcular_standings(matches)
    resolver = _build_resolver(matches, standings)

    # Mapa reverso: nome real → lista de códigos que resolvem para ele
    reverso: dict[str, list[str]] = {}
    for codigo, nome in resolver.items():
        reverso.setdefault(nome.lower(), []).append(codigo)

    def _pertence(m: dict) -> bool:
        t1 = _resolver_nome(m["team1"], resolver).lower()
        t2 = _resolver_nome(m["team2"], resolver).lower()
        return nome_lower in t1 or nome_lower in t2

    jogos_time = [m for m in matches if _pertence(m)]

    if not jogos_time:
        return f"❌ Time '{nome_time}' não encontrado. Verifique o nome em inglês."

    # Nome oficial a partir dos dados do grupo
    nome_oficial = nome_time
    for letra, times in standings.items():
        for t in times:
            if nome_lower in t["time"].lower():
                nome_oficial = t["time"]
                break

    grupo_encontrado = None
    time_info = None
    for letra, times in standings.items():
        for t in times:
            if nome_lower in t["time"].lower():
                grupo_encontrado = letra
                time_info = t
                break
        if grupo_encontrado:
            break

    linhas = [f"🔍 {nome_oficial} - Copa 2026 [openfootball]\n"]

    if time_info and grupo_encontrado:
        classificado = "✅ Classificado" if time_info["pos"] <= 2 else "❌ Fora da zona"
        sg = time_info["gp"] - time_info["gc"]
        linhas.append(f"📊 Grupo {grupo_encontrado} | {time_info['pos']}º lugar")
        linhas.append(f"🏅 Pts: {time_info['pts']} | V:{time_info['v']} E:{time_info['e']} D:{time_info['d']} | GP:{time_info['gp']} GC:{time_info['gc']} SG:{sg:+d}")
        linhas.append(f"📌 Status: {classificado}\n")

    encerrados = [m for m in jogos_time if _encerrado(m)]
    futuros = [m for m in jogos_time if not _encerrado(m)]

    if encerrados:
        linhas.append("📅 Jogos realizados:")
        for m in encerrados:
            data = _format_brt(m["date"], m.get("time"))
            contexto = m.get("group") or m.get("round", "")
            t1 = _resolver_nome(m["team1"], resolver)
            t2 = _resolver_nome(m["team2"], resolver)
            linhas.append(f"  {data} | {contexto}")
            linhas.append(f"  {t1} {_placar(m)} {t2}")
            for g in m.get("goals1", []):
                linhas.append(f"    ⚽ {t1}: {g['name']} {g.get('minute','')}′")
            for g in m.get("goals2", []):
                linhas.append(f"    ⚽ {t2}: {g['name']} {g.get('minute','')}′")

    if futuros:
        linhas.append("\n⏳ Próximos jogos:")
        for m in futuros:
            data = _format_brt(m["date"], m.get("time"))
            contexto = m.get("group") or m.get("round", "")
            local = m.get("ground", "")
            t1 = _resolver_nome(m["team1"], resolver)
            t2 = _resolver_nome(m["team2"], resolver)
            linhas.append(f"  {data} | {contexto}")
            linhas.append(f"  {t1} vs {t2}{' | ' + local if local else ''}")

    return "\n".join(linhas)


@mcp.tool()
async def todos_grupos() -> str:
    """
    Retorna um resumo da classificação de todos os grupos da Copa 2026.
    """
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Erro ao buscar dados: {e}"

    standings = _calcular_standings(matches)
    linhas = ["🏆 COPA DO MUNDO 2026 - Resumo dos Grupos [openfootball]\n"]

    for letra in sorted(standings.keys()):
        times = standings[letra]
        linhas.append(f"GRUPO {letra}:")
        for t in times:
            icone = "✅" if t["pos"] <= 2 else "❌"
            sg = t["gp"] - t["gc"]
            linhas.append(f"  {t['pos']}º {icone} {t['time']:<25} {t['pts']}pts  SG:{sg:+d}")
        linhas.append("")

    return "\n".join(linhas)


@mcp.tool()
async def estatisticas_copa() -> str:
    """
    Retorna estatísticas gerais da Copa do Mundo 2026: gols, médias e destaques.
    """
    try:
        matches = await _fetch_data()
    except Exception as e:
        return f"❌ Erro ao buscar dados: {e}"

    encerrados = [m for m in matches if _encerrado(m)]
    total_jogos = len(encerrados)
    total_gols = sum(m["score"]["ft"][0] + m["score"]["ft"][1] for m in encerrados)
    media_gols = round(total_gols / total_jogos, 2) if total_jogos else 0

    maior_goleada = max(
        encerrados,
        key=lambda m: abs(m["score"]["ft"][0] - m["score"]["ft"][1]),
        default=None,
    )

    artilheiros: dict[str, int] = {}
    for m in encerrados:
        for g in m.get("goals1", []) + m.get("goals2", []):
            artilheiros[g["name"]] = artilheiros.get(g["name"], 0) + 1

    top_artilheiros = sorted(artilheiros.items(), key=lambda x: x[1], reverse=True)[:5]

    linhas = ["📈 ESTATÍSTICAS - Copa 2026 [openfootball]\n"]
    linhas.append(f"⚽ Jogos realizados: {total_jogos} de {len(matches)}")
    linhas.append(f"🥅 Total de gols: {total_gols}")
    linhas.append(f"📊 Média de gols por jogo: {media_gols}")

    if maior_goleada:
        g1, g2 = maior_goleada["score"]["ft"]
        linhas.append(
            f"\n💥 Maior goleada: {maior_goleada['team1']} {g1}-{g2} {maior_goleada['team2']} ({maior_goleada['date']})"
        )

    if top_artilheiros:
        linhas.append("\n🏅 Artilheiros:")
        for nome, gols in top_artilheiros:
            linhas.append(f"  {gols}⚽ {nome}")

    return "\n".join(linhas)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
