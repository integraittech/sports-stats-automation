"""Build playoff trend rows for Google Sheets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.nhl.api_client import get_club_schedule_season, get_game_play_by_play
from src.nhl.slate import SlateGame


PLAYOFF_TRENDS_COLUMNS = [
    "UNIQUE_ID",
    "Date",
    "Away Team",
    "Home Team",
    "Series Game Number",
    "Home Wins",
    "Away Wins",
    "First Period Trend",
    "First Period Signal",
    "Last 1P Goals",
    "Last 1P Away Shots",
    "Last 1P Home Shots",
    "Last 1P Away Team",
    "Last 1P Home Team",
    "Full Game Totals",
    "Full Game Signal",
    "Last Game Total Goals",
    "Last Game Away Goals",
    "Last Game Home Goals",
    "Last Game Away Shots",
    "Last Game Home Shots",
    "Last Game Away Team",
    "Last Game Home Team",
    "Last Game Overtime",
    "Updated At",
]


@dataclass(frozen=True)
class PlayoffTrendBuildResult:
    row: list[str | int | bool]
    skipped_reason: str | None = None


def build_playoff_trend_row(
    date_string: str,
    game: SlateGame,
    *,
    debug: bool = False,
) -> PlayoffTrendBuildResult:
    season_id = _season_id_for_date(date_string)
    schedule = get_club_schedule_season(game.away_team_abbrev, season_id)
    games = schedule.get("games", [])

    series_games = _series_games(
        games,
        game.away_team_abbrev,
        game.home_team_abbrev,
        scheduled_date=date_string,
    )
    scheduled_game_number = _scheduled_series_game_number(
        games,
        game.away_team_abbrev,
        game.home_team_abbrev,
        date_string,
        len(series_games) + 1,
    )

    if not series_games:
        return PlayoffTrendBuildResult(
            row=_empty_row(date_string, game, scheduled_game_number),
            skipped_reason="no completed playoff series games",
        )

    game_details = [get_game_play_by_play(series_game["id"]) for series_game in series_games]

    first_period_trend = [_first_period_total_goals(detail) for detail in game_details]
    full_game_totals = [_full_game_total_goals(detail) for detail in game_details]
    last_detail = game_details[-1]
    last_teams = _game_teams(last_detail)
    last_1p_shots = _first_period_shots(last_detail)
    last_1p_goals = _first_period_total_goals(last_detail)
    home_wins, away_wins = _series_wins(
        game_details,
        scheduled_home=game.home_team_abbrev,
        scheduled_away=game.away_team_abbrev,
    )

    row = [
        _unique_id(date_string, game.away_team_abbrev, game.home_team_abbrev),
        date_string,
        game.away_team_abbrev,
        game.home_team_abbrev,
        scheduled_game_number,
        home_wins,
        away_wins,
        json.dumps(first_period_trend),
        _signal(first_period_trend, over_threshold=2),
        last_1p_goals,
        last_1p_shots["away"],
        last_1p_shots["home"],
        last_teams["away"],
        last_teams["home"],
        json.dumps(full_game_totals),
        _signal(full_game_totals, over_threshold=6),
        _full_game_total_goals(last_detail),
        _score(last_detail, "away"),
        _score(last_detail, "home"),
        _shots(last_detail, "away"),
        _shots(last_detail, "home"),
        last_teams["away"],
        last_teams["home"],
        _is_overtime(last_detail),
        datetime.now(timezone.utc).isoformat(),
    ]

    if debug:
        _debug_log_trend_build(
            date_string=date_string,
            game=game,
            row=row,
            series_games=series_games,
            first_period_trend=first_period_trend,
            full_game_totals=full_game_totals,
            last_detail=last_detail,
        )

    return PlayoffTrendBuildResult(row=row)


def _empty_row(date_string: str, game: SlateGame, series_game_number: int) -> list[str | int | bool]:
    return [
        _unique_id(date_string, game.away_team_abbrev, game.home_team_abbrev),
        date_string,
        game.away_team_abbrev,
        game.home_team_abbrev,
        series_game_number,
        0,
        0,
        "[]",
        "neutral",
        0,
        0,
        0,
        game.away_team_abbrev,
        game.home_team_abbrev,
        "[]",
        "neutral",
        0,
        0,
        0,
        0,
        0,
        game.away_team_abbrev,
        game.home_team_abbrev,
        False,
        datetime.now(timezone.utc).isoformat(),
    ]


def _season_id_for_date(date_string: str) -> int:
    year, month, *_ = [int(part) for part in date_string.split("-")]
    start_year = year if month >= 9 else year - 1
    return int(f"{start_year}{start_year + 1}")


def _series_games(
    games: list[dict[str, Any]],
    team_a: str,
    team_b: str,
    *,
    scheduled_date: str,
) -> list[dict[str, Any]]:
    filtered = [
        game
        for game in games
        if game.get("gameType") == 3
        and game.get("gameState") in {"OFF", "FINAL", "Final"}
        and _is_matchup(game, team_a, team_b)
        and str(game.get("gameDate", ""))[:10] < scheduled_date
    ]
    return sorted(filtered, key=lambda item: item.get("gameDate", ""))[-7:]


def _scheduled_series_game_number(
    games: list[dict[str, Any]],
    team_a: str,
    team_b: str,
    date_string: str,
    fallback: int,
) -> int:
    for game in games:
        if game.get("gameDate") == date_string and game.get("gameType") == 3 and _is_matchup(game, team_a, team_b):
            return int(game.get("seriesStatus", {}).get("gameNumberOfSeries") or fallback)
    return fallback


def _is_matchup(game: dict[str, Any], team_a: str, team_b: str) -> bool:
    away = game.get("awayTeam", {}).get("abbrev")
    home = game.get("homeTeam", {}).get("abbrev")
    return {away, home} == {team_a, team_b}


def _game_teams(detail: dict[str, Any]) -> dict[str, str]:
    return {
        "away": detail.get("awayTeam", {}).get("abbrev", ""),
        "home": detail.get("homeTeam", {}).get("abbrev", ""),
    }


def _score(detail: dict[str, Any], side: str) -> int:
    return int(detail.get(f"{side}Team", {}).get("score") or 0)


def _shots(detail: dict[str, Any], side: str) -> int:
    return int(detail.get(f"{side}Team", {}).get("sog") or 0)


def _full_game_total_goals(detail: dict[str, Any]) -> int:
    return _score(detail, "away") + _score(detail, "home")


def _first_period_total_goals(detail: dict[str, Any]) -> int:
    return sum(
        1
        for play in detail.get("plays", [])
        if play.get("typeDescKey") == "goal"
        and play.get("periodDescriptor", {}).get("number") == 1
    )


def _first_period_shots(detail: dict[str, Any]) -> dict[str, int]:
    away_id = detail.get("awayTeam", {}).get("id")
    home_id = detail.get("homeTeam", {}).get("id")
    shots = {"away": 0, "home": 0}

    for play in detail.get("plays", []):
        if play.get("periodDescriptor", {}).get("number") != 1:
            continue
        if play.get("typeDescKey") not in {"shot-on-goal", "goal"}:
            continue

        owner_id = play.get("details", {}).get("eventOwnerTeamId")
        if owner_id == away_id:
            shots["away"] += 1
        elif owner_id == home_id:
            shots["home"] += 1

    return shots


def _series_wins(
    game_details: list[dict[str, Any]],
    *,
    scheduled_home: str,
    scheduled_away: str,
) -> tuple[int, int]:
    home_wins = 0
    away_wins = 0

    for detail in game_details:
        teams = _game_teams(detail)
        away_score = _score(detail, "away")
        home_score = _score(detail, "home")
        winner = teams["home"] if home_score > away_score else teams["away"]

        if winner == scheduled_home:
            home_wins += 1
        elif winner == scheduled_away:
            away_wins += 1

    return home_wins, away_wins


def _signal(values: list[int], *, over_threshold: int) -> str:
    if not values:
        return "neutral"

    over_count = sum(1 for value in values if value >= over_threshold)
    under_count = len(values) - over_count

    if over_count > under_count:
        return "over"
    if under_count > over_count:
        return "under"
    return "neutral"


def _is_overtime(detail: dict[str, Any]) -> bool:
    return int(detail.get("periodDescriptor", {}).get("number") or 0) > 3


def _unique_id(date_string: str, away_team: str, home_team: str) -> str:
    return f"{date_string}_{away_team.lower()}_{home_team.lower()}"


def _debug_log_trend_build(
    *,
    date_string: str,
    game: SlateGame,
    row: list[str | int | bool],
    series_games: list[dict[str, Any]],
    first_period_trend: list[int],
    full_game_totals: list[int],
    last_detail: dict[str, Any],
) -> None:
    included_games = [
        {
            "gameId": game.get("id"),
            "date": str(game.get("gameDate", ""))[:10],
        }
        for game in series_games
    ]
    print(
        "Playoff_Trends debug | "
        f"scheduled_date={date_string} | "
        f"away={game.away_team_abbrev} | "
        f"home={game.home_team_abbrev} | "
        f"unique_id={row[0]} | "
        f"completed_h2h_count={len(series_games)} | "
        f"included_games={included_games} | "
        f"first_period_trend={first_period_trend} | "
        f"full_game_totals={full_game_totals} | "
        f"last_game_score={_format_score(last_detail)}"
    )


def _format_score(detail: dict[str, Any]) -> str:
    teams = _game_teams(detail)
    return f"{teams['away']} {_score(detail, 'away')} - {teams['home']} {_score(detail, 'home')}"
