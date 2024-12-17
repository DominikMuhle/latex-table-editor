import re
from copy import deepcopy

import pandas as pd

from latex_table_editor.conversion import extract_numbers_from_dataframe
from latex_table_editor.highlighting import table_highlighting
from latex_table_editor.utils import DEFAULT_RULES, Axis, Order, Rule


class Table:
    def __init__(self):
        # data
        self.str_dataframe = pd.DataFrame()
        self.dataframe = pd.DataFrame()
        self.display_dataframe = pd.DataFrame()
        self.num_header_rows = 0
        self.num_index_columns = 0

        # configuration
        self.mode = Axis.COLUMN
        self.default_rule = deepcopy(DEFAULT_RULES)
        self.overrides = {
            Axis.COLUMN: {col: Rule(**{}) for col in self.dataframe.columns},
            Axis.ROW: {row: Rule(**{}) for row in self.dataframe.index},
        }
        self.reset_formatting_rules()
        self.skip = {
            Axis.COLUMN: [],
            Axis.ROW: [],
        }

    def reset_formatting_rules(self):
        """Reset the formatting rules to the default values"""
        self.default_rule = deepcopy(DEFAULT_RULES)
        self.overrides[Axis.COLUMN] = {
            col: Rule(**{}) for col in self.dataframe.columns
        }
        self.overrides[Axis.ROW] = {
            row: Rule(**{}) for row in self.dataframe.index
        }

    def highlight_table(self) -> None:
        """Highlight the table based on the current configuration."""

        self.display_dataframe = deepcopy(self.dataframe)
        self.display_dataframe = table_highlighting(
            self.display_dataframe,
            self.mode,
            self.default_rule,
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

        current_order = self.overrides[axis][name].order or self.default_rule.order
        self.overrides[axis][name].order = swap(current_order)

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

        current_precision = self.overrides[axis][name].precision or self.default_rule.precision
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

        current_precision = self.overrides[axis][name].precision or self.default_rule.precision
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

    def set_headers_and_indices(self, num_header_rows: int, num_index_columns: int) -> None:
        """Set the number of header rows and index columns."""

        self.num_header_rows = num_header_rows
        self.num_index_columns = num_index_columns

        self.update_from_str_dataframe()

    def update_from_str_dataframe(self) -> None:
        """Create the dataframe from _dataframe given the number of header rows and index columns."""
        # Start with a copy of _dataframe
        df = self.str_dataframe.copy()

        # Set up header rows
        if self.num_header_rows > 0:
            # Extract header rows
            header_rows = [df.iloc[i] for i in range(self.num_header_rows)]
            # Remove header rows from data
            df = df.iloc[self.num_header_rows:].reset_index(drop=True)
            # Create MultiIndex for columns
            df.columns = pd.MultiIndex.from_arrays([row.values for row in header_rows])
        else:
            df.columns = df.columns  # Keep existing columns

        # Set up index columns
        if self.num_index_columns > 0:
            # Extract index columns
            index_columns = [df.iloc[:, i] for i in range(self.num_index_columns)]
            # Remove index columns from data
            df = df.iloc[:, self.num_index_columns:]
            # Create MultiIndex for index
            df.index = pd.MultiIndex.from_arrays(index_columns)
        else:
            df.index = df.index  # Keep existing index

        # Assign to dataframe
        self.dataframe = extract_numbers_from_dataframe(df)
