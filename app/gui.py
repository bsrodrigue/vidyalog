from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QFormLayout,
    QComboBox,
    QMessageBox,
    QLabel,
)
from PyQt6.QtCore import Qt
from modules.play_session.services import PlaySessionTimerService, PlaySessionError
from modules.backlog.services import GameBacklogService
from modules.repositories.in_memory_repository import InMemoryRepository
from modules.backlog.models import (
    BacklogPriority,
    BacklogStatus,
    GameBacklog,
    GameMetadata,
)
from typing import Optional
import sys

# Initialize repositories and services
backlog_repo = InMemoryRepository()
entry_repo = InMemoryRepository()
metadata_repo = InMemoryRepository()
session_repo = InMemoryRepository()

service = GameBacklogService(
    backlog_repo=backlog_repo,
    entry_repo=entry_repo,
    metadata_repo=metadata_repo,
)
play_session_service = PlaySessionTimerService(session_repo)


def get_backlog_by_fuzzy_match(query: str) -> Optional[GameBacklog]:
    """Find backlog by ID or fuzzy title match"""
    if query.isdigit():
        backlog = service.get_backlog(int(query))
        if backlog:
            return backlog
    backlogs = service.list_all_backlogs()
    query_lower = query.lower()
    for b in backlogs:
        if b.title.lower() == query_lower:
            return b
    matches = [b for b in backlogs if query_lower in b.title.lower()]
    if len(matches) == 1:
        return matches[0]
    return None


def get_game_by_fuzzy_match(query: str) -> Optional[GameMetadata]:
    """Find game by ID or fuzzy title match"""
    if query.isdigit():
        game = service.get_game_metadata(int(query))
        if game:
            return game
    games = service.list_all_game_metadata()
    query_lower = query.lower()
    for g in games:
        if g.title.lower() == query_lower:
            return g
    matches = [g for g in games if query_lower in g.title.lower()]
    if len(matches) == 1:
        return matches[0]
    return None


def format_status_priority(status: BacklogStatus, priority: BacklogPriority) -> str:
    """Format status and priority with emojis"""
    status_icons = {
        BacklogStatus.INBOX: "📥",
        BacklogStatus.PLAYING: "🎮",
        BacklogStatus.FINISHED: "✅",
        BacklogStatus.ABANDONED: "❌",
        BacklogStatus.PAUSED: "⏸️",
    }
    priority_icons = {
        BacklogPriority.P0: "🔴",
        BacklogPriority.P1: "🟡",
        BacklogPriority.P2: "🟢",
        BacklogPriority.P3: "⚪",
    }
    return f"{status_icons.get(status, '❓')} {status.name} | {priority_icons.get(priority, '❓')} {priority.name}"


