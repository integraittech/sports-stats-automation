"""Print head-to-head stats for one hardcoded NHL matchup."""

from src.nhl.calculations import (
    calculate_head_to_head_stats,
    print_head_to_head_stats,
)
from src.nhl.history import get_last_head_to_head_games, print_head_to_head_history


AWAY_TEAM_ABBREV = "EDM"
HOME_TEAM_ABBREV = "ANA"
MATCHUP_NAME = "Edmonton Oilers at Anaheim Ducks"


def main() -> None:
    """Fetch and print last-10 head-to-head stats for one matchup."""
    print(f"Matchup: {MATCHUP_NAME}")
    games = get_last_head_to_head_games(AWAY_TEAM_ABBREV, HOME_TEAM_ABBREV)
    print("")
    print_head_to_head_history(games)
    stats = calculate_head_to_head_stats(games)
    print_head_to_head_stats(stats)


if __name__ == "__main__":
    main()
