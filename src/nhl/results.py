"""NHL result grading helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.nhl.api_client import get_game_play_by_play, get_schedule


@dataclass(frozen=True)
class FinalGameResult:
    """Final score totals needed to grade simple picks."""

    full_game_total: int
    first_period_total: int


def get_final_game_result(
    date_string: str,
    away_team: str,
    home_team: str,
) -> FinalGameResult | None:
    """Fetch final game totals for one matchup."""
    schedule = get_schedule(date_string)
    game = _find_game(schedule, date_string, away_team, home_team)
    if not game or not _is_final(game):
        return None

    away_score = game.get("awayTeam", {}).get("score", 0)
    home_score = game.get("homeTeam", {}).get("score", 0)
    return FinalGameResult(
        full_game_total=away_score + home_score,
        first_period_total=_first_period_total(game["id"]),
    )


def grade_pick(
    pick: str,
    bet_type: str,
    bet_line: float,
    final_result: FinalGameResult,
) -> str | None:
    """Grade one supported pick against the row's Line column value."""
    pick_text = pick.strip().lower()
    bet_kind = bet_type.strip().lower()

    if not pick_text:
        return None

    if "over" in pick_text:
        direction = "over"
    elif "under" in pick_text:
        direction = "under"
    else:
        return None

    if bet_kind == "1p":
        actual_total = final_result.first_period_total
    else:
        actual_total = final_result.full_game_total

    if actual_total == bet_line:
        return "Push"
    if direction == "over":
        return "Win" if actual_total > bet_line else "Loss"
    return "Win" if actual_total < bet_line else "Loss"


def parse_game_teams(game: str) -> tuple[str, str] | None:
    """Parse a Bets game string into away and home team names."""
    if " vs " not in game:
        return None

    away_team, home_team = game.split(" vs ", 1)
    away_team = away_team.strip()
    home_team = home_team.strip()
    if not away_team or not home_team:
        return None
    return away_team, home_team


def _find_game(
    schedule: dict[str, Any],
    date_string: str,
    away_team: str,
    home_team: str,
) -> dict[str, Any] | None:
    for game in _schedule_games(schedule, date_string):
        if (
            _team_name(game.get("awayTeam", {})) == away_team
            and _team_name(game.get("homeTeam", {})) == home_team
        ):
            return game
    return None


def _schedule_games(schedule: dict[str, Any], date_string: str) -> list[dict[str, Any]]:
    if "gameWeek" not in schedule:
        return schedule.get("games", [])

    for day in schedule["gameWeek"]:
        if day.get("date") == date_string:
            return day.get("games", [])
    return []


def _is_final(game: dict[str, Any]) -> bool:
    return game.get("gameState") in {"OFF", "FINAL", "Final"}


def _first_period_total(game_id: int) -> int:
    play_by_play = get_game_play_by_play(game_id)
    total = 0

    for play in play_by_play.get("plays", []):
        if play.get("typeDescKey") != "goal":
            continue
        if play.get("periodDescriptor", {}).get("number") == 1:
            total += 1

    return total


def _team_name(team: dict[str, Any]) -> str:
    place_name = _localized_value(team.get("placeName"))
    common_name = _localized_value(team.get("commonName"))
    abbrev = team.get("abbrev")

    if place_name and common_name:
        return f"{place_name} {common_name}"
    return common_name or place_name or abbrev or "Unknown"


def _localized_value(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("default")
    if isinstance(value, str):
        return value
    return None
