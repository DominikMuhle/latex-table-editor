from pathlib import Path
from typing import Any
from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.widgets import TextArea, DataTable, Footer, Static, Input
from textual.binding import Binding
from textual.events import Click
from textual.screen import Screen, ModalScreen
import pandas as pd
import json

from latex_table_editor.conversion import latex_table_to_dataframe
from latex_table_editor.table import Table
from latex_table_editor.utils import (
    AVAILABLE_RULES,
    RULES,
    Axis,
    Order,
    filter_rule_keys,
    is_instance_of,
)

WELCOME_TEXT = """Welcome to P2L!\n
P2L is a tool that allows you to convert LaTeX tables to Pandas DataFrames and vice versa.\n
It also provides a way to highlight the table data based on certain rules.\n
Press 'N' to start a new input.\n
"""


class WelcomeScreen(ModalScreen):
    """Welcome screen of the application."""

    BINDINGS = [
        Binding("N", "show_input", "New Input"),
    ]

    def compose(self) -> ComposeResult:
        self.app: LTEApp
        self.welcome_text = Static(WELCOME_TEXT, id="welcome")

        yield Container(self.welcome_text, id="main")

    async def action_show_input(self) -> None:
        """Show the input screen for table input."""
        self.dismiss()
        await self.app.action_show_input()


class LATeXOutputScreen(ModalScreen):
    """Screen for LaTeX output."""

    BINDINGS = [
        Binding("ctrl+r", "dismiss", "Return to DataTable"),
        Binding("ctrl+s", "save_to_file", "Save to File"),
    ]

    def compose(self) -> ComposeResult:
        self.app: LTEApp
        self.latex_output_area = TextArea(read_only=True, id="latex_output")
        self.status_bar = Static("Status: Ready", id="status")
        self.input = Input(placeholder="Enter the file name", id="input")
        self.footer = Footer(id="footer")

        yield Container(self.latex_output_area, self.input, id="main")
        yield self.status_bar
        yield self.footer

    async def on_mount(self) -> None:
        """Focus on the LaTeX output area when the screen is mounted."""
        self.latex_output_area.focus()

        self.app.table.highlight_table()

        self.latex_output_area.text = self.app.table.display_dataframe.to_latex()
        # focus on the input area
        self.input.focus()

    async def action_dismiss(self) -> None:
        """Dismiss the LaTeX output screen."""
        await self.dismiss()

    async def action_save_to_file(self) -> None:
        """Save the LaTeX output to a file."""
        # check if the input is empty
        if not self.input.value:
            self.status_bar.update("Please enter a file name.")
            return

        file_name = Path(self.input.value)
        # check if parent directory exists
        if not file_name.parent.exists():
            self.status_bar.update("Parent directory does not exist.")
            return

        with open(file_name, "w") as file:
            file.write(self.latex_output_area.text)
        self.status_bar.update(f"Saved LaTeX output to '{file_name}'.")


