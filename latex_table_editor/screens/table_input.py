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
        Binding("ctrl+s", "submit", "Submit"),
        Binding("ctrl+l", "open_mode_selection", "Select Mode"),
    ]

    def __init__(self, mode='latex', on_submit=None):
        super().__init__()
        self.mode = mode
        self.on_submit = on_submit
        self.info_text = Static("Enter the table data in LaTeX format.", id="info")
        self.input_area = TextArea(id="input")
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

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

