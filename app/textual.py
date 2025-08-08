from dataclasses import dataclass
from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
    Tab,
    TabPane,
    TabbedContent,
    Tabs,
)
from app.ui.play_session_view import PlaySessionView
from app.ui.play_statistics_view import PlayStatisticsView


@dataclass
class TabData:
    id: str = ""
    label: str = ""

    def to_tab(self) -> Tab:
        return Tab(self.label, id=self.id)


TABS: list[TabData] = [
    TabData(id="play-sessions", label="🕹️ Play Sessions"),
    TabData(id="play-statistics", label="📊 Statistics"),
    TabData(id="game-backlogs", label="📋 Backlog"),
]


class GameBacklogApp(App):
    """
    Textual UI
    """

    BINDINGS = []

    def on_mount(self) -> None:
        self.query_one(Tabs).focus()

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane(TABS[0].label):
                yield PlaySessionView()
            with TabPane(TABS[1].label):
                yield PlayStatisticsView()

        yield Footer()


if __name__ == "__main__":
    app = GameBacklogApp()
    app.run()
