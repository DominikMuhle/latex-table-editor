from typing import Any, Callable

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input

from latex_table_editor.screens import HelpScreen
from latex_table_editor.utils import Order, Rule

HELP_TEXT = """
This screen allows you to view and edit the rules used to format the table. The rules are applied to the table data to customize the appearance of the table. You can edit the default rule and add override rules for specific rows/columns. Only the rules that are currently active (row/column mode of the table) will be displayed here.

To edit a rule, select the cell and press 'Enter'. You can then enter the new value for the rule parameter.

Some best prectices for editing rules:
    - only set the highlighting parameters in the default rules. You probably want consistent hightlighting for the entire table.
    - only set the default rule in the default rule. You probably want the same default rule for the entire table.
    - use the keybindings in the table screen to quickly change the values of the rules, such as precision and order.
"""

class InputModal(ModalScreen):
    """Modal input screen for editing cell values."""

    def __init__(self, param: str, column: str, value: str | None, validate_input: Callable[[str], bool]):
        super().__init__()
        self.param = param
        self.prompt =  f"Enter new value for '{param}' in '{column}':"
        self.input_field = Input(placeholder="Enter value...")
        if value:
            self.input_field.value = value
        self.submit_button = Button("Submit", id="submit_button")
        self.validate_input = validate_input

    def compose(self) -> ComposeResult:
        yield self.input_field
        yield self.submit_button

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_button":
            value = self.input_field.value

            if self.validate_input(value):
                self.dismiss(value)
            else:
                self.error_message = "Invalid input."
                # ...code to display error message...


class RulesScreen(ModalScreen):
    """Screen to display and edit rules in a DataTable."""

    BINDINGS = [
        ("q", "exit_screen", "Return"), 
        ("h", "show_help", "Show Help"),
        ]

    def __init__(self, default_rule: Rule, override_rules: dict, on_rule_change_callback):
        super().__init__()
        self.default_rule = default_rule
        self.override_rules = override_rules  # dict mapping names to Rule instances
        self.on_rule_change_callback = on_rule_change_callback
        self.data_table = DataTable()
        self.footer = Footer()

    def compose(self) -> ComposeResult:
        yield self.data_table
        yield self.footer

    def on_mount(self) -> None:
        self.data_table.focus()
        # Add columns: 'Parameter', 'Default Rule', and override columns
        self.data_table.add_column("Parameter", width=20, key="parameter")
        self.data_table.add_column("Default Rule", width=20, key="default")
        for item in self.override_rules.keys():
            self.data_table.add_column(str(item), width=20, key=item)
        self.data_table.fixed_columns = 2

        # Add rows for each parameter of the Rule dataclass
        parameters = Rule.__annotations__.keys()
        for param in parameters:
            row = [param]
            default_value = getattr(self.default_rule, param, "")
            row.append(str(default_value) if default_value is not None else "")
            for key in self.override_rules.keys():
                rule = self.override_rules[key]
                value = getattr(rule, param, "")
                row.append(str(value) if value is not None else "")
            self.data_table.add_row(*row, key=param)

    async def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        # Open InputModal when a cell is selected for editing
        if event.coordinate.row == -1 or event.coordinate.column <= 0:
            return  # Do not allow editing the 'Parameter' or 'Default Rule' labels
        
        value = event.value
        column = event.cell_key.column_key.value
        param = event.cell_key.row_key.value
        if column == "default":
            rule = self.default_rule
        else:
            rule = self.override_rules[column]

        def update_value(value: str) -> Any:
            if param == "precision":
                try:
                    value = int(value)
                except ValueError:
                    self.error_message = "Precision must be an integer."
                    # ...code to display error message...
                    return False
            if param == "highlighting":
                value = value.split(",")

            if param == "order":
                value = Order(value)

            return value

        def check_validity(value: str) -> bool:
            value = update_value(value)
            
            try:
                setattr(rule, param, value)
            except TypeError as e:
                self.error_message = str(e)
                # ...code to display error message...
                return False
            
            return True

        def update_rule(value: str) -> None:
            value = update_value(value)

            setattr(rule, param, value)
            self.on_rule_change_callback(self.default_rule, self.override_rules)
            self.data_table.update_cell(event.cell_key.row_key, event.cell_key.column_key, getattr(rule, param, ""), update_width=True)

        await self.app.push_screen(InputModal(str(param), str(column), value, check_validity), update_rule)


    async def action_exit_screen(self) -> None:
        await self.dismiss()

    async def action_show_help(self) -> None:
        await self.app.push_screen(HelpScreen(HELP_TEXT))