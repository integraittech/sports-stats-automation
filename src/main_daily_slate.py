"""Write compact NHL matchup reports for today's slate to Google Sheets."""

from __future__ import annotations

from src.nhl.calculations import (
    calculate_head_to_head_stats,
    calculate_recent_team_stats,
)
from src.nhl.history import (
    get_last_completed_games,
    get_last_head_to_head_games,
)
from src.nhl.slate import SlateGame, get_today_slate, get_today_string
from src.sheets.schemas import build_daily_slate_row
from src.sheets.writer import append_daily_slate_rows


def main() -> None:
    """Fetch today's NHL slate and append one row per matchup."""
    date_string = get_today_string()
    slate_games = get_today_slate()
    if not slate_games:
        print("No NHL games found for today.")
        return

    rows = [build_report_row(date_string, game) for game in slate_games]
    result = append_daily_slate_rows(rows)
    print(
        f"Wrote {result.written_count} new NHL matchup rows to Google Sheets. "
        f"Skipped {result.duplicate_count} duplicates."
    )


def build_report_row(date_string: str, game: SlateGame) -> list[str | int | float]:
    """Fetch stats and build one Daily_Slate row."""
    h2h_games = get_last_head_to_head_games(
        game.away_team_abbrev,
        game.home_team_abbrev,
    )
    away_games = get_last_completed_games(game.away_team_abbrev)
    home_games = get_last_completed_games(game.home_team_abbrev)

    h2h_stats = calculate_head_to_head_stats(h2h_games)
    away_stats = calculate_recent_team_stats(away_games)
    home_stats = calculate_recent_team_stats(home_games)

    return build_daily_slate_row(
        date_string=date_string,
        game=game,
        h2h_stats=h2h_stats,
        away_stats=away_stats,
        home_stats=home_stats,
    )


if __name__ == "__main__":
    main()
