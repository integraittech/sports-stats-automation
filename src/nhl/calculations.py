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
    first_period_goals_for: int
    first_period_goals_against: int
    average_first_period_goals_for: float
    average_first_period_goals_against: float
    average_first_period_total_goals: float
    first_period_over_1_5_count: int
    first_period_over_1_5_percentage: float
    first_period_zero_goal_count: int
    first_period_two_plus_goal_count: int


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
    first_period_goals_for = sum(game.first_period_team_score for game in games)
    first_period_goals_against = sum(
        game.first_period_opponent_score for game in games
    )
    first_period_total_goals = first_period_goals_for + first_period_goals_against
    first_period_over_1_5_count = sum(
        1 for game in games
        if game.first_period_team_score + game.first_period_opponent_score > 1.5
    )
    first_period_zero_goal_count = sum(
        1 for game in games
        if game.first_period_team_score + game.first_period_opponent_score == 0
    )
    first_period_two_plus_goal_count = sum(
        1 for game in games
        if game.first_period_team_score + game.first_period_opponent_score >= 2
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
            first_period_goals_for=0,
            first_period_goals_against=0,
            average_first_period_goals_for=0,
            average_first_period_goals_against=0,
            average_first_period_total_goals=0,
            first_period_over_1_5_count=0,
            first_period_over_1_5_percentage=0,
            first_period_zero_goal_count=0,
            first_period_two_plus_goal_count=0,
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
        first_period_goals_for=first_period_goals_for,
        first_period_goals_against=first_period_goals_against,
        average_first_period_goals_for=first_period_goals_for / games_played,
        average_first_period_goals_against=(
            first_period_goals_against / games_played
        ),
        average_first_period_total_goals=first_period_total_goals / games_played,
        first_period_over_1_5_count=first_period_over_1_5_count,
        first_period_over_1_5_percentage=(
            first_period_over_1_5_count / games_played
        ) * 100,
        first_period_zero_goal_count=first_period_zero_goal_count,
        first_period_two_plus_goal_count=first_period_two_plus_goal_count,
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
    print("")
    print("First-period scoring summary:")
    print(f"First-period goals for: {stats.first_period_goals_for}")
    print(f"First-period goals against: {stats.first_period_goals_against}")
    print(
        "Average first-period goals for: "
        f"{stats.average_first_period_goals_for:.2f}"
    )
    print(
        "Average first-period goals against: "
        f"{stats.average_first_period_goals_against:.2f}"
    )
    print(
        "Average first-period total goals per game: "
        f"{stats.average_first_period_total_goals:.2f}"
    )
    print(
        "Games over 1.5 first-period total goals: "
        f"{stats.first_period_over_1_5_count}"
    )
    print(
        "First-period over 1.5 percentage: "
        f"{stats.first_period_over_1_5_percentage:.1f}%"
    )
    print(
        "Games with 0 total first-period goals: "
        f"{stats.first_period_zero_goal_count}"
    )
    print(
        "Games with 2+ total first-period goals: "
        f"{stats.first_period_two_plus_goal_count}"
    )
