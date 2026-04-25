"""Google Sheets row schemas."""

from __future__ import annotations

from src.nhl.calculations import HeadToHeadStats, TeamRecentStats
from src.nhl.slate import SlateGame


DAILY_SLATE_COLUMNS = [
    "Date",
    "Away Team",
    "Home Team",
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
]


def build_daily_slate_row(
    date_string: str,
    game: SlateGame,
    h2h_stats: HeadToHeadStats,
    away_stats: TeamRecentStats,
    home_stats: TeamRecentStats,
) -> list[str | int | float]:
    """Build one Daily_Slate row in the configured column order."""
    return [
        date_string,
        game.away_team,
        game.home_team,
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
    ]
