"""Calculations for Calibry: averages, percentile, sorting and regression ranking.

This file has no print() or input(), so every function is easy to test.
"""

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


def interpret_difference(difference, mae):
    """Return a plain-English sentence comparing a difference in kcal with the formula's MAE."""
    size = abs(difference)
    if size <= mae / 2:
        return (f"Very close: the difference is well inside the formula's usual error "
                f"(MAE {mae:,.0f} kcal).")
    elif size <= mae:
        return (f"The difference is smaller than the formula's average error "
                f"(MAE {mae:,.0f} kcal), so closer than it usually was on the Fitbit data.")
    else:
        return (f"The difference is larger than the formula's usual error "
                f"(MAE {mae:,.0f} kcal). This can happen on days with cycling, hiking, "
                f"stairs or other effort that steps and distance miss.")


def supplied_models(models, supplied):
    """Return the fitted models whose predictor is in the supplied list, keeping their order."""
    result = []
    for model in models:
        if model.is_fitted and model.predictor in supplied:
            result.append(model)
    return result
