# Python

from copy import deepcopy
from typing import Any, Callable
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import TextArea, DataTable, Footer, Static
from textual.binding import Binding
from textual.events import Click
from textual.screen import Screen
import pandas as pd
import json

from interactive import convert2dataframe
from utils import Axis, Order
from highlighting import DEFAULT_HIGHLIGHTING, table_highlighting_by_name


class DataTableScreen(Screen):
    """Screen displaying the DataTable."""
    BINDINGS = [
        Binding("N", "show_input", "New Input"),
        Binding("d", "show_default_highlighting", "Default Rules"),
        Binding("c", "show_column_highlighting", "Column Rules"),
        Binding("S", "start_selection_mode", "Start Swap Mode"),
        # Binding("enter", "submit_highlighting", "Submit Highlighting", show=False),
        Binding("s", "column_selection", "Select Column", show=False),
        Binding("click", "handle_column_click", "Toggle Column Order"),
    ]

    def compose(self) -> ComposeResult:
        self.app: P2LApp
        self.data_table = DataTable()
        self.status_bar = Static("Status: Ready")
        self.footer = Footer()

        yield Container(self.data_table, id="main")
        yield Container(self.status_bar, id="status")
        yield Container(self.footer, id="footer")

    def draw_table(self) -> None:
        # copy the table to avoid modifying the original table
        self.app.displayed_table = deepcopy(self.app.table)
        self.app.displayed_table = table_highlighting_by_name(self.app.displayed_table, Axis.COLUMN, self.app.formatting_rules, self.app.default_highlighting)

        self.data_table.clear(columns=True)
        # add the columns with the index column
        # self.data_table.add_column("Index")
        column_names = []
        for col in self.app.displayed_table.columns:
            # get the ordering of the columns
            order = self.app.formatting_rules.get(col, {}).get("order", self.app.default_highlighting["order"])
            match order:
                case Order.MINIMUM:
                    column_names.append(f"{str(col)} (v)")
                case Order.NEUTRAL:
                    column_names.append(f"{str(col)} (-)")
                case Order.MAXIMUM:
                    column_names.append(f"{str(col)} (^)")

        self.data_table.add_columns(*column_names)

        for _, row in self.app.displayed_table.iterrows():
            self.data_table.add_row(*[str(value) for value in row], key=str(row.name))
        self.refresh()

    async def on_mount(self) -> None:
        """Initialize the DataTable with data."""
        # app = self.app
        # app.draw_table()
        self.data_table.cursor_type = "cell"

    async def on_click(self, message: Click) -> None:
        """Handle click events on the DataTable columns."""
        if message.button != 1:
            return  # Only handle left-clicks

        element = message.widget

        # Check if the clicked element is a column header
        if isinstance(element, DataTable):
            # Check if the clicked element is a column header
            if element.hover_row != -1 or element.hover_column == -1:
                return
            column_name = self.app.displayed_table.columns[element.hover_column]
            self.app.toggle_column_order(column_name)

    async def action_start_selection_mode(self) -> None:
        if self.app.table.empty:
            self.status_bar.update("No data available to select columns.")
            return
        self.selection_mode = True
        self.selected_columns = []
        self.status_bar.update("Selection Mode: Select two columns by pressing 's' on each.")

    async def disable_selection_mode(self) -> None:
        self.selection_mode = False
        self.selected_columns = []
        self.status_bar.update("Exiting Selection Mode.")

    async def action_column_selection(self) -> None:
        try:
            column_name = self.app.displayed_table.columns[self.data_table.cursor_column]
        except IndexError:
            self.status_bar.update("Invalid column selection.")
            return

        if column_name in self.selected_columns:
            self.status_bar.update(f"Column '{column_name}' is already selected.")
            return

        self.selected_columns.append(column_name)
        self.status_bar.update(f"Selected '{column_name}'. Select {2 - len(self.selected_columns)} more column(s).")

        if len(self.selected_columns) == 2:
            col1, col2 = self.selected_columns
            self.app.swap_columns(col1, col2)
            self.status_bar.update(f"Swapped columns '{col1}' and '{col2}'. Exiting Selection Mode.")
            await self.disable_selection_mode()


class InputScreen(Screen):
    """Screen for table input."""
    BINDINGS = [
        Binding("ctrl+s", "submit", "Submit"),
    ]

    class Modes:
        TABLE = "table"
        DEFAULT_HIGHLIGHTING = "default_highlighting"
        COLUMN_HIGHLIGHTING = "column_highlighting"

    def __init__(self):
        super().__init__()
        self.app: P2LApp

    def compose(self) -> ComposeResult:
        self.mode = self.Modes.TABLE
        self.input_area = TextArea()
        self.status_bar = Static("Status: Ready")
        self.footer = Footer()
        yield Container(self.input_area, id="main")
        yield Container(self.status_bar, id="status")
        yield Container(self.footer, id="footer")

    async def on_mount(self) -> None:
        """Focus on the input area when the screen is mounted."""
        self.input_area.focus()

    async def action_submit(self) -> None:
        """Handle submission of input data."""
        await self.handle_submit()

    async def handle_submit(self) -> None:
        """Handle submission of input data."""
        # app = self.app
        self.dismiss(convert2dataframe(self.input_area.text))
    

