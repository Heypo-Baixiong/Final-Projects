"""Small checks of failure-prone methodological choices, using synthetic data."""
import unittest
import numpy as np
import pandas as pd
from weather_analysis import parse_damage, annual_counts, detrend, hac_model, block_means, YEARS


class AnalysisChecks(unittest.TestCase):
    def test_missing_damage_is_not_zero(self):
        values, invalid = parse_damage(pd.Series([None, "", "0", "0K", "1.5M", "2b", "?", "-1K"]))
        self.assertTrue(values.iloc[:2].isna().all())
        np.testing.assert_allclose(values.iloc[2:6], [0, 0, 1.5e6, 2e9])
        self.assertEqual(invalid.tolist(), [False, False, False, False, False, False, True, True])
        components = pd.DataFrame({"p": [np.nan, 0, 100], "c": [np.nan, np.nan, 20]})
        self.assertTrue(np.isnan(components.sum(axis=1, min_count=1).iloc[0]))
        self.assertEqual(components.sum(axis=1, min_count=1).iloc[1], 0)
        self.assertTrue(np.isnan(components.sum(axis=1, min_count=2).iloc[1]))

    def test_counting_unit_does_not_claim_unique_storms(self):
        frame = pd.DataFrame({"year": [1996] * 4, "category": ["Hail"] * 3 + ["Tornado"],
            "STATE": ["NEW YORK"] * 3 + ["TEXAS"],
            "date": pd.to_datetime(["1996-01-01", "1996-01-01", "1996-01-02", "1996-01-02"])})
        counts, days = annual_counts(frame)
        self.assertEqual(counts.loc[1996, "Total"], 4)
        self.assertEqual(days.loc[1996], 3)
        self.assertEqual(counts.loc[1997, "Total"], 0)
        self.assertEqual(len(counts), 29)

    def test_shared_trend_is_removed(self):
        rng = np.random.default_rng(13)
        time = YEARS - YEARS.mean()
        x = detrend(rng.normal(size=len(time)))
        z = detrend(rng.normal(size=len(time)))
        z -= np.dot(z, x) / np.dot(x, x) * x
        observed_x, observed_y = 10 * time + x, 20 * time + z
        self.assertGreater(np.corrcoef(observed_x, observed_y)[0, 1], .99)
        self.assertLess(abs(np.corrcoef(detrend(observed_x), detrend(observed_y))[0, 1]), 1e-10)
        model = hac_model(observed_y, {"sst": observed_x, "year": time})
        self.assertAlmostEqual(model.params["sst"], 0, places=9)

    def test_bootstrap_keeps_complete_month_vectors(self):
        rng = np.random.default_rng(4)
        shares = rng.dirichlet(np.ones(12), size=15)
        means = block_means(shares, 3, rng, 100)
        np.testing.assert_allclose(means.sum(axis=1), 1)
        self.assertEqual(means.shape, (100, 12))


if __name__ == "__main__":
    unittest.main()
