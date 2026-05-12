"""Minimal Google Sheets write helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

from src.sheets.client import (
    append_values,
    append_values_raw,
    get_sheets_service,
    get_spreadsheet_id,
    get_values,
    update_values,
    update_values_raw,
)
from src.sheets.schemas import (
    BETS_COLUMNS,
    DAILY_SLATE_COLUMNS,
    PLAYOFF_TRENDS_COLUMNS,
    DAILY_SLATE_UNIQUE_ID_COLUMN_INDEX,
    RESULT_COLUMN_LETTER,
    START_TIME_COLUMN_INDEX,
    START_TIME_COLUMN_LETTER,
    normalize_sheet_date,
)


BETS_RESULT_COLUMN_LETTER = "K"
BETS_PROFIT_LOSS_COLUMN_LETTER = "M"
BETS_PARLAY_RESULT_COLUMN_LETTER = "N"
BETS_PARLAY_PROFIT_LOSS_COLUMN_LETTER = "O"
BETS_GPT_RESULT_COLUMN_LETTER = "Q"
BETS_GPT_PROFIT_LOSS_COLUMN_LETTER = "R"
DASHBOARD_SHEET_TITLE = "Dashboard"
DAILY_SLATE_RANGE = "Daily_Slate!A:BB"
DAILY_SLATE_HEADER_RANGE = "Daily_Slate!A1:BB1"
PLAYOFF_TRENDS_SHEET_TITLE = "Playoff_Trends"
PLAYOFF_TRENDS_RANGE = "Playoff_Trends!A:Y"
PLAYOFF_TRENDS_HEADER_RANGE = "Playoff_Trends!A1:Y1"


@dataclass(frozen=True)
class DailySlateWriteResult:
    """Counts from a Daily_Slate append operation."""

    written_count: int
    duplicate_count: int


@dataclass(frozen=True)
class PlayoffTrendWriteResult:
    """Counts from a Playoff_Trends upsert operation."""

    inserted_count: int
    updated_count: int


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
    existing_rows = get_values(DAILY_SLATE_RANGE)
    ensure_daily_slate_headers()

    if not existing_rows:
        existing_rows = [DAILY_SLATE_COLUMNS]

    existing_rows_by_key = _daily_slate_rows_by_key(existing_rows)
    existing_keys = set(existing_rows_by_key)
    new_rows = []
    duplicate_count = 0

    for row in rows:
        normalized_row = _normalize_daily_slate_row(row)
        row_key = _row_key(normalized_row)
        if row_key in existing_keys:
            if row_key in existing_rows_by_key:
                row_number, existing_row = existing_rows_by_key[row_key]
                if _should_repair_start_time(existing_row, normalized_row):
                    update_values_raw(
                        f"Daily_Slate!{START_TIME_COLUMN_LETTER}{row_number}",
                        [[str(normalized_row[START_TIME_COLUMN_INDEX]).strip()]],
                    )
                    existing_row[START_TIME_COLUMN_INDEX] = str(
                        normalized_row[START_TIME_COLUMN_INDEX]
                    ).strip()
                    continue
            duplicate_count += 1
            continue
        existing_keys.add(row_key)
        new_rows.append(_row_with_unique_id(normalized_row, row_key))

    if new_rows:
        append_values_raw(DAILY_SLATE_RANGE, new_rows)

    print(f"Inserted {len(new_rows)} rows")
    print(f"Skipped {duplicate_count} duplicates")

    return DailySlateWriteResult(
        written_count=len(new_rows),
        duplicate_count=duplicate_count,
    )


def ensure_daily_slate_headers() -> None:
    """Ensure row 1 matches the Daily_Slate schema."""
    header_rows = get_values(DAILY_SLATE_HEADER_RANGE)
    current_header = header_rows[0] if header_rows else []
    if _headers_match(current_header, DAILY_SLATE_COLUMNS):
        return
    update_values(DAILY_SLATE_HEADER_RANGE, [DAILY_SLATE_COLUMNS])


def ensure_bets_headers() -> None:
    """Ensure row 1 matches the Bets schema."""
    ensure_sheet_exists("Bets")
    header_range = "Bets!A1:R1"
    header_rows = get_values(header_range)
    current_header = header_rows[0] if header_rows else []
    if _headers_match(current_header, BETS_COLUMNS):
        return
    update_values(header_range, [BETS_COLUMNS])


def append_bets_test_row() -> None:
    """Append one smoke-test row to the Bets sheet."""
    ensure_bets_headers()
    append_values(
        "Bets!A:R",
        [
            [
                "2026-04-25",
                "Edmonton Oilers vs Anaheim Ducks",
                "",
                "Full Game",
                "Over 5.5",
                5.5,
                "+230",
                10,
                "No",
                "",
                "",
                "test",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        ],
    )
    print("Wrote 1 test row to Bets")


def create_dashboard() -> None:
    """Create or refresh a formula-driven Dashboard sheet."""
    ensure_sheet_exists(DASHBOARD_SHEET_TITLE)
    _clear_sheet_values(DASHBOARD_SHEET_TITLE)
    update_values("Dashboard!A1:O40", _dashboard_values())
    _format_dashboard()


def ensure_sheet_exists(sheet_title: str) -> None:
    """Create a sheet tab if it does not already exist."""
    service = get_sheets_service()
    spreadsheet = (
        service.spreadsheets()
        .get(spreadsheetId=get_spreadsheet_id())
        .execute()
    )
    sheet_titles = {
        sheet.get("properties", {}).get("title")
        for sheet in spreadsheet.get("sheets", [])
    }
    if sheet_title in sheet_titles:
        return

    service.spreadsheets().batchUpdate(
        spreadsheetId=get_spreadsheet_id(),
        body={
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_title,
                        }
                    }
                }
            ]
        },
    ).execute()


def update_daily_slate_result(row_number: int, result: str) -> None:
    """Write a result value to one Daily_Slate row."""
    update_values(f"Daily_Slate!{RESULT_COLUMN_LETTER}{row_number}", [[result]])


def update_bets_result(row_number: int, result: str) -> None:
    """Write a result value to one Bets row."""
    update_values(f"Bets!{BETS_RESULT_COLUMN_LETTER}{row_number}", [[result]])


def update_bets_profit_loss(row_number: int, profit_loss: float) -> None:
    """Write a profit/loss value to one Bets row."""
    update_values(
        f"Bets!{BETS_PROFIT_LOSS_COLUMN_LETTER}{row_number}",
        [[round(profit_loss, 2)]],
    )


def update_bets_parlay_result(
    row_number: int,
    parlay_result: str,
    parlay_profit_loss: float,
) -> None:
    """Write parlay result values to one Bets row."""
    update_values(
        (
            f"Bets!{BETS_PARLAY_RESULT_COLUMN_LETTER}{row_number}:"
            f"{BETS_PARLAY_PROFIT_LOSS_COLUMN_LETTER}{row_number}"
        ),
        [[parlay_result, round(parlay_profit_loss, 2)]],
    )


def update_bets_gpt_result(row_number: int, result: str) -> None:
    """Write a GPT result value to one Bets row."""
    update_values(f"Bets!{BETS_GPT_RESULT_COLUMN_LETTER}{row_number}", [[result]])


def update_bets_gpt_profit_loss(row_number: int, profit_loss: float) -> None:
    """Write a GPT profit/loss value to one Bets row."""
    update_values(
        f"Bets!{BETS_GPT_PROFIT_LOSS_COLUMN_LETTER}{row_number}",
        [[round(profit_loss, 2)]],
    )


def _dashboard_values() -> list[list[str]]:
    return [
        ["Bets Dashboard"],
        [],
        ["Total Profit/Loss", "Today's Profit/Loss", "Win Rate", "Total Parlays", "Winning Parlays"],
        [
            "=SUM(Bets!M2:M)",
            "=SUMIF(Bets!A2:A,TODAY(),Bets!M2:M)",
            '=IFERROR(COUNTIF(Bets!K2:K,"Win")/COUNTIF(Bets!K2:K,"<>"),0)',
            '=IFERROR(COUNTUNIQUE(FILTER(Bets!J2:J,Bets!I2:I="Yes",Bets!J2:J<>"")),0)',
            '=IFERROR(COUNTUNIQUE(FILTER(Bets!J2:J,Bets!I2:I="Yes",Bets!N2:N="Win",Bets!J2:J<>"")),0)',
        ],
        [],
        ["Today's Bets"],
        BETS_COLUMNS,
        ['=IFERROR(FILTER(Bets!A2:O,Bets!A2:A=TODAY()),"No bets today")'],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        ["Recent Bets"],
        BETS_COLUMNS,
        ['=IFERROR(QUERY(Bets!A2:O,"select * where A is not null order by A desc limit 10",0),"No recent bets")'],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        ["Parlay Summary"],
        ["Metric", "Value"],
        [
            "Total unique parlays",
            '=IFERROR(COUNTUNIQUE(FILTER(Bets!J2:J,Bets!I2:I="Yes",Bets!J2:J<>"")),0)',
        ],
        [
            "Winning parlays",
            '=IFERROR(COUNTUNIQUE(FILTER(Bets!J2:J,Bets!I2:I="Yes",Bets!N2:N="Win",Bets!J2:J<>"")),0)',
        ],
    ]


def _clear_sheet_values(sheet_title: str) -> None:
    service = get_sheets_service()
    service.spreadsheets().values().clear(
        spreadsheetId=get_spreadsheet_id(),
        range=f"{sheet_title}!A:O",
    ).execute()


def _format_dashboard() -> None:
    service = get_sheets_service()
    sheet_id = _get_sheet_id(DASHBOARD_SHEET_TITLE)
    service.spreadsheets().batchUpdate(
        spreadsheetId=get_spreadsheet_id(),
        body={
            "requests": [
                _repeat_cell_request(sheet_id, 0, 1, 0, 5, bold=True, font_size=18),
                _repeat_cell_request(sheet_id, 2, 3, 0, 5, bold=True),
                _repeat_cell_request(sheet_id, 3, 4, 0, 5, font_size=14),
                _repeat_cell_request(sheet_id, 5, 6, 0, 1, bold=True, font_size=14),
                _repeat_cell_request(sheet_id, 6, 7, 0, len(BETS_COLUMNS), bold=True),
                _repeat_cell_request(sheet_id, 19, 20, 0, 1, bold=True, font_size=14),
                _repeat_cell_request(sheet_id, 20, 21, 0, len(BETS_COLUMNS), bold=True),
                _repeat_cell_request(sheet_id, 33, 34, 0, 1, bold=True, font_size=14),
                _repeat_cell_request(sheet_id, 34, 35, 0, 2, bold=True),
                _number_format_request(sheet_id, 3, 4, 0, 2, '$#,##0.00;-$#,##0.00'),
                _number_format_request(sheet_id, 3, 4, 2, 3, "0.0%"),
                _auto_resize_request(sheet_id, 0, len(BETS_COLUMNS)),
            ]
        },
    ).execute()


def _get_sheet_id(sheet_title: str) -> int:
    service = get_sheets_service()
    spreadsheet = (
        service.spreadsheets()
        .get(spreadsheetId=get_spreadsheet_id())
        .execute()
    )
    for sheet in spreadsheet.get("sheets", []):
        properties = sheet.get("properties", {})
        if properties.get("title") == sheet_title:
            return properties["sheetId"]
    raise RuntimeError(f"Sheet not found: {sheet_title}")


def _repeat_cell_request(
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_column: int,
    end_column: int,
    *,
    bold: bool = False,
    font_size: int | None = None,
) -> dict[str, Any]:
    text_format: dict[str, Any] = {"bold": bold}
    if font_size is not None:
        text_format["fontSize"] = font_size

    return {
        "repeatCell": {
            "range": _grid_range(sheet_id, start_row, end_row, start_column, end_column),
            "cell": {"userEnteredFormat": {"textFormat": text_format}},
            "fields": "userEnteredFormat.textFormat",
        }
    }


def _number_format_request(
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_column: int,
    end_column: int,
    pattern: str,
) -> dict[str, Any]:
    return {
        "repeatCell": {
            "range": _grid_range(sheet_id, start_row, end_row, start_column, end_column),
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": pattern,
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat",
        }
    }


def _auto_resize_request(
    sheet_id: int,
    start_column: int,
    end_column: int,
) -> dict[str, Any]:
    return {
        "autoResizeDimensions": {
            "dimensions": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": start_column,
                "endIndex": end_column,
            }
        }
    }


def _grid_range(
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_column: int,
    end_column: int,
) -> dict[str, int]:
    return {
        "sheetId": sheet_id,
        "startRowIndex": start_row,
        "endRowIndex": end_row,
        "startColumnIndex": start_column,
        "endColumnIndex": end_column,
    }


def _headers_match(header_row: list[Any], expected_columns: list[str]) -> bool:
    return [str(value).strip() for value in header_row] == expected_columns


def _row_keys(rows: list[list[Any]]) -> set[str]:
    return {_row_key(row) for row in rows if len(row) >= 3}


def _daily_slate_rows_by_key(rows: list[list[Any]]) -> dict[str, tuple[int, list[Any]]]:
    data_rows = _data_rows(rows)
    first_row_number = 2 if rows and _is_header_row(rows[0]) else 1
    return {
        _row_key(row): (index, row)
        for index, row in enumerate(data_rows, start=first_row_number)
        if len(row) >= 3
    }


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


def _row_key(row: list[Any]) -> str:
    date_string = normalize_sheet_date(row[0])
    away_team = _normalize_team_name(row[1])
    home_team = _normalize_team_name(row[2])
    return f"{date_string}_{away_team}_{home_team}"


def _normalize_team_name(value: Any) -> str:
    return str(value).strip().lower()


def _normalize_daily_slate_row(row: list[Any]) -> list[Any]:
    normalized_row = list(row)
    if normalized_row:
        normalized_row[0] = normalize_sheet_date(normalized_row[0])
    return normalized_row


def _row_with_unique_id(row: list[Any], row_key: str) -> list[Any]:
    row_with_key = list(row)
    while len(row_with_key) <= DAILY_SLATE_UNIQUE_ID_COLUMN_INDEX:
        row_with_key.append("")
    row_with_key[DAILY_SLATE_UNIQUE_ID_COLUMN_INDEX] = row_key
    return row_with_key


def _should_repair_start_time(existing_row: list[Any], new_row: list[Any]) -> bool:
    if len(new_row) <= START_TIME_COLUMN_INDEX:
        return False

    new_start_time = str(new_row[START_TIME_COLUMN_INDEX]).strip()
    if not new_start_time:
        return False

    existing_start_time = _cell(existing_row, START_TIME_COLUMN_INDEX)
    return _is_empty_or_invalid_start_time(existing_start_time)


def _is_empty_or_invalid_start_time(value: Any) -> bool:
    text = str(value).strip()
    if not text:
        return True
    try:
        float(text)
    except ValueError:
        return False
    return True


def _cell(row: list[Any], index: int) -> Any:
    if index >= len(row):
        return ""
    return row[index]


def upsert_playoff_trend_rows(
    rows: list[list[str | int | bool]],
) -> PlayoffTrendWriteResult:
    """Insert or update Playoff_Trends rows by UNIQUE_ID."""
    ensure_sheet_exists(PLAYOFF_TRENDS_SHEET_TITLE)
    ensure_playoff_trends_headers()

    existing_rows = get_values(PLAYOFF_TRENDS_RANGE)
    existing_by_key = _playoff_trend_rows_by_key(existing_rows)

    inserted_rows = []
    updated_count = 0

    for row in rows:
        if not row:
            continue

        row_key = str(row[0]).strip()
        if not row_key:
            continue

        if row_key in existing_by_key:
            row_number = existing_by_key[row_key]
            update_values_raw(
                f"Playoff_Trends!A{row_number}:Y{row_number}",
                [row],
            )
            updated_count += 1
        else:
            inserted_rows.append(row)

    if inserted_rows:
        append_values_raw(PLAYOFF_TRENDS_RANGE, inserted_rows)

    print(f"Inserted {len(inserted_rows)} playoff trend rows")
    print(f"Updated {updated_count} playoff trend rows")

    return PlayoffTrendWriteResult(
        inserted_count=len(inserted_rows),
        updated_count=updated_count,
    )


def ensure_playoff_trends_headers() -> None:
    """Ensure row 1 matches the Playoff_Trends schema."""
    ensure_sheet_exists(PLAYOFF_TRENDS_SHEET_TITLE)
    header_rows = get_values(PLAYOFF_TRENDS_HEADER_RANGE)
    current_header = header_rows[0] if header_rows else []
    if _headers_match(current_header, PLAYOFF_TRENDS_COLUMNS):
        return
    update_values(PLAYOFF_TRENDS_HEADER_RANGE, [PLAYOFF_TRENDS_COLUMNS])


def _playoff_trend_rows_by_key(rows: list[list[Any]]) -> dict[str, int]:
    data_rows = rows[1:] if rows and _headers_match(rows[0], PLAYOFF_TRENDS_COLUMNS) else rows
    first_row_number = 2 if rows and _headers_match(rows[0], PLAYOFF_TRENDS_COLUMNS) else 1

    return {
        str(row[0]).strip(): row_number
        for row_number, row in enumerate(data_rows, start=first_row_number)
        if row and str(row[0]).strip()
    }
