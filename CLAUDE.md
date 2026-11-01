# Calibry: project rules

Read `docs/PRD.md` before doing anything. The PRD is the source of truth.

## Required rules (from the Final Exam brief)

- Python 3, standard library only (csv, os, math, unittest). No pandas, numpy, or any outside library.
- Never use `sorted()` or `.sort()`. Write every sort yourself with loops (selection sort).
- Files: models.py, text_utils.py, data_loader.py, analysis.py, main.py, test_project.py.
- `analysis.py` must not contain `input()` or `print()`, so it stays easy to test.
- Validate every input in a loop; the program must never crash on any input.
- Nothing divides by zero; any text matching ignores capital letters and extra spaces.
- Show results in aligned columns with f-strings, never as raw Python lists.
- Constants go in models.py in capital letters, including `CSV_FILE = "dailyActivity_merged.csv"`.
- Broken CSV rows are skipped and counted; non-wear days are counted separately.
- The menu has exactly four items: Dataset summary, Compare predictors, Check your data (Garmin), Exit.

## Code style

- I am a beginner. Write simple, explicit code; avoid nested comprehensions, lambdas, and clever shortcuts.
- Every function has a short English docstring.
- All names, comments, and interface text are in English.
- Before writing code for a stage, explain the logic first.

## How to work

- Work one stage at a time in the order I ask, then stop and wait.
- After each stage, run `python -m unittest` and report the result.
- Do not create files outside the structure above unless I ask.
- Commit and push to `main` after every change. Commit messages are a short title only: no description body and no Co-Authored-By or other trailers.
