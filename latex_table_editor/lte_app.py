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
    HeaderIndexSelectionScreen,
    InputScreen,
    LATeXOutputScreen,
    RulesInputScreen,
    WelcomeScreen,
)
from latex_table_editor.table import Table
from latex_table_editor.utils import Axis, Rule


class LTEApp(App):
    """Main application class."""

    CSS_PATH = "p2l_ui.tcss"

    BINDINGS = [
        Binding("N", "show_input", "new input"),
        Binding("L", "show_latex_output", "show LaTeX"),
        Binding("T", "toggle_mode", "toggle row/column mode"),
        Binding("d", "show_edit_default_rules", "edit default rules"),
        Binding("e", "show_edit_rules", "edit rules"),
        Binding("o", "toggle_sorting_order", "toggle sorting order"),
        Binding("+", "increase_precision", "increase precision"),
        Binding("-", "decrease_precision", "decrease precision"),
        Binding("x", "toggle_cell", "skip/include row/column"),
        Binding("S", "start_selection_mode", "start swap mode"),
        Binding("s", "data_selection", "select row/column", show=False),
        Binding("click", "handle_click", "toggle order", show=False),
        Binding("t", "show_header_index_selection", "Adjust Headers/Indices"),
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
            self.table.reset_formatting_rules()
            self.data_table_screen.draw_table()

        self.push_screen(HeaderIndexSelectionScreen(self.table), update_table)

    async def action_show_edit_default_rules(self) -> None:
        """Show the input screen for editing the default highlighting rules."""
        info_text = "Enter the default highlighting rules in JSON format."

        def update_highlighting(new_rule: Rule | None) -> None:
            if new_rule is not None:
                self.table.default_rule = new_rule
                self.table.reset_formatting_rules()
            else:
                self.data_table_screen.status_bar.update(
                    "No changes were made to the default rules."
                )

        current_rules_json = json.dumps(self.table.default_rule.__dict__, indent=4)
        self.push_screen(
            RulesInputScreen(current_rules_json, info_text, update_highlighting),
        )
        self.data_table_screen.update_table()

    async def action_show_edit_rules(self) -> None:
        """Show the input screen for column/row-specific highlighting rules."""
        match self.table.mode:
            case Axis.COLUMN:
                await self.show_column_rules()
            case Axis.ROW:
                await self.show_row_rules()

    async def show_column_rules(self) -> None:
        """Show the input screen for column-specific highlighting rules."""
        # Get the name of the current cursor column from DataTableScreen
        try:
            column_name = self.table.dataframe.columns[
                self.data_table_screen.data_table.cursor_column
            ]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No column selected.")
            return

        info_text = (
            f"Enter the highlighting rules for column '{column_name}' in JSON format."
        )

        def update_highlighting(new_rule: Rule | None) -> None:
            if new_rule is not None:
                self.table.overrides[Axis.COLUMN][column_name] = new_rule
                self.data_table_screen.update_table()
                self.data_table_screen.status_bar.update(
                    f"Highlighting rules updated for '{column_name}'."
                )
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.current_highlighting_target = column_name
        column_rules = self.table.overrides[Axis.COLUMN].get(column_name, Rule(**{}))

        self.push_screen(
            RulesInputScreen(json.dumps(column_rules.__dict__, indent=4), info_text, update_highlighting),
        )
        self.data_table_screen.update_table()

    async def show_row_rules(self) -> None:
        """Show the input screen for row-specific highlighting rules."""
        # Get the name of the current cursor row from DataTableScreen
        try:
            row_name = self.table.dataframe.index[
                self.data_table_screen.data_table.cursor_row
            ]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No row selected.")
            return

        info_text = f"Enter the highlighting rules for row '{row_name}' in JSON format."

        def update_highlighting(new_rule: Rule | None) -> None:
            if new_rule is not None:
                self.table.overrides[Axis.ROW][row_name] = new_rule
                self.data_table_screen.update_table()
                self.data_table_screen.status_bar.update(
                    f"Highlighting rules updated for '{row_name}'."
                )
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.current_highlighting_target = row_name
        row_rules = self.table.overrides[Axis.ROW].get(row_name, Rule(**{}))

        self.push_screen(
            RulesInputScreen(json.dumps(row_rules.__dict__, indent=4), info_text, update_highlighting),
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



if __name__ == "__main__":
    LTEApp().run()
