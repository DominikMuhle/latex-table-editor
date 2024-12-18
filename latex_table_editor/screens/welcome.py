from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static

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

    def __init__(self, on_new_input):
        super().__init__()
        self.on_new_input = on_new_input
        self.welcome_text = Static(WELCOME_TEXT, id="welcome")

    def compose(self) -> ComposeResult:
        yield Container(self.welcome_text, id="main")

    async def action_show_input(self) -> None:
        """Show the input screen for table input."""
        self.dismiss()
        await self.on_new_input()