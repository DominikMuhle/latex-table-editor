from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Static, TextArea


class LATeXOutputScreen(ModalScreen):
    """Screen for LaTeX output."""

    BINDINGS = [
        Binding("ctrl+r", "dismiss", "Return to DataTable"),
        Binding("ctrl+s", "save_to_file", "Save to File"),
    ]

    def __init__(self, table):
        super().__init__()
        self.table = table
        self.latex_output_area = TextArea(read_only=True, id="latex_output")
        self.status_bar = Static("Status: Ready", id="status")
        self.input = Input(placeholder="Enter the file name", id="input")
        self.footer = Footer(id="footer")

    def compose(self) -> ComposeResult:
        yield Container(self.latex_output_area, self.input, id="main")
        yield self.status_bar
        yield self.footer

    async def on_mount(self) -> None:
        """Focus on the LaTeX output area when the screen is mounted."""
        self.latex_output_area.focus()

        self.table.highlight_table()

        self.latex_output_area.text = self.table.display_dataframe.to_latex()
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
