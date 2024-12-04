import pandas as pd
from table import Table
from utils import Axis, Order


def test_toggle_order_base_to_neutral():
    dataframe = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
        },
        index=["a", "b", "c", "d", "e"],
    )

    table = Table()
    table.mode = Axis.COLUMN
    table.dataframe = dataframe
    table.reset_formatting_rules()

    table.toggle_order(table.mode, "A")
    assert table.overrides[table.mode]["A"]["order"] == Order.MAXIMUM


def test_toggle_order_min_to_neutral():
    dataframe = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
        },
        index=["a", "b", "c", "d", "e"],
    )

    table = Table()
    table.mode = Axis.COLUMN
    table.dataframe = dataframe
    table.reset_formatting_rules()
    table.overrides[table.mode] = {"A": {"order": Order.MINIMUM}}

    table.toggle_order(table.mode, "A")
    assert table.overrides[table.mode]["A"]["order"] == Order.NEUTRAL


def test_toggle_order_neutral_to_max():
    dataframe = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
        },
        index=["a", "b", "c", "d", "e"],
    )

    table = Table()
    table.mode = Axis.COLUMN
    table.dataframe = dataframe
    table.reset_formatting_rules()
    table.overrides[table.mode] = {"A": {"order": Order.NEUTRAL}}

    table.toggle_order(table.mode, "A")
    assert table.overrides[table.mode]["A"]["order"] == Order.MAXIMUM


def test_toggle_order_max_to_min():
    dataframe = pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
        },
        index=["a", "b", "c", "d", "e"],
    )

    table = Table()
    table.mode = Axis.COLUMN
    table.dataframe = dataframe
    table.reset_formatting_rules()
    table.overrides[table.mode] = {"A": {"order": Order.MAXIMUM}}

    table.toggle_order(table.mode, "A")
    assert table.overrides[table.mode]["A"]["order"] == Order.MINIMUM
