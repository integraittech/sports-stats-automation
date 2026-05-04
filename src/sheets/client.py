"""Minimal Google Sheets client."""

from __future__ import annotations

import json
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
    credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if credentials_json:
        credentials_info = json.loads(credentials_json)
        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=SCOPES,
        )
    elif credentials_path:
        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=SCOPES,
        )
    else:
        raise RuntimeError(
            "Missing Google credentials. Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS."
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


def append_values_raw(
    range_name: str,
    values: list[list[str | int | float]],
) -> dict[str, Any]:
    """Append rows without Google Sheets type coercion."""
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=get_spreadsheet_id(),
            range=range_name,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        )
        .execute()
    )
    return result


def update_values(
    range_name: str,
    values: list[list[str | int | float]],
) -> dict[str, Any]:
    """Update values in the configured spreadsheet."""
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=get_spreadsheet_id(),
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        )
        .execute()
    )
    return result


def update_values_raw(
    range_name: str,
    values: list[list[str | int | float]],
) -> dict[str, Any]:
    """Update values without Google Sheets type coercion."""
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=get_spreadsheet_id(),
            range=range_name,
            valueInputOption="RAW",
            body={"values": values},
        )
        .execute()
    )
    return result
