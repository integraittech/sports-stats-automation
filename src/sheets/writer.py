"""Minimal Google Sheets write helpers."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from src.sheets.client import append_values


def append_test_row() -> dict[str, Any]:
    """Append a simple smoke-test row to the configured Google Sheet."""
    load_dotenv()
    range_name = os.getenv("GOOGLE_SHEETS_APPEND_RANGE", "Daily_Slate!A:B")
    return append_values(range_name, [["TEST", "It works"]])
