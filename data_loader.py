"""Read the Fitbit CSV into a FitbitDataset, counting broken rows and non-wear days."""

import csv
import os

from models import CSV_FILE, USED_COLUMNS, DayRecord, FitbitDataset
from text_utils import clean_text, parse_int, parse_float, parse_date


def data_path(file_name):
    """Return the full path of a data file that sits next to this program."""
    if os.path.isabs(file_name):
        return file_name
    folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(folder, file_name)


def find_column_indexes(header):
    """Return the position of each used column in the header, or None if one is missing."""
    indexes = []
    for wanted in USED_COLUMNS:
        found = -1
        for position in range(len(header)):
            if clean_text(header[position]) == clean_text(wanted):
                found = position
        if found == -1:
            return None
        indexes.append(found)
    return indexes


def parse_row(row, indexes, column_count):
    """Return a DayRecord for one CSV row, or None if the row is broken."""
    if len(row) != column_count:
        return None

    # Take the used cells; a blank cell makes the row broken.
    cells = []
    for index in indexes:
        cell = row[index].strip()
        if cell == "":
            return None
        cells.append(cell)

    user_id = parse_int(cells[0])
    date = parse_date(cells[1])
    steps = parse_int(cells[2])
    distance = parse_float(cells[3])
    very_active_min = parse_int(cells[4])
    fairly_active_min = parse_int(cells[5])
    lightly_active_min = parse_int(cells[6])
    sedentary_min = parse_int(cells[7])
    calories = parse_int(cells[8])

    # Any value that could not be parsed makes the row broken.
    values = [user_id, date, steps, distance, very_active_min, fairly_active_min,
              lightly_active_min, sedentary_min, calories]
    for value in values:
        if value is None:
            return None

    # A negative number makes the row broken.
    numbers = [user_id, steps, distance, very_active_min, fairly_active_min,
               lightly_active_min, sedentary_min, calories]
    for number in numbers:
        if number < 0:
            return None

    return DayRecord(user_id, date, steps, distance, very_active_min,
                     fairly_active_min, lightly_active_min, sedentary_min, calories)


def load_dataset(file_name=CSV_FILE):
    """Read the CSV and return (dataset of worn days, broken row count, non-wear day count).

    The dataset is None if the file is missing, unreadable, or lacks a used column.
    Rows loaded = dataset.count() + non-wear count.
    """
    path = data_path(file_name)
    if not os.path.isfile(path):
        return None, 0, 0

    dataset = FitbitDataset()
    broken = 0
    non_wear = 0
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader, None)
            if header is None:
                return None, 0, 0
            indexes = find_column_indexes(header)
            if indexes is None:
                return None, 0, 0

            for row in reader:
                if len(row) == 0:
                    continue
                record = parse_row(row, indexes, len(header))
                if record is None:
                    broken = broken + 1
                elif record.is_worn():
                    dataset.add(record)
                else:
                    non_wear = non_wear + 1
    except (OSError, UnicodeDecodeError, csv.Error):
        return None, 0, 0

    return dataset, broken, non_wear
