from copy import deepcopy
import json
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import Footer, TextArea, DataTable
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
        Binding("ctrl+s", "submit", "Submit"),
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

        yield Container(self.input_area)
        yield Container(self.highlight_input_area)
        yield Container(self.data_table)
        yield Footer()

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