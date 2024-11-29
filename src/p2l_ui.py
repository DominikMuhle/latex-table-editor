from copy import deepcopy
import json
from os import wait
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import Footer, TextArea, DataTable, Static
from textual.containers import Container
from textual.binding import Binding

import pandas as pd
from highlighting import DEFAULT_HIGHLIGHTING, table_highlighting_by_name
from interactive import convert2dataframe
from utils import Axis, Order

class P2LApp(App):
    BINDINGS = [
        Binding("N", "show_input", "New Input"),
        Binding("d", "show_input_default_highlighting", "Default Rules"),
        Binding("c", "show_input_column_highlighting", "Column Rules"),
        Binding("S", "start_selection_mode", "Swap Mode"),
        Binding("ctrl+s", "submit", "Submit"),
        Binding("s", "column_selection", "Select Column", show=False),
    ]

    def compose(self) -> ComposeResult:
        self.input_area = TextArea()
        self.input_area.visible = False  # Hide the TextArea initially

        self.highlight_input_area = TextArea()
        self.highlight_input_area.visible = False  # Hide initially

        self.data_table = DataTable()
        self.table = pd.DataFrame()
        self.displayed_table = pd.DataFrame()
        self.default_highlighting = deepcopy(DEFAULT_HIGHLIGHTING)
        self.formatting_rules = {}
        self.reset_formatting_rules()

        # Initialize the current active text area
        self.current_active_text_area = None

        # Initialize selection mode attributes
        self.selection_mode = False
        self.selected_columns = []

        # Initialize footers
        self.footer = Footer()
        self.status_bar = Static("Status: Ready")  # Status bar initialized with default message

        # Yield containers in the order: input areas, data table, status bar, primary footer
        yield Container(self.input_area)
        yield Container(self.highlight_input_area)
        yield Container(self.data_table)
        yield Container(self.status_bar)  # Status bar above the main footer
        yield Container(self.footer)

    def action_show_input(self) -> None:
        self.input_area.visible = True
        self.input_area.focus()
        self.highlight_input_area.visible = False
        self.current_active_text_area = 'input'

    def action_show_input_default_highlighting(self) -> None:
        # display the highlighting rules as a json format in the text area
        self.highlight_input_area.text = json.dumps(self.default_highlighting, indent=4)

        # activate the visible text area
        self.highlight_input_area.visible = True
        self.highlight_input_area.focus()
        self.input_area.visible = False
        self.current_active_text_area = 'input_default_highlighting'

    def action_show_input_column_highlighting(self) -> None:
        # get the name of the current cursor column
        column_name = self.displayed_table.columns[self.data_table.cursor_column]

        # display the highlighting rules as a json format in the text area
        self.highlight_input_area.text = json.dumps(self.formatting_rules[column_name], indent=4)

        # activate the visible text area
        self.highlight_input_area.visible = True
        self.highlight_input_area.focus()
        self.input_area.visible = False
        self.current_active_text_area = 'input_column_highlighting'

    def action_start_selection_mode(self) -> None:
        if self.table.empty:
            self.status_bar.update("No data available to select columns.")
            return
        self.selection_mode = True
        self.selected_columns = []
        self.status_bar.update("Selection Mode: Select two columns by pressing Enter on each.")

    def disable_selection_mode(self) -> None:
        self.selection_mode = False
        self.selected_columns = []
        self.status_bar.update("Exiting Selection Mode.")

    def action_column_selection(self) -> None:
        try:
            column_name = self.displayed_table.columns[self.data_table.cursor_column]
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
            self.swap_columns(col1, col2)
            self.status_bar.update(f"Swapped columns '{col1}' and '{col2}'. Exiting Selection Mode.")
            self.disable_selection_mode()


    def action_submit(self) -> None:
        match self.current_active_text_area:
            case 'input':
                if self.input_area.visible:
                    self.submit_input()
            case 'input_default_highlighting':
                if self.highlight_input_area.visible:
                    self.submit_highlighting_input(self.default_highlighting)
            case 'input_column_highlighting':
                if self.highlight_input_area.visible:
                    column_name = self.displayed_table.columns[self.data_table.cursor_column]

                    self.submit_highlighting_input(self.formatting_rules[column_name])
     
    def submit_input(self) -> None:
        self.table = convert2dataframe(self.input_area.text)
        self.reset_formatting_rules()
        self.input_area.visible = False
        self.input_area.text = ""  # Clear the TextArea
        self.current_active_text_area = None
        self.update_data_table()
        self.refresh()

    def submit_highlighting_input(self, update_variable: dict[str, Any]) -> None:
        try:
            new_rules = json.loads(self.highlight_input_area.text)
            update_variable.update(new_rules)
            self.highlight_input_area.visible = False
            self.highlight_input_area.text = ""
            self.current_active_text_area = None
            self.update_data_table()
            self.refresh()
        except json.JSONDecodeError:
            # Handle invalid JSON input. Append a message to the TextArea
            self.highlight_input_area.text += "\n\nInvalid JSON input. Please try again."


    def update_data_table(self):
        # copy the table to avoid modifying the original table
        self.displayed_table = deepcopy(self.table)
        self.displayed_table = table_highlighting_by_name(self.displayed_table, Axis.COLUMN, self.formatting_rules, self.default_highlighting)

        self.data_table.clear(columns=True)
        # add the columns with the index column
        # self.data_table.add_column("Index")
        self.data_table.add_columns(*[str(col) for col in self.displayed_table.columns])

        for _, row in self.displayed_table.iterrows():
            self.data_table.add_row(*[str(value) for value in row], key=str(row.name))

    def swap_columns(self, col1: str, col2: str) -> None:
        # Swap columns in the DataFrame
        cols = list(self.displayed_table.columns)
        idx1, idx2 = cols.index(col1), cols.index(col2)
        cols[idx1], cols[idx2] = cols[idx2], cols[idx1]
        # self.displayed_table = self.displayed_table[cols]

        # Also update the underlying table if necessary
        self.table = self.table[cols]

        self.update_data_table()
        # self.footer.update(f"Swapped columns '{col1}' and '{col2}'.")


    def reset_formatting_rules(self):
        formatting_rules = {}
        for col in self.table.columns:
            formatting_rules[col] = {
            }

        self.default_highlighting = deepcopy(DEFAULT_HIGHLIGHTING)
        self.formatting_rules = formatting_rules


if __name__ == "__main__":
    app = P2LApp()
    app.run()