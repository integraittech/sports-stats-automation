"""Basic team game history retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from src.nhl.api_client import (
    get_club_schedule_now,
    get_club_schedule_season,
    get_game_play_by_play,
)


@dataclass(frozen=True)
class TeamGameResult:
    """A completed game result for one team."""

    game_id: int
    game_date: str
    opponent: str
    team_score: int
    opponent_score: int
    first_period_team_score: int
    first_period_opponent_score: int


@dataclass(frozen=True)
class H2HGameResult:
    """A completed head-to-head game result."""

    game_id: int
    game_date: str
    away_team: str
    home_team: str
    away_score: int
    home_score: int
    first_period_away_score: int
    first_period_home_score: int

    @property
    def full_game_total(self) -> int:
        return self.away_score + self.home_score

    @property
    def first_period_total(self) -> int:
        return self.first_period_away_score + self.first_period_home_score


def get_last_completed_games(
    team_abbrev: str,
    limit: int = 5,
    before_date: str | date | datetime | None = None,
) -> list[TeamGameResult]:
    """Fetch and normalize the latest completed games for one team."""
    schedule = get_club_schedule_now(team_abbrev)
    games = schedule.get("games", [])
    normalized_before_date = _normalize_before_date(before_date)
    completed_games = [
        game
        for game in games
        if _is_completed(game) and _is_before_date(game, normalized_before_date)
    ]
    completed_games.sort(key=lambda game: game.get("gameDate", ""), reverse=True)

    return [
        _to_result(game, team_abbrev)
        for game in completed_games[:limit]
    ]


def get_last_head_to_head_games(
    team_abbrev: str,
    opponent_abbrev: str,
    limit: int = 10,
    before_date: str | date | datetime | None = None,
) -> list[H2HGameResult]:
    """Fetch recent completed games between two NHL teams."""
    schedule = get_club_schedule_now(team_abbrev)
    normalized_before_date = _normalize_before_date(before_date)
    h2h_games = _h2h_games_from_schedule(
        schedule,
        team_abbrev,
        opponent_abbrev,
        normalized_before_date,
    )

    season = schedule.get("previousSeason")
    seasons_checked = 0
    while len(h2h_games) < limit and season and seasons_checked < 6:
        season_schedule = get_club_schedule_season(team_abbrev, season)
        h2h_games.extend(
            _h2h_games_from_schedule(
                season_schedule,
                team_abbrev,
                opponent_abbrev,
                normalized_before_date,
            )
        )
        season = _previous_season(season)
        seasons_checked += 1

    h2h_games.sort(key=lambda game: game.get("gameDate", ""), reverse=True)
    return [_to_h2h_result(game) for game in h2h_games[:limit]]


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


def print_head_to_head_history(games: list[H2HGameResult]) -> None:
    """Print completed head-to-head games."""
    if not games:
        print("No completed head-to-head games found.")
        return

    print(f"Last {len(games)} head-to-head games:")
    for game in games:
        print(
            f"{game.game_date} | {game.away_team} {game.away_score} at "
            f"{game.home_team} {game.home_score} | "
            f"1P total: {game.first_period_total} | "
            f"Game total: {game.full_game_total}"
        )


def _is_completed(game: dict[str, Any]) -> bool:
    return game.get("gameState") in {"OFF", "FINAL", "Final"}


def _h2h_games_from_schedule(
    schedule: dict[str, Any],
    team_abbrev: str,
    opponent_abbrev: str,
    before_date: str | None,
) -> list[dict[str, Any]]:
    games = schedule.get("games", [])
    return [
        game for game in games
        if _is_completed(game)
        and _is_before_date(game, before_date)
        and _is_head_to_head(game, team_abbrev, opponent_abbrev)
    ]


def _is_head_to_head(
    game: dict[str, Any],
    team_abbrev: str,
    opponent_abbrev: str,
) -> bool:
    away_abbrev = game.get("awayTeam", {}).get("abbrev")
    home_abbrev = game.get("homeTeam", {}).get("abbrev")
    return {away_abbrev, home_abbrev} == {team_abbrev, opponent_abbrev}


def _to_result(game: dict[str, Any], team_abbrev: str) -> TeamGameResult:
    away_team = game.get("awayTeam", {})
    home_team = game.get("homeTeam", {})
    is_away = away_team.get("abbrev") == team_abbrev

    team = away_team if is_away else home_team
    opponent = home_team if is_away else away_team
    game_id = game["id"]
    first_period_scores = _first_period_scores(
        game_id=game_id,
        team_id=team.get("id"),
        opponent_id=opponent.get("id"),
    )

    return TeamGameResult(
        game_id=game_id,
        game_date=game.get("gameDate", "Unknown"),
        opponent=_team_name(opponent),
        team_score=team.get("score", 0),
        opponent_score=opponent.get("score", 0),
        first_period_team_score=first_period_scores[0],
        first_period_opponent_score=first_period_scores[1],
    )


def _to_h2h_result(game: dict[str, Any]) -> H2HGameResult:
    away_team = game.get("awayTeam", {})
    home_team = game.get("homeTeam", {})
    game_id = game["id"]
    first_period_scores = _first_period_scores(
        game_id=game_id,
        team_id=away_team.get("id"),
        opponent_id=home_team.get("id"),
    )

    return H2HGameResult(
        game_id=game_id,
        game_date=game.get("gameDate", "Unknown"),
        away_team=_team_name(away_team),
        home_team=_team_name(home_team),
        away_score=away_team.get("score", 0),
        home_score=home_team.get("score", 0),
        first_period_away_score=first_period_scores[0],
        first_period_home_score=first_period_scores[1],
    )


def _first_period_scores(
    game_id: int,
    team_id: int | None,
    opponent_id: int | None,
) -> tuple[int, int]:
    play_by_play = get_game_play_by_play(game_id)
    team_goals = 0
    opponent_goals = 0

    for play in play_by_play.get("plays", []):
        if play.get("typeDescKey") != "goal":
            continue
        if play.get("periodDescriptor", {}).get("number") != 1:
            continue

        scoring_team_id = play.get("details", {}).get("eventOwnerTeamId")
        if scoring_team_id == team_id:
            team_goals += 1
        elif scoring_team_id == opponent_id:
            opponent_goals += 1

    return team_goals, opponent_goals


def _previous_season(season: int) -> int:
    start_year = int(str(season)[:4]) - 1
    return int(f"{start_year}{start_year + 1}")


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


def _normalize_before_date(value: str | date | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10]


def _is_before_date(game: dict[str, Any], before_date: str | None) -> bool:
    if before_date is None:
        return True
    game_date = str(game.get("gameDate", ""))[:10]
    return bool(game_date) and game_date < before_date
