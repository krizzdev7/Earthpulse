"""
Unit tests for backend.trend_analysis module.
"""

import unittest
from backend.trend_analysis import (
    aggregate_annual_climate,
    analyze_climate_trends,
    calculate_monthly_climatology,
    calculate_trend,
    CAUSATION_DISCLAIMER,
)


def generate_synthetic_monthly_data(
    start_year: int,
    end_year: int,
    temp_trend_per_year: float = 0.0,
    base_temp: float = 27.0,
    rain_trend_per_year: float = 0.0,
    base_monthly_rain: float = 150.0,
):
    """Generate synthetic monthly climate records for testing."""
    records = []
    for yr in range(start_year, end_year + 1):
        year_offset = yr - start_year
        annual_temp = base_temp + (temp_trend_per_year * year_offset)
        annual_rain = base_monthly_rain + (rain_trend_per_year * year_offset)

        for m in range(1, 13):
            records.append({
                "month": f"{yr}{m:02d}",
                "temperature": round(annual_temp, 2),
                "precipitation": round(annual_rain / 30.0, 2),
                "precipitation_mm": round(annual_rain, 2),
            })
    return records


class TestTrendAnalysis(unittest.TestCase):
    """Test suite covering climate trend analysis, aggregation, and climatology."""

    def test_increasing_temperature_series(self):
        """Verify increasing trend detection, positive slope, and Kendall tau."""
        # 10 years (2011-2020) with strong warming trend (+0.2°C/year)
        records = generate_synthetic_monthly_data(
            start_year=2011,
            end_year=2020,
            temp_trend_per_year=0.20,
        )

        analysis = analyze_climate_trends(records, location_name="Kochi")
        t_trend = analysis["temperature_trend"]

        self.assertEqual(t_trend["trend_direction"], "increasing")
        self.assertGreater(t_trend["slope_per_year"], 0.15)
        self.assertGreater(t_trend["kendall_tau"], 0.8)
        self.assertLess(t_trend["p_value"], 0.01)
        self.assertTrue(t_trend["is_statistically_significant"])
        self.assertEqual(t_trend["observations"], 10)

    def test_decreasing_rainfall_series(self):
        """Verify decreasing trend detection, negative slope, and negative tau."""
        # 10 years (2011-2020) with declining monthly rainfall (-10 mm/year)
        records = generate_synthetic_monthly_data(
            start_year=2011,
            end_year=2020,
            rain_trend_per_year=-10.0,
        )

        analysis = analyze_climate_trends(records, location_name="Kochi")
        r_trend = analysis["rainfall_trend"]

        self.assertEqual(r_trend["trend_direction"], "decreasing")
        self.assertLess(r_trend["slope_per_year"], -50.0)  # 12 months * -10 = -120 mm/yr
        self.assertLess(r_trend["kendall_tau"], -0.8)
        self.assertLess(r_trend["p_value"], 0.01)
        self.assertTrue(r_trend["is_statistically_significant"])
        self.assertEqual(r_trend["observations"], 10)

    def test_constant_data(self):
        """Verify that constant data safely yields no trend with zero slope and tau."""
        # 8 years with identical values
        years = list(range(2011, 2019))
        const_temps = [28.0] * len(years)

        trend = calculate_trend(years, const_temps, metric_name="temperature")

        self.assertEqual(trend["trend_direction"], "no detected trend")
        self.assertEqual(trend["slope_per_year"], 0.0)
        self.assertEqual(trend["slope_per_decade"], 0.0)
        self.assertEqual(trend["kendall_tau"], 0.0)
        self.assertEqual(trend["p_value"], 1.0)
        self.assertFalse(trend["is_statistically_significant"])

    def test_missing_monthly_values(self):
        """Verify that missing values (-999, None) do not corrupt calculations."""
        # 3 complete years, 1 year with missing data
        records = generate_synthetic_monthly_data(2021, 2024)

        # Corrupt 2022 month 06 with missing indicators
        for r in records:
            if r["month"] == "202206":
                r["temperature"] = -999.0
                r["precipitation_mm"] = None

        aggregation = aggregate_annual_climate(records)

        # 2022 should be excluded from complete annual series
        complete_temp_years = aggregation["temperature_series"]["years"]
        complete_rain_years = aggregation["rainfall_series"]["years"]

        self.assertIn(2021, complete_temp_years)
        self.assertNotIn(2022, complete_temp_years)
        self.assertIn(2023, complete_temp_years)
        self.assertIn(2024, complete_temp_years)

        self.assertNotIn(2022, complete_rain_years)
        self.assertIn(2022, aggregation["incomplete_years"])

        # Climatology should handle missing values gracefully
        climatology = calculate_monthly_climatology(records)
        june_climatology = next(c for c in climatology if c["month"] == 6)
        # June had 3 valid observations instead of 4
        self.assertEqual(june_climatology["temperature_observations"], 3)
        self.assertEqual(june_climatology["precipitation_observations"], 3)

    def test_incomplete_years(self):
        """Verify that years with fewer than 12 months are excluded from annual trend."""
        records = []
        # Year 2021: 12 months (complete)
        for m in range(1, 13):
            records.append({"month": f"2021{m:02d}", "temperature": 27.0, "precipitation_mm": 100.0})

        # Year 2022: only 9 months (incomplete)
        for m in range(1, 10):
            records.append({"month": f"2022{m:02d}", "temperature": 27.5, "precipitation_mm": 100.0})

        # Year 2023: 12 months (complete)
        for m in range(1, 13):
            records.append({"month": f"2023{m:02d}", "temperature": 28.0, "precipitation_mm": 100.0})

        aggregation = aggregate_annual_climate(records)

        self.assertEqual(aggregation["temperature_series"]["years"], [2021, 2023])
        self.assertEqual(aggregation["rainfall_series"]["years"], [2021, 2023])
        self.assertIn(2022, aggregation["incomplete_years"])
        self.assertEqual(aggregation["incomplete_years"][2022]["valid_temperature_months"], 9)

    def test_leap_year_compatibility(self):
        """Verify compatibility with leap-year February (29 days) and non-leap (28 days)."""
        # 2024 is a leap year; 2021 is non-leap
        records = [
            {"month": "202102", "temperature": 28.0, "precipitation_mm": 28.0},  # 1 mm/day * 28d
            {"month": "202402", "temperature": 28.5, "precipitation_mm": 29.0},  # 1 mm/day * 29d
        ]

        climatology = calculate_monthly_climatology(records)
        feb = next(c for c in climatology if c["month"] == 2)

        self.assertEqual(feb["temperature_observations"], 2)
        self.assertEqual(feb["mean_temperature"], 28.25)
        self.assertEqual(feb["mean_precipitation_mm"], 28.5)

    def test_insufficient_annual_observations(self):
        """Verify that datasets with < 3 observations safely return 'no detected trend'."""
        # Only 2 years of observations
        years = [2021, 2022]
        temps = [27.0, 28.0]

        trend = calculate_trend(years, temps, metric_name="temperature")

        self.assertEqual(trend["trend_direction"], "no detected trend")
        self.assertIsNone(trend["slope_per_year"])
        self.assertIsNone(trend["slope_per_decade"])
        self.assertIsNone(trend["kendall_tau"])
        self.assertIsNone(trend["p_value"])
        self.assertEqual(trend["observations"], 2)
        self.assertFalse(trend["is_statistically_significant"])

    def test_correct_trend_units_and_decade_conversion(self):
        """Verify correct units and 10x multiplier for per-decade slope."""
        years = list(range(2011, 2021))
        # Known slope of 0.05 °C/year -> 0.50 °C/decade
        temps = [27.0 + 0.05 * i for i in range(len(years))]

        temp_trend = calculate_trend(years, temps, metric_name="temperature")
        self.assertEqual(temp_trend["unit_per_year"], "°C/year")
        self.assertEqual(temp_trend["unit_per_decade"], "°C/decade")
        self.assertAlmostEqual(temp_trend["slope_per_year"], 0.05, places=3)
        self.assertAlmostEqual(temp_trend["slope_per_decade"], 0.50, places=2)
        self.assertAlmostEqual(
            temp_trend["slope_per_decade"],
            temp_trend["slope_per_year"] * 10.0,
            places=3,
        )

        # Known slope of -12.5 mm/year -> -125.0 mm/decade
        rains = [2500.0 - 12.5 * i for i in range(len(years))]
        rain_trend = calculate_trend(years, rains, metric_name="rainfall")
        self.assertEqual(rain_trend["unit_per_year"], "mm/year")
        self.assertEqual(rain_trend["unit_per_decade"], "mm/decade")
        self.assertAlmostEqual(rain_trend["slope_per_year"], -12.5, places=2)
        self.assertAlmostEqual(rain_trend["slope_per_decade"], -125.0, places=1)

    def test_causation_disclaimer_present(self):
        """Verify that the statistical output includes an explicit causation disclaimer."""
        trend = calculate_trend([2020, 2021, 2022], [27.0, 27.5, 28.0])
        self.assertIn("disclaimer", trend)
        self.assertIn("does not prove or attribute climate change causation", trend["disclaimer"])


if __name__ == "__main__":
    unittest.main()
