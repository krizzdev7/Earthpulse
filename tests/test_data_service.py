"""
Unit tests for backend.data_service module.
"""

import unittest
from unittest.mock import MagicMock, patch
import requests

from backend.data_service import (
    calculate_monthly_rainfall,
    fetch_climate_data,
    is_missing_value,
    NASA_POWER_URL,
)


class TestDataService(unittest.TestCase):
    """Test suite covering NASA POWER data fetching and processing."""

    @patch("backend.data_service.requests.get")
    def test_excluding_yyyy13_entries(self, mock_get):
        """Verify that annual summary entries ending in '13' are excluded."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "202101": 27.1,
                        "202112": 26.4,
                        "202113": 27.8,  # Annual summary to exclude
                        "202201": 27.3,
                        "202213": 28.0,  # Annual summary to exclude
                    },
                    "PRECTOTCORR": {
                        "202101": 4.11,
                        "202112": 0.63,
                        "202113": 7.86,
                        "202201": 3.50,
                        "202213": 6.50,
                    },
                }
            }
        }
        mock_get.return_value = mock_response

        records = fetch_climate_data(9.9312, 76.2673, 2021, 2022)

        months = [r["month"] for r in records]
        self.assertEqual(len(records), 3)
        self.assertEqual(months, ["202101", "202112", "202201"])
        self.assertNotIn("202113", months)
        self.assertNotIn("202213", months)
        self.assertTrue(all(not str(m).endswith("13") for m in months))

    @patch("backend.data_service.requests.get")
    def test_monthly_rainfall_calculation(self, mock_get):
        """Verify rainfall calculation from daily rate (mm/day) to monthly total (mm)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "202101": 27.10,  # Jan (31 days)
                        "202104": 29.50,  # Apr (30 days)
                    },
                    "PRECTOTCORR": {
                        "202101": 4.11,   # 4.11 mm/day * 31 days = 127.41 mm
                        "202104": 2.50,   # 2.50 mm/day * 30 days = 75.00 mm
                    },
                }
            }
        }
        mock_get.return_value = mock_response

        records = fetch_climate_data(9.9312, 76.2673, 2021, 2021)

        self.assertEqual(len(records), 2)

        # January check (31 days)
        jan = records[0]
        self.assertEqual(jan["month"], "202101")
        self.assertEqual(jan["temperature"], 27.10)
        self.assertEqual(jan["precipitation"], 4.11)
        self.assertEqual(jan["precipitation_mm"], 127.41)

        # April check (30 days)
        apr = records[1]
        self.assertEqual(apr["month"], "202104")
        self.assertEqual(apr["temperature"], 29.50)
        self.assertEqual(apr["precipitation"], 2.50)
        self.assertEqual(apr["precipitation_mm"], 75.00)

    @patch("backend.data_service.requests.get")
    def test_february_leap_and_non_leap_years(self, mock_get):
        """Verify February days in leap year (29 days) vs non-leap year (28 days)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "202102": 28.09,  # 2021 is non-leap (28 days)
                        "202402": 28.50,  # 2024 is leap year (29 days)
                    },
                    "PRECTOTCORR": {
                        "202102": 2.0,    # 2.0 * 28 = 56.0 mm
                        "202402": 2.0,    # 2.0 * 29 = 58.0 mm
                    },
                }
            }
        }
        mock_get.return_value = mock_response

        records = fetch_climate_data(9.9312, 76.2673, 2021, 2024)

        feb_2021 = records[0]
        self.assertEqual(feb_2021["month"], "202102")
        self.assertEqual(feb_2021["precipitation"], 2.0)
        self.assertEqual(feb_2021["precipitation_mm"], 56.0)

        feb_2024 = records[1]
        self.assertEqual(feb_2024["month"], "202402")
        self.assertEqual(feb_2024["precipitation"], 2.0)
        self.assertEqual(feb_2024["precipitation_mm"], 58.0)

        # Direct function tests for leap century rules
        self.assertEqual(calculate_monthly_rainfall(1.0, 2000, 2), 29.0)  # 2000 was a leap year
        self.assertEqual(calculate_monthly_rainfall(1.0, 1900, 2), 28.0)  # 1900 was not a leap year

    @patch("backend.data_service.requests.get")
    def test_exactly_60_monthly_records_2021_2025(self, mock_get):
        """Verify that 2021-2025 query returns exactly 60 monthly records (excluding 13s)."""
        # Construct realistic NASA POWER response with 5 years x 13 entries = 65 total entries
        t2m_data = {}
        precip_data = {}
        for yr in range(2021, 2026):
            for m in range(1, 14):
                key = f"{yr}{m:02d}"
                t2m_data[key] = 27.5
                precip_data[key] = 3.0

        self.assertEqual(len(t2m_data), 65)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {
                "parameter": {
                    "T2M": t2m_data,
                    "PRECTOTCORR": precip_data,
                }
            }
        }
        mock_get.return_value = mock_response

        records = fetch_climate_data(9.9312, 76.2673, 2021, 2025)

        self.assertEqual(len(records), 60)
        for r in records:
            self.assertIn("month", r)
            self.assertIn("temperature", r)
            self.assertIn("precipitation", r)
            self.assertIn("precipitation_mm", r)
            self.assertFalse(str(r["month"]).endswith("13"))

        # Verify start and end months
        self.assertEqual(records[0]["month"], "202101")
        self.assertEqual(records[-1]["month"], "202512")

    @patch("backend.data_service.requests.get")
    def test_missing_values_explicit_handling(self, mock_get):
        """Verify that missing values (-999, None) are not silently converted to valid measurements."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "202101": -999.0,
                        "202102": 25.0,
                    },
                    "PRECTOTCORR": {
                        "202101": -999.0,
                        "202102": None,
                    },
                }
            }
        }
        mock_get.return_value = mock_response

        records = fetch_climate_data(9.9312, 76.2673, 2021, 2021)

        self.assertEqual(len(records), 2)

        # Record 1: -999.0 precipitation must result in precipitation_mm = None (NOT -30969 and NOT 0.0)
        rec1 = records[0]
        self.assertEqual(rec1["precipitation"], -999.0)
        self.assertIsNone(rec1["precipitation_mm"])
        self.assertTrue(is_missing_value(rec1["precipitation"]))
        self.assertTrue(is_missing_value(rec1["temperature"]))

        # Record 2: None precipitation must result in precipitation_mm = None
        rec2 = records[1]
        self.assertIsNone(rec2["precipitation"])
        self.assertIsNone(rec2["precipitation_mm"])

    @patch("backend.data_service.requests.get")
    def test_http_and_network_error_handling(self, mock_get):
        """Verify that HTTP/network errors raise RuntimeError with informative message."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        with self.assertRaises(RuntimeError) as ctx:
            fetch_climate_data(0.0, 0.0)
        self.assertIn("NASA API request failed", str(ctx.exception))

    @patch("backend.data_service.requests.get")
    def test_unexpected_payload_handling(self, mock_get):
        """Verify that malformed API responses raise RuntimeError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid structure"}
        mock_get.return_value = mock_response

        with self.assertRaises(RuntimeError) as ctx:
            fetch_climate_data(0.0, 0.0)
        self.assertIn("Unexpected NASA response", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
