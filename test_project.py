"""Unit tests for Calibry. Run with: python -m unittest"""

import os
import tempfile
import unittest

from models import (DayRecord, LinearModel, LEVEL_SEDENTARY,
                    LEVEL_LIGHTLY_ACTIVE, LEVEL_ACTIVE)
from text_utils import parse_date
from data_loader import load_dataset
from analysis import (average, percentage, percentile, sort_by, rank_predictors,
                      supplied_models)

HEADER = ("Id,ActivityDate,TotalSteps,TotalDistance,TrackerDistance,"
          "LoggedActivitiesDistance,VeryActiveDistance,ModeratelyActiveDistance,"
          "LightActiveDistance,SedentaryActiveDistance,VeryActiveMinutes,"
          "FairlyActiveMinutes,LightlyActiveMinutes,SedentaryMinutes,Calories")


def make_record(user_id=1, steps=5000, calories=2000, distance=3.5, very_active=10,
                fairly_active=10, lightly_active=200, sedentary=900):
    """Return a DayRecord with simple default values for testing."""
    return DayRecord(user_id, (2016, 4, 1), steps, distance, very_active,
                     fairly_active, lightly_active, sedentary, calories)


def write_csv(folder, lines):
    """Write the header plus the given lines to a CSV file in folder and return its path."""
    path = os.path.join(folder, "test.csv")
    with open(path, "w", encoding="utf-8", newline="") as csv_file:
        csv_file.write(HEADER + "\n")
        for line in lines:
            csv_file.write(line + "\n")
    return path


class TestLinearModel(unittest.TestCase):
    """Tests for fitting one straight-line formula."""

    def test_perfect_line(self):
        """y = 2x + 1 gives a = 1, b = 2, R squared = 1 and MAE = 0."""
        model = LinearModel("steps", "Total steps")
        self.assertTrue(model.fit([1, 2, 3, 4, 5], [3, 5, 7, 9, 11]))
        self.assertAlmostEqual(model.intercept, 1.0)
        self.assertAlmostEqual(model.slope, 2.0)
        self.assertAlmostEqual(model.r_squared, 1.0)
        self.assertAlmostEqual(model.mae, 0.0)
        self.assertAlmostEqual(model.predict(10), 21.0)

    def test_equal_x_values_do_not_fit(self):
        """Equal x values are refused instead of dividing by zero."""
        model = LinearModel("steps", "Total steps")
        self.assertFalse(model.fit([3, 3, 3], [1, 2, 3]))
        self.assertFalse(model.is_fitted)
        self.assertNotEqual(model.note, "")

    def test_empty_list_does_not_fit(self):
        """An empty list cannot be fitted."""
        model = LinearModel("steps", "Total steps")
        self.assertFalse(model.fit([], []))
        self.assertFalse(model.is_fitted)
        self.assertNotEqual(model.note, "")


class TestSafeMath(unittest.TestCase):
    """Tests for average, percentage and percentile edge cases."""

    def test_average_empty(self):
        """The average of an empty list is 0.0."""
        self.assertEqual(average([]), 0.0)

    def test_percentage_whole_zero(self):
        """A percentage of zero is 0.0 instead of a division error."""
        self.assertEqual(percentage(3, 0), 0.0)

    def test_percentile_empty(self):
        """The percentile in an empty list is 0.0."""
        self.assertEqual(percentile(5, []), 0.0)

    def test_percentile_counts_strictly_below(self):
        """Only values strictly below are counted: 1 and 3 of four values is 50%."""
        self.assertEqual(percentile(5, [1, 5, 9, 3]), 50.0)


class TestSortBy(unittest.TestCase):
    """Tests for the hand-written selection sort."""

    def test_ascending_dicts(self):
        """Dicts are sorted from small to large."""
        items = [{"v": 3}, {"v": 1}, {"v": 2}]
        result = sort_by(items, "v")
        self.assertEqual([result[0]["v"], result[1]["v"], result[2]["v"]], [1, 2, 3])

    def test_descending_objects(self):
        """Objects are sorted from large to small."""
        records = [make_record(steps=200), make_record(steps=900), make_record(steps=500)]
        result = sort_by(records, "steps", True)
        self.assertEqual([result[0].steps, result[1].steps, result[2].steps], [900, 500, 200])

    def test_original_unchanged(self):
        """Sorting returns a copy and leaves the original list as it was."""
        items = [{"v": 3}, {"v": 1}, {"v": 2}]
        sort_by(items, "v")
        self.assertEqual([items[0]["v"], items[1]["v"], items[2]["v"]], [3, 1, 2])


class TestRankPredictors(unittest.TestCase):
    """Tests for building and ranking one model per predictor."""

    def test_unfitted_models_last(self):
        """Predictors with all-equal values come after every fitted model."""
        records = [
            make_record(steps=1000, distance=1.0, sedentary=1000, calories=1800),
            make_record(steps=5000, distance=3.0, sedentary=900, calories=2100),
            make_record(steps=9000, distance=6.5, sedentary=950, calories=2500),
            make_record(steps=12000, distance=8.0, sedentary=700, calories=2600),
        ]
        models = rank_predictors(records)
        self.assertEqual(len(models), 6)
        for i in range(3):
            self.assertTrue(models[i].is_fitted)
        for i in range(3, 6):
            self.assertFalse(models[i].is_fitted)
        self.assertGreaterEqual(models[0].r_squared, models[1].r_squared)
        self.assertGreaterEqual(models[1].r_squared, models[2].r_squared)


