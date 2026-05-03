"""Tests for NHL history filtering helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.nhl import history


class NhlHistoryTests(unittest.TestCase):
    def test_get_last_completed_games_filters_to_games_before_before_date(self) -> None:
        schedule = {
            "games": [
                {
                    "id": 1,
                    "gameDate": "2026-04-28",
                    "gameState": "OFF",
                    "gameType": 2,
                    "awayTeam": {"abbrev": "EDM", "id": 1, "score": 4},
                    "homeTeam": {"abbrev": "LAK", "id": 2, "score": 2},
                },
                {
                    "id": 2,
                    "gameDate": "2026-04-27",
                    "gameState": "OFF",
                    "gameType": 2,
                    "awayTeam": {"abbrev": "VAN", "id": 3, "score": 3},
                    "homeTeam": {"abbrev": "EDM", "id": 1, "score": 5},
                },
                {
                    "id": 3,
                    "gameDate": "2026-04-26",
                    "gameState": "OFF",
                    "gameType": 2,
                    "awayTeam": {"abbrev": "EDM", "id": 1, "score": 1},
                    "homeTeam": {"abbrev": "SEA", "id": 4, "score": 2},
                },
            ]
        }

        with (
            patch.object(history, "get_club_schedule_now", return_value=schedule),
            patch.object(history, "_first_period_scores", return_value=(0, 0)),
        ):
            games = history.get_last_completed_games(
                "EDM",
                limit=5,
                before_date="2026-04-28",
            )

        self.assertEqual([game.game_date for game in games], ["2026-04-27", "2026-04-26"])

    def test_get_last_completed_games_excludes_playoff_games_when_game_type_is_regular_season(
        self,
    ) -> None:
        schedule = {
            "games": [
                {
                    "id": 1,
                    "gameDate": "2026-04-28",
                    "gameState": "OFF",
                    "gameType": 3,
                    "awayTeam": {"abbrev": "EDM", "id": 1, "score": 4},
                    "homeTeam": {"abbrev": "LAK", "id": 2, "score": 2},
                },
                {
                    "id": 2,
                    "gameDate": "2026-04-27",
                    "gameState": "OFF",
                    "gameType": 2,
                    "awayTeam": {"abbrev": "VAN", "id": 3, "score": 3},
                    "homeTeam": {"abbrev": "EDM", "id": 1, "score": 5},
                },
            ]
        }

        with (
            patch.object(history, "get_club_schedule_now", return_value=schedule),
            patch.object(history, "_first_period_scores", return_value=(0, 0)),
        ):
            games = history.get_last_completed_games(
                "EDM",
                limit=5,
                game_type=2,
            )

        self.assertEqual([game.game_id for game in games], [2])

    def test_get_last_head_to_head_games_filters_across_current_and_previous_seasons(
        self,
    ) -> None:
        current_schedule = {
            "previousSeason": 20252026,
            "games": [
                {
                    "id": 10,
                    "gameDate": "2026-04-28",
                    "gameState": "OFF",
                    "gameType": 2,
                    "awayTeam": {"abbrev": "EDM", "id": 1, "score": 4},
                    "homeTeam": {"abbrev": "LAK", "id": 2, "score": 2},
                },
                {
                    "id": 11,
                    "gameDate": "2026-04-01",
                    "gameState": "OFF",
                    "gameType": 2,
                    "awayTeam": {"abbrev": "LAK", "id": 2, "score": 3},
                    "homeTeam": {"abbrev": "EDM", "id": 1, "score": 5},
                },
            ],
        }
        previous_schedule = {
            "games": [
                {
                    "id": 12,
                    "gameDate": "2025-12-15",
                    "gameState": "OFF",
                    "gameType": 2,
                    "awayTeam": {"abbrev": "EDM", "id": 1, "score": 2},
                    "homeTeam": {"abbrev": "LAK", "id": 2, "score": 1},
                }
            ]
        }

        with (
            patch.object(history, "get_club_schedule_now", return_value=current_schedule),
            patch.object(
                history,
                "get_club_schedule_season",
                side_effect=[previous_schedule] + [{"games": []}] * 6,
            ),
            patch.object(history, "_first_period_scores", return_value=(1, 0)),
        ):
            games = history.get_last_head_to_head_games(
                "EDM",
                "LAK",
                limit=10,
                before_date="2026-04-28",
            )

        self.assertEqual(
            [game.game_date for game in games],
            ["2026-04-01", "2025-12-15"],
        )

    def test_get_last_head_to_head_games_excludes_playoff_games_when_game_type_is_regular_season(
        self,
    ) -> None:
        current_schedule = {
            "previousSeason": 20252026,
            "games": [
                {
                    "id": 10,
                    "gameDate": "2026-04-28",
                    "gameState": "OFF",
                    "gameType": 3,
                    "awayTeam": {"abbrev": "EDM", "id": 1, "score": 4},
                    "homeTeam": {"abbrev": "LAK", "id": 2, "score": 2},
                },
                {
                    "id": 11,
                    "gameDate": "2026-04-01",
                    "gameState": "OFF",
                    "gameType": 2,
                    "awayTeam": {"abbrev": "LAK", "id": 2, "score": 3},
                    "homeTeam": {"abbrev": "EDM", "id": 1, "score": 5},
                },
            ],
        }

        with (
            patch.object(history, "get_club_schedule_now", return_value=current_schedule),
            patch.object(
                history,
                "get_club_schedule_season",
                side_effect=[{"games": []}] * 7,
            ),
            patch.object(history, "_first_period_scores", return_value=(1, 0)),
        ):
            games = history.get_last_head_to_head_games(
                "EDM",
                "LAK",
                limit=10,
                game_type=2,
            )

        self.assertEqual([game.game_id for game in games], [11])


if __name__ == "__main__":
    unittest.main()
