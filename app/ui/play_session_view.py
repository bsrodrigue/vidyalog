from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Button,
    Input,
    Label,
)
from textual.containers import Horizontal, Vertical, VerticalScroll
from app.service import backlog_service, play_session_service
from app.ui.data_service import DataService


class PlaySessionView(Vertical):
    _cols = [
        ("ID", "Title", "Start", "End", "Playtime"),
    ]

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            DataTable(),
            Horizontal(
                Button("Start Play Session", id="start-play-session"),
                Button("Stop Play Session", id="stop-play-session"),
            ),
        )

    def refresh_data(self):
        _rows = []
        _rows.clear()
        _rows.append(*self._cols)

        sessions = DataService.get_play_sessions_data()
        table = self.query_one(DataTable)

        for s in sessions:
            _rows.append((s.id, s.title, s.start, s.end, s.playtime))

        table.clear()
        table.add_rows(_rows[1:])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "start-play-session":
                self.app.push_screen(StartPlaySessionModal())
            case "stop-play-session":
                play_session_service.stop_session()
            case _:
                pass

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*PlaySessionView._cols[0])
        self.refresh_data()
        self.set_interval(1, self.refresh_data)


class StartPlaySessionModal(Screen):
    CSS = """
            Screen {
                background: rgba(0, 0, 0, 0.8);
            }
         
        """

    # Make it a modal screen
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Select the game you want to play"),
            Input(placeholder="Game Title", id="backlog-entry-title"),
            Button("Submit", variant="primary", id="submit"),
            Button("Cancel", variant="error", id="cancel"),
            id="start-play-session-modal",
        )

    def action_cancel(self) -> None:
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()
            return

        if event.button.id == "submit":
            title_input = self.query_one("#backlog-entry-title", Input)
            title = title_input.value

            backlog_entry = backlog_service.get_entry_by_fuzzy_match(title)

            if not backlog_entry:
                # You might want to show an error message here
                return

            play_session_service.start_session(backlog_entry.id)
            self.dismiss()
