
from copy import copy
from typing import Any

import pandas as pd

from utils import Axis, Order


def highlight_extrema(data, extrema, highlights, precision):
    if isinstance(data, str):
        return data
    for extremum, highlight in zip(extrema, highlights):
        if data == extremum:
            return highlight % data
    return precision % data


def column_highlighting(df_column: pd.DataFrame, indices: list[int], order: Order, highlighting: list[str], default: str) -> pd.DataFrame:
    num_highlights = len(highlighting)
    df_column_numeric = pd.to_numeric(df_column, errors="coerce")
    match order:
        case Order.MINIMUM:
            extrema = df_column_numeric.iloc[indices].nsmallest(num_highlights)
        case Order.MAXIMUM:
            extrema = df_column_numeric.iloc[indices].nlargest(num_highlights)

    df_column = df_column.apply(lambda data: highlight_extrema(data, extrema, highlighting, default)).astype(str)
    return df_column

def table_highlighting(
    dataframe: pd.DataFrame,
    axis: Axis = Axis.COLUMN,
    order: Order | list[Order] = Order.MINIMUM,
    highlighting: list[str] | list[list[str]] = ["\\bfseries{%.3f}", "\\underline{%.3f}"],
    default: str | list[str] = "%.3f",
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
        dataframe[k] = column_highlighting(dataframe[k], remaining_indices, order_, highlighting_, default_)

    if axis == Axis.ROW:
        # transpose the dataframe back to the original orientation
        dataframe = dataframe.T

    return dataframe


def table_highlighting_by_name(dataframe: pd.DataFrame, axis: Axis, metrics: list[dict[str, Any]], ignore_idx: list[int] | None = None) -> pd.DataFrame:
    if axis == Axis.ROW:
        # transpose the dataframe to make the row operations column operations
        dataframe = dataframe.T

    rows, columns = dataframe.shape
    if ignore_idx is None:
        ignore_idx = []
    remaining_indices = [idx for idx in range(rows) if idx not in ignore_idx]

    for metric in metrics:
        name = metric["name"]
        order = metric.get("order", Order.MINIMUM)
        highlighting = metric.get("highlighting", ["\\bfseries{%.3f}", "\\underline{%.3f}"])
        default = metric.get("default", "%.3f")

        dataframe[name] = column_highlighting(dataframe[name], remaining_indices, order, highlighting, default)

    if axis == Axis.ROW:
        # transpose the dataframe back to the original orientation
        dataframe = dataframe.T

    return dataframe



