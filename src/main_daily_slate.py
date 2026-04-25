"""Print recent stats for both teams in one hardcoded NHL matchup."""

from src.nhl.calculations import calculate_recent_team_stats, print_recent_team_stats
from src.nhl.history import get_last_completed_games, print_team_history


MATCHUP = (
    ("EDM", "Edmonton Oilers"),
    ("ANA", "Anaheim Ducks"),
)


def main() -> None:
    """Fetch and print last-five summaries for both matchup teams."""
    print("Matchup: Edmonton Oilers at Anaheim Ducks")
    for team_abbrev, team_name in MATCHUP:
        print("")
        print("=" * 48)
        print(team_name)
        print("=" * 48)
        print_team_report(team_abbrev, team_name)


def print_team_report(team_abbrev: str, team_name: str) -> None:
    """Print recent games and summaries for one team."""
    games = get_last_completed_games(team_abbrev)
    print_team_history(team_name, games)
    stats = calculate_recent_team_stats(games)
    print_recent_team_stats(stats)


if __name__ == "__main__":
    main()