class HighlightingInputScreen(Screen):
    """Screen for default or column highlighting input."""
    BINDINGS = [
        Binding("ctrl+s", "submit", "Submit"),
    ]

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        self.app: P2LApp
        self.highlight_input_area = TextArea()
        self.highlight_input_area.text = self.text
        self.status_bar = Static("Status: Ready")
        self.footer = Footer()
        yield Container(self.highlight_input_area, id="main")
        yield Container(self.status_bar, id="status")
        yield Container(self.footer, id="footer")

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
            if "order" in new_rules:
                new_rules["order"] = Order(new_rules["order"])

            self.dismiss(new_rules)
        except json.JSONDecodeError:
            self.status_bar.update("Invalid JSON input. Please try again.")


class P2LApp(App):
    """Main application class."""

    CSS = """
    Screen {
        layout: vertical;
    }
    Container#main {
        height: 1fr;
    }
    Container#status {
        height: 1;
    }
    Container#footer {
        height: 1;
    }
    """

    BINDINGS = [
        Binding("N", "show_input", "New Input"),
        Binding("d", "show_default_highlighting", "Default Rules"),
        Binding("c", "show_column_highlighting", "Column Rules"),
        Binding("S", "start_selection_mode", "Start Column Selection"),
    ]

    def __init__(self):
        super().__init__()
        self.table = pd.DataFrame()
        self.displayed_table = pd.DataFrame()
        self.default_highlighting = deepcopy(DEFAULT_HIGHLIGHTING)
        self.formatting_rules = {}
        self.current_active_text_area = None
        self.selection_mode = False
        self.selected_columns = []
        self.current_highlighting_target = None  # Tracks which column to highlight

    def compose(self) -> ComposeResult:
        yield from super().compose()
        # Register Screens
        self.data_table_screen = DataTableScreen()
        self.push_screen(self.data_table_screen)

    async def reset_screen(self) -> None:
        """Reset the screen to the DataTable."""
        await self.switch_screen(self.data_table_screen)

    def reset_formatting_rules(self):
        formatting_rules = {}
        for col in self.table.columns:
            formatting_rules[col] = {
            }

        self.default_highlighting = deepcopy(DEFAULT_HIGHLIGHTING)
        self.formatting_rules = formatting_rules

    async def action_show_input(self) -> None:
        """Show the input screen for table input."""
        def update_table(table : pd.DataFrame | None) -> None:
            if table is not None:
                self.table = table
                self.reset_formatting_rules()
                self.draw_table()
                self.data_table_screen.status_bar.update("Table input successful.")
            else:
                self.data_table_screen.status_bar.update("Invalid table input.")

        self.push_screen(InputScreen(), update_table)
        self.draw_table()

    async def action_show_default_highlighting(self) -> None:
        """Show the input screen for default highlighting."""
        def update_highlighting(highlighting : dict[str, Any] | None) -> None:
            if highlighting is not None:
                self.default_highlighting = highlighting
                self.draw_table()
                self.data_table_screen.status_bar.update("Default Highlighting rules updated.")
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.push_screen(HighlightingInputScreen(json.dumps(self.default_highlighting, indent=4)), update_highlighting)
        self.draw_table()

    async def action_show_column_highlighting(self) -> None:
        """Show the input screen for column-specific highlighting."""
        # Get the name of the current cursor column from DataTableScreen
        try:
            column_name = self.displayed_table.columns[self.data_table_screen.data_table.cursor_column]
        except (IndexError, AttributeError):
            self.data_table_screen.status_bar.update("No column selected.")
            return
        
        def update_highlighting(highlighting : dict[str, Any] | None) -> None:
            if highlighting is not None:
                self.formatting_rules[column_name] = highlighting
                self.draw_table()
                self.data_table_screen.status_bar.update(f"Highlighting rules updated for '{column_name}'.")
            else:
                self.data_table_screen.status_bar.update("Invalid highlighting rules.")

        self.current_highlighting_target = column_name
        column_rules = self.formatting_rules.get(column_name, {})

        self.push_screen(HighlightingInputScreen(json.dumps(column_rules, indent=4)), update_highlighting)
        self.draw_table()

    def swap_columns(self, col1: str, col2: str) -> None:
        """Swap two columns in the DataFrame."""
        if col1 not in self.displayed_table.columns or col2 not in self.displayed_table.columns:
            self.data_table_screen.status_bar.update("One or both columns do not exist.")
            return

        # Swap columns in the DataFrame
        cols = list(self.displayed_table.columns)
        idx1, idx2 = cols.index(col1), cols.index(col2)
        cols[idx1], cols[idx2] = cols[idx2], cols[idx1]
        self.displayed_table = self.displayed_table[cols]

        # Also update the underlying table if necessary
        self.table = self.table[cols]

        self.draw_table()
        self.data_table_screen.status_bar.update(f"Swapped columns '{col1}' and '{col2}'.")


    def draw_table(self) -> None:
        """Draw the table with highlighting."""
        self.data_table_screen.draw_table()

    def toggle_column_order(self, column_name: str) -> None:
        """Toggle the order of the specified column between min, neutral, and max."""
        current_order = self.formatting_rules[column_name].get("order", self.default_highlighting["order"])

        # Define the toggle sequence
        match current_order:
            case Order.MINIMUM:
                new_order = Order.NEUTRAL
            case Order.NEUTRAL:
                new_order = Order.MAXIMUM
            case Order.MAXIMUM:
                new_order = Order.MINIMUM

        # Update the order in the formatting rules
        self.formatting_rules[column_name]["order"] = new_order

        # Update the status bar
        self.data_table_screen.status_bar.update(f"Column '{column_name}' order set to {new_order.name}.")

        # Re-apply highlighting with updated order
        self.draw_table()

# Ensure the App runs only if executed as the main module
if __name__ == "__main__":
    P2LApp().run()