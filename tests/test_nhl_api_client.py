"""Tests for NHL API client configuration."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from src.nhl import api_client


class NhlApiClientTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
