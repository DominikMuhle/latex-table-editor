from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static

from latex_table_editor.utils import Axis, Order, Rule


class DataTableScreen(Screen):
    """Screen displaying the DataTable."""

    def __init__(self, table):
        super().__init__()
        self.table = table
        self.data_table = DataTable(id="data_table")
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

    def compose(self) -> ComposeResult:
        yield Container(self.data_table, id="main")
        yield self.status_bar
        yield self.footer

    def draw_table(self) -> None:
        self.table.highlight_table()

        self.data_table.clear(columns=True)
        # set the header height to the number of header rows in the dataframe
        self.data_table.header_height = self.table.dataframe.columns.nlevels

        column_keys = []
        for col in self.table.display_dataframe.columns:
            key = self.table.col_index_to_str(col)
            name = self.table.col_index_to_str(col)

            self.data_table.add_column(label=name, key=key)
            column_keys.append(key)

        row_keys = []
        for row in self.table.display_dataframe.index:
            row_data = self.table.display_dataframe.loc[row]
            key = self.table.row_index_to_str(row)
            name = self.table.row_index_to_str(row)

            self.data_table.add_row(
                *[str(value) for value in row_data], key=key, label=name
            )
            row_keys.append(key)

        self.update_table()
        self.refresh()

    def update_table(self) -> None:
        """Update the DataTable without recreating it."""
        self.table.highlight_table()

        column_keys = [
            self.table.col_index_to_str(col)
            for col in self.table.display_dataframe.columns
        ]
        row_keys = [
            self.table.row_index_to_str(row)
            for row in self.table.display_dataframe.index
        ]

        # # Update the table column names
        for col in self.table.display_dataframe.columns:
            label = self.table.col_index_to_str(col)
            dt_column = self.data_table.columns[label]
            if self.table.mode == Axis.COLUMN:
                order = (
                    self.table.overrides[Axis.COLUMN]
                    .get(col, Rule(**{})).order
                )
                if order is None:
                    order = self.table.default_rule.order
                match order:
                    case Order.MINIMUM:
                        label = f"{label} (v)"
                    case Order.NEUTRAL:
                        label = f"{label} (-)"
                    case Order.MAXIMUM:
                        label = f"{label} (^)"

            dt_column.label = (
                Text.from_markup(label) if isinstance(label, str) else label
            )

        # Update the table row names
        for row in self.table.display_dataframe.index:
            label = self.table.row_index_to_str(row)
            dt_row = self.data_table.rows[label]
            if self.table.mode == Axis.ROW:
                order = (
                    self.table.overrides[Axis.ROW]
                    .get(row, Rule(**{})).order
                )
                if order is None:
                    order = self.table.default_rule.order
                match order:
                    case Order.MINIMUM:
                        label = f"(v) {label}"
                    case Order.NEUTRAL:
                        label = f"{label} (-)"
                    case Order.MAXIMUM:
                        label = f"{label} (^)"

            dt_row.label = Text.from_markup(label) if isinstance(label, str) else label

        for row in self.table.display_dataframe.index:
            row_key = self.table.row_index_to_str(row)
            for col in self.table.display_dataframe.columns:
                col_key = self.table.col_index_to_str(col)
                cell_content = self.table.display_dataframe[col][row]
                self.data_table.update_cell(
                    row_key=row_key,
                    column_key=col_key,
                    value=cell_content,
                    update_width=True,
                )

        # Apply any necessary styles or highlights
        match self.table.mode:
            case Axis.ROW:
                for col_key in self.table.skip[Axis.COLUMN]:
                    col_key = self.table.col_index_to_str(col_key)
                    for row_key in row_keys:
                        cell_content = self.data_table.get_cell(
                            row_key=row_key, column_key=col_key
                        )
                        self.data_table.update_cell(
                            row_key=row_key,
                            column_key=col_key,
                            value=f"[grey54]{cell_content}[/grey54]",
                            update_width=True,
                        )
            case Axis.COLUMN:
                for row_key in self.table.skip[Axis.ROW]:
                    row_key = self.table.row_index_to_str(row_key)
                    for col_key in column_keys:
                        cell_content = self.data_table.get_cell(
                            row_key=row_key, column_key=col_key
                        )
                        self.data_table.update_cell(
                            row_key=row_key,
                            column_key=col_key,
                            value=f"[grey54]{cell_content}[/grey54]",
                            update_width=True,
                        )

        self.refresh()
        # self.data_table._update_column_widths()
        self.data_table.show_row_labels = False
        self.refresh()
        self.data_table.show_row_labels = True
        self.refresh()

    async def on_mount(self) -> None:
        """Initialize the DataTable with data."""
        self.data_table.cursor_type = "cell"

