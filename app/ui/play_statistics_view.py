from textual.app import ComposeResult
from textual.widgets import (
    DataTable,
    Button,
)
from textual.containers import Vertical, VerticalScroll
from app.ui.data_service import DataService


class PlayStatisticsView(Vertical):
    _cols = [
        ("ID", "Title", "Playtime"),
    ]

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            DataTable(),
        )

    def refresh_data(self):
        _rows = []
        _rows.clear()
        _rows.append(*self._cols)

        stats = DataService.get_play_statitics()
        table = self.query_one(DataTable)

        for s in stats:
            _rows.append((s.id, s.title, s.playtime))

        table.clear()
        table.add_rows(_rows[1:])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case _:
                pass

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*PlayStatisticsView._cols[0])
        self.refresh_data()
        self.set_interval(1, self.refresh_data)
