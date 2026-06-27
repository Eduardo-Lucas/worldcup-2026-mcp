"""
Tests for the FIFA World Cup 2026 MCP Server
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.server import (
    recent_matches,
    upcoming_matches,
    group_standings,
    search_team,
    all_groups,
    cup_statistics,
)


class TestRecentMatches:
    async def test_returns_matches(self):
        result = await recent_matches()
        assert "World Cup 2026" in result
        assert "RECENT MATCHES" in result

    async def test_max_count_respected(self):
        result = await recent_matches(count=100)
        lines_with_pipe = [l for l in result.split("\n") if "|" in l]
        assert len(lines_with_pipe) <= 20

    async def test_has_score(self):
        import re
        result = await recent_matches(3)
        assert re.search(r"\d-\d", result)


class TestUpcomingMatches:
    async def test_returns_upcoming(self):
        result = await upcoming_matches()
        assert "UPCOMING MATCHES" in result

    async def test_has_vs(self):
        result = await upcoming_matches(3)
        assert "vs" in result


class TestGroupStandings:
    async def test_group_c_has_brazil(self):
        result = await group_standings("C")
        assert "Brazil" in result
        assert "GROUP C" in result

    async def test_invalid_group(self):
        result = await group_standings("Z")
        assert "not found" in result

    async def test_lowercase_group(self):
        result = await group_standings("c")
        assert "Brazil" in result

    async def test_has_qualified_marker(self):
        result = await group_standings("A")
        assert "✅" in result

    async def test_all_groups_valid(self):
        for g in "ABCDEFGHIJKL":
            result = await group_standings(g)
            assert "not found" not in result


class TestSearchTeam:
    async def test_search_brazil(self):
        result = await search_team("Brazil")
        assert "Brazil" in result
        assert "Group C" in result

    async def test_search_france(self):
        result = await search_team("France")
        assert "France" in result

    async def test_search_argentina(self):
        result = await search_team("Argentina")
        assert "Argentina" in result
        assert "Group J" in result

    async def test_team_not_found(self):
        result = await search_team("Planet Mars FC")
        assert "not found" in result

    async def test_case_insensitive(self):
        result_upper = await search_team("BRAZIL")
        result_lower = await search_team("brazil")
        assert "Brazil" in result_upper
        assert "Brazil" in result_lower

    async def test_brazil_has_played_matches(self):
        result = await search_team("Brazil")
        assert "Matches played" in result

    async def test_brazil_has_scorers(self):
        result = await search_team("Brazil")
        assert "⚽" in result


class TestAllGroups:
    async def test_has_all_groups(self):
        result = await all_groups()
        for letter in "ABCDEFGHIJKL":
            assert f"GROUP {letter}" in result

    async def test_has_qualified_markers(self):
        result = await all_groups()
        assert "✅" in result
        assert "❌" in result


class TestCupStatistics:
    async def test_has_goals(self):
        result = await cup_statistics()
        assert "goals" in result.lower()

    async def test_has_average(self):
        result = await cup_statistics()
        assert "Average" in result

    async def test_has_biggest_win(self):
        result = await cup_statistics()
        assert "Biggest win" in result

    async def test_has_top_scorers(self):
        result = await cup_statistics()
        assert "Top Scorers" in result
