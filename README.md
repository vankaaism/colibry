# Calibry

Calibry is a command-line program in Python 3 (standard library only) that uses a public Fitbit dataset as material for building formulas. From 396 usable days of activity it builds one straight-line formula per activity variable, `calories = a + b × predictor`, using simple linear regression written by hand. It then ranks the formulas by how well they fit (R²). The user can type in one day of data from a Garmin watch and see how the best formula's estimate compares with Garmin's own calorie figure. The name plays on *colibri* (hummingbird) and *calibrate*.

## Dataset

| | |
|---|---|
| Name | FitBit Fitness Tracker Data |
| Source | Kaggle: https://www.kaggle.com/datasets/arashnic/fitbit |
| License | CC0: Public Domain |
| File used | `dailyActivity_merged.csv` (the 3.12.16-4.11.16 export) |
| Rows | 457 data rows plus a header, 15 columns |
| Users | 35 |
| Dates | 12 March to 12 April 2016 (32 dates) |
| Personal information | None. Users are identified only by an anonymous numeric `Id`; the file has no names, ages, or body measurements. |

## Why I chose it

I use a Garmin watch and wanted to test whether a calorie formula built from other people's data matches what my watch tells me.

## Columns and data handling

**Columns used**

| Column | Type | Used for |
|---|---|---|
| Id | int | Grouping days by user |
| ActivityDate | date (M/D/YYYY) | Parsed and stored with each day |
| TotalSteps | int | Predictor, step percentile, non-wear check |
| TotalDistance | float (km) | Predictor |
| VeryActiveMinutes | int | Predictor |
| FairlyActiveMinutes | int | Predictor |
| LightlyActiveMinutes | int | Predictor |
| SedentaryMinutes | int | Predictor |
| Calories | int | The value every formula estimates |

**Columns skipped**

| Column | Reason |
|---|---|
| TrackerDistance | Almost identical to TotalDistance (differs on only 16 of 457 rows) |
| LoggedActivitiesDistance | Mostly zero (non-zero on only 24 of 457 rows) |
| VeryActiveDistance, ModeratelyActiveDistance, LightActiveDistance, SedentaryActiveDistance | Already covered by the minute columns for each intensity |

**Blank cells and broken rows.** The file has no blank cells in any column. The loader still checks: a row is skipped and counted as *broken* if it has the wrong number of columns, a blank cell in any used column, a number that cannot be read, a negative number, or a date that is not M/D/YYYY. A blank cell in a skipped column does not matter. On the real file, 0 rows are broken.

**Non-wear days.** A day with `TotalSteps == 0` is treated as a day the watch was not worn, whatever its sedentary minutes. These days are counted and left out of the formulas, averages and percentile. The real file has 61 such days (53 of them also show 1440 sedentary minutes). All 5 days with 0 calories are among them. One of the 35 users has only non-wear days, so the program works with **396 days from 34 users**.

## How to run

You need Python 3 only; there is nothing to install. Keep `dailyActivity_merged.csv` in the same folder as `main.py`, then run from that folder:

```
python main.py
python -m unittest
```

On systems where `python` points to Python 2 or does not exist, use `python3` instead.

## Features

On start the program loads the file and reports what it found:

```
Loaded 457 rows.
Broken rows skipped       : 0
Non-wear days excluded    : 61
Days used                 : 396 days from 34 users
```

The menu repeats until you choose 4. Every answer is checked in a loop: an empty answer, text, a decimal at a whole-number prompt, or a number out of range gives a message and asks again.

**1. Dataset summary.** Shows the load counts, number of users, average steps, very active minutes, sedentary minutes and calories, and how many days fall into each activity level (Sedentary under 5,000 steps, Lightly Active 5,000 to 9,999, Active 10,000 or more).

```
Average steps             : 7,555
Average very active min   : 19.1
Average sedentary min     : 942.2
Average calories          : 2,284 kcal
------------------------------------------------------------------
Activity level      Days   Percent
Sedentary            136     34.3%
Lightly Active       133     33.6%
Active               127     32.1%
```

**2. Compare predictors.** Explains how the formula works, builds one formula for each of six predictors, ranks them by R² with a hand-written selection sort, and states the best one in plain words.

