"""Tests for Playoff_Trends row generation."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from src.nhl.playoff_trends import build_playoff_trend_row
from src.nhl.slate import SlateGame


def _schedule_game(
    game_id: int,
    game_date: str,
    away: str,
    home: str,
    *,
    state: str = "OFF",
    game_type: int = 3,
    series_number: int | None = None,
) -> dict[str, object]:
    game: dict[str, object] = {
        "id": game_id,
        "gameDate": game_date,
        "gameState": state,
        "gameType": game_type,
        "awayTeam": {"abbrev": away},
        "homeTeam": {"abbrev": home},
    }
    if series_number is not None:
        game["seriesStatus"] = {"gameNumberOfSeries": series_number}
    return game


def _play_detail(
    game_id: int,
    away: str,
    home: str,
    away_score: int,
    home_score: int,
    *,
    away_sog: int = 0,
    home_sog: int = 0,
    first_period_away_shots: int = 0,
    first_period_home_shots: int = 0,
    first_period_goals: tuple[int, int] = (0, 0),
) -> dict[str, object]:
    away_id = game_id * 10 + 1
    home_id = game_id * 10 + 2
    plays: list[dict[str, object]] = []

    for _ in range(first_period_away_shots):
        plays.append(
            {
                "typeDescKey": "shot-on-goal",
                "periodDescriptor": {"number": 1},
                "details": {"eventOwnerTeamId": away_id},
            }
        )
    for _ in range(first_period_home_shots):
        plays.append(
            {
                "typeDescKey": "shot-on-goal",
                "periodDescriptor": {"number": 1},
                "details": {"eventOwnerTeamId": home_id},
            }
        )
    for _ in range(first_period_goals[0]):
        plays.append(
            {
                "typeDescKey": "goal",
                "periodDescriptor": {"number": 1},
                "details": {"eventOwnerTeamId": away_id},
            }
        )
    for _ in range(first_period_goals[1]):
        plays.append(
            {
                "typeDescKey": "goal",
                "periodDescriptor": {"number": 1},
                "details": {"eventOwnerTeamId": home_id},
            }
        )

    return {
        "id": game_id,
        "awayTeam": {"abbrev": away, "id": away_id, "score": away_score, "sog": away_sog},
        "homeTeam": {"abbrev": home, "id": home_id, "score": home_score, "sog": home_sog},
        "plays": plays,
        "periodDescriptor": {"number": 3},
    }


class PlayoffTrendTests(unittest.TestCase):
    def test_build_playoff_trend_row_excludes_same_day_and_later_games(self) -> None:
        game = SlateGame(
            game_id=7,
            away_team_abbrev="MTL",
            away_team="Montreal Canadiens",
            home_team_abbrev="BUF",
            home_team="Buffalo Sabres",
            start_time="7:00 PM",
        )
        schedule = {
            "games": [
                _schedule_game(1, "2026-05-10", "MTL", "BUF"),
                _schedule_game(2, "2026-05-12", "BUF", "MTL"),
                _schedule_game(3, "2026-05-16", "BUF", "MTL"),
                _schedule_game(4, "2026-05-18", "MTL", "BUF", series_number=4),
                _schedule_game(5, "2026-05-20", "BUF", "MTL"),
            ]
        }
        details = {
            1: _play_detail(1, "MTL", "BUF", 3, 2, first_period_goals=(1, 1)),
            2: _play_detail(2, "BUF", "MTL", 4, 3, first_period_goals=(2, 0)),
            3: _play_detail(3, "BUF", "MTL", 5, 1, first_period_goals=(1, 2)),
        }

        with (
            patch("src.nhl.playoff_trends.get_club_schedule_season", return_value=schedule),
            patch(
                "src.nhl.playoff_trends.get_game_play_by_play",
                side_effect=lambda game_id, fresh=False: details[game_id],
            ),
        ):
            result = build_playoff_trend_row("2026-05-18", game)

        self.assertEqual(json.loads(result.row[7]), [2, 2, 3])
        self.assertEqual(json.loads(result.row[14]), [5, 7, 6])
        self.assertEqual(result.row[4], 4)

    def test_build_playoff_trend_row_includes_prior_games_regardless_of_orientation(self) -> None:
        game = SlateGame(
            game_id=7,
            away_team_abbrev="MTL",
            away_team="Montreal Canadiens",
            home_team_abbrev="BUF",
            home_team="Buffalo Sabres",
            start_time="7:00 PM",
        )
        schedule = {
            "games": [
                _schedule_game(1, "2026-05-10", "MTL", "BUF"),
                _schedule_game(2, "2026-05-12", "BUF", "MTL"),
                _schedule_game(7, "2026-05-18", "MTL", "BUF", state="FUT", series_number=3),
            ]
        }
        details = {
            1: _play_detail(1, "MTL", "BUF", 3, 2, first_period_goals=(1, 0)),
            2: _play_detail(2, "BUF", "MTL", 4, 1, first_period_goals=(0, 2)),
        }

        with (
            patch("src.nhl.playoff_trends.get_club_schedule_season", return_value=schedule),
            patch(
                "src.nhl.playoff_trends.get_game_play_by_play",
                side_effect=lambda game_id, fresh=False: details[game_id],
            ),
        ):
            result = build_playoff_trend_row("2026-05-18", game)

        self.assertEqual(json.loads(result.row[7]), [1, 2])
        self.assertEqual(json.loads(result.row[14]), [5, 5])

    def test_build_playoff_trend_row_buf_mtl_series_uses_six_completed_games_before_may_18(self) -> None:
        game = SlateGame(
            game_id=107,
            away_team_abbrev="MTL",
            away_team="Montreal Canadiens",
            home_team_abbrev="BUF",
            home_team="Buffalo Sabres",
            start_time="7:00 PM",
        )
        schedule = {
            "games": [
                _schedule_game(101, "2026-05-06", "MTL", "BUF"),
                _schedule_game(102, "2026-05-08", "BUF", "MTL"),
                _schedule_game(103, "2026-05-10", "MTL", "BUF"),
                _schedule_game(104, "2026-05-12", "BUF", "MTL"),
                _schedule_game(105, "2026-05-14", "MTL", "BUF"),
                _schedule_game(106, "2026-05-16", "BUF", "MTL"),
                _schedule_game(107, "2026-05-18", "MTL", "BUF", state="FUT", series_number=7),
            ]
        }
        details = {
            101: _play_detail(101, "MTL", "BUF", 2, 4, first_period_goals=(1, 2)),
            102: _play_detail(102, "BUF", "MTL", 5, 1, first_period_goals=(1, 1)),
            103: _play_detail(103, "MTL", "BUF", 5, 3, first_period_goals=(1, 1)),
            104: _play_detail(104, "BUF", "MTL", 3, 2, first_period_goals=(2, 1)),
            105: _play_detail(105, "MTL", "BUF", 5, 4, first_period_goals=(2, 3)),
            106: _play_detail(
                106,
                "BUF",
                "MTL",
                8,
                3,
                away_sog=36,
                home_sog=29,
                first_period_away_shots=7,
                first_period_home_shots=9,
                first_period_goals=(2, 3),
            ),
        }

        with (
            patch("src.nhl.playoff_trends.get_club_schedule_season", return_value=schedule),
            patch(
                "src.nhl.playoff_trends.get_game_play_by_play",
                side_effect=lambda game_id, fresh=False: details[game_id],
            ),
        ):
            result = build_playoff_trend_row("2026-05-18", game)

        self.assertEqual(result.row[0], "2026-05-18_mtl_buf")
        self.assertEqual(result.row[4], 7)
        self.assertEqual(result.row[5], 4)
        self.assertEqual(result.row[6], 2)
        self.assertEqual(json.loads(result.row[7]), [3, 2, 2, 3, 5, 5])
        self.assertEqual(json.loads(result.row[14]), [6, 6, 8, 5, 9, 11])
        self.assertEqual(result.row[16], 11)
        self.assertEqual(result.row[17], 8)
        self.assertEqual(result.row[18], 3)


if __name__ == "__main__":
    unittest.main()
