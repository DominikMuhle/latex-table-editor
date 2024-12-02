# Python

from copy import deepcopy
from pathlib import Path
from typing import Any
from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.widgets import TextArea, DataTable, Footer, Static, Input
from textual.binding import Binding
from textual.events import Click
from textual.screen import Screen, ModalScreen
from textual.coordinate import Coordinate
import pandas as pd
import json

from interactive import latex_table_to_dataframe
from utils import AVAILABLE_RULES, RULES, Axis, Order, filter_rule_keys, is_instance_of_union
from highlighting import DEFAULT_RULES, table_highlighting_by_name

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
        self.app: P2LApp
        self.welcome_text = Static(WELCOME_TEXT, id="welcome")

        yield Container(
            self.welcome_text,
            id="main"
        )

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
        self.app: P2LApp
        self.latex_output_area = TextArea(read_only=True, id="latex_output")
        self.status_bar = Static("Status: Ready", id="status")
        self.input = Input(placeholder="Enter the file name", id="input")
        self.footer = Footer(id="footer")

        yield Container(
            self.latex_output_area,
            self.input,
            id="main"
        )
        yield self.status_bar
        yield self.footer


    async def on_mount(self) -> None:
        """Focus on the LaTeX output area when the screen is mounted."""
        self.latex_output_area.focus()
        # copy the table to avoid modifying the original table
        manipulated_table = deepcopy(self.app.table)
        match self.app.mode:
            case Axis.ROW:
                rule_overrides = self.app.row_rules_overrides
            case Axis.COLUMN:
                rule_overrides = self.app.col_rules_overrides
        manipulated_table = table_highlighting_by_name(
            manipulated_table,
            self.app.mode,
            rule_overrides,
            self.app.default_rules,
        )
        self.latex_output_area.text = manipulated_table.to_latex()#
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
    BINDINGS = [
        # Binding("N", "show_input", "New Input"),
        # Binding("T", "toggle_mode", "Toggle Row/Column Mode"),
        # Binding("L", "show_latex_output", "Show LaTeX Output"),
        # Binding("d", "show_edit_default_rules", "Edit Default Rules"),
        # Binding("e", "show_edit_rules", "Edit Rules"),
        Binding("S", "start_selection_mode", "Start Swap Mode"),
        Binding("s", "data_selection", "Select Row/Column", show=False),
        Binding("click", "handle_click", "Toggle Order"),
    ]

    def compose(self) -> ComposeResult:
        self.app: P2LApp
        self.data_table = DataTable(id="data_table")
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

        yield Container(
            self.data_table,
            id="main"
        )
        yield self.status_bar
        yield self.footer

    def draw_table(self) -> None:
        # copy the table to avoid modifying the original table
        self.app.displayed_table = deepcopy(self.app.table)
        match self.app.mode:
            case Axis.ROW:
                rule_overrides = self.app.row_rules_overrides
                ignore = self.app.skipped_cols
            case Axis.COLUMN:
                rule_overrides = self.app.col_rules_overrides
                ignore = self.app.skipped_rows
        self.app.displayed_table = table_highlighting_by_name(
            self.app.displayed_table,
            self.app.mode,
            rule_overrides,
            self.app.default_rules,
            ignore
        )

        self.data_table.clear(columns=True)
        # add the columns with the index column
        column_keys = []
        for col in self.app.displayed_table.columns:
            key = str(col)
            name = str(col)

            if self.app.mode == Axis.COLUMN:
                # get the ordering of the columns
                order = self.app.col_rules_overrides.get(col, {}).get(
                    "order", self.app.default_rules["order"]
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
        for _, row in self.app.displayed_table.iterrows():
            key = str(row.name)
            name = str(row.name)
            if self.app.mode == Axis.ROW:
                order = self.app.row_rules_overrides.get(name, {}).get(
                    "order", self.app.default_rules["order"]
                )
                match order:
                    case Order.MINIMUM:
                        name = f"{name} (v)"
                    case Order.NEUTRAL:
                        name = f"{name} (-)"
                    case Order.MAXIMUM:
                        name = f"{name} (^)"

            self.data_table.add_row(
                *[str(value) for value in row], key=key, label=name
            )
            row_keys.append(key)

        match self.app.mode:
            case Axis.ROW:
                for col_key in self.app.skipped_cols:
                    for row_key in row_keys:
                        cell_content = self.data_table.get_cell(row_key=row_key, column_key=col_key)
                        self.data_table.update_cell(row_key=row_key, column_key=col_key, value=f"[grey54]{cell_content}[/grey54]", update_width=True)
            case Axis.COLUMN:
                for row_key in self.app.skipped_rows:
                    for col_key in column_keys:
                        cell_content = self.data_table.get_cell(row_key=row_key, column_key=col_key)
                        self.data_table.update_cell(row_key=row_key, column_key=col_key, value=f"[grey54]{cell_content}[/grey54]", update_width=True)

        self.refresh()

    async def on_mount(self) -> None:
        """Initialize the DataTable with data."""
        self.data_table.cursor_type = "cell"

    async def on_click(self, message: Click) -> None:
        """Handle click events on the DataTable columns."""
        if message.button != 1:
            return  # Only handle left-clicks

        element = message.widget

        # Check if the clicked element is a column header
        if isinstance(element, DataTable):
            match self.app.mode:
                case Axis.ROW:
                    # Check if the clicked element is a row header
                    if element.hover_column != -1 or element.hover_row == -1:
                        return
                    row_name = self.app.displayed_table.index[element.hover_row]
                    self.app.toggle_row_order(row_name)
                case Axis.COLUMN:
                    # Check if the clicked element is a column header
                    if element.hover_row != -1 or element.hover_column == -1:
                        return
                    column_name = self.app.displayed_table.columns[element.hover_column]
                    self.app.toggle_column_order(column_name)

    async def action_start_selection_mode(self) -> None:
        if self.app.table.empty:
            match self.app.mode:
                case Axis.ROW:
                    self.status_bar.update("No data available to select rows.")
                case Axis.COLUMN:
                    self.status_bar.update("No data available to select columns.")
            return
        self.selection_mode = True
        self.selected_data = []
        match self.app.mode:
            case Axis.ROW:
                self.status_bar.update(
                    "Selection Mode: Select two rows by pressing 's' on each."
                )
            case Axis.COLUMN:
                self.status_bar.update(
                    "Selection Mode: Select two columns by pressing 's' on each."
                )

    async def disable_selection_mode(self) -> None:
        self.selection_mode = False
        self.selected_data = []
        self.status_bar.update("Exiting Selection Mode.")

    async def action_data_selection(self) -> None:
        if not self.selection_mode:
            return
        if self.app.mode == Axis.COLUMN:
            items = self.app.displayed_table.columns
            cursor_position = self.data_table.cursor_column
            item_type = "column"
            swap_method = self.app.swap_columns
        elif self.app.mode == Axis.ROW:
            items = self.app.displayed_table.index
            cursor_position = self.data_table.cursor_row
            item_type = "row"
            swap_method = self.app.swap_rows
        else:
            self.status_bar.update("Invalid mode.")
            return

        try:
            item_name = items[cursor_position]
        except IndexError:
            self.status_bar.update(f"Invalid {item_type} selection.")
            return

        if item_name in self.selected_data:
            self.status_bar.update(f"{item_type.capitalize()} '{item_name}' is already selected.")
            return

        self.selected_data.append(item_name)
        remaining = 2 - len(self.selected_data)
        if remaining > 0:
            self.status_bar.update(
                f"Selected '{item_name}'. Select {remaining} more {item_type}(s)."
            )
        else:
            item1, item2 = self.selected_data
            swap_method(item1, item2)
            self.status_bar.update(
                f"Swapped {item_type}s '{item1}' and '{item2}'. Exiting Selection Mode."
            )
            await self.disable_selection_mode()

class InputScreen(ModalScreen):
    """Screen for table input."""

    BINDINGS = [
        Binding("ctrl+s", "submit", "Submit"),
    ]

    def __init__(self):
        super().__init__()
        self.app: P2LApp

    def compose(self) -> ComposeResult:
        self.info_text = Static("Enter the table data in LaTeX format.", id="info")
        self.input_area = TextArea(id="input")
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

        yield Grid(
            self.info_text,
            self.input_area,
            id="grid_input"
        )
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

    def __init__(self, rules: str, info_text: str = "Enter the highlighting rules in JSON format."):
        super().__init__()
        self.rules = rules
        self.info_text = info_text

    def compose(self) -> ComposeResult:
        self.app: P2LApp
        self.info_text = Static(self.info_text, id="info")
        self.highlight_input_area = TextArea(id="highlight_input")
        self.highlight_input_area.text = self.rules
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

        yield Grid(
            self.info_text,
            self.highlight_input_area,
            id="grid_input"
        )
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
            self.status_bar.update(
                f"Invalid keys {pop_keys}. They have been removed."
            )

        # Filter out the keys that don't have matching types
        pop_keys = []
        for key, value in rules.items():
            if key not in AVAILABLE_RULES:
                continue
            rule_type = AVAILABLE_RULES[key]

            if not is_instance_of_union(value, rule_type):
                self.status_bar.update(
                    f"Invalid value '{value}' for key '{key}'. Expected '{rule_type}' . It has been removed."
                )
                pop_keys.append(key)


        for key in pop_keys:
            rules.pop(key)

        return rules
        

class P2LApp(App):
    """Main application class."""

    CSS_PATH = "p2l_ui.tcss"

    BINDINGS = [
        Binding("N", "show_input", "New Input"),
        Binding("T", "toggle_mode", "Toggle Row/Column Mode"),
        Binding("L", "show_latex_output", "Show LaTeX Output"),
        Binding("d", "show_edit_default_rules", "Edit Default Rules"),
        Binding("x", "toggle_cell", "skip/include row/column"),
        Binding("e", "show_edit_rules", "Edit Rules"),
    ]

    def __init__(self):
        super().__init__()
        self.table = pd.DataFrame()
        self.mode = Axis.COLUMN
        self.displayed_table = pd.DataFrame()
        self.default_rules = deepcopy(DEFAULT_RULES)
        self.col_rules_overrides = {}
        self.row_rules_overrides = {}
        self.skipped_cols = []
        self.skipped_rows = []
        self.current_active_text_area = None
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

    def reset_formatting_rules(self):
        """Reset the formatting rules to the default values"""
        self.default_rules = deepcopy(DEFAULT_RULES)
        self.col_rules_overrides = {col: {} for col in self.table.columns}
        self.row_rules_overrides = {row: {} for row in self.table.index}

    async def action_show_input(self) -> None:
        """Show the input screen for table input."""

        def update_table(table: pd.DataFrame | None) -> None:
            if table is not None:
                self.table = table
                self.reset_formatting_rules()
                self.draw_table()
                self.data_table_screen.status_bar.update("Table input successful.")
            else:
                self.data_table_screen.status_bar.update("Invalid table input.")

        self.push_screen(InputScreen(), update_table)
        self.draw_table()

    async def action_show_latex_output(self) -> None:
        """Show the LaTeX output screen."""

        self.push_screen(LATeXOutputScreen())
        self.draw_table()

    async def action_show_edit_default_rules(self) -> None:
        """Show the input screen for editing the default highlighting rules."""
        info_text = "Enter the default highlighting rules in JSON format."

        def update_highlighting(highlighting: dict[str, Any] | None) -> None:
            if highlighting is not None:
                self.default_rules = highlighting
                self.draw_table()
                self.data_table_screen.status_bar.update(
                    "Default Highlighting rules updated."
                )
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.push_screen(
            RulesInputScreen(json.dumps(self.default_rules, indent=4), info_text),
            update_highlighting,
        )
        self.draw_table()

    async def action_show_edit_rules(self) -> None:
        """Show the input screen for column/row-specific highlighting rules."""
        match self.mode:
            case Axis.COLUMN:
                await self.show_column_rules()
            case Axis.ROW:
                await self.show_row_rules()

    async def show_column_rules(self) -> None:
        """Show the input screen for column-specific highlighting rules."""
        # Get the name of the current cursor column from DataTableScreen
        try:
            column_name = self.displayed_table.columns[
                self.data_table_screen.data_table.cursor_column
            ]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No column selected.")
            return
        
        info_text = f"Enter the highlighting rules for column '{column_name}' in JSON format."

        def update_highlighting(highlighting: dict[str, Any] | None) -> None:
            if highlighting is not None:
                self.col_rules_overrides[column_name] = highlighting
                self.draw_table()
                self.data_table_screen.status_bar.update(
                    f"Highlighting rules updated for '{column_name}'."
                )
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.current_highlighting_target = column_name
        column_rules = self.col_rules_overrides.get(column_name, {})

        self.push_screen(
            RulesInputScreen(json.dumps(column_rules, indent=4), info_text),
            update_highlighting,
        )
        self.draw_table()

    async def show_row_rules(self) -> None:
        """Show the input screen for row-specific highlighting rules."""
        # Get the name of the current cursor row from DataTableScreen
        try:
            row_name = self.displayed_table.index[
                self.data_table_screen.data_table.cursor_row
            ]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No row selected.")
            return
        
        info_text = f"Enter the highlighting rules for row '{row_name}' in JSON format."

        def update_highlighting(highlighting: dict[str, Any] | None) -> None:
            if highlighting is not None:
                self.row_rules_overrides[row_name] = highlighting
                self.draw_table()
                self.data_table_screen.status_bar.update(
                    f"Highlighting rules updated for '{row_name}'."
                )
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.current_highlighting_target = row_name
        row_rules = self.row_rules_overrides.get(row_name, {})

        self.push_screen(
            RulesInputScreen(json.dumps(row_rules, indent=4), info_text),
            update_highlighting,
        )
        self.draw_table()

    async def action_toggle_mode(self) -> None:
        """Toggle the row/column mode."""
        self.mode = Axis.ROW if self.mode == Axis.COLUMN else Axis.COLUMN
        self.draw_table()
        self.data_table_screen.status_bar.update(f"Mode toggled to {self.mode.name}.")

    async def action_toggle_cell(self) -> None:
        """Toggle the row/column mode."""
        if self.mode == Axis.ROW:
            self.toggle_column()
        elif self.mode == Axis.COLUMN:
            self.toggle_row()

    def toggle_column(self) -> None:
        try:
            column_name = self.displayed_table.columns[
                self.data_table_screen.data_table.cursor_column
            ]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No column selected.")
            return
        
        if column_name in self.skipped_cols:
            self.skipped_cols.remove(column_name)
            self.data_table_screen.status_bar.update(f"Included column '{column_name}'.")
        else:
            self.skipped_cols.append(column_name)
            self.data_table_screen.status_bar.update(f"Skipped column '{column_name}'.")
        self.draw_table()

    def toggle_row(self) -> None:
        try:
            row_name = self.displayed_table.index[
                self.data_table_screen.data_table.cursor_row
            ]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No row selected.")
            return
        
        if row_name in self.skipped_rows:
            self.skipped_rows.remove(row_name)
            self.data_table_screen.status_bar.update(f"Included row '{row_name}'.")
        else:
            self.skipped_rows.append(row_name)
            self.data_table_screen.status_bar.update(f"Skipped row '{row_name}'.")
        self.draw_table()

    def swap_columns(self, col1: str, col2: str) -> None:
        """Swap two columns in the DataFrame."""
        if (
            col1 not in self.displayed_table.columns
            or col2 not in self.displayed_table.columns
        ):
            self.data_table_screen.status_bar.update(
                "One or both columns do not exist."
            )
            return

        # Swap columns in the DataFrame
        cols = list(self.displayed_table.columns)
        idx1, idx2 = cols.index(col1), cols.index(col2)
        cols[idx1], cols[idx2] = cols[idx2], cols[idx1]
        self.displayed_table = self.displayed_table[cols]

        # Also update the underlying table if necessary
        self.table = self.table[cols]

        self.draw_table()
        self.data_table_screen.status_bar.update(
            f"Swapped columns '{col1}' and '{col2}'."
        )

    def swap_rows(self, row1: str, row2: str) -> None:
        """Swap two rows in the DataFrame."""
        if (
            row1 not in self.displayed_table.index
            or row2 not in self.displayed_table.index
        ):
            self.data_table_screen.status_bar.update("One or both rows do not exist.")
            return

        # Swap rows in the DataFrame
        rows = list(self.displayed_table.index)
        idx1, idx2 = rows.index(row1), rows.index(row2)
        rows[idx1], rows[idx2] = rows[idx2], rows[idx1]
        self.displayed_table = self.displayed_table.reindex(rows)

        # Also update the underlying table if necessary
        self.table = self.table.reindex(rows)

        self.draw_table()
        self.data_table_screen.status_bar.update(f"Swapped rows '{row1}' and '{row2}'.")

    def draw_table(self) -> None:
        """Draw the table with highlighting."""
        self.data_table_screen.draw_table()

    def toggle_column_order(self, column_name: str) -> None:
        """Toggle the order of the specified column between min, neutral, and max."""
        current_order = self.col_rules_overrides[column_name].get(
            "order", self.default_rules["order"]
        )

        # Define the toggle sequence
        match current_order:
            case Order.MINIMUM:
                new_order = Order.NEUTRAL
            case Order.NEUTRAL:
                new_order = Order.MAXIMUM
            case Order.MAXIMUM:
                new_order = Order.MINIMUM

        # Update the order in the formatting rules
        self.col_rules_overrides[column_name]["order"] = new_order

        # Update the status bar
        self.data_table_screen.status_bar.update(
            f"Column '{column_name}' order set to {new_order.name}."
        )

        # Re-apply highlighting with updated order
        self.draw_table()

    def toggle_row_order(self, row_name: str) -> None:
        """Toggle the order of the specified row between min, neutral, and max."""
        current_order = self.row_rules_overrides[row_name].get(
            "order", self.default_rules["order"]
        )

        # Define the toggle sequence
        match current_order:
            case Order.MINIMUM:
                new_order = Order.NEUTRAL
            case Order.NEUTRAL:
                new_order = Order.MAXIMUM
            case Order.MAXIMUM:
                new_order = Order.MINIMUM

        # Update the order in the formatting rules
        self.row_rules_overrides[row_name]["order"] = new_order

        # Update the status bar
        self.data_table_screen.status_bar.update(
            f"Row '{row_name}' order set to {new_order.name}."
        )

        # Re-apply highlighting with updated order
        self.draw_table()


# Ensure the App runs only if executed as the main module
if __name__ == "__main__":
    P2LApp().run()
