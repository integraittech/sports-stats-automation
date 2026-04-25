"""Minimal Google Sheets write helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from dotenv import load_dotenv

from src.sheets.client import append_values, get_values
from src.sheets.schemas import DAILY_SLATE_COLUMNS


@dataclass(frozen=True)
class DailySlateWriteResult:
    """Counts from a Daily_Slate append operation."""

    written_count: int
    duplicate_count: int


def append_test_row() -> dict[str, Any]:
    """Append a simple smoke-test row to the configured Google Sheet."""
    load_dotenv()
    range_name = os.getenv("GOOGLE_SHEETS_APPEND_RANGE", "Daily_Slate!A:B")
    return append_values(range_name, [["TEST", "It works"]])


def append_daily_slate_rows(
    rows: list[list[str | int | float]],
) -> DailySlateWriteResult:
    """Append new Daily_Slate rows, skipping duplicates."""
    load_dotenv()
    range_name = os.getenv("GOOGLE_SHEETS_APPEND_RANGE", "Daily_Slate!A:Y")
    existing_rows = get_values("Daily_Slate!A:Y")

    if not existing_rows:
        append_values(range_name, [DAILY_SLATE_COLUMNS])
        existing_rows = [DAILY_SLATE_COLUMNS]

    existing_keys = _row_keys(_data_rows(existing_rows))
    new_rows = []
    duplicate_count = 0

    for row in rows:
        row_key = _row_key(row)
        if row_key in existing_keys:
            duplicate_count += 1
            continue
        existing_keys.add(row_key)
        new_rows.append(row)

    if new_rows:
        append_values(range_name, new_rows)

    return DailySlateWriteResult(
        written_count=len(new_rows),
        duplicate_count=duplicate_count,
    )


def _row_keys(rows: list[list[Any]]) -> set[tuple[str, str, str]]:
    return {_row_key(row) for row in rows if len(row) >= 3}


def _data_rows(rows: list[list[Any]]) -> list[list[Any]]:
    if rows and _is_header_row(rows[0]):
        return rows[1:]
    return rows


def _is_header_row(row: list[Any]) -> bool:
    if len(row) < 3:
        return False
    return (
        str(row[0]).strip() == DAILY_SLATE_COLUMNS[0]
        and str(row[1]).strip() == DAILY_SLATE_COLUMNS[1]
        and str(row[2]).strip() == DAILY_SLATE_COLUMNS[2]
    )


def _row_key(row: list[Any]) -> tuple[str, str, str]:
    return (
        _normalize_date(row[0]),
        str(row[1]).strip(),
        str(row[2]).strip(),
    )


def _normalize_date(value: Any) -> str:
    """Normalize sheet date values to YYYY-MM-DD."""
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if _looks_like_iso_date(text):
        return text[:10]
    if _looks_like_number(text):
        serial_number = float(text)
        google_epoch = datetime(1899, 12, 30)
        return (google_epoch + timedelta(days=serial_number)).date().isoformat()
    return text


def _looks_like_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _looks_like_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True
