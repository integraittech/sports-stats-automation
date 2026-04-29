"""Tests for NHL slate normalization."""

from __future__ import annotations

from datetime import datetime
import unittest

from src.nhl.slate import normalize_schedule


class NhlSlateTests(unittest.TestCase):
    def test_normalize_schedule_formats_start_time_from_start_time_utc_in_local_timezone(
        self,
    ) -> None:
        schedule = {
            "games": [
                {
                    "id": 1,
                    "gameDate": "2026-04-20",
                    "startTimeUTC": "2026-04-21T02:00:00Z",
                    "awayTeam": {"abbrev": "EDM", "placeName": {"default": "Edmonton"}, "commonName": {"default": "Oilers"}},
                    "homeTeam": {"abbrev": "LAK", "placeName": {"default": "Los Angeles"}, "commonName": {"default": "Kings"}},
                }
            ]
        }

        games = normalize_schedule(schedule, "2026-04-20")

        expected_time = (
            datetime.fromisoformat("2026-04-21T02:00:00+00:00")
            .astimezone()
            .strftime("%-I:%M %p")
        )
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0].start_time, expected_time)

    def test_normalize_schedule_falls_back_to_game_date_time_for_start_time(self) -> None:
        schedule = {
            "games": [
                {
                    "id": 1,
                    "gameDate": "2026-04-20",
                    "gameDateTime": "2026-04-21T03:30:00Z",
                    "awayTeam": {"abbrev": "TOR", "placeName": {"default": "Toronto"}, "commonName": {"default": "Maple Leafs"}},
                    "homeTeam": {"abbrev": "OTT", "placeName": {"default": "Ottawa"}, "commonName": {"default": "Senators"}},
                }
            ]
        }

        games = normalize_schedule(schedule, "2026-04-20")

        expected_time = (
            datetime.fromisoformat("2026-04-21T03:30:00+00:00")
            .astimezone()
            .strftime("%-I:%M %p")
        )
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0].start_time, expected_time)


if __name__ == "__main__":
    unittest.main()
