from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, ListItem, ListView, Static, TextArea

from latex_table_editor.conversion import (
    json_to_dataframe,
    latex_table_to_dataframe,
    string_to_dataframe,
    yaml_to_dataframe,
)
from latex_table_editor.screens import HelpScreen

HELP_TEXT = """
    To enter a table into the app, follow these steps:
    1. Prepare your table data in LaTeX, JSON, YAML, or string format.
    2. (Optional) Use "Ctrl+l" to change the input mode.
    3. Enter the table data in the input area, by pasting or typing.
    4. Use "Ctrl+s" to submit the data and display the table.
    """

class ModeSelectionScreen(ModalScreen):
    """Screen for selecting the input mode."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def compose(self) -> ComposeResult:
        self.title = Static("Select Input Mode:", id="mode_select_title")
        options = ["LaTeX", "String", "JSON", "YAML"]
        self.option_list = ListView(
            *[ListItem(Label(option), id=option.lower()) for option in options],
            id="mode_options",
        )
        # yield self.title
        yield self.option_list

    async def on_mount(self) -> None:
        """Focus on the options list when the screen is mounted."""
        self.option_list.focus()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection from the mode list."""
        mode = event.item.id
        self.callback(mode)
        await self.dismiss()


class InputScreen(ModalScreen):
    """Screen for table input."""

    BINDINGS = [
        Binding("h", "show_help", "Show Help"),
        Binding("q", "exit_screen", "Exit"),
        Binding("escape", "read_only", "Navigation Mode"),
        Binding("i", "input_mode", "Input Mode"),
        Binding("s", "submit", "Submit"),
        Binding("m", "open_mode_selection", "Select Mode"),
    ]

    def __init__(self, mode='latex', on_submit=None):
        super().__init__()
        self.mode = mode
        self.on_submit = on_submit
        self.info_text = Static("Enter the table data in LaTeX format.", id="info")
        self.input_area = TextArea(id="input", read_only=True)
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        match action:
            case "read_only":
                return not self.input_area.read_only
            case _:
                return self.input_area.read_only

    def compose(self) -> ComposeResult:
        yield Grid(self.info_text, self.input_area, id="grid_input")
        yield self.status_bar
        yield self.footer

    async def on_mount(self) -> None:
        """Focus on the input area when the screen is mounted."""
        self.input_area.focus()
        self.update_info_text()

    async def action_open_mode_selection(self) -> None:
        """Open the mode selection menu."""

        def on_mode_selected(mode: str) -> None:
            self.mode = mode
            self.update_info_text()
            self.app.pop_screen()

        await self.app.push_screen(ModeSelectionScreen(on_mode_selected))

    def update_info_text(self) -> None:
        """Update the info text based on the current input mode."""
        mode_names = {
            'latex': 'LaTeX',
            'string': 'String',
            'json': 'JSON',
            'yaml': 'YAML',
        }
        self.info_text.update(f"Enter the table data in {mode_names[self.mode]} format.")

    async def action_submit(self) -> None:
        """Handle submission of input data."""
        input_text = self.input_area.text
        try:
            if self.mode == 'latex':
                dataframe = latex_table_to_dataframe(input_text)
            elif self.mode == 'string':
                dataframe = string_to_dataframe(input_text)
            elif self.mode == 'json':
                dataframe = json_to_dataframe(input_text)
            elif self.mode == 'yaml':
                dataframe = yaml_to_dataframe(input_text)
            else:
                self.status_bar.update("Invalid input mode.")
                return
            self.dismiss(dataframe)
        except Exception as e:
            pass
            self.status_bar.update(f"Invalid input: {e}")

    async def action_exit_screen(self) -> None:
        """Exit the screen."""
        self.dismiss()

    async def action_show_help(self) -> None:
        """Show the help screen."""
        await self.app.push_screen(HelpScreen(HELP_TEXT))

    async def action_read_only(self) -> None:
        """Shift focus to the rest of the screen."""
        self.input_area.read_only = True
        self.refresh_bindings() 

    async def action_input_mode(self) -> None:
        """Shift focus back to the input area."""
        self.input_area.read_only = False
        self.refresh_bindings()