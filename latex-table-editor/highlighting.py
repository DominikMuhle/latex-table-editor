from copy import copy
from typing import Any
import warnings

import pandas as pd

from .utils import Axis, Order

DEFAULT_RULES = {
    "order": Order.NEUTRAL,
    "highlighting": ["\\bfseries{%s}", "\\underline{%s}"],
    "default": "%s",
    "precision": "%.2f",
}


def highlight_extrema(
    data: str | float | int,
    extrema: list[float | int],
    highlights: str,
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
    order: Order,
    highlighting: list[str],
    default: str,
    precision: str,
) -> pd.Series:
    num_highlights = len(highlighting)
    df_column_numeric = pd.to_numeric(df_column, errors="coerce")
    match order:
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
                data, extrema, highlighting, default, precision
            )
        )
        .astype(str)
    )

    all_indices = df_column.index
    ignore_indices = [idx for idx in all_indices if idx not in indices]
    highlighted_column[ignore_indices] = (
        df_column[ignore_indices]
        .apply(
            lambda data: highlight_extrema(data, extrema, [default], default, precision)
        )
        .astype(str)
    )

    return highlighted_column


def table_highlighting(
    dataframe: pd.DataFrame,
    axis: Axis,
    default_rules: dict[str, Any],
    column_override_rules: dict[str, dict[str, Any]] = {},
    ignore: list[str] | None = None,
) -> pd.DataFrame:
    if axis == Axis.ROW:
        # transpose the dataframe to make the row operations column operations
        dataframe = dataframe.T

    missing_keys = []
    for key in DEFAULT_RULES.keys():
        if key not in default_rules:
            missing_keys.append(key)
            default_rules[key] = DEFAULT_RULES[key]
    if missing_keys:
        warnings.warn(
            f"The following keys were missing in the default highlighting: {missing_keys}"
        )

    if ignore is None:
        ignore = []
    for key in ignore:
        if key not in dataframe.index:
            warnings.warn(f"Key {key} not found in the dataframe index")
    remaining_indices = [idx for idx in dataframe.index if idx not in ignore]

    for name in dataframe.columns:
        if name in column_override_rules:
            rules = column_override_rules[name]
        else:
            rules = copy(default_rules)
        order = rules.get("order", default_rules["order"])
        highlighting = rules.get("highlighting", default_rules["highlighting"])
        default = rules.get("default", default_rules["default"])
        precision = rules.get("precision", default_rules["precision"])

        dataframe[name] = column_highlighting(
            dataframe[name], remaining_indices, order, highlighting, default, precision
        )

    if axis == Axis.ROW:
        # transpose the dataframe back to the original orientation
        dataframe = dataframe.T

    return dataframe
