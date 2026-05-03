"""Tests for Daily_Slate backfill orchestration."""

from __future__ import annotations

from datetime import date
import unittest
from unittest.mock import call, patch

from src.nhl.slate import SlateGame
from src.sheets.writer import DailySlateWriteResult


def test_default_run_fetches_last_three_days(monkeypatch):
    """No CLI args should fetch today and tomorrow."""
    from src import main_daily_slate

    seen_dates: list[str] = []

    monkeypatch.setattr(main_daily_slate, "get_today_string", lambda: "2026-04-27")

    def fake_get_slate_for_date(date_string: str) -> list[SlateGame]:
        seen_dates.append(date_string)
        return []

    monkeypatch.setattr(main_daily_slate, "get_slate_for_date", fake_get_slate_for_date)
    monkeypatch.setattr(
        main_daily_slate,
        "append_daily_slate_rows",
        lambda rows: DailySlateWriteResult(written_count=len(rows), duplicate_count=0),
    )

    main_daily_slate.main([])

    assert seen_dates == ["2026-04-27", "2026-04-28"]


def test_explicit_backfill_builds_rows_for_each_date_before_append(monkeypatch):
    """Explicit start/end args should backfill every date inclusively."""
    from src import main_daily_slate

    game = SlateGame(
        game_id=1,
        away_team_abbrev="EDM",
        away_team="Edmonton Oilers",
        home_team_abbrev="LAK",
        home_team="Los Angeles Kings",
        start_time="2026-04-15T02:00:00Z",
    )
    seen_dates: list[str] = []
    appended_rows: list[list[str | int | float]] = []

    def fake_get_slate_for_date(date_string: str) -> list[SlateGame]:
        seen_dates.append(date_string)
        return [game]

    def fake_build_report_row(date_string: str, slate_game: SlateGame) -> list[str]:
        return [date_string, slate_game.away_team, slate_game.home_team]

    def fake_append_daily_slate_rows(
        rows: list[list[str | int | float]],
    ) -> DailySlateWriteResult:
        appended_rows.extend(rows)
        return DailySlateWriteResult(written_count=2, duplicate_count=1)

    monkeypatch.setattr(main_daily_slate, "get_slate_for_date", fake_get_slate_for_date)
    monkeypatch.setattr(main_daily_slate, "build_report_row", fake_build_report_row)
    monkeypatch.setattr(
        main_daily_slate,
        "append_daily_slate_rows",
        fake_append_daily_slate_rows,
    )

    main_daily_slate.main(["--start", "2026-04-15", "--end", "2026-04-17"])

    assert seen_dates == ["2026-04-15", "2026-04-16", "2026-04-17"]
    assert appended_rows == [
        ["2026-04-15", "Edmonton Oilers", "Los Angeles Kings"],
        ["2026-04-16", "Edmonton Oilers", "Los Angeles Kings"],
        ["2026-04-17", "Edmonton Oilers", "Los Angeles Kings"],
    ]


