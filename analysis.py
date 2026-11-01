"""Calculations for Calibry: averages, percentile, sorting, regression ranking and similarity.

This file has no print() or input(), so every function is easy to test.
"""

import math

from models import ACTIVITY_LEVELS, PREDICTORS, LinearModel


def average(values):
    """Return the mean of a list of numbers, or 0.0 for an empty list."""
    if len(values) == 0:
        return 0.0
    total = 0.0
    for value in values:
        total = total + value
    return total / len(values)


def percentage(part, whole):
    """Return part as a percentage of whole, or 0.0 when whole is 0."""
    if whole == 0:
        return 0.0
    return part / whole * 100


def percentile(value, values):
    """Return the percentage of values strictly below value, or 0.0 for an empty list."""
    if len(values) == 0:
        return 0.0
    below = 0
    for other in values:
        if other < value:
            below = below + 1
    return percentage(below, len(values))


def maximum(values):
    """Return the largest number in a list, or 0.0 for an empty list."""
    if len(values) == 0:
        return 0.0
    largest = values[0]
    for value in values:
        if value > largest:
            largest = value
    return largest


def get_value(item, key_name):
    """Return one field from a dict or one attribute from an object."""
    if isinstance(item, dict):
        return item[key_name]
    return getattr(item, key_name)


def column_values(records, key_name):
    """Return a list with one field taken from every record."""
    values = []
    for record in records:
        values.append(get_value(record, key_name))
    return values


def sort_by(items, key_name, descending=False):
    """Return a sorted copy of items using selection sort on one field."""
    result = items[:]
    for i in range(len(result)):
        best = i
        for j in range(i + 1, len(result)):
            value_j = get_value(result[j], key_name)
            value_best = get_value(result[best], key_name)
            if descending:
                if value_j > value_best:
                    best = j
            else:
                if value_j < value_best:
                    best = j
        temporary = result[i]
        result[i] = result[best]
        result[best] = temporary
    return result


def dataset_summary(dataset):
    """Return a dict with days, users, averages and the days per activity level."""
    records = dataset.records
    days = len(records)

    levels = []
    for level in ACTIVITY_LEVELS:
        count = 0
        for record in records:
            if record.activity_level() == level:
                count = count + 1
        levels.append({"level": level, "count": count, "percent": percentage(count, days)})

    return {
        "days": days,
        "users": len(dataset.user_ids()),
        "avg_steps": average(column_values(records, "steps")),
        "avg_very_active": average(column_values(records, "very_active_min")),
        "avg_sedentary": average(column_values(records, "sedentary_min")),
        "avg_calories": average(column_values(records, "calories")),
        "levels": levels,
    }


def build_model(records, predictor):
    """Return a LinearModel for one (attribute, label) predictor, fitted if possible."""
    attribute = predictor[0]
    label = predictor[1]
    model = LinearModel(attribute, label)
    xs = column_values(records, attribute)
    ys = column_values(records, "calories")
    model.fit(xs, ys)
    return model


def rank_predictors(records):
    """Return one model per predictor, ranked by R squared, with unfitted models last."""
    fitted = []
    unfitted = []
    for predictor in PREDICTORS:
        model = build_model(records, predictor)
        if model.is_fitted:
            fitted.append(model)
        else:
            unfitted.append(model)
    return sort_by(fitted, "r_squared", True) + unfitted


def choose_model(models, supplied):
    """Return the best-ranked fitted model whose predictor is in the supplied list, or None."""
    for model in models:
        if model.is_fitted and model.predictor in supplied:
            return model
    return None


def find_model(models, predictor):
    """Return the fitted model for one predictor attribute, or None."""
    for model in models:
        if model.is_fitted and model.predictor == predictor:
            return model
    return None


def user_averages(dataset):
    """Return one dict per user with average steps, very active and sedentary minutes."""
    result = []
    for user_id in dataset.user_ids():
        records = dataset.records_of(user_id)
        result.append({
            "user_id": user_id,
            "days": len(records),
            "avg_steps": average(column_values(records, "steps")),
            "avg_very_active": average(column_values(records, "very_active_min")),
            "avg_sedentary": average(column_values(records, "sedentary_min")),
        })
    return result


def scale(value, largest):
    """Return value divided by largest, or 0.0 when largest is 0."""
    if largest == 0:
        return 0.0
    return value / largest


def most_similar_users(dataset, steps, very_active, sedentary, n):
    """Return the n users whose averages are closest to the given day, nearest first."""
    if n <= 0:
        return []

    max_steps = maximum(column_values(dataset.records, "steps"))
    max_very_active = maximum(column_values(dataset.records, "very_active_min"))
    max_sedentary = maximum(column_values(dataset.records, "sedentary_min"))

    users = user_averages(dataset)
    for user in users:
        d_steps = scale(user["avg_steps"], max_steps) - scale(steps, max_steps)
        d_very_active = (scale(user["avg_very_active"], max_very_active)
                         - scale(very_active, max_very_active))
        d_sedentary = (scale(user["avg_sedentary"], max_sedentary)
                       - scale(sedentary, max_sedentary))
        user["distance"] = math.sqrt(d_steps * d_steps
                                     + d_very_active * d_very_active
                                     + d_sedentary * d_sedentary)

    ranked = sort_by(users, "distance")
    return ranked[:n]
