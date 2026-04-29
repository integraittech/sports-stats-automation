"""Tests for Google Sheets write helpers."""

from __future__ import annotations

from datetime import date
import unittest
from unittest.mock import patch

from src.sheets import writer
from src.sheets.schemas import DAILY_SLATE_COLUMNS


class AppendDailySlateRowsTests(unittest.TestCase):
    def test_normalizes_date_column_to_iso_string_before_append(self) -> None:
        new_rows = [
            [date(2026, 4, 25), "Edmonton Oilers", "Los Angeles Kings"],
        ]

        with (
            patch.object(writer, "load_dotenv"),
            patch.object(writer, "get_values", return_value=[DAILY_SLATE_COLUMNS]),
            patch.object(writer, "ensure_daily_slate_headers"),
            patch.object(writer, "append_values_raw") as append_values_raw,
        ):
            result = writer.append_daily_slate_rows(new_rows)

        self.assertEqual(result.written_count, 1)
        self.assertEqual(result.duplicate_count, 0)
        expected_row = ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings"]
        expected_row.extend([""] * (len(DAILY_SLATE_COLUMNS) - len(expected_row) - 1))
        expected_row.append("2026-04-25_edmonton oilers_los angeles kings")
        append_values_raw.assert_called_once_with("Daily_Slate!A:AX", [expected_row])
        self.assertEqual(expected_row[48], "")
        self.assertEqual(
            expected_row[49],
            "2026-04-25_edmonton oilers_los angeles kings",
        )

    def test_skips_existing_rows_with_normalized_date_and_team_names(self) -> None:
        existing_rows = [
            DAILY_SLATE_COLUMNS,
            ["4/25/2026", " Edmonton Oilers ", "LOS ANGELES KINGS"],
        ]
        new_rows = [
            ["2026-04-25", "edmonton oilers", "los angeles kings"],
            ["2026-04-25", "Toronto Maple Leafs", "Ottawa Senators"],
        ]

        with (
            patch.object(writer, "load_dotenv"),
            patch.object(writer, "get_values", return_value=existing_rows),
            patch.object(writer, "ensure_daily_slate_headers"),
            patch.object(writer, "append_values_raw") as append_values_raw,
        ):
            result = writer.append_daily_slate_rows(new_rows)

        self.assertEqual(result.written_count, 1)
        self.assertEqual(result.duplicate_count, 1)
        expected_row = ["2026-04-25", "Toronto Maple Leafs", "Ottawa Senators"]
        expected_row.extend([""] * (len(DAILY_SLATE_COLUMNS) - len(expected_row) - 1))
        expected_row.append("2026-04-25_toronto maple leafs_ottawa senators")
        append_values_raw.assert_called_once_with(
            "Daily_Slate!A:AX",
            [expected_row],
        )

    def test_skips_duplicates_within_same_append_batch_and_logs_counts(self) -> None:
        new_rows = [
            ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings"],
            ["2026-04-25", " edmonton oilers ", "LOS ANGELES KINGS"],
        ]

        with (
            patch.object(writer, "load_dotenv"),
            patch.object(writer, "get_values", return_value=[DAILY_SLATE_COLUMNS]),
            patch.object(writer, "ensure_daily_slate_headers"),
            patch.object(writer, "append_values_raw") as append_values_raw,
            patch("builtins.print") as print_mock,
        ):
            result = writer.append_daily_slate_rows(new_rows)

        self.assertEqual(result.written_count, 1)
        self.assertEqual(result.duplicate_count, 1)
        expected_row = ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings"]
        expected_row.extend([""] * (len(DAILY_SLATE_COLUMNS) - len(expected_row) - 1))
        expected_row.append("2026-04-25_edmonton oilers_los angeles kings")
        append_values_raw.assert_called_once_with(
            "Daily_Slate!A:AX",
            [expected_row],
        )
        print_mock.assert_any_call("Inserted 1 rows")
        print_mock.assert_any_call("Skipped 1 duplicates")

    def test_repairs_existing_row_when_start_time_is_blank(self) -> None:
        existing_rows = [
            DAILY_SLATE_COLUMNS,
            ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings", ""],
        ]
        new_rows = [
            ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings", "7:00 PM"],
        ]

        with (
            patch.object(writer, "load_dotenv"),
            patch.object(writer, "get_values", return_value=existing_rows),
            patch.object(writer, "ensure_daily_slate_headers"),
            patch.object(writer, "append_values_raw") as append_values_raw,
            patch.object(writer, "update_values_raw") as update_values_raw,
        ):
            result = writer.append_daily_slate_rows(new_rows)

        self.assertEqual(result.written_count, 0)
        self.assertEqual(result.duplicate_count, 0)
        append_values_raw.assert_not_called()
        update_values_raw.assert_called_once_with("Daily_Slate!D2", [["7:00 PM"]])

    def test_repairs_existing_row_when_start_time_is_numeric(self) -> None:
        existing_rows = [
            DAILY_SLATE_COLUMNS,
            ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings", 7],
        ]
        new_rows = [
            ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings", "7:00 PM"],
        ]

        with (
            patch.object(writer, "load_dotenv"),
            patch.object(writer, "get_values", return_value=existing_rows),
            patch.object(writer, "ensure_daily_slate_headers"),
            patch.object(writer, "append_values_raw") as append_values_raw,
            patch.object(writer, "update_values_raw") as update_values_raw,
        ):
            result = writer.append_daily_slate_rows(new_rows)

        self.assertEqual(result.written_count, 0)
        self.assertEqual(result.duplicate_count, 0)
        append_values_raw.assert_not_called()
        update_values_raw.assert_called_once_with("Daily_Slate!D2", [["7:00 PM"]])

    def test_keeps_duplicate_protection_for_existing_row_with_valid_start_time(self) -> None:
        existing_rows = [
            DAILY_SLATE_COLUMNS,
            ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings", "7:00 PM"],
        ]
        new_rows = [
            ["2026-04-25", "Edmonton Oilers", "Los Angeles Kings", "7:00 PM"],
        ]

        with (
            patch.object(writer, "load_dotenv"),
            patch.object(writer, "get_values", return_value=existing_rows),
            patch.object(writer, "ensure_daily_slate_headers"),
            patch.object(writer, "append_values_raw") as append_values_raw,
            patch.object(writer, "update_values_raw") as update_values_raw,
        ):
            result = writer.append_daily_slate_rows(new_rows)

        self.assertEqual(result.written_count, 0)
        self.assertEqual(result.duplicate_count, 1)
        append_values_raw.assert_not_called()
        update_values_raw.assert_not_called()


if __name__ == "__main__":
    unittest.main()
