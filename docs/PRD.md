# PRD: Calibry

**Product:** Command-line (terminal) program in Python 3, standard library only
**Context:** Intro to Computer Programming Final Exam (individual take-home project)
**Version:** 1.3 (1 November 2026)
**Name:** "Calibry", a play on *colibri* (hummingbird) and *calibrate*: the program builds a calorie formula from other people's data, then tests it against the user's own Garmin data.

This document has two parts: **(1) Program Design** and **(2) PRD**. Save it as `docs/PRD.md` so the coding agent can read it. The `docs/` folder does not need to be submitted.

---

## 1. Program Design

### 1.1 Concept

Calibry is a terminal menu program that uses a Fitbit dataset from Kaggle as material for **building formulas**, not only for reading data. From 457 days of activity by 35 Fitbit users (12 March to 12 April 2016), the program computes its own straight-line formulas (simple linear regression) that estimate daily calories from one activity variable. The user then enters data from their Garmin watch, and the program compares the formula's estimate with Garmin's calorie figure.

Three features, one per menu item:

- **Dataset summary:** what the data contains and how many days were usable.
- **Compare predictors:** build one calorie formula per activity variable and rank them by accuracy.
- **Check your data:** enter one day of Garmin data and see how it compares.

### 1.2 Project story (for the report and video)

- **From pattern to formula:** health formulas such as the Uth et al. VO2 max estimate come from regression on lab measurements. Calibry repeats the same idea on a small scale: find the multiplier that best fits the data.
- **Test the formula, do not trust it blindly:** a formula from 35 Fitbit users may not hold for one Garmin user. A large difference is a finding, and the program shows it as it is.

### 1.3 Menu map

| No | Menu | What it does |
|---|---|---|
| 1 | Dataset summary | Days loaded, users, broken rows skipped, non-wear days excluded, averages, and how many days fall into each activity level |
| 2 | Compare predictors | Explains how the formula is built, builds `calories = a + b × x` for every predictor, ranks them by R², and states the best formula in plain words |
| 3 | Check your data (Garmin) | Takes one day of Garmin data, shows the estimates from the two best formulas the user has data for, the difference from Garmin, and the user's step percentile |
| 4 | Exit | Ends the program |

### 1.4 Text wireframes

**Start screen**

```
Loaded 457 rows.
Broken rows skipped       : 0
Non-wear days excluded    : 61
Days used                 : 396 days from 34 users

===== CALIBRY =====
1. Dataset summary
2. Compare predictors
3. Check your data (Garmin)
4. Exit
Choose (1-4):
```

The program computes these numbers from the file at run time. The values above are what the current file (the 3.12.16-4.11.16 export) gives. One of the 35 users has only non-wear days, so 34 users remain.

**Menu 2: Compare predictors**

```
How this works
Calibry draws the straight line that best fits 396 days of Fitbit data:
    calories = a + b × predictor
a is the baseline (calories at zero), b is how many calories each unit adds.
R² shows how much of the variation in calories the line explains (0 to 1).
MAE is the average error in kcal.

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

**Menu 3: Check your data** (illustrative day: 6,534 steps, 4.9 km, 20 very active minutes, 2,150 kcal; made-up values, not the user's real Garmin data)

```
Type the numbers from one day in Garmin Connect.
Steps that day          : 6534
Distance (km)           : 4.9
Very active minutes     : 20
Total calories (Garmin) : 2150

