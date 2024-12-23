import json

import pandas as pd
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.widgets import DataTable

from latex_table_editor.conversion import (
    extract_numbers_from_dataframe,
    infer_headers_and_indices,
)
from latex_table_editor.screens import (
    DataTableScreen,
    InputScreen,
    LATeXOutputScreen,
    RawDataScreen,
    RulesScreen,
    WelcomeScreen,
)
from latex_table_editor.table import Table
from latex_table_editor.utils import Axis, Rule

HELP_TEXT = """
To enter a table into the app, follow these steps:
1. Prepare your table data in a CSV or Excel file.
2. Use the 'Import' button to load your file into the app.
3. The table will be displayed on the screen.
4. You can edit the table cells directly by clicking on them.
5. Use the toolbar options to format and customize your table.
6. Once done, you can export the table using the 'Export' button.
"""

class LTEApp(App):
    """Main application class."""

    CSS_PATH = "p2l_ui.tcss"

    BINDINGS = [
        Binding("h", "show_help", "help"),
        Binding("N", "show_input", "new table"),
        Binding("D", "show_header_index_selection", "raw data"),
        Binding("L", "show_latex_output", "LaTeX"),
        Binding("R", "show_edit_rules", "rules"),
        Binding("S", "start_selection_mode", "swap mode"),
        Binding("t", "toggle_mode", "toggle row/column"),
        Binding("o", "toggle_sorting_order", "sorting"),
        Binding("+", "increase_precision", "inc. precision"),
        Binding("-", "decrease_precision", "dec. precision"),
        Binding("x", "toggle_cell", "skip/include row/column"),
        Binding("s", "data_selection", "select row/column", show=False),
        Binding("click", "handle_click", "toggle order", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.table = Table()
        self.selection_mode = False
        self.selected_columns = []
        self.current_highlighting_target = None  # Tracks which column to highlight

    def compose(self) -> ComposeResult:
        yield from super().compose()
        # Register Screens
        self.data_table_screen = DataTableScreen(self.table)
        self.push_screen(self.data_table_screen)
        self.push_screen(WelcomeScreen(on_new_input=self.action_show_input))

    async def reset_screen(self) -> None:
        """Reset the screen to the DataTable."""
        await self.switch_screen(self.data_table_screen)

    async def show_help(self) -> None:
        """Show the help screen."""
        await self.push_screen(WelcomeScreen(on_new_input=self.action_show_input))

    async def action_show_input(self) -> None:
        """Show the input screen for table input."""

        def update_table(str_table: pd.DataFrame | None) -> None:
            if str_table is not None:
                # infer how many header rows and columns are from the raw data. This can be changed by the user manually later.
                self.table.str_dataframe = str_table
                
                numeric_df = extract_numbers_from_dataframe(str_table.copy())
                self.table.set_headers_and_indices(*infer_headers_and_indices(numeric_df))

                self.table.reset_formatting_rules()
                self.data_table_screen.draw_table()
                self.data_table_screen.status_bar.update("Table input successful.")
            else:
                self.data_table_screen.status_bar.update("Invalid table input.")

        self.push_screen(InputScreen(), update_table)
        self.data_table_screen.draw_table()

    async def action_show_latex_output(self) -> None:
        """Show the LaTeX output screen."""

        self.push_screen(LATeXOutputScreen(self.table))
        self.data_table_screen.update_table()

    async def action_show_header_index_selection(self) -> None:
        """Show the screen for adjusting header rows and index columns."""
        def update_table(_: None) -> None:
            self.table.update_from_str_dataframe()
            self.table.reset_formatting_rules()
            self.data_table_screen.draw_table()

        self.push_screen(RawDataScreen(self.table), update_table)

    async def action_show_edit_rules(self) -> None:
        """Show the rules screen with override rules based on the current mode."""
        match self.table.mode:
            case Axis.COLUMN:
                override_rules = self.table.overrides[Axis.COLUMN]
            case Axis.ROW:
                override_rules = self.table.overrides[Axis.ROW]

        def update_highlighting(default_rule: Rule, updated_override_rules: dict) -> None:
            if self.table.mode == Axis.COLUMN:
                self.table.overrides[Axis.COLUMN] = updated_override_rules
            else:
                self.table.overrides[Axis.ROW] = updated_override_rules
            self.table.default_rule = default_rule
            self.data_table_screen.update_table()
            self.data_table_screen.status_bar.update("Highlighting rules updated.")

        self.push_screen(
            RulesScreen(
                self.table.default_rule,
                override_rules,
                update_highlighting
            ),
        )
        self.data_table_screen.update_table()

    async def action_toggle_mode(self) -> None:
        """Toggle the row/column mode."""
        self.table.toggle_mode()

        self.data_table_screen.update_table()

    async def action_toggle_cell(self) -> None:
        """Toggle skipping or including a row/column."""
        match self.table.mode:
            case Axis.COLUMN:
                self.toggle_row()
            case Axis.ROW:
                self.toggle_column()

        self.data_table_screen.update_table()

    def toggle_column(self) -> None:
        try:
            column_name = self.table.dataframe.columns[
                self.data_table_screen.data_table.cursor_column
            ]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No column selected.")
            return

        self.table.toggle_skipping(Axis.COLUMN, column_name)

    def toggle_row(self) -> None:
        try:
            row_name = self.table.dataframe.index[
                self.data_table_screen.data_table.cursor_row
            ]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No row selected.")
            return

        self.table.toggle_skipping(Axis.ROW, row_name)

    async def action_increase_precision(self) -> None:
        """Increase the precision of a column or row."""
        self.data_table_screen.status_bar.update("Increasing precision.")
        match self.table.mode:
            case Axis.COLUMN:
                try:
                    column_name = self.table.dataframe.columns[
                        self.data_table_screen.data_table.cursor_column
                    ]
                except (IndexError, AttributeError):
                    self.data_table_screen.status_bar.update("No column selected.")
                    return
                self.data_table_screen.status_bar.update("Increasing precision 2.")
                self.table.increase_precision(Axis.COLUMN, column_name)
            case Axis.ROW:
                try:
                    row_name = self.table.dataframe.index[
                        self.data_table_screen.data_table.cursor_row
                    ]
                except (IndexError, AttributeError):
                    self.data_table_screen.status_bar.update("No row selected.")
                    return
                self.data_table_screen.status_bar.update("Increasing precision 2.")
                self.table.increase_precision(Axis.ROW, row_name)

        self.data_table_screen.update_table()

    async def action_decrease_precision(self) -> None:
        """Decrease the precision of a column or row."""
        match self.table.mode:
            case Axis.COLUMN:
                try:
                    column_name = self.table.dataframe.columns[
                        self.data_table_screen.data_table.cursor_column
                    ]
                except (IndexError, AttributeError):
                    self.data_table_screen.status_bar.update("No column selected.")
                    return
                self.table.decrease_precision(Axis.COLUMN, column_name)
            case Axis.ROW:
                try:
                    row_name = self.table.dataframe.index[
                        self.data_table_screen.data_table.cursor_row
                    ]
                except (IndexError, AttributeError):
                    self.data_table_screen.status_bar.update("No row selected.")
                    return
                self.table.decrease_precision(Axis.ROW, row_name)

        self.data_table_screen.update_table()

    async def on_click(self, message: Click) -> None:
        """Handle click events on the DataTable columns."""
        if message.button != 1:
            return  # Only handle left-clicks

        element = message.widget

        # Check if the clicked element is a column header
        if isinstance(element, DataTable):
            match self.table.mode:
                case Axis.ROW:
                    # Check if the clicked element is a row header
                    if element.hover_column != -1 or element.hover_row == -1:
                        return
                    row_name = self.table.dataframe.index[element.hover_row]
                    self.table.toggle_order(self.table.mode, row_name)
                case Axis.COLUMN:
                    # Check if the clicked element is a column header
                    if element.hover_row != -1 or element.hover_column == -1:
                        return
                    column_name = self.table.dataframe.columns[element.hover_column]
                    self.table.toggle_order(self.table.mode, column_name)

            self.data_table_screen.update_table()

    async def action_toggle_sorting_order(self) -> None:
        """Toggle the sorting order of a column or row."""
        match self.table.mode:
            case Axis.COLUMN:
                try:
                    column_name = self.table.dataframe.columns[
                        self.data_table_screen.data_table.cursor_column
                    ]
                except (IndexError, AttributeError):
                    self.data_table_screen.status_bar.update("No column selected.")
                    return
                self.table.toggle_order(self.table.mode, column_name)
            case Axis.ROW:
                try:
                    row_name = self.table.dataframe.index[
                        self.data_table_screen.data_table.cursor_row
                    ]
                except (IndexError, AttributeError):
                    self.data_table_screen.status_bar.update("No row selected.")
                    return
                self.table.toggle_order(self.table.mode, row_name)

        self.data_table_screen.update_table()

    async def action_start_selection_mode(self) -> None:
        if self.table.dataframe.empty:
            match self.table.mode:
                case Axis.ROW:
                    self.data_table_screen.status_bar.update(
                        "No data available to select rows."
                    )
                case Axis.COLUMN:
                    self.data_table_screen.status_bar.update(
                        "No data available to select columns."
                    )
            return
        self.selection_mode = True
        self.selected_data = []
        match self.table.mode:
            case Axis.ROW:
                self.data_table_screen.status_bar.update(
                    "Selection Mode: Select two rows by pressing 's' on each."
                )
            case Axis.COLUMN:
                self.data_table_screen.status_bar.update(
                    "Selection Mode: Select two columns by pressing 's' on each."
                )

    async def disable_selection_mode(self) -> None:
        self.selection_mode = False
        self.selected_data = []
        self.data_table_screen.status_bar.update("Exiting Selection Mode.")

    async def action_data_selection(self) -> None:
        if not self.selection_mode:
            return

        match self.table.mode:
            case Axis.COLUMN:
                items = self.table.dataframe.columns
                cursor_position = self.data_table_screen.data_table.cursor_column
                swap_method = self.table.swap_columns
            case Axis.ROW:
                items = self.table.dataframe.index
                cursor_position = self.data_table_screen.data_table.cursor_row
                swap_method = self.table.swap_rows

        try:
            item_name = items[cursor_position]
        except IndexError:
            self.data_table_screen.status_bar.update(
                f"Invalid {self.table.mode} selection."
            )
            return

        if item_name in self.selected_data:
            self.data_table_screen.status_bar.update(
                f"{self.table.mode} '{item_name}' is already selected."
            )
            return

        self.selected_data.append(item_name)
        remaining = 2 - len(self.selected_data)
        if remaining > 0:
            self.data_table_screen.status_bar.update(
                f"Selected '{item_name}'. Select {remaining} more {self.table.mode}(s)."
            )
        else:
            worked = swap_method(*self.selected_data)
            if worked:
                self.data_table_screen.status_bar.update(
                    f"Swapped {self.table.mode}s '{self.selected_data[0]}' and '{self.selected_data[1]}'. Exiting Selection Mode."
                )
            else:
                self.data_table_screen.status_bar.update(
                    f"Failed to swap {self.table.mode}s '{self.selected_data[0]}' and '{self.selected_data[1]}'. Exiting Selection Mode."
                )
            await self.disable_selection_mode()

        self.data_table_screen.update_table()

    async def on_input_submitted(self, value: str) -> None:
        # Placeholder for handling input submission if necessary
        pass


if __name__ == "__main__":
    LTEApp().run()
