"""Calibry: a terminal menu that builds calorie formulas from Fitbit data and checks them against Garmin data."""

from models import (CSV_FILE, MINUTES_PER_DAY, MAX_STEPS, MAX_DISTANCE_KM,
                    MAX_CALORIES, ESTIMATES_SHOWN, LINE_WIDTH)
from text_utils import parse_int, parse_float
from data_loader import load_dataset
from analysis import (dataset_summary, rank_predictors, supplied_models,
                      interpret_difference, percentile, percentage, column_values)


# ----- Input -----

def ask_int(prompt, low, high):
    """Ask until the user types a whole number from low to high, then return it."""
    while True:
        answer = input(prompt)
        if answer.strip() == "":
            print("  The answer was empty. Please type a number.")
            continue
        number = parse_int(answer)
        if number is None:
            if parse_float(answer) is not None:
                print("  Please type a whole number without decimals.")
            else:
                print("  That is not a number. Please type digits only, for example 42.")
        elif number < low or number > high:
            print(f"  Please type a number from {low:,} to {high:,}.")
        else:
            return number


def ask_float(prompt, low, high):
    """Ask until the user types a number (decimals allowed) from low to high, then return it."""
    while True:
        answer = input(prompt)
        if answer.strip() == "":
            print("  The answer was empty. Please type a number.")
            continue
        number = parse_float(answer)
        if number is None:
            print("  That is not a number. Please type digits, for example 4.8.")
        elif number < low or number > high:
            print(f"  Please type a number from {low} to {high}.")
        else:
            return number


# ----- Output helpers -----

def print_line():
    """Print a horizontal line."""
    print("-" * LINE_WIDTH)


def unit_info(predictor):
    """Return (amount, text) used to explain a slope in plain words."""
    if predictor == "steps":
        return 1000, "1,000 steps"
    elif predictor == "distance":
        return 1, "1 km"
    else:
        return 10, "10 minutes"


def variable_name(model):
    """Return the predictor name as used inside a formula."""
    if model.predictor == "distance":
        return "distance (km)"
    return model.label.lower()


def plain_effect(model):
    """Return a sentence saying how much one unit step of the predictor changes calories."""
    amount, text = unit_info(model.predictor)
    change = model.slope * amount
    if change >= 0:
        return f"Every extra {text} adds about {change:,.0f} kcal."
    return f"Every extra {text} lowers the estimate by about {-change:,.0f} kcal."


# ----- Screens -----

def show_start(dataset, broken, non_wear):
    """Print the load results shown when the program starts."""
    print(f"Loaded {dataset.count() + non_wear} rows.")
    print(f"Broken rows skipped       : {broken}")
    print(f"Non-wear days excluded    : {non_wear}")
    print(f"Days used                 : {dataset.count()} days from {len(dataset.user_ids())} users")


def show_menu():
    """Print the main menu."""
    print()
    print("===== CALIBRY =====")
    print("1. Dataset summary")
    print("2. Compare predictors")
    print("3. Check your data (Garmin)")
    print("4. Exit")


def show_summary(dataset, broken, non_wear):
    """Print menu 1: the dataset summary."""
    summary = dataset_summary(dataset)
    print()
    print("Dataset summary")
    print_line()
    print(f"Rows loaded               : {dataset.count() + non_wear}")
    print(f"Broken rows skipped       : {broken}")
    print(f"Non-wear days excluded    : {non_wear}")
    print(f"Days used                 : {summary['days']}")
    print(f"Users                     : {summary['users']}")
    print(f"Average steps             : {summary['avg_steps']:,.0f}")
    print(f"Average very active min   : {summary['avg_very_active']:.1f}")
    print(f"Average sedentary min     : {summary['avg_sedentary']:.1f}")
    print(f"Average calories          : {summary['avg_calories']:,.0f} kcal")
    print_line()
    print(f"{'Activity level':<18}{'Days':>6}{'Percent':>10}{'Avg steps':>11}{'Avg calories':>14}")
    for level in summary["levels"]:
        print(f"{level['level']:<18}{level['count']:>6}{level['percent']:>9.1f}%"
              f"{level['avg_steps']:>11,.0f}{level['avg_calories']:>14,.0f}")
    print_line()
    print("Levels: Sedentary under 5,000 steps, Lightly Active 5,000 to 9,999, Active 10,000 or more.")
    print("Limits follow Tudor-Locke & Bassett (2004); their 5,000-7,499 and "
          "7,500-9,999 groups are merged into Lightly Active.")


