"""Simple NHL stat calculations."""

from __future__ import annotations

from dataclasses import dataclass

from src.nhl.history import TeamGameResult


@dataclass(frozen=True)
class TeamRecentStats:
    """Summary stats for one team's recent completed games."""

    games_played: int
    total_goals_for: int
    total_goals_against: int
    average_goals_for: float
    average_goals_against: float
    average_total_goals: float
    over_5_5_count: int
    over_5_5_percentage: float


def calculate_recent_team_stats(games: list[TeamGameResult]) -> TeamRecentStats:
    """Calculate basic scoring stats from completed games."""
    games_played = len(games)
    total_goals_for = sum(game.team_score for game in games)
    total_goals_against = sum(game.opponent_score for game in games)
    total_goals = total_goals_for + total_goals_against
    over_5_5_count = sum(
        1 for game in games
        if game.team_score + game.opponent_score > 5.5
    )

    if games_played == 0:
        return TeamRecentStats(
            games_played=0,
            total_goals_for=0,
            total_goals_against=0,
            average_goals_for=0,
            average_goals_against=0,
            average_total_goals=0,
            over_5_5_count=0,
            over_5_5_percentage=0,
        )

    return TeamRecentStats(
        games_played=games_played,
        total_goals_for=total_goals_for,
        total_goals_against=total_goals_against,
        average_goals_for=total_goals_for / games_played,
        average_goals_against=total_goals_against / games_played,
        average_total_goals=total_goals / games_played,
        over_5_5_count=over_5_5_count,
        over_5_5_percentage=(over_5_5_count / games_played) * 100,
    )


def print_recent_team_stats(stats: TeamRecentStats) -> None:
    """Print basic scoring stats for recent completed games."""
    print("")
    print("Recent scoring summary:")
    print(f"Total goals for: {stats.total_goals_for}")
    print(f"Total goals against: {stats.total_goals_against}")
    print(f"Average goals for: {stats.average_goals_for:.2f}")
    print(f"Average goals against: {stats.average_goals_against:.2f}")
    print(f"Average total goals per game: {stats.average_total_goals:.2f}")
    print(f"Games over 5.5 total goals: {stats.over_5_5_count}")
    print(f"Over 5.5 percentage: {stats.over_5_5_percentage:.1f}%")
