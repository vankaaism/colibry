"""Constants and classes (DayRecord, FitbitDataset, LinearModel) for Calibry."""

from text_utils import format_date

# ----- File -----
CSV_FILE = "dailyActivity_merged.csv"

# ----- Columns used from the CSV (exact header names, in DayRecord order) -----
USED_COLUMNS = [
    "Id",
    "ActivityDate",
    "TotalSteps",
    "TotalDistance",
    "VeryActiveMinutes",
    "FairlyActiveMinutes",
    "LightlyActiveMinutes",
    "SedentaryMinutes",
    "Calories",
]

# ----- Day rules -----
MINUTES_PER_DAY = 1440
NON_WEAR_STEPS = 0

# ----- Activity levels (by steps per day) -----
LIGHTLY_ACTIVE_MIN_STEPS = 5000
ACTIVE_MIN_STEPS = 10000
LEVEL_SEDENTARY = "Sedentary"
LEVEL_LIGHTLY_ACTIVE = "Lightly Active"
LEVEL_ACTIVE = "Active"
ACTIVITY_LEVELS = [LEVEL_SEDENTARY, LEVEL_LIGHTLY_ACTIVE, LEVEL_ACTIVE]

# ----- Input limits for menu 3 -----
MAX_STEPS = 100000
MAX_DISTANCE_KM = 100.0
MAX_CALORIES = 10000

# ----- Output -----
SIMILAR_USERS = 3
LINE_WIDTH = 66

# ----- Predictors for the calorie formulas: (DayRecord attribute, label) -----
PREDICTORS = [
    ("steps", "Total steps"),
    ("distance", "Total distance"),
    ("very_active_min", "Very active minutes"),
    ("fairly_active_min", "Fairly active minutes"),
    ("lightly_active_min", "Lightly active minutes"),
    ("sedentary_min", "Sedentary minutes"),
]


class DayRecord:
    """One CSV row: one day of activity for one user."""

    def __init__(self, user_id, date, steps, distance, very_active_min,
                 fairly_active_min, lightly_active_min, sedentary_min, calories):
        """Store the nine used columns of one day."""
        self.user_id = user_id
        self.date = date
        self.steps = steps
        self.distance = distance
        self.very_active_min = very_active_min
        self.fairly_active_min = fairly_active_min
        self.lightly_active_min = lightly_active_min
        self.sedentary_min = sedentary_min
        self.calories = calories

    def activity_level(self):
        """Return the activity level of this day based on its steps."""
        if self.steps < LIGHTLY_ACTIVE_MIN_STEPS:
            return LEVEL_SEDENTARY
        elif self.steps < ACTIVE_MIN_STEPS:
            return LEVEL_LIGHTLY_ACTIVE
        else:
            return LEVEL_ACTIVE

    def is_worn(self):
        """Return True if the watch was worn (steps above 0)."""
        return self.steps > NON_WEAR_STEPS

    def __str__(self):
        """Return a short readable description of this day."""
        return (f"User {self.user_id} on {format_date(self.date)}: "
                f"{self.steps} steps, {self.calories} kcal")


class FitbitDataset:
    """A collection of DayRecord objects."""

    def __init__(self):
        """Start with an empty list of records."""
        self.records = []

    def add(self, record):
        """Add one DayRecord to the dataset."""
        self.records.append(record)

    def count(self):
        """Return the number of records."""
        return len(self.records)

    def user_ids(self):
        """Return the unique user IDs in the order they first appear."""
        ids = []
        for record in self.records:
            if record.user_id not in ids:
                ids.append(record.user_id)
        return ids

    def records_of(self, user_id):
        """Return all records that belong to one user."""
        result = []
        for record in self.records:
            if record.user_id == user_id:
                result.append(record)
        return result

    def __str__(self):
        """Return a short readable description of the dataset."""
        return f"Fitbit dataset: {self.count()} days from {len(self.user_ids())} users"


class LinearModel:
    """One straight-line formula: calories = intercept + slope * predictor."""

    def __init__(self, predictor, label):
        """Create an empty model for one predictor."""
        self.predictor = predictor
        self.label = label
        self.intercept = 0.0
        self.slope = 0.0
        self.r_squared = 0.0
        self.mae = 0.0
        self.is_fitted = False
        self.note = "Not fitted yet"

    def fit(self, xs, ys):
        """Fit the line to the data with simple linear regression; return True on success."""
        n = len(xs)
        if n == 0 or n != len(ys):
            self.is_fitted = False
            self.note = "No data to fit"
            return False

        # Step 1: the means of x and y.
        total_x = 0.0
        total_y = 0.0
        for i in range(n):
            total_x = total_x + xs[i]
            total_y = total_y + ys[i]
        mean_x = total_x / n
        mean_y = total_y / n

        # Step 2: the sums needed for the slope and for R squared.
        sum_xy = 0.0
        sum_xx = 0.0
        sum_yy = 0.0
        for i in range(n):
            dx = xs[i] - mean_x
            dy = ys[i] - mean_y
            sum_xy = sum_xy + dx * dy
            sum_xx = sum_xx + dx * dx
            sum_yy = sum_yy + dy * dy

        # Guard against division by zero.
        if sum_xx == 0:
            self.is_fitted = False
            self.note = "All predictor values are the same"
            return False
        if sum_yy == 0:
            self.is_fitted = False
            self.note = "All calorie values are the same"
            return False

        # Step 3: slope and intercept.
        self.slope = sum_xy / sum_xx
        self.intercept = mean_y - self.slope * mean_x

        # Steps 4 and 5: R squared and mean absolute error.
        sum_squared_error = 0.0
        sum_absolute_error = 0.0
        for i in range(n):
            error = ys[i] - self.predict(xs[i])
            sum_squared_error = sum_squared_error + error * error
            sum_absolute_error = sum_absolute_error + abs(error)
        self.r_squared = 1 - sum_squared_error / sum_yy
        self.mae = sum_absolute_error / n

        self.is_fitted = True
        self.note = ""
        return True

    def predict(self, x):
        """Return the estimated calories for one predictor value."""
        return self.intercept + self.slope * x

    def __str__(self):
        """Return the formula as readable text."""
        if not self.is_fitted:
            return f"{self.label}: not fitted ({self.note})"
        return (f"{self.label}: calories = {self.intercept:.1f} + "
                f"{self.slope:.4f} x value (R² {self.r_squared:.2f}, MAE {self.mae:.0f})")
