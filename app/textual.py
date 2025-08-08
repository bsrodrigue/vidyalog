from dataclasses import dataclass
from textual.app import App, ComposeResult
from textual.content import ContentText
from textual.screen import Screen
from textual.widgets import DataTable, Header, Footer, Button, Input, Label
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from app.service import backlog_service, play_session_service
from libs.fmt.datetime_formatter import DateTimeFormatter


@dataclass
class PlaySessionData:
    id = "0"
    title = ""
    start = ""
    end = ""
    playtime = ""


class DataService:
    @staticmethod
    def get_play_sessions_data() -> list[PlaySessionData]:
        sessions = []
        result = play_session_service.get_all_sessions()

        for s in result:
            data = PlaySessionData()
            data.id = str(s.id)
            data.start = DateTimeFormatter.fmt(s.session_start)
            data.end = DateTimeFormatter.fmt(s.session_end) if s.session_end else ""
            data.playtime = DateTimeFormatter.fmt_playtime(s.time_played)

            entry = backlog_service.get_entry(s.backlog_entry)

            if not entry:
                raise ValueError(f"Entry {s.backlog_entry} not found")

            meta_data = backlog_service.get_game_metadata(entry.meta_data)

            if not meta_data:
                raise ValueError(f"Metadata {entry.meta_data} not found")

            data.title = meta_data.title
            sessions.append(data)

        return sessions


# ID, Title, Start, End, Playtime
class PlaySessionList(VerticalScroll):
    _cols = [
        ("ID", "Title", "Start", "End", "Playtime"),
    ]

    def compose(self) -> ComposeResult:
        yield DataTable()

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

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*PlaySessionList._cols[0])
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


class GameBacklogApp(App):
    """
    Textual UI
    """

    BINDINGS = [
        ("ctrl+l", "list_backlogs", "List all backlogs"),
        ("ctrl+s", "start_play_session", "Start a play session"),
    ]

    #############
    # ACTIONS
    #############

    def action_list_backlogs(self) -> None:
        backlogs = backlog_service.list_all_backlogs()
        if not backlogs:
            print("📝 No backlogs found. Create one with 'new <title>'")
            return

        print(f"\n📋 Your Backlogs ({len(backlogs)}):")
        for b in backlogs:
            entry_count = len(backlog_service.list_entries_in_backlog(b.id))
            print(f"  {b.id}: {b.title} ({entry_count} games)")

    def action_start_play_session(self) -> None:
        # Use push_screen as a modal
        self.push_screen(StartPlaySessionModal())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-play-session":
            self.action_start_play_session()

    def compose(self) -> ComposeResult:
        yield Header()
        yield PlaySessionList()
        yield Button("Start Play Session", id="start-play-session")
        yield Footer()


if __name__ == "__main__":
    app = GameBacklogApp()
    app.run()