def show_predictors(dataset):
    """Print menu 2: how the formulas work, the ranked table and the best formula."""
    days = dataset.count()
    models = rank_predictors(dataset.records)

    print()
    print("How this works")
    print(f"Calibry draws the straight line that best fits {days} days of Fitbit data:")
    print("    calories = a + b × predictor")
    print("a is the baseline (calories at zero), b is how many calories each unit adds.")
    print("R² shows how much of the variation in calories the line explains (0 to 1).")
    print("MAE is the average error in kcal.")
    print()
    print_line()
    print(f"{'Rank':<6}{'Predictor':<24}{'a (base)':>10}{'b (per unit)':>14}{'R²':>6}{'MAE':>6}")
    print_line()
    rank = 1
    for model in models:
        if model.is_fitted:
            print(f"{rank:<6}{model.label:<24}{model.intercept:>10,.1f}{model.slope:>14.4f}"
                  f"{model.r_squared:>6.2f}{model.mae:>6.0f}")
        else:
            print(f"{rank:<6}{model.label:<24}  not fitted: {model.note}")
        rank = rank + 1
    print_line()

    best = models[0]
    if not best.is_fitted:
        print("No formula could be built from this data.")
        return
    print(f"Best formula: calories = {best.intercept:,.0f} + {best.slope:.4f} × {variable_name(best)}")
    print(plain_effect(best))
    print(f"This formula explains about {best.r_squared * 100:.0f}% of the variation in calories.")


def show_check(dataset):
    """Print menu 3: compare one day of Garmin data with the best formula."""
    models = rank_predictors(dataset.records)

    print()
    print("Type the numbers from one day in Garmin Connect.")
    steps = ask_int("Steps that day          : ", 0, MAX_STEPS)
    distance = ask_float("Distance (km)           : ", 0.0, MAX_DISTANCE_KM)
    very_active = ask_int("Very active minutes     : ", 0, MINUTES_PER_DAY)
    garmin = ask_int("Total calories (Garmin) : ", 0, MAX_CALORIES)

    supplied = ["steps", "distance", "very_active_min"]
    values = {"steps": steps, "distance": distance, "very_active_min": very_active}

    # Fitted models for the values typed in, still in ranked order; show the first two.
    matching = supplied_models(models, supplied)
    if len(matching) == 0:
        print("No formula could be built from the values you typed.")
        return
    shown = matching[:ESTIMATES_SHOWN]
    best = shown[0]
    estimate = best.predict(values[best.predictor])

    print()
    print_line()
    for model in shown:
        model_estimate = model.predict(values[model.predictor])
        print(f"{'Estimate (' + model.label + ' formula)':<34}: {model_estimate:,.0f} kcal")
    print(f"{'Garmin':<34}: {garmin:,} kcal")

    difference = estimate - garmin
    if garmin == 0:
        percent_text = "n/a, Garmin is 0"
    else:
        percent_text = f"{percentage(difference, garmin):+.1f}%"
    print(f"{'Difference (best formula)':<34}: {difference:+,.0f} kcal ({percent_text})")
    if garmin != 0:
        print(interpret_difference(difference, best.mae))

    step_rank = percentile(steps, column_values(dataset.records, "steps"))
    print(f"{'Your steps percentile':<34}: {step_rank:.0f} (of {dataset.count()} days)")
    print_line()
    print("Garmin uses heart rate and your body profile, so a difference is expected.")


# ----- Main loop -----

def run_menu(dataset, broken, non_wear):
    """Show the menu again and again until the user chooses Exit."""
    while True:
        show_menu()
        choice = ask_int("Choose (1-4): ", 1, 4)
        if choice == 1:
            show_summary(dataset, broken, non_wear)
        elif choice == 2:
            show_predictors(dataset)
        elif choice == 3:
            show_check(dataset)
        else:
            print("Goodbye.")
            break


def main():
    """Load the data, print the start screen and run the menu."""
    dataset, broken, non_wear = load_dataset(CSV_FILE)
    if dataset is None:
        print(f"Could not read {CSV_FILE}.")
        print("Put the file in the same folder as main.py and check that it has the Fitbit columns.")
        return
    show_start(dataset, broken, non_wear)
    if dataset.count() == 0:
        print("The file has no usable days, so there is nothing to analyse.")
        return
    try:
        run_menu(dataset, broken, non_wear)
    except (EOFError, KeyboardInterrupt):
        print()
        print("Input ended. Goodbye.")


if __name__ == "__main__":
    main()
