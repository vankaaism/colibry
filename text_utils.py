"""Helpers for cleaning text and parsing numbers and dates. Parsers return None on bad input."""

import math

DIGITS = "0123456789"


def clean_text(text):
    """Return the text in lower case with extra spaces removed."""
    if text is None:
        return ""
    words = str(text).split()
    return " ".join(words).lower()


def parse_int(text):
    """Return the text as a whole number, or None if it is not one."""
    cleaned = clean_text(text)
    if cleaned == "":
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def parse_float(text):
    """Return the text as a decimal number, or None if it is not a normal number."""
    cleaned = clean_text(text)
    if cleaned == "":
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def is_plain_digits(text):
    """Return True if the text is not empty and contains only the digits 0-9."""
    if text == "":
        return False
    for character in text:
        if character not in DIGITS:
            return False
    return True


def is_leap_year(year):
    """Return True if the year is a leap year."""
    if year % 400 == 0:
        return True
    elif year % 100 == 0:
        return False
    elif year % 4 == 0:
        return True
    else:
        return False


def days_in_month(month, year):
    """Return how many days the month has in the given year."""
    if month == 2:
        if is_leap_year(year):
            return 29
        return 28
    elif month == 4 or month == 6 or month == 9 or month == 11:
        return 30
    else:
        return 31


def parse_date(text):
    """Return a date in M/D/YYYY form as (year, month, day), or None if it is not valid."""
    cleaned = clean_text(text)
    parts = cleaned.split("/")
    if len(parts) != 3:
        return None

    month_text = parts[0].strip()
    day_text = parts[1].strip()
    year_text = parts[2].strip()

    if len(month_text) < 1 or len(month_text) > 2 or not is_plain_digits(month_text):
        return None
    if len(day_text) < 1 or len(day_text) > 2 or not is_plain_digits(day_text):
        return None
    if len(year_text) != 4 or not is_plain_digits(year_text):
        return None

    month = int(month_text)
    day = int(day_text)
    year = int(year_text)

    if month < 1 or month > 12:
        return None
    if day < 1 or day > days_in_month(month, year):
        return None
    return (year, month, day)


def format_date(date):
    """Return a (year, month, day) date as M/D/YYYY text."""
    year = date[0]
    month = date[1]
    day = date[2]
    return f"{month}/{day}/{year}"
