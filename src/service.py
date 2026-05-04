"""Railway API service for BetTracker automations."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from src.main_daily_slate import build_report_row
from src.nhl.slate import get_slate_for_date, get_today_string
from src.sheets.writer import append_daily_slate_rows


app = FastAPI(title="BetTracker Automation Service")


class DailySlateRefreshResponse(BaseModel):
    start_date: str
    end_date: str
    inserted: int
    skipped: int
    dates: list[dict[str, Any]]


def _clean_token(value: str | None) -> str:
    return (value or "").strip().strip("\"").strip("'")


def _check_refresh_token(authorization: str | None) -> None:
    load_dotenv()
    expected_token = _clean_token(os.getenv("DAILY_SLATE_REFRESH_TOKEN"))
    if not expected_token:
        raise HTTPException(status_code=500, detail="Missing DAILY_SLATE_REFRESH_TOKEN.")

    header_value = (authorization or "").strip()
    bearer_prefix = "Bearer "
    provided_token = (
        header_value[len(bearer_prefix):]
        if header_value.startswith(bearer_prefix)
        else header_value
    )
    provided_token = _clean_token(provided_token)

    if provided_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized.")


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _date_range(start_date: date, end_date: date) -> list[str]:
    day_count = (end_date - start_date).days + 1
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range(day_count)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/daily-slate/refresh", response_model=DailySlateRefreshResponse)
def refresh_daily_slate(
    start: str | None = None,
    end: str | None = None,
    authorization: str | None = Header(default=None),
) -> DailySlateRefreshResponse:
    """Refresh Daily_Slate rows for a date range, defaulting to today and tomorrow."""
    _check_refresh_token(authorization)

    if start or end:
        if not start or not end:
            raise HTTPException(status_code=400, detail="Provide both start and end, or neither.")
        start_date = _parse_date(start)
        end_date = _parse_date(end)
    else:
        start_date = _parse_date(get_today_string())
        end_date = start_date + timedelta(days=1)

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start must be on or before end.")

    total_inserted = 0
    total_skipped = 0
    date_summaries: list[dict[str, Any]] = []

    for date_string in _date_range(start_date, end_date):
        slate_games = get_slate_for_date(date_string)
        rows = [build_report_row(date_string, game) for game in slate_games]
        result = append_daily_slate_rows(rows)

        total_inserted += result.written_count
        total_skipped += result.duplicate_count
        date_summaries.append(
            {
                "date": date_string,
                "games": len(slate_games),
                "inserted": result.written_count,
                "skipped": result.duplicate_count,
            }
        )

    return DailySlateRefreshResponse(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        inserted=total_inserted,
        skipped=total_skipped,
        dates=date_summaries,
    )
