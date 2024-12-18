from textual.app import ComposeResult
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Input

from latex_table_editor.utils import Rule


class InputModal(ModalScreen):
    """Modal input screen for editing cell values."""

    def __init__(self, param: str, column: str, value: str):
        super().__init__()
        self.param = param
        self.prompt =  f"Enter new value for '{param}' in '{column}':"
        self.input_field = Input(placeholder="Enter value...")
        self.input_field.value = value
        self.submit_button = Button("Submit", id="submit_button")
        self.error_message = ""

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

    def validate_input(self, value: str) -> bool:
        # Implement validation logic here
        return True  # Replace with actual validation

class RulesScreen(ModalScreen):
    """Screen to display and edit rules in a DataTable."""

    BINDINGS = [("q", "exit_screen", "Return")]

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

        def update_rule(value: str) -> None:
            if column == "default":
                rule = self.default_rule
            else:
                rule = self.override_rules[column]
            setattr(rule, param, value)
            self.on_rule_change_callback(self.default_rule, self.override_rules)
            self.data_table.update_cell(event.cell_key.row_key, event.cell_key.column_key, getattr(rule, param, ""), update_width=True)

        await self.app.push_screen(InputModal(str(param), str(column), value), update_rule)

    # def on_input_submitted(self, value: str) -> None:
    #     # Validate input and update rules
    #     param, column_key = self.selected_cell
    #     new_value = value if value != "" else None

    #     if column_key == "default":
    #         setattr(self.default_rule, param, new_value)
    #     else:
    #         rule = self.override_rules.get(column_key)
    #         if rule is not None:
    #             setattr(rule, param, new_value)
    #         else:
    #             self.override_rules[column_key] = Rule(**{param: new_value})

    #     # Update the DataTable cell
    #     self.data_table.update_cell(
    #         row_key=param,
    #         column_key=column_key,
    #         value=str(new_value) if new_value else "",
    #         update_width=True,
    #     )

    #     # Callback to update the rules in the main app
    #     self.on_rule_change_callback(self.default_rule, self.override_rules)

    def validate_input(self, value: str) -> bool:
        # Implement validation logic specific to Rule parameters
        return True  # Replace with actual validation

    def action_exit_screen(self) -> None:
        self.app.pop_screen()