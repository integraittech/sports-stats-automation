"""Small NHL API client for public schedule data."""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv


DEFAULT_BASE_URL = "https://api-web.nhle.com"


def get_base_url() -> str:
    """Return the configured NHL API base URL."""
    load_dotenv()
    return os.getenv("NHL_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def get_schedule(date_string: str) -> dict[str, Any]:
    """Fetch the NHL schedule for a date in YYYY-MM-DD format."""
    url = f"{get_base_url()}/v1/schedule/{date_string}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


def get_club_schedule_now(team_abbrev: str) -> dict[str, Any]:
    """Fetch the current season schedule for one NHL team."""
    url = f"{get_base_url()}/v1/club-schedule-season/{team_abbrev}/now"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()
