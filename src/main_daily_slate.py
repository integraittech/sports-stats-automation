"""Append a simple Google Sheets connection test row."""

from src.sheets.writer import append_test_row


def main() -> None:
    """Write one test row to Google Sheets."""
    result = append_test_row()
    updated_cells = result.get("updates", {}).get("updatedCells", 0)
    print(f"Google Sheets test row appended. Updated cells: {updated_cells}")


if __name__ == "__main__":
    main()