------------------------------------------------------------------
Estimate (Total distance formula) : 2,226 kcal
Estimate (Total steps formula)    : 2,196 kcal
Garmin                            : 2,150 kcal
Difference (best formula)         : +76 kcal (+3.5%)
Your steps percentile             : 45 (of 396 days)
------------------------------------------------------------------
Garmin uses heart rate and your body profile, so a difference is expected.
```

Both wireframes show real program output on the current file (396 days). The menu 3 inputs are an illustrative day, not real Garmin data.

Display rule: every result is shown in aligned columns, never as a raw Python list.

### 1.5 Architecture

- **Language:** Python 3, standard library only (`csv`, `os`, `math`, `unittest`). No pandas, no numpy, no `sorted()` or `.sort()` for ranking.
- **Data:** one Kaggle CSV, `dailyActivity_merged.csv`, placed in the same folder as `main.py`.
- **User input:** Garmin data is typed in while the program runs and is not saved to a file.
- **No network and no API.**

Files:

| File | Responsibility |
|---|---|
| `models.py` | Constants (file name, thresholds, predictor list) and the classes `DayRecord`, `FitbitDataset`, `LinearModel` |
| `text_utils.py` | Clean text, parse dates in M/D/YYYY form with a one- or two-digit month and day ("3/9/2016", "4/12/2016"), parse numbers from text |
| `data_loader.py` | Read the CSV, skip broken rows, separate non-wear days |
| `analysis.py` | Averages, percentile, hand-written sorting, regression ranking, choosing the formulas for menu 3 |
| `main.py` | Menu, input validation, table output |
| `test_project.py` | Unit tests |

### 1.6 Main flows

**A. Loading data.** The loader reads each row with `csv.reader`. A row is skipped and counted as *broken* if it has the wrong number of columns, a blank cell in any used column, a number that cannot be converted, or a date that is not in M/D/YYYY form. A row that reads correctly but has `TotalSteps == 0` is counted as *non-wear*, whatever its sedentary minutes, and is not used for formulas, averages, or percentiles. Both counts are reported separately on the start screen.

**B. Building one formula (simple linear regression).** For predictor x and target y (calories):

1. Compute the means x̄ and ȳ.
2. b = Σ(x − x̄)(y − ȳ) / Σ(x − x̄)²
3. a = ȳ − b × x̄
4. R² = 1 − Σ(y − ŷ)² / Σ(y − ȳ)²
5. MAE = mean of |y − ŷ|

If Σ(x − x̄)² or Σ(y − ȳ)² is 0, the formula is not built and the program shows a message instead, so nothing divides by zero.

**C. Compare predictors (menu 2).** The program prints the "How this works" explanation, builds one formula for each predictor in `PREDICTORS`, stores them in a list, ranks the list by R² with a hand-written selection sort, prints the table, and states the best formula in a plain sentence.

**D. Check your data (menu 3).** The user types steps, distance (km, decimals allowed), very active minutes, and Garmin total calories. The program:

1. Builds the list of fitted formulas whose predictor the user supplied (steps, distance, or very active minutes), keeping the R² ranking from menu 2, and shows the estimates from the first 2 with slicing `[:2]`. The first one is the main estimate. On the current file these are Total distance (R² 0.36) and Total steps (R² 0.31). If only one formula matches, only one line is shown.
2. Computes the difference (estimate − Garmin) in kcal and as a percentage of Garmin's figure (safe when Garmin's figure is 0).
3. Computes the step percentile: the share of dataset days with fewer steps than the user.

### 1.7 Data dictionary

Columns used from `dailyActivity_merged.csv`:

| Column | Type | Used for |
|---|---|---|
| Id | int | Grouping by user (anonymous number) |
| ActivityDate | str | Parsed and stored (M/D/YYYY, one- or two-digit month and day) |
| TotalSteps | int | Predictor, percentile, non-wear check |
| TotalDistance | float | Predictor |
| VeryActiveMinutes | int | Predictor |
| FairlyActiveMinutes | int | Predictor |
| LightlyActiveMinutes | int | Predictor |
| SedentaryMinutes | int | Predictor (shown in menu 2 only) |
| Calories | int | Formula target |

Skipped columns: TrackerDistance (almost identical to TotalDistance), LoggedActivitiesDistance (mostly zero), and the four distance-by-intensity columns (already covered by the minute columns).

File check (Stage 0, on the 3.12.16-4.11.16 export): 457 data rows plus a header, 15 columns with the exact names above, 35 users, dates from 3/12/2016 to 4/12/2016 (32 dates). No column has blank cells. If a blank cell does appear in a used column, the row is treated as broken (see 1.6 A). Lines end in `\r\n`, which `csv.reader` handles.

### 1.8 Use cases

Actors: **User** (Garmin owner) and **Examiner** (lecturer who runs the program and tests).

| ID | Use case | Relation |
|---|---|---|
| UC-01 | Start the program and load data | |
| UC-02 | View dataset summary | include UC-01 |
| UC-03 | Compare predictors | include UC-01 |
| UC-04 | Check own Garmin data | include UC-03 (uses the best formula) |
| UC-05 | Run unit tests | Examiner |

### 1.9 Class design

| Class | Responsibility | Key attributes and methods |
|---|---|---|
| DayRecord | One CSV row = one day for one user | `user_id`, `date`, `steps`, `distance`, `very_active_min`, `fairly_active_min`, `lightly_active_min`, `sedentary_min`, `calories`, `activity_level()`, `is_worn()` (True when steps are above 0), `__str__()` |
| FitbitDataset | Holds the list of `DayRecord` | `records`, `add()`, `count()`, `user_ids()`, `records_of(user_id)`, `__str__()` |
| LinearModel | One regression formula for one predictor | `predictor`, `label`, `intercept`, `slope`, `r_squared`, `mae`, `fit(xs, ys)`, `predict(x)`, `__str__()` |

`activity_level()` returns one of three levels with if, elif, else: Sedentary (under 5,000 steps), Lightly Active (5,000 to 9,999), Active (10,000 or more).

---

## 2. PRD (Product Requirements Document)

### 2.1 Background and problem

- The exam asks for a menu program that explores a real Kaggle dataset, with at least 3 features and the eight core Python concepts, without pandas or numpy.
- A program that only reads and prints a CSV is passive and of little use to anyone else.
- Smartwatch owners see a calorie number every day but rarely know where it comes from or how far to trust it.
- Popular health formulas come from regression on data, and that process can be demonstrated with basic Python.

### 2.2 Goals and non-goals

**Goals**

1. Meet every requirement of the Final Exam and its grading rubric.
2. Use the CSV as material for building formulas, not only as data to display.
3. Let the user test those formulas with their own wearable data.
4. Write all logic (averages, regression, sorting) by hand so every line can be explained in the video.

**Non-goals**

- No automatic import of Garmin export files; input is typed manually.
- No VO2 max formula, because the dataset has no measured VO2 max to fit against.
- No medical, diet, or calorie-target advice.
- No multiple regression, matrices, or machine learning libraries.
- No graphical interface, web version, or saved input history.

### 2.3 Personas

- **Vankaa, student and Garmin user:** wants to know whether his watch's calorie number is reasonable compared with other people's patterns. Needs fast input and a clear comparison.
- **Examiner (lecturer):** runs `python main.py` and `python -m unittest` with plain Python 3. Needs a program that never crashes and code where each concept is easy to find.
- **Friend with a smartwatch:** no statistics background. Needs results in plain words, for example "this formula explains about 40% of the variation in calories".

### 2.4 Functional requirements

Priority: P0 required to pass the rubric, P1 strongly wanted, P2 only if time allows.

**FR-1 Load data (P0)**

- On start, read the CSV and print rows loaded, broken rows skipped, and non-wear days excluded.
- A row is broken if it has the wrong column count, a blank cell in any used column, an invalid number, or an invalid date.
- A day with `TotalSteps == 0` is non-wear, whatever its sedentary minutes, and is excluded from formulas and statistics.
- Dates are parsed as M/D/YYYY with a one- or two-digit month and day.
- If the file is missing, print a clear message and stop without a traceback.
- Acceptance: rows with invalid numbers, blank used cells, invalid dates, or the wrong column count are skipped and counted; loaded + broken = data rows in the file; on the current file this gives 457 loaded, 0 broken, 61 non-wear excluded, 396 days used from 34 users.

**FR-2 Repeating menu and input validation (P0)**

- The menu repeats until the user chooses Exit (`while`).
- Every input is validated in a loop: empty, non-numeric, or out-of-range input gives a clear message and a new prompt.
- Acceptance: "abc", "", "-5", "99", and "3.5" at the menu prompt never crash the program.

**FR-3 Dataset summary (P0)**

- Show days used, unique users, average steps, very active minutes, sedentary minutes, and calories, plus the number and percentage of days in each activity level.
- Acceptance: averages match hand calculations on the small test data in the unit tests.

**FR-4 Compare predictors (P0)**

- Print a short "How this works" explanation of the formula, a, b, R², and MAE before the table.
- Build one formula per predictor (total steps, total distance, very active minutes, fairly active minutes, lightly active minutes, sedentary minutes), rank them by R² with hand-written sorting, and print the table.
- End with the best formula in a plain sentence, for example "Every extra 1,000 steps adds about X kcal".
- Acceptance: on test data y = 2x + 1 the model gives a = 1, b = 2, R² = 1; x values that are all equal do not cause division by zero; ranking order is correct on test data; a predictor that cannot be fitted is listed with a note and does not stop the program.

**FR-5 Check your data with Garmin (P0)**

- Input: steps, distance (km, decimals allowed), very active minutes, and Garmin total calories. Sedentary minutes are not asked for.
- Output: estimates from the first 2 fitted formulas, in ranked order, whose predictor the user supplied (Total distance and Total steps on the current file); difference in kcal and percent from the first (main) estimate; step percentile.
- Acceptance: very active minutes over 1,440 are rejected with a message; Garmin calories of 0 do not cause division by zero (the percent is shown as n/a); the illustrative day in 1.4 (6,534 steps, 4.9 km, 20, 2,150 kcal; not real Garmin data) gives 2,226 kcal from the distance formula and 2,196 kcal from the steps formula.

**FR-6 Train/test check (DROPPED)**

Dropped in version 1.2: the file covers only 32 dates, too few for a meaningful split by date. The original text is kept below for reference only.

- Split days by date: roughly the first 80% build the formulas, the rest measure test MAE.
- Acceptance: menu 2 shows training MAE and test MAE side by side.

### 2.5 Non-functional requirements

- **Environment:** runs with `python main.py` and `python -m unittest` from inside the folder with only Python 3 installed.
- **Code:** at least four `.py` files split by job; constants in capital letters; no `__pycache__` in the submission.
- **Robustness:** no traceback under any input the user can type.
- **Output:** aligned columns with f-strings; consistent rounding.
- **Text handling:** any text matching (yes/no answers, column headers) ignores capital letters and extra spaces.
- **Privacy:** the user's Garmin data is not saved; the Fitbit dataset uses anonymous IDs.
- **Language:** interface, code, comments, and docstrings in English.

### 2.6 Success metrics

- All unit tests pass, at least 5 tests covering normal, edge, and bad input.
- Zero crashes in the bad-input scenarios for every menu.
- Every core concept can be pointed to one file and function in the report's concept table.
- The video is 15 minutes or less and shows each feature once, including invalid input.

### 2.7 Risks and mitigations

| Risk | Mitigation |
|---|---|
| Low R² because calories depend heavily on body weight, which this file does not contain | Show R² as it is and discuss it in the report as a finding |
| Garmin estimates calories from heart rate and body profile, unlike a step-based formula | Explain in menu 3 and in the report that a difference is expected |
| 35 users over one month in 2016 do not represent the wider population | State it under known limitations |
| Non-wear days distort the formulas | Exclude every day with 0 steps (61 days), then report the count |
| Date or number formats differ from expectations | Check the file after download; parsers return a failure value so the row is skipped without a crash |
| Deadline is very close | Build P0 first; FR-6 is dropped |

**Known limitations**

- **Sedentary 1440 with steps:** 10 days have exactly 1440 sedentary minutes but more than 0 steps (368 to 10,330 steps, consecutive dates 3/18 to 3/27). Their minute data looks unrecorded, but they stay in the data because the steps and calories look real. They can weaken the sedentary-minutes formula.
- **Partly logged days:** 224 of 457 days have minute totals (very active + fairly active + lightly active + sedentary) under 1440, so part of the day was not logged. These days stay in the data. Minute-based predictors may be less accurate because of this.
- **Small sample:** 35 users, one month (12 March to 12 April 2016), no body weight, so R² is expected to be modest.

### 2.8 Rubric mapping

| Rubric item | Points | How Calibry covers it |
|---|---|---|
| Dataset and loading | 8 | CC0 Kaggle CSV, 200 to 2,000 rows, loader skips and counts broken rows |
| Program features | 24 | Three features (FR-3 to FR-5), validated input, aligned output |
| Core concepts | 24 | See the concept table below |
| Unit tests | 6 | Regression, empty average, percentile, sorting, loader, bad input |
| README / report | 4 | PDF report with every required item |
| Video | 34 | Demo of each feature, concepts explained with code locations, at least 5 likes and 5 views |
| OOP bonus | up to 10 | `DayRecord` with `__init__` and `__str__`; `FitbitDataset` holds the list of records |

**Concept table (plan)**

| Concept | File | Function |
|---|---|---|
| Variables, data types, constants | `models.py` | `CSV_FILE`, `PREDICTORS`, `DayRecord.__init__` |
| Input and output | `main.py` | `ask_int`, `print_table` |
| Operators | `analysis.py` | `average`, `LinearModel.fit`, `percentile` |
| Conditionals | `models.py` | `DayRecord.activity_level` |
| Loops | `main.py` / `analysis.py` | `main` (while), `sort_by` (for) |
| Functions | `analysis.py` | `build_model`, `supplied_models` |
| Lists and slicing | `analysis.py` / `main.py` | `rank_predictors`, `show_check` (`[:2]`) |
| String manipulation | `text_utils.py` | `clean_text`, `parse_date` |
| OOP | `models.py` | `DayRecord`, `FitbitDataset`, `LinearModel` |
| Unit tests | `test_project.py` | at least 5 tests |

### 2.9 Data and sources

- **Dataset:** FitBit Fitness Tracker Data (Kaggle), file `dailyActivity_merged.csv`, export folder 3.12.16-4.11.16 (457 rows, 12 March to 12 April 2016), license CC0: Public Domain, 35 users who consented to sharing their tracker data.
- **Comparison data:** the user's own Garmin Connect summaries, typed in manually in menu 3. Example week with the most complete data: 2 to 8 August 2026.
- **Concept reference:** the Uth et al. VO2 max formula as an example of a regression-derived formula (mentioned in the report and video, not implemented).
