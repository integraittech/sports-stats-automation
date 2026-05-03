"""Tests for NHL calculation helpers."""

from __future__ import annotations

import unittest

from src.nhl.calculations import (
    calculate_head_to_head_stats,
    calculate_recent_team_stats,
)
from src.nhl.history import H2HGameResult, TeamGameResult
from src.nhl.slate import SlateGame
from src.sheets.schemas import DAILY_SLATE_COLUMNS, build_daily_slate_row


class NhlCalculationsTests(unittest.TestCase):
    def test_calculate_recent_team_stats_uses_raw_game_results_for_totals_and_record(
        self,
    ) -> None:
        games = [
        TeamGameResult(
            game_id=1,
            game_date="2026-04-20",
            opponent="Los Angeles Kings",
            team_score=4,
            opponent_score=2,
            first_period_team_score=1,
            first_period_opponent_score=1,
        ),
        TeamGameResult(
            game_id=2,
            game_date="2026-04-18",
            opponent="Vegas Golden Knights",
            team_score=2,
            opponent_score=5,
            first_period_team_score=0,
            first_period_opponent_score=1,
        ),
        TeamGameResult(
            game_id=3,
            game_date="2026-04-16",
            opponent="Calgary Flames",
            team_score=3,
            opponent_score=2,
            first_period_team_score=1,
            first_period_opponent_score=0,
        ),
        TeamGameResult(
            game_id=4,
            game_date="2026-04-14",
            opponent="Vancouver Canucks",
            team_score=1,
            opponent_score=4,
            first_period_team_score=0,
            first_period_opponent_score=0,
        ),
        TeamGameResult(
            game_id=5,
            game_date="2026-04-12",
            opponent="Seattle Kraken",
            team_score=5,
            opponent_score=3,
            first_period_team_score=2,
            first_period_opponent_score=0,
        ),
        ]

        stats = calculate_recent_team_stats(games)

        self.assertEqual(stats.total_goals_for, 15)
        self.assertEqual(stats.total_goals_against, 16)
        self.assertEqual(stats.total_goals, 31)
        self.assertEqual(stats.record, "3-2")
        self.assertEqual(stats.first_period_scored_count, 3)
        self.assertEqual(stats.first_period_zero_goal_count, 1)
        self.assertEqual(stats.first_period_two_plus_goal_count, 1)

    def test_calculate_recent_team_stats_counts_games_where_team_scored_in_first_period(
        self,
    ) -> None:
        games = [
            TeamGameResult(1, "2026-04-20", "A", 4, 2, 1, 0),
            TeamGameResult(2, "2026-04-18", "B", 2, 5, 0, 1),
            TeamGameResult(3, "2026-04-16", "C", 3, 2, 1, 1),
            TeamGameResult(4, "2026-04-14", "D", 1, 4, 2, 0),
            TeamGameResult(5, "2026-04-12", "E", 5, 3, 0, 0),
        ]

        stats = calculate_recent_team_stats(games)

        self.assertEqual(stats.first_period_scored_count, 3)
        self.assertEqual(stats.first_period_zero_goal_count, 1)
        self.assertEqual(stats.first_period_two_plus_goal_count, 1)

    def test_calculate_recent_team_stats_counts_two_plus_first_period_goals_for_team_only(
        self,
    ) -> None:
        games = [
            TeamGameResult(1, "2026-04-20", "A", 4, 2, 1, 1),
            TeamGameResult(2, "2026-04-18", "B", 2, 5, 0, 2),
            TeamGameResult(3, "2026-04-16", "C", 3, 2, 2, 0),
            TeamGameResult(4, "2026-04-14", "D", 1, 4, 3, 1),
            TeamGameResult(5, "2026-04-12", "E", 5, 3, 1, 0),
        ]

        stats = calculate_recent_team_stats(games)

        self.assertEqual(stats.first_period_over_1_5_count, 4)
        self.assertEqual(stats.first_period_two_plus_goal_count, 2)

    def test_calculate_recent_team_stats_handles_ten_game_window_record_and_totals(
        self,
    ) -> None:
        games = [
        TeamGameResult(
            game_id=index,
            game_date=f"2026-04-{30 - index:02d}",
            opponent=f"Opponent {index}",
            team_score=4 if index % 2 else 2,
            opponent_score=1 if index % 2 else 3,
            first_period_team_score=1,
            first_period_opponent_score=0 if index % 3 else 1,
        )
        for index in range(1, 11)
        ]

        stats = calculate_recent_team_stats(games)

        self.assertEqual(stats.total_goals_for, 30)
        self.assertEqual(stats.total_goals_against, 20)
        self.assertEqual(stats.total_goals, 50)
        self.assertEqual(stats.record, "5-5")

    def test_calculate_head_to_head_stats_exposes_last_game_scores(self) -> None:
        games = [
        H2HGameResult(
            game_id=1,
            game_date="2026-04-20",
            away_team="Edmonton Oilers",
            home_team="Los Angeles Kings",
            away_score=4,
            home_score=3,
            first_period_away_score=2,
            first_period_home_score=1,
        ),
        H2HGameResult(
            game_id=2,
            game_date="2026-03-15",
            away_team="Los Angeles Kings",
            home_team="Edmonton Oilers",
            away_score=2,
            home_score=5,
            first_period_away_score=0,
            first_period_home_score=2,
        ),
        ]

        stats = calculate_head_to_head_stats(games)

        self.assertEqual(stats.last_h2h_first_period_score, "2-1")
        self.assertEqual(stats.last_h2h_full_game_score, "4-3")

    def test_build_daily_slate_row_appends_new_research_fields_beside_existing_schema(
        self,
    ) -> None:
        game = SlateGame(
        game_id=1,
        away_team_abbrev="EDM",
        away_team="Edmonton Oilers",
        home_team_abbrev="LAK",
        home_team="Los Angeles Kings",
        start_time="7:00 PM",
        )
        h2h_stats = calculate_head_to_head_stats(
            [
                H2HGameResult(
                    game_id=1,
                    game_date="2026-04-20",
                    away_team="Edmonton Oilers",
                    home_team="Los Angeles Kings",
                    away_score=4,
                    home_score=3,
                    first_period_away_score=2,
                    first_period_home_score=1,
                )
            ]
        )
        away_last_5 = calculate_recent_team_stats(
            [
                TeamGameResult(1, "2026-04-20", "A", 4, 2, 1, 1),
                TeamGameResult(2, "2026-04-18", "B", 2, 5, 0, 1),
                TeamGameResult(3, "2026-04-16", "C", 3, 2, 1, 0),
                TeamGameResult(4, "2026-04-14", "D", 1, 4, 0, 0),
                TeamGameResult(5, "2026-04-12", "E", 5, 3, 2, 0),
            ]
        )
        home_last_5 = calculate_recent_team_stats(
            [
                TeamGameResult(6, "2026-04-20", "A", 3, 2, 1, 0),
                TeamGameResult(7, "2026-04-18", "B", 6, 1, 2, 0),
                TeamGameResult(8, "2026-04-16", "C", 2, 4, 0, 1),
                TeamGameResult(9, "2026-04-14", "D", 4, 3, 1, 1),
                TeamGameResult(10, "2026-04-12", "E", 1, 2, 0, 0),
            ]
        )
        away_last_10 = calculate_recent_team_stats(
            [
                TeamGameResult(
                    i,
                    f"2026-04-{30 - i:02d}",
                    f"Opp {i}",
                    4 if i % 2 else 2,
                    1 if i % 2 else 3,
                    1,
                    0 if i % 3 else 1,
                )
                for i in range(1, 11)
            ]
        )
        home_last_10 = calculate_recent_team_stats(
            [
                TeamGameResult(
                    i + 10,
                    f"2026-04-{20 - i:02d}",
                    f"Opp {i}",
                    5 if i % 2 else 1,
                    2 if i % 2 else 4,
                    1,
                    0 if i % 4 else 1,
                )
                for i in range(1, 11)
            ]
        )

        row = build_daily_slate_row(
            date_string="2026-04-20",
            game=game,
            h2h_stats=h2h_stats,
            away_stats=away_last_5,
            home_stats=home_last_5,
            away_last_10_stats=away_last_10,
            home_last_10_stats=home_last_10,
        )

        self.assertEqual(
            row[26:48],
            [
                "5-5",
                "2-1",
                "4-3",
                3,
                15,
                16,
                31,
                "5-5",
                3,
                16,
                12,
                28,
                30,
                20,
                50,
                30,
                30,
                60,
                10,
                3,
                10,
                2,
            ],
        )
        self.assertEqual(len(row), len(DAILY_SLATE_COLUMNS))
        self.assertEqual(DAILY_SLATE_COLUMNS[3], "Start Time")
        self.assertEqual(DAILY_SLATE_COLUMNS[29], "Away Last 5 Scored 1P Count")
        self.assertEqual(DAILY_SLATE_COLUMNS[34], "Home Last 5 Scored 1P Count")
        self.assertEqual(DAILY_SLATE_COLUMNS[44], "Away Last 10 1P Goals For")
        self.assertEqual(DAILY_SLATE_COLUMNS[45], "Away Last 10 1P Goals Against")
        self.assertEqual(DAILY_SLATE_COLUMNS[46], "Home Last 10 1P Goals For")
        self.assertEqual(DAILY_SLATE_COLUMNS[47], "Home Last 10 1P Goals Against")
        self.assertEqual(row[3], "7:00 PM")
        self.assertEqual(row[52], "")
        self.assertEqual(row[53], "")


if __name__ == "__main__":
    unittest.main()
