"""Print compact NHL matchup reports for today's slate."""

from src.nhl.calculations import (
    calculate_head_to_head_stats,
    calculate_recent_team_stats,
    HeadToHeadStats,
    TeamRecentStats,
)
from src.nhl.history import (
    get_last_completed_games,
    get_last_head_to_head_games,
)
from src.nhl.slate import SlateGame, get_today_slate


def main() -> None:
    """Fetch today's NHL slate and print one compact report per game."""
    slate_games = get_today_slate()
    if not slate_games:
        print("No NHL games found for today.")
        return

    for index, game in enumerate(slate_games):
        if index:
            print("")
            print("-" * 64)
            print("")
        print_report_for_game(game)


def print_report_for_game(game: SlateGame) -> None:
    """Fetch stats and print one compact matchup report."""
    h2h_games = get_last_head_to_head_games(
        game.away_team_abbrev,
        game.home_team_abbrev,
    )
    away_games = get_last_completed_games(game.away_team_abbrev)
    home_games = get_last_completed_games(game.home_team_abbrev)

    h2h_stats = calculate_head_to_head_stats(h2h_games)
    away_stats = calculate_recent_team_stats(away_games)
    home_stats = calculate_recent_team_stats(home_games)

    print_matchup_report(
        matchup_name=f"{game.away_team} at {game.home_team}",
        away_team_name=game.away_team,
        home_team_name=game.home_team,
        h2h_stats=h2h_stats,
        away_stats=away_stats,
        home_stats=home_stats,
    )


def print_matchup_report(
    matchup_name: str,
    away_team_name: str,
    home_team_name: str,
    h2h_stats: HeadToHeadStats,
    away_stats: TeamRecentStats,
    home_stats: TeamRecentStats,
) -> None:
    """Print a clean matchup report without detailed game rows."""
    print(matchup_name)
    print("=" * len(matchup_name))
    print("")
    print_h2h_summary(h2h_stats)
    print("")
    print_team_summary(away_team_name, away_stats)
    print("")
    print_team_summary(home_team_name, home_stats)


def print_h2h_summary(stats: HeadToHeadStats) -> None:
    """Print compact H2H totals summary."""
    print("Last 10 head-to-head")
    print(
        "1P over 1.5: "
        f"{stats.first_period_over_1_5_count}/{stats.games_played} "
        f"({stats.first_period_over_1_5_percentage:.1f}%)"
    )
    print(
        "Full game over 5.5: "
        f"{stats.full_game_over_5_5_count}/{stats.games_played} "
        f"({stats.full_game_over_5_5_percentage:.1f}%)"
    )


def print_team_summary(team_name: str, stats: TeamRecentStats) -> None:
    """Print compact last-five team totals summary."""
    print(f"{team_name} last 5")
    print(f"Avg goals for: {stats.average_goals_for:.2f}")
    print(f"Avg goals against: {stats.average_goals_against:.2f}")
    print(f"Avg total goals: {stats.average_total_goals:.2f}")
    print(
        "Over 5.5: "
        f"{stats.over_5_5_count}/{stats.games_played} "
        f"({stats.over_5_5_percentage:.1f}%)"
    )
    print(
        "1P over 1.5: "
        f"{stats.first_period_over_1_5_count}/{stats.games_played} "
        f"({stats.first_period_over_1_5_percentage:.1f}%)"
    )
    print(f"0-goal first periods: {stats.first_period_zero_goal_count}")
    print(f"2+ goal first periods: {stats.first_period_two_plus_goal_count}")


if __name__ == "__main__":
    main()
