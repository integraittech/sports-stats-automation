"""Write compact NHL matchup reports to Google Sheets."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from datetime import date, datetime, timedelta

from src.nhl.calculations import (
    calculate_head_to_head_stats,
    calculate_recent_team_stats,
)
from src.nhl.history import (
    get_last_completed_games,
    get_last_head_to_head_games,
)
from src.nhl.slate import SlateGame, get_slate_for_date, get_today_string
from src.sheets.schemas import build_daily_slate_row
from src.sheets.writer import append_daily_slate_rows


def main(argv: Sequence[str] | None = None) -> None:
    """Fetch NHL slates and append one row per matchup."""
    args = parse_args(argv)
    total_inserted = 0
    total_skipped = 0

    for date_string in iter_date_strings(args.start_date, args.end_date):
        print(f"Processing {date_string}...")
        try:
            slate_games = get_slate_for_date(date_string)
            print(f"Fetched {len(slate_games)} games")
            if not slate_games:
                print(f"No NHL games found for {date_string}.")
                continue

            rows = [build_report_row(date_string, game) for game in slate_games]
            result = append_daily_slate_rows(rows)
            total_inserted += result.written_count
            total_skipped += result.duplicate_count
            print(f"Inserted {result.written_count}, Skipped {result.duplicate_count}")
        except Exception:
            print(f"Failed {date_string}, skipping")
            continue
        finally:
            time.sleep(0.3)

    print(f"Summary: Inserted {total_inserted}, Skipped {total_skipped}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse optional Daily_Slate backfill dates."""
    parser = argparse.ArgumentParser(
        description="Write NHL Daily_Slate rows to Google Sheets."
    )
    parser.add_argument(
        "--start",
        dest="start_date",
        type=parse_date,
        help="First slate date to fetch, in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--end",
        dest="end_date",
        type=parse_date,
        help="Last slate date to fetch, in YYYY-MM-DD format.",
    )
    args = parser.parse_args(argv)

    if args.start_date is None and args.end_date is None:
        args.end_date = parse_date(get_today_string())
        args.start_date = args.end_date
        args.end_date = args.start_date + timedelta(days=1)
    elif args.start_date is None or args.end_date is None:
        parser.error("--start and --end must be provided together")

    if args.start_date > args.end_date:
        parser.error("--start must be on or before --end")

    return args


def parse_date(value: str) -> date:
    """Parse an ISO slate date for CLI input."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date {value!r}; expected YYYY-MM-DD."
        ) from exc


def iter_date_strings(start_date: date, end_date: date) -> list[str]:
    """Return inclusive YYYY-MM-DD dates between start and end."""
    day_count = (end_date - start_date).days + 1
    return [
        (start_date + timedelta(days=offset)).isoformat()
        for offset in range(day_count)
    ]


def build_report_row(date_string: str | date | datetime, game: SlateGame) -> list[str | int | float]:
    """Fetch stats and build one Daily_Slate row."""
    if isinstance(date_string, datetime):
        report_date_string = date_string.strftime("%Y-%m-%d")
    elif isinstance(date_string, date):
        report_date_string = date_string.strftime("%Y-%m-%d")
    else:
        report_date_string = str(date_string)

    h2h_games = get_last_head_to_head_games(
        game.away_team_abbrev,
        game.home_team_abbrev,
        before_date=report_date_string,
    )
    away_games = get_last_completed_games(
        game.away_team_abbrev,
        limit=5,
        before_date=report_date_string,
    )
    home_games = get_last_completed_games(
        game.home_team_abbrev,
        limit=5,
        before_date=report_date_string,
    )
    away_last_10_games = get_last_completed_games(
        game.away_team_abbrev,
        limit=10,
        before_date=report_date_string,
    )
    home_last_10_games = get_last_completed_games(
        game.home_team_abbrev,
        limit=10,
        before_date=report_date_string,
    )

    h2h_stats = calculate_head_to_head_stats(h2h_games)
    away_stats = calculate_recent_team_stats(away_games)
    home_stats = calculate_recent_team_stats(home_games)
    away_last_10_stats = calculate_recent_team_stats(away_last_10_games)
    home_last_10_stats = calculate_recent_team_stats(home_last_10_games)

    return build_daily_slate_row(
        date_string=report_date_string,
        game=game,
        h2h_stats=h2h_stats,
        away_stats=away_stats,
        home_stats=home_stats,
        away_last_10_stats=away_last_10_stats,
        home_last_10_stats=home_last_10_stats,
    )


if __name__ == "__main__":
    main()
