"""Print today's NHL slate to the console."""

from src.nhl.slate import get_today_slate, print_slate


def main() -> None:
    """Fetch today's NHL games and print a simple slate."""
    games = get_today_slate()
    print_slate(games)


if __name__ == "__main__":
    main()
