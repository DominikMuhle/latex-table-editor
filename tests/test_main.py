import copy
from typing import Any
import pandas as pd
import pytest

from main import table_highlighting, Order, Axis

base_dataframe = pd.DataFrame(
    {
        "A": [1, 2, 3, 4, 5],
        "B": [5, 4, 3, 2, 1],
        "C": [1, 3, 5, 7, 9],
    }
)

@pytest.mark.parametrize(
    "table, kwargs, location, expected",
    [
        # Test case 1
        (copy.deepcopy(base_dataframe), {
            "order": Order.MINIMUM,
            "axis": Axis.COLUMN,
        },
        (0, 0),
        "\\bfseries{1.000}"
        ),
        # Test case 2
        (copy.deepcopy(base_dataframe), {
            "order": Order.MINIMUM,
            "axis": Axis.COLUMN,
        },
        (1, 0),
        "\\underline{2.000}"
        ),
        # Test case 3
        (copy.deepcopy(base_dataframe), {
            "order": Order.MAXIMUM,
            "axis": Axis.COLUMN,
        },
        (4, 0),
        "\\bfseries{5.000}"
        )
    ]
)
def test_table_highlighting(table: pd.DataFrame, expected: int, location: tuple[int, int], kwargs: dict[str, Any]) -> None:
    assert table_highlighting(table, **kwargs).iloc[location[0], location[1]] == expected