class GameDialog(QDialog):
    """Dialog for creating/editing games"""

    def __init__(self, parent=None, game=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Game" if game else "Add Game")
        self.game = game
        layout = QFormLayout()

        self.title_input = QLineEdit(game.title if game else "")
        self.desc_input = QLineEdit(game.description or "" if game else "")
        self.dev_input = QLineEdit(game.developer or "" if game else "")
        self.pub_input = QLineEdit(game.publisher or "" if game else "")
        self.time_input = QLineEdit(
            str(game.avg_completion_time) if game and game.avg_completion_time else ""
        )

        layout.addRow("Title:", self.title_input)
        layout.addRow("Description:", self.desc_input)
        layout.addRow("Developer:", self.dev_input)
        layout.addRow("Publisher:", self.pub_input)
        layout.addRow("Completion Time (hours):", self.time_input)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout.addRow(buttons)
        self.setLayout(layout)

    def get_data(self):
        try:
            completion_time = (
                float(self.time_input.text()) if self.time_input.text().strip() else 0
            )
        except ValueError:
            completion_time = 0
        return {
            "title": self.title_input.text(),
            "description": self.desc_input.text(),
            "developer": self.dev_input.text(),
            "publisher": self.pub_input.text(),
            "avg_completion_time": completion_time,
        }


class EntryDialog(QDialog):
    """Dialog for editing entry status and priority"""

    def __init__(self, parent=None, entry=None, game_title=""):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Entry: {game_title}")
        self.entry = entry
        layout = QFormLayout()

        self.status_combo = QComboBox()
        self.status_combo.addItems([s.name for s in BacklogStatus])
        if entry:
            self.status_combo.setCurrentText(entry.status.name)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems([f"P{i}" for i in range(4)])
        if entry:
            priority_map = {
                BacklogPriority.P0: "P0",
                BacklogPriority.P1: "P1",
                BacklogPriority.P2: "P2",
                BacklogPriority.P3: "P3",
            }
            self.priority_combo.setCurrentText(priority_map.get(entry.priority, "P3"))

        layout.addRow("Status:", self.status_combo)
        layout.addRow("Priority:", self.priority_combo)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout.addRow(buttons)
        self.setLayout(layout)

    def get_data(self):
        status = BacklogStatus[self.status_combo.currentText()]
        priority_map = {
            "P0": BacklogPriority.P0,
            "P1": BacklogPriority.P1,
            "P2": BacklogPriority.P2,
            "P3": BacklogPriority.P3,
        }
        priority = priority_map[self.priority_combo.currentText()]
        return {"status": status, "priority": priority}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 GameBacklog Manager")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Backlogs Tab
        self.backlog_widget = QWidget()
        self.backlog_layout = QVBoxLayout()
        self.backlog_widget.setLayout(self.backlog_layout)

        backlog_input_layout = QHBoxLayout()
        self.backlog_title_input = QLineEdit()
        self.backlog_title_input.setPlaceholderText("Backlog title")
        create_backlog_btn = QPushButton("Create Backlog")
        create_backlog_btn.clicked.connect(self.create_backlog)
        backlog_input_layout.addWidget(self.backlog_title_input)
        backlog_input_layout.addWidget(create_backlog_btn)
        self.backlog_layout.addLayout(backlog_input_layout)

        self.backlog_list = QListWidget()
        self.backlog_list.itemDoubleClicked.connect(self.show_backlog_details)
        self.backlog_layout.addWidget(self.backlog_list)

        self.tabs.addTab(self.backlog_widget, "Backlogs")

        # Games Tab
        self.games_widget = QWidget()
        self.games_layout = QVBoxLayout()
        self.games_widget.setLayout(self.games_layout)

        games_input_layout = QHBoxLayout()
        self.game_title_input = QLineEdit()
        self.game_title_input.setPlaceholderText("Game title")
        add_game_btn = QPushButton("Add Game")
        add_game_btn.clicked.connect(self.add_game)
        games_input_layout.addWidget(self.game_title_input)
        games_input_layout.addWidget(add_game_btn)
        self.games_layout.addLayout(games_input_layout)

        self.games_list = QListWidget()
        self.games_list.itemDoubleClicked.connect(self.show_game_details)
        self.games_layout.addWidget(self.games_list)

        self.tabs.addTab(self.games_widget, "Games")

        # Entries Tab
        self.entries_widget = QWidget()
        self.entries_layout = QVBoxLayout()
        self.entries_widget.setLayout(self.entries_layout)

        entries_input_layout = QHBoxLayout()
        self.entry_game_input = QLineEdit()
        self.entry_game_input.setPlaceholderText("Game name or ID")
        self.entry_backlog_input = QLineEdit()
        self.entry_backlog_input.setPlaceholderText("Backlog name or ID")
        add_entry_btn = QPushButton("Add Entry")
        add_entry_btn.clicked.connect(self.add_entry)
        entries_input_layout.addWidget(self.entry_game_input)
        entries_input_layout.addWidget(self.entry_backlog_input)
        entries_input_layout.addWidget(add_entry_btn)
        self.entries_layout.addLayout(entries_input_layout)

        view_entries_layout = QHBoxLayout()
        self.view_backlog_input = QLineEdit()
        self.view_backlog_input.setPlaceholderText("Backlog name or ID to view entries")
        view_entries_btn = QPushButton("View Entries")
        view_entries_btn.clicked.connect(self.view_entries)
        view_entries_layout.addWidget(self.view_backlog_input)
        view_entries_layout.addWidget(view_entries_btn)
        self.entries_layout.addLayout(view_entries_layout)

        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(3)
        self.entries_table.setHorizontalHeaderLabels(["ID", "Game", "Status"])
        self.entries_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.entries_table.itemDoubleClicked.connect(self.show_entry_details)
        self.entries_layout.addWidget(self.entries_table)

        self.tabs.addTab(self.entries_widget, "Entries")

        # Sessions Tab
        self.sessions_widget = QWidget()
        self.sessions_layout = QVBoxLayout()
        self.sessions_widget.setLayout(self.sessions_layout)

        sessions_control_layout = QHBoxLayout()
        start_session_btn = QPushButton("Start Session")
        start_session_btn.clicked.connect(self.start_session)
        stop_session_btn = QPushButton("Stop Session")
        stop_session_btn.clicked.connect(self.stop_session)
        sessions_control_layout.addWidget(start_session_btn)
        sessions_control_layout.addWidget(stop_session_btn)
        self.sessions_layout.addLayout(sessions_control_layout)

        self.sessions_list = QListWidget()
        self.sessions_layout.addWidget(self.sessions_list)

        self.tabs.addTab(self.sessions_widget, "Sessions")

        # Initial refresh
        self.refresh_all()

    def create_backlog(self):
        title = self.backlog_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Error", "Title cannot be empty")
            return
        try:
            backlog = service.create_backlog(title)
            QMessageBox.information(
                self, "Success", f"Created backlog: {backlog.title}"
            )
            self.backlog_title_input.clear()
            self.refresh_backlogs()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh_backlogs(self):
        self.backlog_list.clear()
        backlogs = service.list_all_backlogs()
        for b in backlogs:
            entry_count = len(service.list_entries_in_backlog(b.id))
            self.backlog_list.addItem(f"{b.id}: {b.title} ({entry_count} games)")

    def show_backlog_details(self, item):
        backlog_id = int(item.text().split(":")[0])
        backlog = service.get_backlog(backlog_id)
        if not backlog:
            QMessageBox.warning(self, "Error", "Backlog not found")
            return
        entries = service.list_entries_in_backlog(backlog_id)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Backlog: {backlog.title}")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"📋 {backlog.title} ({len(entries)} games)"))
        for e in entries:
            md = service.metadata_repo.get_by_id(e.meta_data or 0)
            if md:
                status_str = format_status_priority(e.status, e.priority)
                layout.addWidget(QLabel(f"{e.id}: {md.title} - {status_str}"))
        delete_btn = QPushButton("Delete Backlog")
        delete_btn.clicked.connect(lambda: self.delete_backlog(backlog_id, dialog))
        layout.addWidget(delete_btn)
        dialog.setLayout(layout)
        dialog.exec()

    def delete_backlog(self, backlog_id, dialog):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this backlog? This will remove all entries.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = service.delete_backlog(backlog_id)
            QMessageBox.information(
                self,
                "Success" if success else "Error",
                "Deleted backlog" if success else "Failed to delete",
            )
            self.refresh_backlogs()
            dialog.accept()

    def add_game(self):
        title = self.game_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Error", "Title cannot be empty")
            return
        try:
            metadata = service.create_game_metadata(title)
            dialog = GameDialog(self, metadata)
            if dialog.exec():
                data = dialog.get_data()
                updated = service.update_game_metadata(metadata.id, data)
                QMessageBox.information(self, "Success", f"Added game: {updated.title}")
                self.game_title_input.clear()
                self.refresh_games()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh_games(self):
        self.games_list.clear()
        games = service.list_all_game_metadata()
        for g in games:
            desc = f" - {g.description[:30]}..." if g.description else ""
            self.games_list.addItem(f"{g.id}: {g.title}{desc}")

    def show_game_details(self, item):
        game_id = int(item.text().split(":")[0])
        game = service.get_game_metadata(game_id)
        if not game:
            QMessageBox.warning(self, "Error", "Game not found")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Game: {game.title}")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"🎮 {game.title}"))
        layout.addWidget(QLabel(f"ID: {game.id}"))
        if game.description:
            layout.addWidget(QLabel(f"Description: {game.description}"))
        if game.developer:
            layout.addWidget(QLabel(f"Developer: {game.developer}"))
        if game.publisher:
            layout.addWidget(QLabel(f"Publisher: {game.publisher}"))
        if game.avg_completion_time:
            layout.addWidget(
                QLabel(f"Completion Time: {game.avg_completion_time} hours")
            )

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.edit_game(game_id, dialog))
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.delete_game(game_id, dialog))
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        dialog.setLayout(layout)
        dialog.exec()

    def edit_game(self, game_id, parent_dialog):
        game = service.get_game_metadata(game_id)
        dialog = GameDialog(self, game)
        if dialog.exec():
            try:
                data = dialog.get_data()
                updated = service.update_game_metadata(game_id, data)
                QMessageBox.information(self, "Success", f"Updated: {updated.title}")
                self.refresh_games()
                parent_dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_game(self, game_id, dialog):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this game?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = service.delete_game_metadata(game_id)
            QMessageBox.information(
                self,
                "Success" if success else "Error",
                "Removed game" if success else "Failed to remove",
            )
            self.refresh_games()
            dialog.accept()

    def add_entry(self):
        game = get_game_by_fuzzy_match(self.entry_game_input.text().strip())
        backlog = get_backlog_by_fuzzy_match(self.entry_backlog_input.text().strip())
        if not game or not backlog:
            QMessageBox.warning(self, "Error", "Game or backlog not found")
            return
        try:
            service.add_game_to_backlog(backlog.id, game.id)
            QMessageBox.information(
                self, "Success", f"Added '{game.title}' to '{backlog.title}'"
            )
            self.entry_game_input.clear()
            self.entry_backlog_input.clear()
            if (
                self.view_backlog_input.text().strip() == str(backlog.id)
                or self.view_backlog_input.text().strip() == backlog.title
            ):
                self.view_entries()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def view_entries(self):
        backlog = get_backlog_by_fuzzy_match(self.view_backlog_input.text().strip())
        if not backlog:
            QMessageBox.warning(self, "Error", "Backlog not found")
            return
        entries = service.list_entries_in_backlog(backlog.id)
        self.entries_table.setRowCount(len(entries))
        for i, e in enumerate(entries):
            md = service.metadata_repo.get_by_id(e.meta_data or 0)
            if md:
                self.entries_table.setItem(i, 0, QTableWidgetItem(str(e.id)))
                self.entries_table.setItem(i, 1, QTableWidgetItem(md.title))
                self.entries_table.setItem(
                    i, 2, QTableWidgetItem(format_status_priority(e.status, e.priority))
                )
        self.entries_table.resizeColumnsToContents()

    def show_entry_details(self, item):
        row = item.row()
        entry_id = int(self.entries_table.item(row, 0).text())
        entry = service.entry_repo.get_by_id(entry_id)
        if not entry:
            return
        md = service.metadata_repo.get_by_id(entry.meta_data or 0)
        if not entry or not md:
            QMessageBox.warning(self, "Error", "Entry not found")
            return
        dialog = EntryDialog(self, entry, md.title)
        if dialog.exec():
            try:
                data = dialog.get_data()
                service.update_entry_status(entry_id, data["status"])
                service.update_entry_priority(entry_id, data["priority"])
                QMessageBox.information(self, "Success", "Entry updated")
                self.view_entries()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        delete_btn = QPushButton("Delete Entry")
        delete_btn.clicked.connect(lambda: self.delete_entry(entry_id, dialog))
        layout = dialog.layout()
        if not layout:
            return

        layout.addWidget(delete_btn)
        dialog.exec()

    def delete_entry(self, entry_id, dialog):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = service.delete_entry(entry_id)
            QMessageBox.information(
                self,
                "Success" if success else "Error",
                "Removed entry" if success else "Failed to remove",
            )
            self.view_entries()
            dialog.accept()

    def start_session(self):
        try:
            s = play_session_service.start_session()
            QMessageBox.information(
                self, "Success", f"Started session {s.id} at {s.session_start}"
            )
            self.refresh_sessions()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def stop_session(self):
        sessions = play_session_service.get_all_sessions()
        active = [s for s in sessions if s.session_end is None]
        if not active:
            QMessageBox.warning(self, "Error", "No active session to stop")
            return
        try:
            s = play_session_service.stop_session(active[0].id)
            QMessageBox.information(
                self, "Success", f"Stopped session {s.id} at {s.session_end}"
            )
            self.refresh_sessions()
        except PlaySessionError as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh_sessions(self):
        self.sessions_list.clear()
        sessions = play_session_service.get_all_sessions()
        for s in sessions:
            status = (
                "In Progress" if s.session_end is None else f"Ended: {s.session_end}"
            )
            self.sessions_list.addItem(f"{s.id}: Started {s.session_start} | {status}")

    def refresh_all(self):
        self.refresh_backlogs()
        self.refresh_games()
        self.refresh_sessions()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