class DataTableScreen(Screen):
    """Screen displaying the DataTable."""

    def compose(self) -> ComposeResult:
        self.app: LTEApp
        self.data_table = DataTable(id="data_table")
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

        yield Container(self.data_table, id="main")
        yield self.status_bar
        yield self.footer

    def draw_table(self) -> None:
        self.app.table.highlight_table()

        self.data_table.clear(columns=True)

        column_keys = []
        for col in self.app.table.display_dataframe.columns:
            key = self.app.table.multi_index_to_str(col)
            name = self.app.table.multi_index_to_str(col)

            if self.app.table.mode == Axis.COLUMN:
                # get the ordering of the columns
                order = (
                    self.app.table.overrides[Axis.COLUMN]
                    .get(col, {})
                    .get("order", self.app.table.default_rules["order"])
                )
                match order:
                    case Order.MINIMUM:
                        name = f"{name} (v)"
                    case Order.NEUTRAL:
                        name = f"{name} (-)"
                    case Order.MAXIMUM:
                        name = f"{name} (^)"

            self.data_table.add_column(label=name, key=key)
            column_keys.append(key)

        row_keys = []
        for row in self.app.table.display_dataframe.index:
            row_data = self.app.table.display_dataframe.loc[row]
            key = self.app.table.multi_index_to_str(row)
            name = self.app.table.multi_index_to_str(row)
            if self.app.table.mode == Axis.ROW:
                order = (
                    self.app.table.overrides[Axis.ROW]
                    .get(name, {})
                    .get("order", self.app.table.default_rules["order"])
                )
                match order:
                    case Order.MINIMUM:
                        name = f"{name} (v)"
                    case Order.NEUTRAL:
                        name = f"{name} (-)"
                    case Order.MAXIMUM:
                        name = f"{name} (^)"

            self.data_table.add_row(
                *[str(value) for value in row_data], key=key, label=name
            )
            row_keys.append(key)

        match self.app.table.mode:
            case Axis.ROW:
                for col_key in self.app.table.skip[Axis.COLUMN]:
                    col_key = self.app.table.multi_index_to_str(col_key)
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
                for row_key in self.app.table.skip[Axis.ROW]:
                    row_key = self.app.table.multi_index_to_str(row_key)
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

    async def on_mount(self) -> None:
        """Initialize the DataTable with data."""
        self.data_table.cursor_type = "cell"


class InputScreen(ModalScreen):
    """Screen for table input."""

    BINDINGS = [
        Binding("ctrl+s", "submit", "Submit"),
    ]

    def __init__(self):
        super().__init__()
        self.app: LTEApp

    def compose(self) -> ComposeResult:
        self.info_text = Static("Enter the table data in LaTeX format.", id="info")
        self.input_area = TextArea(id="input")
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

        yield Grid(self.info_text, self.input_area, id="grid_input")
        yield self.status_bar
        yield self.footer

    async def on_mount(self) -> None:
        """Focus on the input area when the screen is mounted."""
        self.input_area.focus()

    async def action_submit(self) -> None:
        """Handle submission of input data."""
        await self.handle_submit()

    async def handle_submit(self) -> None:
        """Handle submission of input data."""
        # app = self.app
        self.dismiss(latex_table_to_dataframe(self.input_area.text))


