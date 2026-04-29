"""Google Sheets row schemas."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from src.nhl.calculations import HeadToHeadStats, TeamRecentStats
from src.nhl.slate import SlateGame


DAILY_SLATE_COLUMNS = [
    "Date",
    "Away Team",
    "Home Team",
    "Start Time",
    "H2H 1P Over 1.5 Count",
    "H2H 1P Over 1.5 %",
    "H2H Full Game Over 5.5 Count",
    "H2H Full Game Over 5.5 %",
    "Away Avg Goals For",
    "Away Avg Goals Against",
    "Away Avg Total Goals",
    "Away Over 5.5 Count",
    "Away Over 5.5 %",
    "Away 1P Over 1.5 Count",
    "Away 1P Over 1.5 %",
    "Away 0-Goal First Periods",
    "Away 2+ Goal First Periods",
    "Home Avg Goals For",
    "Home Avg Goals Against",
    "Home Avg Total Goals",
    "Home Over 5.5 Count",
    "Home Over 5.5 %",
    "Home 1P Over 1.5 Count",
    "Home 1P Over 1.5 %",
    "Home 0-Goal First Periods",
    "Home 2+ Goal First Periods",
    "Away Last 10 Record",
    "Last H2H 1P Score",
    "Last H2H Full Game Score",
    "Away Last 5 1P Exactly 1 Count",
    "Away Last 5 Goals For",
    "Away Last 5 Goals Against",
    "Away Last 5 Total Goals",
    "Home Last 10 Record",
    "Home Last 5 1P Exactly 1 Count",
    "Home Last 5 Goals For",
    "Home Last 5 Goals Against",
    "Home Last 5 Total Goals",
    "Away Last 10 Goals For",
    "Away Last 10 Goals Against",
    "Away Last 10 Total Goals",
    "Home Last 10 Goals For",
    "Home Last 10 Goals Against",
    "Home Last 10 Total Goals",
    "My Pick",
    "Pick Type",
    "In Parlay",
    "Result",
    "Notes",
    "UNIQUE_ID",
]

BETS_COLUMNS = [
    "Date",
    "Game",
    "Team",
    "Bet Type",
    "Pick",
    "Line",
    "Odds",
    "Stake",
    "In Parlay",
    "Parlay ID",
    "Result",
    "Notes",
    "Profit/Loss",
    "Parlay Result",
    "Parlay Profit/Loss",
    "GPT Pick",
    "GPT Result",
    "GPT Profit/Loss",
]

DATE_COLUMN_INDEX = 0
AWAY_TEAM_COLUMN_INDEX = 1
HOME_TEAM_COLUMN_INDEX = 2
START_TIME_COLUMN_INDEX = 3
START_TIME_COLUMN_LETTER = "D"
MY_PICK_COLUMN_INDEX = 44
PICK_TYPE_COLUMN_INDEX = 45
RESULT_COLUMN_INDEX = 47
RESULT_COLUMN_LETTER = "AV"
DAILY_SLATE_UNIQUE_ID_COLUMN_INDEX = 49


def build_daily_slate_row(
    date_string: str,
    game: SlateGame,
    h2h_stats: HeadToHeadStats,
    away_stats: TeamRecentStats,
    home_stats: TeamRecentStats,
    away_last_10_stats: TeamRecentStats,
    home_last_10_stats: TeamRecentStats,
) -> list[str | int | float]:
    """Build one Daily_Slate row in the configured column order."""
    return [
        date_string,
        game.away_team,
        game.home_team,
        game.start_time,
        h2h_stats.first_period_over_1_5_count,
        round(h2h_stats.first_period_over_1_5_percentage, 1),
        h2h_stats.full_game_over_5_5_count,
        round(h2h_stats.full_game_over_5_5_percentage, 1),
        round(away_stats.average_goals_for, 2),
        round(away_stats.average_goals_against, 2),
        round(away_stats.average_total_goals, 2),
        away_stats.over_5_5_count,
        round(away_stats.over_5_5_percentage, 1),
        away_stats.first_period_over_1_5_count,
        round(away_stats.first_period_over_1_5_percentage, 1),
        away_stats.first_period_zero_goal_count,
        away_stats.first_period_two_plus_goal_count,
        round(home_stats.average_goals_for, 2),
        round(home_stats.average_goals_against, 2),
        round(home_stats.average_total_goals, 2),
        home_stats.over_5_5_count,
        round(home_stats.over_5_5_percentage, 1),
        home_stats.first_period_over_1_5_count,
        round(home_stats.first_period_over_1_5_percentage, 1),
        home_stats.first_period_zero_goal_count,
        home_stats.first_period_two_plus_goal_count,
        away_last_10_stats.record,
        h2h_stats.last_h2h_first_period_score,
        h2h_stats.last_h2h_full_game_score,
        away_stats.first_period_exactly_1_count,
        away_stats.total_goals_for,
        away_stats.total_goals_against,
        away_stats.total_goals,
        home_last_10_stats.record,
        home_stats.first_period_exactly_1_count,
        home_stats.total_goals_for,
        home_stats.total_goals_against,
        home_stats.total_goals,
        away_last_10_stats.total_goals_for,
        away_last_10_stats.total_goals_against,
        away_last_10_stats.total_goals,
        home_last_10_stats.total_goals_for,
        home_last_10_stats.total_goals_against,
        home_last_10_stats.total_goals,
        "",
        "",
        "",
        "",
        "",
        "",
    ]


def normalize_sheet_date(value: Any) -> str:
    """Normalize Google Sheets date values to YYYY-MM-DD."""
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if _looks_like_iso_date(text):
        return text[:10]
    parsed_date = _parse_display_date(text)
    if parsed_date is not None:
        return parsed_date.isoformat()
    if _looks_like_number(text):
        google_epoch = datetime(1899, 12, 30)
        return (google_epoch + timedelta(days=float(text))).date().isoformat()
    return text


def _looks_like_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _parse_display_date(value: str) -> date | None:
    for date_format in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    return None


def _looks_like_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True