class MainDailySlateBackfillTests(unittest.TestCase):
    def test_build_report_row_converts_date_to_iso_string_before_schema_build(
        self,
    ) -> None:
        from src import main_daily_slate

        game = SlateGame(
            game_id=1,
            away_team_abbrev="EDM",
            away_team="Edmonton Oilers",
            home_team_abbrev="LAK",
            home_team="Los Angeles Kings",
            start_time="2026-04-15T02:00:00Z",
        )

        with (
            patch.object(main_daily_slate, "get_last_head_to_head_games", return_value=[]),
            patch.object(main_daily_slate, "get_last_completed_games", return_value=[]),
            patch.object(main_daily_slate, "calculate_head_to_head_stats", return_value="h2h"),
            patch.object(main_daily_slate, "calculate_recent_team_stats", return_value="team"),
            patch.object(
                main_daily_slate,
                "build_daily_slate_row",
                return_value=["2026-04-15", "Edmonton Oilers", "Los Angeles Kings"],
            ) as build_row,
        ):
            result = main_daily_slate.build_report_row(date(2026, 4, 15), game)

        self.assertEqual(result, ["2026-04-15", "Edmonton Oilers", "Los Angeles Kings"])
        build_row.assert_called_once_with(
            date_string="2026-04-15",
            game=game,
            h2h_stats="h2h",
            away_stats="team",
            home_stats="team",
            away_last_10_stats="team",
            home_last_10_stats="team",
        )

    def test_build_report_row_passes_game_date_as_before_date_to_history_lookups(
        self,
    ) -> None:
        from src import main_daily_slate

        game = SlateGame(
            game_id=1,
            away_team_abbrev="EDM",
            away_team="Edmonton Oilers",
            home_team_abbrev="LAK",
            home_team="Los Angeles Kings",
            start_time="2026-04-15T02:00:00Z",
        )

        with (
            patch.object(
                main_daily_slate,
                "get_last_head_to_head_games",
                return_value=[],
            ) as get_h2h,
            patch.object(
                main_daily_slate,
                "get_last_completed_games",
                return_value=[],
            ) as get_games,
            patch.object(main_daily_slate, "calculate_head_to_head_stats", return_value="h2h"),
            patch.object(main_daily_slate, "calculate_recent_team_stats", return_value="team"),
            patch.object(
                main_daily_slate,
                "build_daily_slate_row",
                return_value=["2026-04-15", "Edmonton Oilers", "Los Angeles Kings"],
            ),
        ):
            main_daily_slate.build_report_row("2026-04-15", game)

        get_h2h.assert_called_once_with(
            "EDM",
            "LAK",
            before_date="2026-04-15",
            game_type=2,
        )
        self.assertEqual(
            get_games.call_args_list,
            [
                call("EDM", limit=5, before_date="2026-04-15", game_type=2),
                call("LAK", limit=5, before_date="2026-04-15", game_type=2),
                call("EDM", limit=10, before_date="2026-04-15", game_type=2),
                call("LAK", limit=10, before_date="2026-04-15", game_type=2),
            ],
        )

    def test_build_report_row_forwards_formatted_start_time_string(self) -> None:
        from src import main_daily_slate

        game = SlateGame(
            game_id=1,
            away_team_abbrev="EDM",
            away_team="Edmonton Oilers",
            home_team_abbrev="LAK",
            home_team="Los Angeles Kings",
            start_time="7:00 PM",
        )

        with (
            patch.object(main_daily_slate, "get_last_head_to_head_games", return_value=[]),
            patch.object(main_daily_slate, "get_last_completed_games", return_value=[]),
            patch.object(main_daily_slate, "calculate_head_to_head_stats", return_value="h2h"),
            patch.object(main_daily_slate, "calculate_recent_team_stats", return_value="team"),
            patch.object(
                main_daily_slate,
                "build_daily_slate_row",
                return_value=["2026-04-15", "Edmonton Oilers", "Los Angeles Kings", "7:00 PM"],
            ) as build_row,
        ):
            main_daily_slate.build_report_row("2026-04-15", game)

        passed_game = build_row.call_args.kwargs["game"]
        self.assertEqual(passed_game.start_time, "7:00 PM")
        self.assertIsInstance(passed_game.start_time, str)

    def test_logs_progress_counts_and_continues_after_fetch_error(self) -> None:
        from src import main_daily_slate

        game = SlateGame(
            game_id=1,
            away_team_abbrev="EDM",
            away_team="Edmonton Oilers",
            home_team_abbrev="LAK",
            home_team="Los Angeles Kings",
            start_time="2026-04-15T02:00:00Z",
        )
        appended_rows: list[list[str | int | float]] = []

        def fake_get_slate_for_date(date_string: str) -> list[SlateGame]:
            if date_string == "2026-04-16":
                raise TimeoutError("slow schedule response")
            if date_string == "2026-04-17":
                return []
            return [game, game]

        def fake_build_report_row(
            date_string: str,
            slate_game: SlateGame,
        ) -> list[str | int | float]:
            return [date_string, slate_game.away_team, slate_game.home_team]

        def fake_append_daily_slate_rows(
            rows: list[list[str | int | float]],
        ) -> DailySlateWriteResult:
            appended_rows.extend(rows)
            return DailySlateWriteResult(written_count=1, duplicate_count=1)

        with (
            patch.object(main_daily_slate, "get_slate_for_date", fake_get_slate_for_date),
            patch.object(main_daily_slate, "build_report_row", fake_build_report_row),
            patch.object(
                main_daily_slate,
                "append_daily_slate_rows",
                fake_append_daily_slate_rows,
            ),
            patch.object(main_daily_slate.time, "sleep") as sleep,
            patch("builtins.print") as print_mock,
        ):
            main_daily_slate.main(["--start", "2026-04-15", "--end", "2026-04-17"])

        self.assertEqual(
            appended_rows,
            [
                ["2026-04-15", "Edmonton Oilers", "Los Angeles Kings"],
                ["2026-04-15", "Edmonton Oilers", "Los Angeles Kings"],
            ],
        )
        sleep.assert_has_calls([call(0.3), call(0.3), call(0.3)])
        print_mock.assert_any_call("Processing 2026-04-15...")
        print_mock.assert_any_call("Fetched 2 games")
        print_mock.assert_any_call("Inserted 1, Skipped 1")
        print_mock.assert_any_call("Failed 2026-04-16, skipping")
        print_mock.assert_any_call("Processing 2026-04-17...")
        print_mock.assert_any_call("Fetched 0 games")
        print_mock.assert_any_call("No NHL games found for 2026-04-17.")
        print_mock.assert_any_call("Summary: Inserted 1, Skipped 1")
