from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Footer, Static


class HelpScreen(ModalScreen):
    """A modal screen to display help text."""

    BINDINGS = [
        Binding("q", "exit_screen", "Return"),
    ]

    def __init__(self, help_text: str):
        super().__init__()
        self.help_text = help_text

    def compose(self):
        yield Static(self.help_text, id="help_text")
        yield Footer(id="footer")

    def action_exit_screen(self):
        self.dismiss()
