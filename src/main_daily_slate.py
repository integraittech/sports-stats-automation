"""Print one team's recent completed NHL games to the console."""

from src.nhl.calculations import calculate_recent_team_stats, print_recent_team_stats
from src.nhl.history import get_last_completed_games, print_team_history


TEAM_ABBREV = "EDM"
TEAM_NAME = "Edmonton Oilers"


def main() -> None:
    """Fetch Edmonton's last five completed games and print simple stats."""
    games = get_last_completed_games(TEAM_ABBREV)
    print_team_history(TEAM_NAME, games)
    stats = calculate_recent_team_stats(games)
    print_recent_team_stats(stats)


if __name__ == "__main__":
    main()
