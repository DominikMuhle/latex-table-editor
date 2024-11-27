# BSD 3-Clause License
#
# This file is part of the PNEC project.
# https://github.com/tum-vision/pnec
#
# Copyright (c) 2022, Dominik Muhle.
# All rights reserved.

import warnings

import numpy as np
import pandas as pd


def highlight_extrema(data, extrema, highlights, precision):
    for extremum, highlight in zip(extrema, highlights):
        if data == extremum:
            return highlight % data
    return precision % data


def table_highlighting(
    dataframe: pd.DataFrame,
    minimum: bool = True,
    axis: int = 0,
    highlighting: list[str] = ["\\bfseries{%.3f}", "\\underline{%.3f}"],
    precision: str = "%.3f",
    ignore_idx: list[int] | None = None,
) -> pd.DataFrame:
    if not axis in [0, 1]:
        warnings.warn("Axis must be 0 or 1. Returning original dataframe.")
        return dataframe

    num_highlights = len(highlighting)
    if axis == 0:
        # non_ignored_inx = [i for i in range(dataframe.shape[0]) if i not in ignore_idx]
        for k in range(dataframe.shape[0]):
            row = dataframe.iloc[k, :].to_numpy()
            if ignore_idx is not None:
                filtered_row = np.delete(row, ignore_idx, 0)
            else:
                filtered_row = row
            row_sorted = np.sort(filtered_row, axis=0)
            if minimum:
                extrema = row_sorted[:num_highlights]
            else:
                extrema = np.flip(row_sorted, axis=0)[:num_highlights]
            dataframe.iloc[k, :] = dataframe.iloc[k, :].apply(
                lambda data: highlight_extrema(data, extrema, highlighting, precision)
            )
    if axis == 1:
        if ignore_idx is None:
            ignore_idx = []
        non_ignored_inx = [i for i in range(dataframe.shape[1]) if i not in ignore_idx]
        for k in dataframe.columns:
            if minimum:
                extrema = dataframe[k].nsmallest(num_highlights)
            else:
                extrema = dataframe[k].nlargest(num_highlights)
            dataframe[k] = dataframe[k].apply(lambda data: highlight_extrema(data, extrema, highlighting, precision))

    return dataframe



def main() -> None:
    table = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [5, 4, 3, 2, 1],
            "C": [1, 3, 5, 7, 9],
        }
    )
    print(table_highlighting(table, minimum=True, axis=0).to_latex())


if __name__ == "__main__":
    main()
