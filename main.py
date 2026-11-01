"""Calibry: a terminal menu that builds calorie formulas from Fitbit data and checks them against Garmin data."""

from models import (CSV_FILE, MINUTES_PER_DAY, MAX_STEPS, MAX_DISTANCE_KM,
                    MAX_CALORIES, SIMILAR_USERS, LINE_WIDTH)
from text_utils import parse_int, parse_float
from data_loader import load_dataset
from analysis import (dataset_summary, rank_predictors, choose_model, find_model,
                      percentile, percentage, column_values, most_similar_users)


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


def ask_minutes():
    """Ask for very active and sedentary minutes until together they fit in one day."""
    while True:
        very_active = ask_int("Very active minutes     : ", 0, MINUTES_PER_DAY)
        sedentary = ask_int("Sedentary minutes       : ", 0, MINUTES_PER_DAY)
        if very_active + sedentary > MINUTES_PER_DAY:
            print(f"  Very active + sedentary minutes is {very_active + sedentary}, "
                  f"but a day has only {MINUTES_PER_DAY}. Please type both again.")
        else:
            return very_active, sedentary


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
    print(f"{'Activity level':<18}{'Days':>6}{'Percent':>10}")
    for level in summary["levels"]:
        print(f"{level['level']:<18}{level['count']:>6}{level['percent']:>9.1f}%")
    print_line()
    print("Levels: Sedentary under 5,000 steps, Lightly Active 5,000 to 9,999, Active 10,000 or more.")


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
    very_active, sedentary = ask_minutes()
    garmin = ask_int("Total calories (Garmin) : ", 0, MAX_CALORIES)

    supplied = ["steps", "distance", "very_active_min", "sedentary_min"]
    values = {"steps": steps, "distance": distance,
              "very_active_min": very_active, "sedentary_min": sedentary}

    best = choose_model(models, supplied)
    if best is None:
        print("No formula could be built from the values you typed.")
        return
    estimate = best.predict(values[best.predictor])
    steps_model = find_model(models, "steps")

    print()
    print_line()
    print(f"{'Estimate (' + best.label + ' formula)':<34}: {estimate:,.0f} kcal")
    if steps_model is not None and steps_model is not best:
        steps_estimate = steps_model.predict(steps)
        print(f"{'Estimate (' + steps_model.label + ' formula)':<34}: {steps_estimate:,.0f} kcal")
    print(f"{'Garmin':<34}: {garmin:,} kcal")

    difference = estimate - garmin
    if garmin == 0:
        percent_text = "n/a, Garmin is 0"
    else:
        percent_text = f"{percentage(difference, garmin):+.1f}%"
    print(f"{'Difference (best formula)':<34}: {difference:+,.0f} kcal ({percent_text})")

    step_rank = percentile(steps, column_values(dataset.records, "steps"))
    print(f"{'Your steps percentile':<34}: {step_rank:.0f} (of {dataset.count()} days)")
    print_line()
    print("Garmin uses heart rate and your body profile, so a difference is expected.")

    print()
    print("Most similar Fitbit users")
    print(f"{'Rank':<6}{'User':<14}{'Avg steps':>10}{'Very active':>13}{'Sedentary':>11}")
    similar = most_similar_users(dataset, steps, very_active, sedentary, SIMILAR_USERS)
    rank = 1
    for user in similar:
        print(f"{rank:<6}{user['user_id']:<14}{user['avg_steps']:>10,.0f}"
              f"{user['avg_very_active']:>13.1f}{user['avg_sedentary']:>11.0f}")
        rank = rank + 1


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