```
------------------------------------------------------------------
Rank  Predictor                 a (base)  b (per unit)    R²   MAE
------------------------------------------------------------------
1     Total distance             1,636.8      120.2781  0.36   504
2     Total steps                1,634.0        0.0861  0.31   528
3     Very active minutes        2,027.6       13.4630  0.27   521
4     Fairly active minutes      2,090.8       14.4107  0.14   568
5     Lightly active minutes     1,881.7        2.0502  0.08   599
6     Sedentary minutes          1,958.4        0.3457  0.02   611
------------------------------------------------------------------
Best formula: calories = 1,637 + 120.2781 × distance (km)
Every extra 1 km adds about 120 kcal.
This formula explains about 36% of the variation in calories.
```

**3. Check your data (Garmin).** Asks for steps, distance (km), very active minutes and Garmin's total calories. It takes the fitted formulas whose predictor you typed in, keeps them in ranked order, and shows the estimates from the first two (Total distance and Total steps on this data). The first one is the main estimate: the program compares it with Garmin and also shows your step percentile. The sample below uses an illustrative day, not real Garmin data.

```
------------------------------------------------------------------
Estimate (Total distance formula) : 2,226 kcal
Estimate (Total steps formula)    : 2,196 kcal
Garmin                            : 2,150 kcal
Difference (best formula)         : +76 kcal (+3.5%)
Your steps percentile             : 45 (of 396 days)
------------------------------------------------------------------
Garmin uses heart rate and your body profile, so a difference is expected.
```

**4. Exit.** Ends the program. Garmin data you type is not saved anywhere.

## Known limitations

- **Modest fit.** Calories depend heavily on body weight, which this file does not contain. The best formula explains only about 36% of the variation in calories (R² 0.36), with an average error of about 504 kcal.
- **Different devices.** Garmin estimates calories from heart rate and the user's body profile, not from one activity variable, so a difference from the formula is expected.
- **Small, old sample.** 35 users over one month in 2016 do not represent the wider population.
- **No separate test set.** The planned train/test check was dropped because the file covers only 32 dates. The R² and MAE shown are measured on the same days the formulas were built from.
- **Sedentary 1440 with steps.** 10 days have exactly 1440 sedentary minutes but more than 0 steps (368 to 10,330 steps, consecutive dates 3/18 to 3/27). Their minute data looks unrecorded, but they stay in the data because the steps and calories look real. They can weaken the sedentary-minutes formula.
- **Partly logged days.** 224 of 457 days have very active + fairly active + lightly active + sedentary minutes adding up to less than 1440, so part of the day was not logged. These days stay in the data, which may make the minute-based formulas less accurate.
- **Garmin vs Fitbit distance.** The distance formula was built from Fitbit's distance figures. Garmin may measure distance differently, so the distance estimate for a Garmin day may be less reliable than the formula's R² suggests.
- **Why distance beats steps (a guess).** Total distance fits slightly better than total steps (R² 0.36 vs 0.31). My guess, not tested, is that this is partly because distance depends on stride length, which reflects body size, and body size also affects calories.

## Video

Video: (link coming soon)

## Concept table

| Concept | File | Function | Where it shows |
|---|---|---|---|
| Variables and data types | `main.py` | `show_check` | `steps` (int), `distance` (float), `garmin` (int), `supplied` (list), `values` (dict) |
| Constants | `models.py` | module level | `CSV_FILE`, `PREDICTORS`, `MINUTES_PER_DAY` and the other capital-letter names at the top of the file |
| Input and output | `main.py` | `ask_int` | `input()` for the answer, `print()` for the error messages |
| Operators | `models.py` | `LinearModel.fit` | `+`, `-`, `*`, `/` for the means and regression sums, `1 - sum_squared_error / sum_yy` for R², `==` to guard against division by zero |
| Conditionals | `models.py` | `DayRecord.activity_level` | `if` / `elif` / `else` for the three activity levels |
| Loops | `main.py` | `run_menu` | `while True` menu loop that stops with `break` on Exit |
| Functions | `analysis.py` | `build_model` | Takes records and a predictor, returns a fitted `LinearModel` |
| Lists and slicing | `main.py` | `show_check` | `supplied_models` builds the list of matching formulas in ranked order; `matching[:ESTIMATES_SHOWN]` (`ESTIMATES_SHOWN = 2`) keeps the first two |
| String manipulation | `text_utils.py` | `parse_date` | `split("/")`, `strip()`, `len()` and a digit check on each part |
| OOP | `models.py` | `DayRecord` | Class with `__init__`, `activity_level`, `is_worn` and `__str__` |
| Unit tests | `test_project.py` | `TestLinearModel.test_perfect_line` | Checks that y = 2x + 1 gives a = 1, b = 2, R² = 1 (22 tests in total) |
