from copy import deepcopy
import re
import pandas as pd

from latex_table_editor.highlighting import DEFAULT_RULES, table_highlighting
from latex_table_editor.utils import Axis, Order


class Table:
    def __init__(self):
        # data
        self.dataframe = pd.DataFrame()
        self.display_dataframe = pd.DataFrame()

        # configuration
        self.mode = Axis.COLUMN
        self.default_rules = deepcopy(DEFAULT_RULES)
        self.overrides = {
            Axis.COLUMN: {},
            Axis.ROW: {},
        }
        self.reset_formatting_rules()
        self.skip = {
            Axis.COLUMN: [],
            Axis.ROW: [],
        }

    def reset_formatting_rules(self):
        """Reset the formatting rules to the default values"""
        self.default_rules = deepcopy(DEFAULT_RULES)
        self.overrides[Axis.COLUMN] = {col: {} for col in self.dataframe.columns}
        self.overrides[Axis.ROW] = {row: {} for row in self.dataframe.index}

    def highlight_table(self) -> None:
        """Highlight the table based on the current configuration."""

        self.display_dataframe = deepcopy(self.dataframe)
        self.display_dataframe = table_highlighting(
            self.display_dataframe,
            self.mode,
            self.default_rules,
            self.overrides[self.mode],
            self.skip[Axis.COLUMN] if self.mode == Axis.ROW else self.skip[Axis.ROW],
        )

    def col_index_to_str(self, multi_index: tuple[str | int] | str | int) -> str:
        """Convert a multi-index to a string."""
        if isinstance(multi_index, tuple):
            # Convert each element to a string
            multi_index_ = [str(elem) for elem in multi_index]
            return "\n".join(multi_index_)
        if isinstance(multi_index, str):
            return multi_index
        if isinstance(multi_index, int):
            return str(multi_index)
        raise ValueError("multi_index must be a tuple or a string.")

    def row_index_to_str(self, multi_index: tuple[str | int] | str | int) -> str:
        """Convert a multi-index to a string."""
        if isinstance(multi_index, tuple):
            # Convert each element to a string
            multi_index_ = [str(elem) for elem in multi_index]
            return " ".join(multi_index_)
        if isinstance(multi_index, str):
            return multi_index
        if isinstance(multi_index, int):
            return str(multi_index)
        raise ValueError("multi_index must be a tuple or a string.")

    def toggle_mode(self) -> None:
        """Toggle between column and row mode."""
        self.mode = Axis.ROW if self.mode == Axis.COLUMN else Axis.COLUMN

    def toggle_order(self, axis: Axis, name: str) -> bool:
        """Toggle the order of a column or row."""

        def swap(order: Order) -> Order:
            match order:
                case Order.NEUTRAL:
                    return Order.MAXIMUM
                case Order.MAXIMUM:
                    return Order.MINIMUM
                case Order.MINIMUM:
                    return Order.NEUTRAL

        # Check if the column or row exists in the DataFrame
        if axis == Axis.COLUMN and name not in self.dataframe.columns:
            return False
        if axis == Axis.ROW and name not in self.dataframe.index:
            return False

        current_order = self.overrides[axis][name].get(
            "order", self.default_rules["order"]
        )
        self.overrides[axis][name]["order"] = swap(current_order)

        return True

    def toggle_skipping(self, axis: Axis, name: str) -> bool:
        """Toggle skipping a column or row."""

        # Check if the column or row exists in the DataFrame
        if axis == Axis.COLUMN and name not in self.dataframe.columns:
            return False
        if axis == Axis.ROW and name not in self.dataframe.index:
            return False

        if name in self.skip[axis]:
            self.skip[axis].remove(name)
        else:
            self.skip[axis].append(name)

        return True

    def increase_precision(self, axis: Axis, name: str) -> bool:
        """Increase the precision of a column or row."""
        if axis == Axis.COLUMN and name not in self.dataframe.columns:
            return False
        if axis == Axis.ROW and name not in self.dataframe.index:
            return False

        current_precision = self.overrides[axis][name].get(
            "precision", self.default_rules["precision"]
        )  # string of form "%.Xf"
        matching = re.match(r"%.(\d+)f", current_precision)
        if not matching:
            return False
        significant_digits = int(matching.group(1))

        self.overrides[axis][name]["precision"] = f"%.{significant_digits + 1}f"
        return True

    def decrease_precision(self, axis: Axis, name: str) -> bool:
        """Decrease the precision of a column or row."""
        if axis == Axis.COLUMN and name not in self.dataframe.columns:
            return False
        if axis == Axis.ROW and name not in self.dataframe.index:
            return False

        current_precision = self.overrides[axis][name].get(
            "precision", self.default_rules["precision"]
        )
        matching = re.match(r"%.(\d+)f", current_precision)
        if not matching:
            return False
        significant_digits = int(matching.group(1))
        if significant_digits == 0:
            return False

        self.overrides[axis][name]["precision"] = f"%.{significant_digits - 1}f"
        return True

    def swap_columns(self, col1: tuple[str] | str, col2: tuple[str] | str) -> bool:
        """Swap two columns in the DataFrame."""
        if col1 not in self.dataframe.columns or col2 not in self.dataframe.columns:
            return False

        self.dataframe[[col1, col2]] = self.dataframe[[col2, col1]]

        # Swap columns in the DataFrame
        cols = list(self.dataframe.columns)
        idx1, idx2 = cols.index(col1), cols.index(col2)
        cols[idx1], cols[idx2] = cols[idx2], cols[idx1]
        self.dataframe = self.dataframe[cols]

        return True

    def swap_rows(self, row1: tuple[str] | str, row2: tuple[str] | str) -> bool:
        """Swap two rows in the DataFrame."""
        if row1 not in self.dataframe.index or row2 not in self.dataframe.index:
            return False

        # Swap rows in the DataFrame
        rows = list(self.dataframe.index)
        idx1, idx2 = rows.index(row1), rows.index(row2)
        rows[idx1], rows[idx2] = rows[idx2], rows[idx1]

        self.dataframe = self.dataframe.reindex(rows)

        return True
