
from copy import copy
from typing import Any
import warnings

import pandas as pd

from utils import Axis, Order

DEFAULT_HIGHLIGHTING = {
    "order": Order.NEUTRAL,
    "highlighting": ["%s"],
    "default": "%s",
    "precision": "%.2f",
}

def highlight_extrema(data: str | float | int, extrema: list[float | int], highlights: str, default: str, precision: str="%.3f") -> str:
    if isinstance(data, str):
        return data
    
    data_ = precision % data
    
    for extremum, highlight in zip(extrema, highlights):
        # highlight_ = highlight.replace("precision", precision)
        if data == extremum:
            return highlight % data_
        
    # default_ = default.replace("precision", precision)
    return default % data_


def column_highlighting(df_column: pd.DataFrame, indices: list[int], order: Order, highlighting: list[str], default: str, precision: str) -> pd.DataFrame:
    num_highlights = len(highlighting)
    df_column_numeric = pd.to_numeric(df_column, errors="coerce")
    match order:
        case Order.MINIMUM:
            extrema = df_column_numeric.iloc[indices].nsmallest(num_highlights)
        case Order.NEUTRAL:
            extrema = []
        case Order.MAXIMUM:
            extrema = df_column_numeric.iloc[indices].nlargest(num_highlights)

    df_column = df_column.apply(lambda data: highlight_extrema(data, extrema, highlighting, default, precision)).astype(str)
    return df_column

def table_highlighting(
    dataframe: pd.DataFrame,
    axis: Axis = Axis.COLUMN,
    order: Order | list[Order] = Order.MINIMUM,
    highlighting: list[str] | list[list[str]] = ["\\bfseries{%s}", "\\underline{%s}"],
    default: str | list[str] = "%s",
    precision: str = "%.3f",
    ignore_idx: list[int] | None = None,
) -> pd.DataFrame:
    
    if axis == Axis.ROW:
        # transpose the dataframe to make the row operations column operations
        dataframe = dataframe.T

    rows, columns = dataframe.shape
    if ignore_idx is None:
        ignore_idx = []
    remaining_indices = [idx for idx in range(rows) if idx not in ignore_idx]

    if isinstance(order, Order):
        order = [order] * columns
    if isinstance(highlighting[0], str):
        highlighting = [highlighting] * columns
    if isinstance(default, str):
        default = [default] * columns
    
    for idx, (k, order_, highlighting_, default_) in enumerate(zip(dataframe.columns, order, highlighting, default)):
        # if idx in ignore_idx:
        #     continue
        dataframe[k] = column_highlighting(dataframe[k], remaining_indices, order_, highlighting_, default_, precision)

    if axis == Axis.ROW:
        # transpose the dataframe back to the original orientation
        dataframe = dataframe.T

    return dataframe


def table_highlighting_by_name(dataframe: pd.DataFrame, axis: Axis, formatting_rules: dict[str, dict[str, Any]], default_highlighting: dict[str, Any] = {}, ignore_idx: list[int] | None = None) -> pd.DataFrame:
    if axis == Axis.ROW:
        # transpose the dataframe to make the row operations column operations
        dataframe = dataframe.T

    missing_keys = []
    for key in DEFAULT_HIGHLIGHTING.keys():
        if key not in default_highlighting:
            missing_keys.append(key)
            default_highlighting[key] = DEFAULT_HIGHLIGHTING[key]
    if missing_keys:
        warnings.warn(f"The following keys were missing in the default highlighting: {missing_keys}")


    rows, columns = dataframe.shape
    if ignore_idx is None:
        ignore_idx = []
    remaining_indices = [idx for idx in range(rows) if idx not in ignore_idx]

    for name, rules in formatting_rules.items():
        order = rules.get("order", default_highlighting["order"])
        highlighting = rules.get("highlighting", default_highlighting["highlighting"])
        default = rules.get("default", default_highlighting["default"])
        precision = rules.get("precision", default_highlighting["precision"])

        dataframe[name] = column_highlighting(dataframe[name], remaining_indices, order, highlighting, default, precision)

    if axis == Axis.ROW:
        # transpose the dataframe back to the original orientation
        dataframe = dataframe.T

    return dataframe



