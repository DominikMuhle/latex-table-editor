import copy
import pandas as pd

from highlighting import table_highlighting, table_highlighting_by_name
from interactive import interacitve_highlighting
from utils import Axis, Order

BASE_TABLE = pd.DataFrame(
    {
        "Metric1": [1, '-', 3, 4, 5],
        "Metric2": [5, 4, 3, 2, 1],
        "Metric3": [1, 3, 5, 7, 9],
    },
    index=[f"Method {i}" for i in range(1, 6)]
)
HIGHLIGHTING_RULES = [
    {
        "name": "Metric1",
        "order": Order.MINIMUM,
        "highlighting": ["\\bfseries{%.3f}", "\\underline{%.3f}"],
        "default": "%.3f",
    },
    {
        "name": "Metric2",
        "order": Order.MAXIMUM,
        "highlighting": ["\{\color{red}{%.3f}}", "\{\color{green}{%.3f}}"],
        "default": "%.3f",
    },
    {
        "name": "Metric3",
        "order": Order.MAXIMUM,
        "highlighting": ["\\bfseries{%.2f}", "\\underline{%.2f}"],
        "default": "%.2f",
    },
]

def main() -> None:
    print(interacitve_highlighting().to_latex())

    # print(table_highlighting(copy.deepcopy(BASE_TABLE), order=Order.MINIMUM, axis=Axis.COLUMN, ignore_idx=[1]).to_latex())
    # print(table_highlighting_by_name(copy.deepcopy(BASE_TABLE), axis=Axis.COLUMN, metrics=HIGHLIGHTING_RULES).to_latex())


if __name__ == "__main__":
    main()
