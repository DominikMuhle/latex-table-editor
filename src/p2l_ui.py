from copy import deepcopy
from textual.app import App, ComposeResult
from textual.widgets import Footer, TextArea, DataTable
from textual.containers import Container
from textual.binding import Binding

import pandas as pd
from highlighting import table_highlighting_by_name
from interactive import convert2dataframe
from utils import Axis, Order

class P2LApp(App):
    BINDINGS = [
        Binding("N", "show_input", "New Input"),
        Binding("ctrl+s", "submit_input", show=False),
    ]

    def compose(self) -> ComposeResult:
        self.input_area = TextArea()
        self.input_area.visible = False  # Hide the TextArea initially
        self.data_table = DataTable()
        self.table = pd.DataFrame()
        self.displayed_table = pd.DataFrame()
        self.default_highlighting = {
            "order": Order.NEUTRAL,
            "highlighting": ["%s"],
            "default": "%s",
            "precision": "%.2f",
        } 
        self.formatting_rules = {}
        self.reset_formatting_rules()

        yield Container(self.input_area)
        yield Container(self.data_table)
        yield Footer()

    def action_show_input(self) -> None:
        self.input_area.visible = True
        self.input_area.focus()

    def action_submit_input(self) -> None:
        self.table = convert2dataframe(self.input_area.text)
        self.reset_formatting_rules()
        self.input_area.visible = False
        self.input_area.text = ""  # Clear the TextArea
        self.update_data_table()
        self.refresh()

    def update_data_table(self):
        # copy the table to avoid modifying the original table
        self.displayed_table = deepcopy(self.table)
        self.displayed_table = table_highlighting_by_name(self.displayed_table, Axis.COLUMN, self.formatting_rules, self.default_highlighting)

        self.data_table.clear(columns=True)
        # add the columns with the index column
        self.data_table.add_column("Index")
        self.data_table.add_columns(*[str(col) for col in self.displayed_table.columns])

        for _, row in self.displayed_table.iterrows():
            self.data_table.add_row(row.name, *[str(value) for value in row])


    def reset_formatting_rules(self):
        formatting_rules = {}
        for col in self.table.columns:
            formatting_rules[col] = {
            }

        self.default_highlighting = {
            "order": Order.NEUTRAL,
            "highlighting": ["%s"],
            "default": "%s",
            "precision": "%.2f",
        }
        self.formatting_rules = formatting_rules


if __name__ == "__main__":
    app = P2LApp()
    app.run()