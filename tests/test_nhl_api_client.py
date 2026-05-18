"""Tests for NHL API client configuration."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from src.nhl import api_client


class NhlApiClientTests(unittest.TestCase):
    def tearDown(self) -> None:
        api_client.clear_response_cache()

    def test_get_schedule_uses_ten_second_timeout(self) -> None:
        response = Mock()
        response.json.return_value = {"games": []}

        with (
            patch.object(api_client, "get_base_url", return_value="https://example.com"),
            patch.object(api_client.requests, "get", return_value=response) as get,
        ):
            schedule = api_client.get_schedule("2026-04-15")

        self.assertEqual(schedule, {"games": []})
        get.assert_called_once_with(
            "https://example.com/v1/schedule/2026-04-15",
            timeout=10,
        )
        response.raise_for_status.assert_called_once_with()

    def test_get_schedule_fresh_bypasses_existing_cache(self) -> None:
        first_response = Mock()
        first_response.json.return_value = {"games": [1, 2, 3, 4]}
        second_response = Mock()
        second_response.json.return_value = {"games": [1, 2, 3, 4, 5, 6]}

        with (
            patch.object(api_client, "get_base_url", return_value="https://example.com"),
            patch.object(
                api_client.requests,
                "get",
                side_effect=[first_response, second_response],
            ) as get,
        ):
            cached_schedule = api_client.get_schedule("2026-05-18")
            fresh_schedule = api_client.get_schedule("2026-05-18", fresh=True)

        self.assertEqual(cached_schedule, {"games": [1, 2, 3, 4]})
        self.assertEqual(fresh_schedule, {"games": [1, 2, 3, 4, 5, 6]})
        self.assertEqual(get.call_count, 2)

    def test_clear_response_cache_removes_cached_responses(self) -> None:
        first_response = Mock()
        first_response.json.return_value = {"games": [1, 2, 3, 4]}
        second_response = Mock()
        second_response.json.return_value = {"games": [1, 2, 3, 4, 5, 6]}

        with (
            patch.object(api_client, "get_base_url", return_value="https://example.com"),
            patch.object(
                api_client.requests,
                "get",
                side_effect=[first_response, second_response],
            ) as get,
        ):
            first_schedule = api_client.get_schedule("2026-05-18")
            api_client.clear_response_cache()
            refreshed_schedule = api_client.get_schedule("2026-05-18")

        self.assertEqual(first_schedule, {"games": [1, 2, 3, 4]})
        self.assertEqual(refreshed_schedule, {"games": [1, 2, 3, 4, 5, 6]})
        self.assertEqual(get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
