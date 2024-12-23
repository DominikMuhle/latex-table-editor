from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, Static

from latex_table_editor.screens import HelpScreen


class InputModal(ModalScreen):
    """Modal input screen for editing cell values."""

    def __init__(self, row_key, column_key, value):
        super().__init__()
        self.row_key = row_key
        self.column_key = column_key
        self.input_field = Input(placeholder="Enter new value...")
        self.input_field.value = value
        self.submit_button = Button("Submit", id="submit_button")

    def compose(self) -> ComposeResult:
        yield self.input_field
        yield self.submit_button


HELP_TEXT = """
This screen directly displays the raw data in the table. You can navigate the table using the arrow keys. If you want to change a value of a cell, select the cell and press 'Enter' to edit the value.

This screen also allows you to adjust the number of header rows and index columns. Use the following keybindings to adjust the table:
- 'k': Increase the number of header rows.
- 'i': Decrease the number of header rows.
- 'l': Increase the number of index columns.
- 'j': Decrease the number of index columns.
"""

class RawDataScreen(ModalScreen):
    """Screen to adjust header rows and index columns."""

    BINDINGS = [
        Binding("k", "increase_num_header_rows", "Increase Header Rows"),
        Binding("i", "decrease_num_header_rows", "Decrease Header Rows"),
        Binding("l", "increase_num_index_columns", "Increase Index Columns"),
        Binding("j", "decrease_num_index_columns", "Decrease Index Columns"),
        Binding("h", "show_help", "Show Help"),
        Binding("q", "exit", "Exit"),
    ]

    def __init__(self, table):
        super().__init__()
        self.table = table
        self.data_table = DataTable(id="str_data_table")
        self.status_bar = Static("Use arrow keys to adjust headers and indices.", id="status")
        self.footer = Footer(id="footer")

    def compose(self) -> ComposeResult:
        yield Container(self.data_table, id="main")
        yield self.status_bar
        yield self.footer

    async def on_mount(self) -> None:
        """Initialize the DataTable with str_dataframe."""
        self.draw_table()

    def draw_table(self) -> None:
        """Draw the DataTable with str_dataframe."""
        self.data_table.clear(columns=True)
        df = self.table.str_dataframe

        # Add columns
        for col in df.columns:
            self.data_table.add_column(str(col), key=col)

        # Add rows
        for index, row in df.iterrows():
            self.data_table.add_row(*[str(value) for value in row], key=index)

        self.update_table()

    def update_table(self) -> None:
        """Update the DataTable to display str_dataframe with highlights."""
        df = self.table.str_dataframe

        for index, row in df.iterrows():
            for col, value in row.items():
                value = str(value)
                if index < self.table.num_header_rows:
                    value = f"[red]{value}[/red]"
                if col in df.columns[: self.table.num_index_columns]:
                    value = f"[red]{value}[/red]"

                self.data_table.update_cell_at(
                    (index, col), value=value
                )

    async def action_increase_num_header_rows(self) -> None:
        """Increase the number of header rows."""
        self.table.num_header_rows += 1
        self.table.update_from_str_dataframe()
        self.update_table()

    async def action_decrease_num_header_rows(self) -> None:
        """Decrease the number of header rows."""
        if self.table.num_header_rows > 0:
            self.table.num_header_rows -= 1
            self.table.update_from_str_dataframe()
            self.update_table()

    async def action_increase_num_index_columns(self) -> None:
        """Increase the number of index columns."""
        self.table.num_index_columns += 1
        self.table.update_from_str_dataframe()
        self.update_table()

    async def action_decrease_num_index_columns(self) -> None:
        """Decrease the number of index columns."""
        if self.table.num_index_columns > 0:
            self.table.num_index_columns -= 1
            self.table.update_from_str_dataframe()
            self.update_table()

    async def action_exit(self) -> None:
        """Exit the screen."""
        self.dismiss()

    async def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection to allow editing."""
        row_key = event.coordinate.row
        column_key = event.coordinate.column

        # Do not allow editing of header rows and index columns
        if row_key < self.table.num_header_rows or column_key < self.table.num_index_columns:
            return

        df = self.table.str_dataframe
        idx = df.index[row_key]
        col = df.columns[column_key]
        value = df.at[idx, col]
        self.input_modal = InputModal(row_key, column_key, str(value))
        await self.app.push_screen(self.input_modal, self.update_cell_value)

    def update_cell_value(self, value: str) -> None:
        """Update the cell value in the data table and dataframe."""
        row_key = self.input_modal.row_key
        column_key = self.input_modal.column_key

        df = self.table.str_dataframe
        idx = df.index[row_key]
        col = df.columns[column_key]
        df.at[idx, col] = value
        self.table.update_from_str_dataframe()

        # Update the data table
        self.data_table.update_cell_at((row_key, col), value=str(value))

        # Redraw the table to reflect any changes
        self.update_table()

    
    async def action_show_help(self) -> None:
        """Show the help screen."""
        await self.push_screen(HelpScreen(HELP_TEXT))