from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Footer, Static, TextArea


class RulesInputScreen(ModalScreen):
    """Screen for default or column highlighting input."""

    BINDINGS = [
        Binding("ctrl+s", "submit", "Submit"),
    ]

    def __init__(self, rules: str, info_text: str, on_submit):
        super().__init__()
        self.rules = rules
        self.info_text = info_text
        self.on_submit = on_submit
        self.highlight_input_area = TextArea(id="highlight_input")
        self.highlight_input_area.text = self.rules
        self.status_bar = Static("Status: Ready", id="status")
        self.footer = Footer(id="footer")

    def compose(self) -> ComposeResult:
        yield Grid(Static(str(self.info_text), id="info"), self.highlight_input_area, id="grid_input")
        yield self.status_bar
        yield self.footer

    async def on_mount(self) -> None:
        """Focus on the highlighting input area when the screen is mounted."""
        self.highlight_input_area.focus()

    async def action_submit(self) -> None:
        """Handle submission of highlighting rules."""
        await self.on_submit(self.highlight_input_area.text)