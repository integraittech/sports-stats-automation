"""Minimal Google Sheets write helpers."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from src.sheets.client import append_values, get_values
from src.sheets.schemas import DAILY_SLATE_COLUMNS


def append_test_row() -> dict[str, Any]:
    """Append a simple smoke-test row to the configured Google Sheet."""
    load_dotenv()
    range_name = os.getenv("GOOGLE_SHEETS_APPEND_RANGE", "Daily_Slate!A:B")
    return append_values(range_name, [["TEST", "It works"]])


def append_daily_slate_rows(rows: list[list[str | int | float]]) -> dict[str, Any]:
    """Append Daily_Slate rows, adding headers first if the sheet is empty."""
    load_dotenv()
    range_name = os.getenv("GOOGLE_SHEETS_APPEND_RANGE", "Daily_Slate!A:Y")
    if _is_sheet_empty("Daily_Slate!A1:Y1"):
        append_values(range_name, [DAILY_SLATE_COLUMNS])
    return append_values(range_name, rows)


def _is_sheet_empty(header_range: str) -> bool:
    values = get_values(header_range)
    return not values
