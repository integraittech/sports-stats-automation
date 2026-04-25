"""Minimal Google Sheets client."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_spreadsheet_id() -> str:
    """Return the configured Google Sheets spreadsheet ID."""
    load_dotenv()
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    if not spreadsheet_id:
        raise RuntimeError("Missing GOOGLE_SHEETS_SPREADSHEET_ID in environment.")
    return spreadsheet_id


def get_sheets_service() -> Any:
    """Create an authenticated Google Sheets API service."""
    load_dotenv()
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS in environment.")

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=credentials)


def get_values(range_name: str) -> list[list[Any]]:
    """Read values from the configured spreadsheet."""
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=get_spreadsheet_id(),
            range=range_name,
        )
        .execute()
    )
    return result.get("values", [])


def append_values(
    range_name: str,
    values: list[list[str | int | float]],
) -> dict[str, Any]:
    """Append rows to the configured spreadsheet."""
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=get_spreadsheet_id(),
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        )
        .execute()
    )
    return result
