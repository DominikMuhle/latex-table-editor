import warnings
from copy import copy
from typing import Any

import pandas as pd

from latex_table_editor.utils import DEFAULT_RULES, Axis, Order, Rule

# Remove DEFAULT_RULES definition here

def highlight_extrema(
    data: str | float | int,
    extrema: list[float | int],
    highlights: list[str],
    default: str,
    precision: str = "%.3f",
) -> str:
    if isinstance(data, str):
        return data

    data_ = precision % data

    for extremum, highlight in zip(extrema, highlights):
        # highlight_ = highlight.replace("precision", precision)
        if data == extremum:
            return highlight % data_

    # default_ = default.replace("precision", precision)
    return default % data_


def column_highlighting(
    df_column: pd.Series,
    indices: list[str],
    rule: Rule,
) -> pd.Series:
    num_highlights = len(rule.highlighting)
    df_column_numeric = pd.to_numeric(df_column, errors="coerce")
    match rule.order:
        case Order.MINIMUM:
            extrema = df_column_numeric[indices].nsmallest(num_highlights)
            extrema = extrema.tolist()
        case Order.NEUTRAL:
            extrema = []
        case Order.MAXIMUM:
            extrema = df_column_numeric[indices].nlargest(num_highlights)
            extrema = extrema.tolist()

    highlighted_column = df_column.copy().astype(object)
    highlighted_column[indices] = (
        df_column[indices]
        .apply(
            lambda data: highlight_extrema(
                data, extrema, rule.highlighting, rule.default, rule.precision
            )
        )
        .astype(str)
    )

    all_indices = df_column.index
    ignore_indices = [idx for idx in all_indices if idx not in indices]
    highlighted_column[ignore_indices] = (
        df_column[ignore_indices]
        .apply(
            lambda data: highlight_extrema(data, extrema, [rule.default], rule.default, rule.precision)
        )
        .astype(str)
    )

    return highlighted_column


def table_highlighting(
    dataframe: pd.DataFrame,
    axis: Axis,
    default_rule: Rule,
    override_rules: dict[str, Rule] = {},
    ignore: list[str] | None = None,
) -> pd.DataFrame:
    # replace the missing values in the default rule with the values from DEFAULT_RULES
    default_rule = copy(default_rule)
    for key, value in DEFAULT_RULES.__dict__.items():
        if getattr(default_rule, key) is None:
            setattr(default_rule, key, value)

    if axis == Axis.ROW:
        # transpose the dataframe to make the row operations column operations
        dataframe = dataframe.T

    if ignore is None:
        ignore = []
    for key in ignore:
        if key not in dataframe.index:
            warnings.warn(f"Key {key} not found in the dataframe index")
    remaining_indices = [idx for idx in dataframe.index if idx not in ignore]

    for name in dataframe.columns:
        rule = copy(override_rules.get(name, default_rule))
        # replace the missing values in the override rule with the values from the default rule
        for key, value in default_rule.__dict__.items():
            if getattr(rule, key) is None:
                setattr(rule, key, value)

        dataframe[name] = column_highlighting(
            dataframe[name], remaining_indices, rule
        )

    if axis == Axis.ROW:
        # transpose the dataframe back to the original orientation
        dataframe = dataframe.T

    return dataframe
