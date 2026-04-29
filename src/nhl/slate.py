"""Daily NHL slate retrieval."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.nhl.api_client import get_schedule


@dataclass(frozen=True)
class SlateGame:
    """A single NHL game in the daily slate."""

    game_id: int
    away_team_abbrev: str
    away_team: str
    home_team_abbrev: str
    home_team: str
    start_time: str


def get_today_string() -> str:
    """Return today's date in the configured app timezone."""
    load_dotenv()
    timezone = os.getenv("APP_TIMEZONE", "America/Vancouver")
    return datetime.now(ZoneInfo(timezone)).date().isoformat()


def get_today_slate() -> list[SlateGame]:
    """Fetch and normalize today's NHL slate."""
    date_string = get_today_string()
    return get_slate_for_date(date_string)


def get_slate_for_date(date_string: str) -> list[SlateGame]:
    """Fetch and normalize the NHL slate for one date."""
    schedule = get_schedule(date_string)
    return normalize_schedule(schedule, date_string)


def normalize_schedule(schedule: dict[str, Any], date_string: str) -> list[SlateGame]:
    """Extract today's games from an NHL schedule response."""
    games = []

    if "gameWeek" in schedule:
        for day in schedule["gameWeek"]:
            if day.get("date") == date_string:
                games.extend(day.get("games", []))
    else:
        games.extend(schedule.get("games", []))

    slate_games = []
    for game in games:
        if game.get("gameDate") and game["gameDate"] != date_string:
            continue

        slate_games.append(
            SlateGame(
                game_id=game["id"],
                away_team_abbrev=game.get("awayTeam", {}).get("abbrev", ""),
                away_team=_team_name(game.get("awayTeam", {})),
                home_team_abbrev=game.get("homeTeam", {}).get("abbrev", ""),
                home_team=_team_name(game.get("homeTeam", {})),
                start_time=_format_local_start_time(game),
            )
        )

    return slate_games


def print_slate(games: list[SlateGame]) -> None:
    """Print the daily slate to the console."""
    if not games:
        print("No NHL games found for today.")
        return

    for game in games:
        print(
            f"{game.away_team} at {game.home_team} | "
            f"Game ID: {game.game_id} | Start: {game.start_time}"
        )


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


def _format_local_start_time(game: dict[str, Any]) -> str:
    timestamp = game.get("startTimeUTC") or game.get("gameDateTime")
    if not timestamp or not isinstance(timestamp, str):
        return "TBD"

    try:
        utc_start = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return "TBD"

    if utc_start.tzinfo is None:
        utc_start = utc_start.replace(tzinfo=timezone.utc)

    return utc_start.astimezone().strftime("%-I:%M %p")
