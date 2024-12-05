import pandas as pd
import pytest

from highlighting import table_highlighting
from utils import Order, Axis

base_dataframe = pd.DataFrame(
    {
        "A": [1, 2, 3, 4, 5],
        "B": [5, 4, 3, 2, 1],
        "C": [1, 3, 5, 7, 9],
    },
    index=["a", "b", "c", "d", "e"],
)


def test_minimum_column_highlighting() -> None:
    dataframe = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
        },
        index=["a", "b", "c", "d", "e"],
    )
    default_rules = {
        "order": Order.MINIMUM,
        "highlighting": ["\\bfseries{%s}", "\\underline{%s}"],
        "default": "%s",
        "precision": "%.2f",
    }
    expected = pd.DataFrame(
        {
            "A": ["\\bfseries{1.00}", "\\underline{2.00}", "3.00", "4.00", "5.00"],
        },
        index=["a", "b", "c", "d", "e"],
    )
    assert table_highlighting(dataframe, Axis.COLUMN, default_rules).equals(expected)


def test_maximum_column_highlighting() -> None:
    dataframe = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
        },
        index=["a", "b", "c", "d", "e"],
    )
    default_rules = {
        "order": Order.MAXIMUM,
        "highlighting": ["\\bfseries{%s}", "\\underline{%s}"],
        "default": "%s",
        "precision": "%.2f",
    }
    expected = pd.DataFrame(
        {
            "A": ["1.00", "2.00", "3.00", "\\underline{4.00}", "\\bfseries{5.00}"],
        },
        index=["a", "b", "c", "d", "e"],
    )
    assert table_highlighting(dataframe, Axis.COLUMN, default_rules).equals(expected)


def test_minimum_row_highlighting() -> None:
    dataframe = pd.DataFrame(
        {
            "A": [1],
            "B": [2],
            "C": [3],
            "D": [4],
            "E": [5],
        },
        index=["a"],
    )
    default_rules = {
        "order": Order.MINIMUM,
        "highlighting": ["\\bfseries{%s}", "\\underline{%s}"],
        "default": "%s",
        "precision": "%.2f",
    }
    expected = pd.DataFrame(
        {
            "A": ["\\bfseries{1.00}"],
            "B": ["\\underline{2.00}"],
            "C": ["3.00"],
            "D": ["4.00"],
            "E": ["5.00"],
        },
        index=["a"],
    )
    assert table_highlighting(dataframe, Axis.ROW, default_rules).equals(expected)


def test_maximum_row_highlighting() -> None:
    dataframe = pd.DataFrame(
        {
            "A": [1],
            "B": [2],
            "C": [3],
            "D": [4],
            "E": [5],
        },
        index=["a"],
    )
    default_rules = {
        "order": Order.MAXIMUM,
        "highlighting": ["\\bfseries{%s}", "\\underline{%s}"],
        "default": "%s",
        "precision": "%.2f",
    }
    expected = pd.DataFrame(
        {
            "A": ["1.00"],
            "B": ["2.00"],
            "C": ["3.00"],
            "D": ["\\underline{4.00}"],
            "E": ["\\bfseries{5.00}"],
        },
        index=["a"],
    )
    assert table_highlighting(dataframe, Axis.ROW, default_rules).equals(expected)


def test_override_column() -> None:
    dataframe = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [1, 2, 3, 4, 5],
        },
        index=["a", "b", "c", "d", "e"],
    )
    default_rules = {
        "order": Order.MINIMUM,
        "highlighting": ["\\bfseries{%s}", "\\underline{%s}"],
        "default": "%s",
        "precision": "%.2f",
    }
    overrides = {
        "B": {
            "order": Order.MAXIMUM,
            "highlighting": ["\\textbf{%s}", "\\underline{%s}"],
            "default": "%s",
            "precision": "%.2f",
        }
    }
    expected = pd.DataFrame(
        {
            "A": ["\\bfseries{1.00}", "\\underline{2.00}", "3.00", "4.00", "5.00"],
            "B": ["1.00", "2.00", "3.00", "\\underline{4.00}", "\\textbf{5.00}"],
        },
        index=["a", "b", "c", "d", "e"],
    )
    assert table_highlighting(dataframe, Axis.COLUMN, default_rules, overrides).equals(
        expected
    )


def test_override_row() -> None:
    dataframe = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [2, 3, 4, 5, 6],
        },
        index=["a", "b", "c", "d", "e"],
    )
    default_rules = {
        "order": Order.MINIMUM,
        "highlighting": ["\\bfseries{%s}", "\\underline{%s}"],
        "default": "%s",
        "precision": "%.2f",
    }
    overrides = {
        "b": {
            "order": Order.MAXIMUM,
            "highlighting": ["\\textbf{%s}", "\\underline{%s}"],
            "default": "%s",
            "precision": "%.2f",
        }
    }
    expected = pd.DataFrame(
        {
            "A": [
                "\\bfseries{1.00}",
                "\\underline{2.00}",
                "\\bfseries{3.00}",
                "\\bfseries{4.00}",
                "\\bfseries{5.00}",
            ],
            "B": [
                "\\underline{2.00}",
                "\\textbf{3.00}",
                "\\underline{4.00}",
                "\\underline{5.00}",
                "\\underline{6.00}",
            ],
        },
        index=["a", "b", "c", "d", "e"],
    )
    assert table_highlighting(dataframe, Axis.ROW, default_rules, overrides).equals(
        expected
    )