class TestSuppliedModels(unittest.TestCase):
    """Tests for picking the formulas used in menu 3."""

    def make_model(self, predictor, fitted):
        """Return a LinearModel marked as fitted or not, without real data."""
        model = LinearModel(predictor, predictor)
        model.is_fitted = fitted
        return model

    def test_keeps_ranked_order(self):
        """Supplied fitted models come back in their ranked order, best first."""
        models = [self.make_model("distance", True), self.make_model("sedentary_min", True),
                  self.make_model("steps", True)]
        result = supplied_models(models, ["steps", "distance"])
        self.assertEqual(len(result), 2)
        self.assertIs(result[0], models[0])
        self.assertIs(result[1], models[2])

    def test_skips_unfitted(self):
        """An unfitted model is skipped even if its predictor was supplied."""
        models = [self.make_model("distance", False), self.make_model("steps", True)]
        result = supplied_models(models, ["distance", "steps"])
        self.assertEqual(len(result), 1)
        self.assertIs(result[0], models[1])

    def test_empty_when_nothing_matches(self):
        """An empty list is returned when no fitted model matches the supplied predictors."""
        models = [self.make_model("distance", True), self.make_model("steps", False)]
        self.assertEqual(supplied_models(models, ["steps", "sedentary_min"]), [])
        self.assertEqual(supplied_models(models, []), [])

    def test_first_two_with_slicing(self):
        """Slicing [:2] keeps at most two models and works when fewer exist."""
        models = [self.make_model("distance", True), self.make_model("steps", True),
                  self.make_model("very_active_min", True)]
        self.assertEqual(len(supplied_models(models, ["steps", "distance", "very_active_min"])[:2]), 2)
        self.assertEqual(len(supplied_models(models, ["steps"])[:2]), 1)


class TestParseDate(unittest.TestCase):
    """Tests for reading M/D/YYYY dates."""

    def test_valid_dates(self):
        """One- and two-digit months and days are accepted."""
        self.assertEqual(parse_date("3/9/2016"), (2016, 3, 9))
        self.assertEqual(parse_date("12/31/2016"), (2016, 12, 31))
        self.assertEqual(parse_date("04/12/2016"), (2016, 4, 12))

    def test_invalid_dates(self):
        """Bad dates return None instead of crashing."""
        self.assertIsNone(parse_date("13/1/2016"))
        self.assertIsNone(parse_date("3/12/16"))
        self.assertIsNone(parse_date("abc"))
        self.assertIsNone(parse_date(""))


class TestActivityLevel(unittest.TestCase):
    """Tests for the activity level boundaries and the non-wear check."""

    def test_boundaries(self):
        """5,000 and 10,000 steps start a new level."""
        self.assertEqual(make_record(steps=4999).activity_level(), LEVEL_SEDENTARY)
        self.assertEqual(make_record(steps=5000).activity_level(), LEVEL_LIGHTLY_ACTIVE)
        self.assertEqual(make_record(steps=9999).activity_level(), LEVEL_LIGHTLY_ACTIVE)
        self.assertEqual(make_record(steps=10000).activity_level(), LEVEL_ACTIVE)

    def test_zero_steps_not_worn(self):
        """A day with 0 steps counts as not worn."""
        self.assertFalse(make_record(steps=0).is_worn())
        self.assertTrue(make_record(steps=1).is_worn())


class TestLoader(unittest.TestCase):
    """Tests for reading the CSV file."""

    def test_broken_and_non_wear_rows(self):
        """Blank, non-numeric and short rows are broken; a 0-step day is non-wear."""
        lines = [
            "1,3/25/2016,8000,5.5,5.5,0,1,1,3.5,0,20,10,200,800,2200",
            "2,3/26/2016,4000,2.5,2.5,0,0,0,2.5,0,0,5,150,1000,1800",
            "1,3/27/2016,,5.5,5.5,0,1,1,3.5,0,20,10,200,800,2200",
            "1,3/28/2016,abc,5.5,5.5,0,1,1,3.5,0,20,10,200,800,2200",
            "1,3/29/2016,8000,5.5",
            "2,3/30/2016,0,0,0,0,0,0,0,0,0,0,0,900,1500",
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = write_csv(folder, lines)
            dataset, broken, non_wear = load_dataset(path)
        self.assertEqual(dataset.count(), 2)
        self.assertEqual(broken, 3)
        self.assertEqual(non_wear, 1)

    def test_missing_file(self):
        """A missing file returns (None, 0, 0) instead of crashing."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "missing.csv")
            self.assertEqual(load_dataset(path), (None, 0, 0))

    def test_real_file_counts(self):
        """The real Fitbit file gives the figures in the PRD."""
        dataset, broken, non_wear = load_dataset()
        self.assertEqual(dataset.count() + non_wear, 457)
        self.assertEqual(broken, 0)
        self.assertEqual(non_wear, 61)
        self.assertEqual(dataset.count(), 396)
        self.assertEqual(len(dataset.user_ids()), 34)


if __name__ == "__main__":
    unittest.main()