class RulesInputScreen(ModalScreen):
    """Screen for default or column highlighting input."""

    BINDINGS = [
        Binding("ctrl+s", "submit", "Submit"),
    ]

    def __init__(
        self,
        rules: str,
        info_text: str = "Enter the highlighting rules in JSON format.",
    ):
        super().__init__()
        self.rules = rules
        self.info_text = info_text

    def compose(self) -> ComposeResult:
        self.app: LTEApp
        self.info_text = Static(str(self.info_text), id="info")
        self.highlight_input_area = TextArea(id="highlight_input")
        self.highlight_input_area.text = self.rules
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

        yield Grid(self.info_text, self.highlight_input_area, id="grid_input")
        yield self.status_bar
        yield self.footer

    async def on_mount(self) -> None:
        """Focus on the highlighting input area when the screen is mounted."""
        self.highlight_input_area.focus()

    async def action_submit(self) -> None:
        """Handle submission of highlighting rules."""
        await self.handle_submit_highlighting()

    async def handle_submit_highlighting(self) -> None:
        """Handle submission of highlighting rules."""
        try:
            new_rules = json.loads(self.highlight_input_area.text)
            new_rules = self.check_input_highlighting(new_rules)
            if "order" in new_rules:
                new_rules["order"] = Order(new_rules["order"])

            self.dismiss(new_rules)
        except json.JSONDecodeError:
            self.status_bar.update("Invalid JSON input. Please try again.")

    def check_input_highlighting(self, rules: dict[str, Any]) -> RULES:
        """Check the input highlighting rules for validity."""

        # Filter out the keys that are not available in the rules dictionary
        rules, pop_keys = filter_rule_keys(rules)
        if pop_keys:
            self.status_bar.update(f"Invalid keys {pop_keys}. They have been removed.")

        # Filter out the keys that don't have matching types
        pop_keys = []
        for key, value in rules.items():
            if key not in AVAILABLE_RULES:
                continue
            rule_type = AVAILABLE_RULES[key]

            if not is_instance_of(value, rule_type):
                self.status_bar.update(
                    f"Invalid value '{value}' for key '{key}'. Expected '{rule_type}' . It has been removed."
                )
                pop_keys.append(key)

        for key in pop_keys:
            rules.pop(key)

        return rules


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
        self.data_table_screen = DataTableScreen()
        self.push_screen(self.data_table_screen)
        self.push_screen(WelcomeScreen())

    async def reset_screen(self) -> None:
        """Reset the screen to the DataTable."""
        await self.switch_screen(self.data_table_screen)

    async def action_show_input(self) -> None:
        """Show the input screen for table input."""

        def update_table(table: pd.DataFrame | None) -> None:
            if table is not None:
                self.table.dataframe = table
                self.table.reset_formatting_rules()
                self.data_table_screen.draw_table()
                self.data_table_screen.status_bar.update("Table input successful.")
            else:
                self.data_table_screen.status_bar.update("Invalid table input.")

        self.push_screen(InputScreen(), update_table)
        self.data_table_screen.draw_table()

    async def action_show_latex_output(self) -> None:
        """Show the LaTeX output screen."""

        self.push_screen(LATeXOutputScreen())
        self.data_table_screen.draw_table()

    async def action_show_edit_default_rules(self) -> None:
        """Show the input screen for editing the default highlighting rules."""
        info_text = "Enter the default highlighting rules in JSON format."

        def update_highlighting(highlighting: dict[str, Any] | None) -> None:
            if highlighting is not None:
                self.table.default_rules = highlighting
                self.data_table_screen.draw_table()
                self.data_table_screen.status_bar.update(
                    "Default Highlighting rules updated."
                )
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.push_screen(
            RulesInputScreen(json.dumps(self.table.default_rules, indent=4), info_text),
            update_highlighting,
        )
        self.data_table_screen.draw_table()

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

        def update_highlighting(highlighting: dict[str, Any] | None) -> None:
            if highlighting is not None:
                self.table.overrides[Axis.COLUMN][column_name] = highlighting
                self.data_table_screen.draw_table()
                self.data_table_screen.status_bar.update(
                    f"Highlighting rules updated for '{column_name}'."
                )
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.current_highlighting_target = column_name
        column_rules = self.table.overrides[Axis.COLUMN].get(column_name, {})

        self.push_screen(
            RulesInputScreen(json.dumps(column_rules, indent=4), info_text),
            update_highlighting,
        )
        self.data_table_screen.draw_table()

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

        def update_highlighting(highlighting: dict[str, Any] | None) -> None:
            if highlighting is not None:
                self.table.overrides[Axis.ROW][row_name] = highlighting
                self.data_table_screen.draw_table()
                self.data_table_screen.status_bar.update(
                    f"Highlighting rules updated for '{row_name}'."
                )
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.current_highlighting_target = row_name
        row_rules = self.table.overrides[Axis.ROW].get(row_name, {})

        self.push_screen(
            RulesInputScreen(json.dumps(row_rules, indent=4), info_text),
            update_highlighting,
        )
        self.data_table_screen.draw_table()

    async def action_toggle_mode(self) -> None:
        """Toggle the row/column mode."""
        self.table.toggle_mode()

        self.data_table_screen.draw_table()

    async def action_toggle_cell(self) -> None:
        """Toggle skipping or including a row/column."""
        match self.table.mode:
            case Axis.COLUMN:
                self.toggle_row()
            case Axis.ROW:
                self.toggle_column()

        self.data_table_screen.draw_table()

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

        self.data_table_screen.draw_table()

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

        self.data_table_screen.draw_table()

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

        self.data_table_screen.draw_table()

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

        self.data_table_screen.draw_table()

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

        self.data_table_screen.draw_table()


if __name__ == "__main__":
    LTEApp().run()
