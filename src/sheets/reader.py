"""Google Sheets read helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.sheets.client import get_values
from src.sheets.schemas import (
    AWAY_TEAM_COLUMN_INDEX,
    BETS_COLUMNS,
    DAILY_SLATE_COLUMNS,
    DATE_COLUMN_INDEX,
    HOME_TEAM_COLUMN_INDEX,
    MY_PICK_COLUMN_INDEX,
    PICK_TYPE_COLUMN_INDEX,
    RESULT_COLUMN_INDEX,
    normalize_sheet_date,
)


BETS_DATE_COLUMN_INDEX = 0
BETS_GAME_COLUMN_INDEX = 1
BETS_BET_TYPE_COLUMN_INDEX = 3
BETS_PICK_COLUMN_INDEX = 4
BETS_LINE_COLUMN_INDEX = 5
BETS_ODDS_COLUMN_INDEX = 6
BETS_STAKE_COLUMN_INDEX = 7
BETS_IN_PARLAY_COLUMN_INDEX = 8
BETS_PARLAY_ID_COLUMN_INDEX = 9
BETS_RESULT_COLUMN_INDEX = 10
BETS_PROFIT_LOSS_COLUMN_INDEX = 12
BETS_PARLAY_RESULT_COLUMN_INDEX = 13
BETS_PARLAY_PROFIT_LOSS_COLUMN_INDEX = 14
BETS_GPT_PICK_COLUMN_INDEX = 15
BETS_GPT_RESULT_COLUMN_INDEX = 16
BETS_GPT_PROFIT_LOSS_COLUMN_INDEX = 17


@dataclass(frozen=True)
class DailySlatePickRow:
    """Daily_Slate row data needed for result grading."""

    row_number: int
    date: str
    away_team: str
    home_team: str
    my_pick: str
    pick_type: str
    result: str


@dataclass(frozen=True)
class BetsRow:
    """Bets row data needed for result grading."""

    row_number: int
    date: str
    game: str
    bet_type: str
    pick: str
    line: float | None
    odds: float | None
    stake: float | None
    in_parlay: str
    parlay_id: str
    result: str
    profit_loss: str
    parlay_result: str
    parlay_profit_loss: str
    gpt_pick: str
    gpt_result: str
    gpt_profit_loss: str


def read_daily_slate_pick_rows() -> list[DailySlatePickRow]:
    """Read Daily_Slate rows that may need result grading."""
    rows = get_values("Daily_Slate!A:AX")
    pick_rows = []

    for index, row in enumerate(rows, start=1):
        if _is_header_row(row):
            continue
        if len(row) <= MY_PICK_COLUMN_INDEX:
            continue

        pick_rows.append(
            DailySlatePickRow(
                row_number=index,
                date=normalize_sheet_date(_cell(row, DATE_COLUMN_INDEX)),
                away_team=str(_cell(row, AWAY_TEAM_COLUMN_INDEX)).strip(),
                home_team=str(_cell(row, HOME_TEAM_COLUMN_INDEX)).strip(),
                my_pick=str(_cell(row, MY_PICK_COLUMN_INDEX)).strip(),
                pick_type=str(_cell(row, PICK_TYPE_COLUMN_INDEX)).strip(),
                result=str(_cell(row, RESULT_COLUMN_INDEX)).strip(),
            )
        )

    return pick_rows


def read_bets_rows() -> list[BetsRow]:
    """Read Bets rows that may need result grading."""
    rows = get_values("Bets!A:R")
    bets_rows = []

    for index, row in enumerate(rows, start=1):
        if _is_bets_header_row(row):
            continue
        if len(row) <= BETS_PICK_COLUMN_INDEX:
            continue

        bets_rows.append(
            BetsRow(
                row_number=index,
                date=normalize_sheet_date(_cell(row, BETS_DATE_COLUMN_INDEX)),
                game=str(_cell(row, BETS_GAME_COLUMN_INDEX)).strip(),
                bet_type=str(_cell(row, BETS_BET_TYPE_COLUMN_INDEX)).strip(),
                pick=str(_cell(row, BETS_PICK_COLUMN_INDEX)).strip(),
                line=_parse_line(_cell(row, BETS_LINE_COLUMN_INDEX)),
                odds=_parse_line(_cell(row, BETS_ODDS_COLUMN_INDEX)),
                stake=_parse_line(_cell(row, BETS_STAKE_COLUMN_INDEX)),
                in_parlay=str(_cell(row, BETS_IN_PARLAY_COLUMN_INDEX)).strip(),
                parlay_id=str(_cell(row, BETS_PARLAY_ID_COLUMN_INDEX)).strip(),
                result=str(_cell(row, BETS_RESULT_COLUMN_INDEX)).strip(),
                profit_loss=str(_cell(row, BETS_PROFIT_LOSS_COLUMN_INDEX)).strip(),
                parlay_result=str(_cell(row, BETS_PARLAY_RESULT_COLUMN_INDEX)).strip(),
                parlay_profit_loss=str(
                    _cell(row, BETS_PARLAY_PROFIT_LOSS_COLUMN_INDEX)
                ).strip(),
                gpt_pick=str(_cell(row, BETS_GPT_PICK_COLUMN_INDEX)).strip(),
                gpt_result=str(_cell(row, BETS_GPT_RESULT_COLUMN_INDEX)).strip(),
                gpt_profit_loss=str(
                    _cell(row, BETS_GPT_PROFIT_LOSS_COLUMN_INDEX)
                ).strip(),
            )
        )

    return bets_rows


def _cell(row: list[Any], index: int) -> Any:
    if index >= len(row):
        return ""
    return row[index]


def _is_header_row(row: list[Any]) -> bool:
    return [str(value).strip() for value in row[:3]] == DAILY_SLATE_COLUMNS[:3]


def _is_bets_header_row(row: list[Any]) -> bool:
    return [str(value).strip() for value in row[:3]] == BETS_COLUMNS[:3]


def _parse_line(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except ValueError:
        return None
