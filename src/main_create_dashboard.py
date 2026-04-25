"""Create or refresh the Google Sheets Dashboard tab."""

from __future__ import annotations

from src.sheets.writer import create_dashboard


def main() -> None:
    """Build the formula-driven Dashboard tab."""
    create_dashboard()
    print("Created Dashboard tab.")


if __name__ == "__main__":
    main()
