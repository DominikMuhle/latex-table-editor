from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Static


class RawDataScreen(ModalScreen):
    """Screen to adjust header rows and index columns."""

    BINDINGS = [
        Binding("k", "increase_num_header_rows", "Increase Header Rows"),
        Binding("i", "decrease_num_header_rows", "Decrease Header Rows"),
        Binding("l", "increase_num_index_columns", "Increase Index Columns"),
        Binding("j", "decrease_num_index_columns", "Decrease Index Columns"),
        Binding("escape", "exit", "Exit"),
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
            self.data_table.add_column(str(col), key=str(col))

        # Add rows
        for index, row in df.iterrows():
            self.data_table.add_row(*[str(value) for value in row], key=str(index))

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

                self.data_table.update_cell(
                    row_key=str(index), column_key=str(col), value=value
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

