"""Small NHL API client for public schedule data."""

from __future__ import annotations

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv


DEFAULT_BASE_URL = "https://api-web.nhle.com"
REQUEST_TIMEOUT_SECONDS = 10
REQUEST_RETRY_COUNT = 3
REQUEST_RETRY_DELAY_SECONDS = 1.5
_RESPONSE_CACHE: dict[str, dict[str, Any]] = {}


def get_base_url() -> str:
    """Return the configured NHL API base URL."""
    load_dotenv()
    return os.getenv("NHL_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def clear_response_cache() -> None:
    """Clear cached NHL API responses for a fresh refresh run."""
    _RESPONSE_CACHE.clear()


def _get_json(url: str, *, use_cache: bool = True) -> dict[str, Any]:
    """Fetch JSON with retry/backoff and optional in-process caching."""
    if use_cache and url in _RESPONSE_CACHE:
        return _RESPONSE_CACHE[url]

    last_response = None

    for attempt in range(REQUEST_RETRY_COUNT + 1):
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        last_response = response

        if response.status_code != 429:
            response.raise_for_status()
            data = response.json()
            _RESPONSE_CACHE[url] = data
            return data

        if attempt < REQUEST_RETRY_COUNT:
            retry_after = response.headers.get("Retry-After")
            try:
                delay = float(retry_after) if retry_after else REQUEST_RETRY_DELAY_SECONDS * (attempt + 1)
            except ValueError:
                delay = REQUEST_RETRY_DELAY_SECONDS * (attempt + 1)
            time.sleep(delay)

    assert last_response is not None
    last_response.raise_for_status()
    return last_response.json()


def get_schedule(date_string: str, *, fresh: bool = False) -> dict[str, Any]:
    """Fetch the NHL schedule for a date in YYYY-MM-DD format."""
    url = f"{get_base_url()}/v1/schedule/{date_string}"
    return _get_json(url, use_cache=not fresh)


def get_club_schedule_now(team_abbrev: str, *, fresh: bool = False) -> dict[str, Any]:
    """Fetch the current season schedule for one NHL team."""
    url = f"{get_base_url()}/v1/club-schedule-season/{team_abbrev}/now"
    return _get_json(url, use_cache=not fresh)


def get_club_schedule_season(
    team_abbrev: str,
    season: int,
    *,
    fresh: bool = False,
) -> dict[str, Any]:
    """Fetch one season schedule for one NHL team."""
    url = f"{get_base_url()}/v1/club-schedule-season/{team_abbrev}/{season}"
    return _get_json(url, use_cache=not fresh)


def get_game_play_by_play(game_id: int, *, fresh: bool = False) -> dict[str, Any]:
    """Fetch play-by-play data for one NHL game."""
    url = f"{get_base_url()}/v1/gamecenter/{game_id}/play-by-play"
    return _get_json(url, use_cache=not fresh)
