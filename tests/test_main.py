import pandas as pd
import pytest

from main import table_highlighting


@pytest.mark.parametrize(
    "table, expected",
    [
        (pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [5, 4, 3, 2, 1],
            "C": [1, 3, 5, 7, 9],
        }), 
        "\\bfseries{1.000}"
        ),
    ]
)
def test_levenshtein_distance(table: pd.DataFrame, expected: int) -> None:
    assert table_highlighting(table).iloc[0, 0] == expected
