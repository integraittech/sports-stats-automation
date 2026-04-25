"""Basic team game history retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.nhl.api_client import get_club_schedule_now


@dataclass(frozen=True)
class TeamGameResult:
    """A completed game result for one team."""

    game_date: str
    opponent: str
    team_score: int
    opponent_score: int


def get_last_completed_games(team_abbrev: str, limit: int = 5) -> list[TeamGameResult]:
    """Fetch and normalize the latest completed games for one team."""
    schedule = get_club_schedule_now(team_abbrev)
    games = schedule.get("games", [])
    completed_games = [game for game in games if _is_completed(game)]
    completed_games.sort(key=lambda game: game.get("gameDate", ""), reverse=True)

    return [
        _to_result(game, team_abbrev)
        for game in completed_games[:limit]
    ]


def print_team_history(team_name: str, games: list[TeamGameResult]) -> None:
    """Print completed game results for one team."""
    if not games:
        print(f"No completed games found for {team_name}.")
        return

    print(f"Last {len(games)} completed games for {team_name}:")
    for game in games:
        print(
            f"{game.game_date} | Opponent: {game.opponent} | "
            f"Score: {game.team_score}-{game.opponent_score}"
        )


def _is_completed(game: dict[str, Any]) -> bool:
    return game.get("gameState") in {"OFF", "FINAL", "Final"}


def _to_result(game: dict[str, Any], team_abbrev: str) -> TeamGameResult:
    away_team = game.get("awayTeam", {})
    home_team = game.get("homeTeam", {})
    is_away = away_team.get("abbrev") == team_abbrev

    team = away_team if is_away else home_team
    opponent = home_team if is_away else away_team

    return TeamGameResult(
        game_date=game.get("gameDate", "Unknown"),
        opponent=_team_name(opponent),
        team_score=team.get("score", 0),
        opponent_score=opponent.get("score", 0),
    )


def _team_name(team: dict[str, Any]) -> str:
    city = _localized_value(team.get("city"))
    common_name = _localized_value(team.get("commonName"))
    abbrev = team.get("abbrev")

    if city and common_name:
        return f"{city} {common_name}"
    return common_name or city or abbrev or "Unknown"


def _localized_value(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("default")
    if isinstance(value, str):
        return value
    return None
