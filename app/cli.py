import typer

from modules.play_session_timer.services import (
    PlaySessionError,
    PlaySessionTimerService,
)
from modules.play_session_timer.models import InputPlaySession, PlaySession
from modules.backlog.services import GameBacklogService
from modules.repositories.repositories import LocalStorageRepository
from modules.backlog.models import (
    GameBacklog,
    GameBacklogEntry,
    GameMetadata,
    InputGameBacklog,
    InputGameBacklogEntry,
    InputGameMetadata,
    BacklogPriority,
    BacklogStatus,
)

app = typer.Typer()

# Repository and service setup
backlog_repo = LocalStorageRepository(InputGameBacklog, GameBacklog, "backlogs")
entry_repo = LocalStorageRepository(InputGameBacklogEntry, GameBacklogEntry, "entries")
metadata_repo = LocalStorageRepository(InputGameMetadata, GameMetadata, "metadata")
session_repo = LocalStorageRepository(InputPlaySession, PlaySession, "play_sessions")


service = GameBacklogService(
    backlog_repo=backlog_repo,
    entry_repo=entry_repo,
    metadata_repo=metadata_repo,
)

play_session_service = PlaySessionTimerService(session_repo)


# ----------------------------------------
# BACKLOG COMMANDS
# ----------------------------------------
@app.command("create-backlog")
def create_backlog(title: str):
    backlog = service.create_backlog(title)
    typer.echo(f"Backlog created with ID {backlog.id}")


@app.command("list-backlogs")
def list_backlogs():
    backlogs = service.list_all_backlogs()
    if not backlogs:
        typer.echo("No backlogs found.")
    else:
        for b in backlogs:
            typer.echo(f"ID: {b.id} | Title: {b.title}")


@app.command("show-backlog")
def show_backlog(id: int):
    backlog = service.get_backlog(id)
    if backlog:
        typer.echo(
            f"Backlog ID: {backlog.id}\nTitle: {backlog.title}\nEntries: {backlog.entries}"
        )
    else:
        typer.echo("Backlog not found.")


@app.command("delete-backlog")
def delete_backlog(id: int):
    success = service.delete_backlog(id)
    typer.echo("Backlog deleted." if success else "Backlog not found.")


# ----------------------------------------
# METADATA COMMANDS
# ----------------------------------------
@app.command("create-metadata")
def create_metadata(title: str):
    metadata = service.create_game_metadata(title=title)
    typer.echo(f"Metadata created with ID {metadata.id}")


@app.command("list-metadata")
def list_metadata():
    metadata_list = service.list_all_game_metadata()
    if not metadata_list:
        typer.echo("No metadata found.")
    else:
        for m in metadata_list:
            typer.echo(f"ID: {m.id} | Title: {m.title}")


@app.command("show-metadata")
def show_metadata(id: int):
    metadata = service.get_game_metadata(id)
    if metadata:
        typer.echo(
            f"Metadata ID: {metadata.id}\nTitle: {metadata.title}\nDescription: {metadata.description}"
        )
    else:
        typer.echo("Metadata not found.")


@app.command("delete-metadata")
def delete_metadata(id: int):
    success = service.delete_game_metadata(id)
    typer.echo("Metadata deleted." if success else "Metadata not found.")


# ----------------------------------------
# ENTRY COMMANDS
# ----------------------------------------
@app.command("add-entry")
def add_entry(
    backlog_id: int,
    metadata_id: int,
    priority: BacklogPriority = BacklogPriority.P2,
    status: BacklogStatus = BacklogStatus.INBOX,
):
    try:
        entry = service.add_game_to_backlog(backlog_id, metadata_id, priority, status)
        typer.echo(f"Entry added with ID {entry.id}")
    except ValueError as e:
        typer.echo(f"Error: {e}")


@app.command("list-entries")
def list_entries(backlog_id: int):
    entries = service.list_entries_in_backlog(backlog_id)
    if not entries:
        typer.echo("No entries found or backlog does not exist.")
    else:
        for e in entries:
            typer.echo(
                f"ID: {e.id} | MetaData ID: {e.meta_data} | Priority: {e.priority.name} | Status: {e.status.name}"
            )


@app.command("update-entry-status")
def update_entry_status(entry_id: int, status: BacklogStatus):
    updated = service.update_entry_status(entry_id, status)
    if updated:
        typer.echo(f"Entry {entry_id} status updated to {status.name}.")
    else:
        typer.echo("Entry not found.")


@app.command("update-entry-priority")
def update_entry_priority(entry_id: int, priority: BacklogPriority):
    updated = service.update_entry_priority(entry_id, priority)
    if updated:
        typer.echo(f"Entry {entry_id} priority updated to {priority.name}.")
    else:
        typer.echo("Entry not found.")


@app.command("delete-entry")
def delete_entry(entry_id: int):
    success = service.delete_entry(entry_id)
    typer.echo("Entry deleted." if success else "Entry not found.")


# ----------------------------------------
# PLAY SESSION COMMANDS
# ----------------------------------------


@app.command("start-session")
def start_session():
    """Start a new play session."""
    session = play_session_service.start_session()
    typer.echo(f"Started session {session.id} at {session.session_start}")


@app.command("stop-session")
def stop_session(session_id: int):
    """Stop a running play session by ID."""
    try:
        session = play_session_service.stop_session(session_id)
        typer.echo(f"Stopped session {session.id} at {session.session_end}")
    except PlaySessionError as e:
        typer.echo(f"Error: {e}")


@app.command("list-sessions")
def list_sessions():
    """List all play sessions."""
    sessions = play_session_service.get_all_sessions()
    if not sessions:
        typer.echo("No play sessions found.")
    else:
        for s in sessions:
            typer.echo(
                f"ID: {s.id} | Start: {s.session_start} | End: {s.session_end or 'In Progress'}"
            )


if __name__ == "__main__":
    app()
