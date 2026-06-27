"""
Testes do MCP Server - Copa 2026 (openfootball)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.server import (
    jogos_recentes,
    proximos_jogos,
    classificacao_grupo,
    buscar_time,
    todos_grupos,
    estatisticas_copa,
)


class TestJogosRecentes:
    async def test_retorna_jogos(self):
        resultado = await jogos_recentes()
        assert "Copa 2026" in resultado
        assert "JOGOS RECENTES" in resultado

    async def test_quantidade_maxima_respeitada(self):
        resultado = await jogos_recentes(quantidade=100)
        # Cada jogo gera ao menos 2 linhas; 20 jogos = até 40 linhas de partida
        assert resultado.count("vs") == 0  # encerrados não têm "vs"

    async def test_tem_placar(self):
        resultado = await jogos_recentes(3)
        # placares no formato N-N
        import re
        assert re.search(r"\d-\d", resultado)


class TestProximosJogos:
    async def test_retorna_proximos_jogos(self):
        resultado = await proximos_jogos()
        assert "PRÓXIMOS JOGOS" in resultado

    async def test_tem_vs(self):
        resultado = await proximos_jogos(3)
        assert "vs" in resultado


class TestClassificacaoGrupo:
    async def test_grupo_c_tem_brasil(self):
        resultado = await classificacao_grupo("C")
        assert "Brazil" in resultado
        assert "GRUPO C" in resultado

    async def test_grupo_invalido(self):
        resultado = await classificacao_grupo("Z")
        assert "não encontrado" in resultado

    async def test_grupo_minusculo(self):
        resultado = await classificacao_grupo("c")
        assert "Brazil" in resultado

    async def test_tem_indicador_classificacao(self):
        resultado = await classificacao_grupo("A")
        assert "✅" in resultado

    async def test_todos_grupos_validos(self):
        for g in "ABCDEFGHIJKL":
            resultado = await classificacao_grupo(g)
            assert "não encontrado" not in resultado


class TestBuscarTime:
    async def test_buscar_brasil(self):
        resultado = await buscar_time("Brazil")
        assert "Brazil" in resultado
        assert "Grupo C" in resultado

    async def test_buscar_franca(self):
        resultado = await buscar_time("France")
        assert "France" in resultado

    async def test_buscar_argentina(self):
        resultado = await buscar_time("Argentina")
        assert "Argentina" in resultado
        assert "Grupo J" in resultado

    async def test_time_inexistente(self):
        resultado = await buscar_time("Planeta Marte FC")
        assert "não encontrado" in resultado

    async def test_busca_case_insensitive(self):
        resultado_upper = await buscar_time("BRAZIL")
        resultado_lower = await buscar_time("brazil")
        assert "Brazil" in resultado_upper
        assert "Brazil" in resultado_lower

    async def test_brasil_tem_jogos_realizados(self):
        resultado = await buscar_time("Brazil")
        assert "Jogos realizados" in resultado

    async def test_brasil_tem_artilheiros(self):
        resultado = await buscar_time("Brazil")
        assert "⚽" in resultado


class TestTodosGrupos:
    async def test_tem_todos_grupos(self):
        resultado = await todos_grupos()
        for letra in "ABCDEFGHIJKL":
            assert f"GRUPO {letra}" in resultado

    async def test_tem_marcadores_classificacao(self):
        resultado = await todos_grupos()
        assert "✅" in resultado
        assert "❌" in resultado


class TestEstatisticas:
    async def test_tem_gols(self):
        resultado = await estatisticas_copa()
        assert "gols" in resultado.lower()

    async def test_tem_media(self):
        resultado = await estatisticas_copa()
        assert "Média" in resultado

    async def test_tem_maior_goleada(self):
        resultado = await estatisticas_copa()
        assert "goleada" in resultado.lower()

    async def test_tem_artilheiros(self):
        resultado = await estatisticas_copa()
        assert "Artilheiros" in resultado
