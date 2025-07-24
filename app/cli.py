from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import confirm, prompt
from prompt_toolkit.formatted_text import HTML
from typing import Optional

from modules.play_session.services import (
    PlaySessionError,
    PlaySessionService,
)
from modules.backlog.services import GameBacklogService
from modules.repositories.in_memory_repository import InMemoryRepository
from modules.backlog.models import BacklogPriority, BacklogStatus

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

play_session_service = PlaySessionService(session_repo)

# Enhanced command structure with aliases and descriptions
COMMANDS = {
    # Backlog management
    "new": {
        "aliases": ["n", "create"],
        "desc": "Create a new backlog",
        "category": "Backlog",
    },
    "list": {
        "aliases": ["l", "ls"],
        "desc": "List all backlogs",
        "category": "Backlog",
    },
    "show": {
        "aliases": ["s", "view"],
        "desc": "Show backlog details",
        "category": "Backlog",
    },
    "delete": {
        "aliases": ["del", "rm"],
        "desc": "Delete a backlog",
        "category": "Backlog",
    },
    # Game metadata management
    "add-game": {
        "aliases": ["ag", "game"],
        "desc": "Add a new game",
        "category": "Games",
    },
    "games": {
        "aliases": ["g", "list-games"],
        "desc": "List all games",
        "category": "Games",
    },
    "game-info": {
        "aliases": ["gi", "info"],
        "desc": "Show game details",
        "category": "Games",
    },
    "edit-game": {
        "aliases": ["eg", "edit"],
        "desc": "Edit game details",
        "category": "Games",
    },
    "remove-game": {
        "aliases": ["rg", "remove"],
        "desc": "Remove a game",
        "category": "Games",
    },
    # Entry management
    "add": {
        "aliases": ["a", "add-to"],
        "desc": "Add game to backlog",
        "category": "Entries",
    },
    "entries": {
        "aliases": ["e", "list-entries"],
        "desc": "List entries in backlog",
        "category": "Entries",
    },
    "done": {
        "aliases": ["d", "complete"],
        "desc": "Mark entry as completed",
        "category": "Entries",
    },
    "playing": {
        "aliases": ["p", "start"],
        "desc": "Mark entry as currently playing",
        "category": "Entries",
    },
    "priority": {
        "aliases": ["pri", "prio"],
        "desc": "Change entry priority",
        "category": "Entries",
    },
    "status": {"aliases": ["st"], "desc": "Change entry status", "category": "Entries"},
    "drop": {
        "aliases": ["drop-entry"],
        "desc": "Remove entry from backlog",
        "category": "Entries",
    },
    # Session management
    "session": {
        "aliases": ["sess"],
        "desc": "Start a play session",
        "category": "Sessions",
    },
    "stop": {
        "aliases": ["end"],
        "desc": "Stop current session",
        "category": "Sessions",
    },
    "sessions": {
        "aliases": ["history"],
        "desc": "Show session history",
        "category": "Sessions",
    },
    # Utility
    "help": {"aliases": ["h", "?"], "desc": "Show this help", "category": "Utility"},
    "clear": {"aliases": ["cls"], "desc": "Clear screen", "category": "Utility"},
    "exit": {
        "aliases": ["quit", "q"],
        "desc": "Exit the application",
        "category": "Utility",
    },
}

# Create completer with all commands and aliases
all_commands = []
for cmd, info in COMMANDS.items():
    all_commands.append(cmd)
    all_commands.extend(info["aliases"])

cli_completer = WordCompleter(all_commands, ignore_case=True)
session = PromptSession(history=InMemoryHistory())


def print_welcome():
    """Print welcome message with quick start guide"""
    print("🎮 Welcome to GameBacklog CLI")
    print("=" * 50)
    print("Quick start:")
    print("  • Type 'help' for all commands")
    print("  • Type 'new My Backlog' to create your first backlog")
    print("  • Type 'add-game Game Title' to add a game")
    print("  • Type 'exit' to quit")
    print("=" * 50)


def print_help():
    """Print organized help with categories"""
    print("\n📖 Available Commands:")
    print("=" * 60)

    categories = {}
    for cmd, info in COMMANDS.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []

        aliases = ", ".join(info["aliases"][:2])  # Show first 2 aliases
        categories[cat].append(f"  {cmd:<12} ({aliases:<8}) - {info['desc']}")

    for category, cmds in categories.items():
        print(f"\n{category}:")
        for cmd in cmds:
            print(cmd)

    print("\n💡 Tips:")
    print("  • Most commands work with partial names (e.g., 'l' for list)")
    print("  • Use Tab for auto-completion")
    print("  • Commands are case-insensitive")
    print("=" * 60)


def resolve_command(cmd: str) -> Optional[str]:
    """Resolve command aliases to main command"""
    cmd = cmd.lower()

    # Direct match
    if cmd in COMMANDS:
        return cmd

    # Check aliases
    for main_cmd, info in COMMANDS.items():
        if cmd in [alias.lower() for alias in info["aliases"]]:
            return main_cmd

    return None


def format_status_priority(status: BacklogStatus, priority: BacklogPriority) -> str:
    """Format status and priority with colors/emojis"""
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


def handle_command(command: str):
    """Enhanced command handler with better UX"""
    if not command.strip():
        return

    parts = command.strip().split()
    main_cmd = resolve_command(parts[0])
    args = parts[1:] if len(parts) > 1 else []

    if not main_cmd:
        print(f"❌ Unknown command: '{parts[0]}'. Type 'help' for available commands.")
        return

    try:
        # Backlog management
        if main_cmd == "new":
            title = " ".join(args) if args else prompt("Backlog title: ")
            if not title.strip():
                print("❌ Title cannot be empty")
                return
            backlog = service.create_backlog(title)
            print(f"✅ Created backlog: {backlog.id} - {backlog.title}")

        elif main_cmd == "list":
            backlogs = service.list_all_backlogs()
            if not backlogs:
                print("📝 No backlogs found. Create one with 'new <title>'")
                return

            print(f"\n📋 Your Backlogs ({len(backlogs)}):")
            for b in backlogs:
                entry_count = len(service.list_entries_in_backlog(b.id))
                print(f"  {b.id}: {b.title} ({entry_count} games)")

        elif main_cmd == "show":
            if not args:
                print("Usage: show <backlog_id_or_name>")
                return

            backlog = service.get_backlog_by_fuzzy_match(args[0])
            if not backlog:
                return

            entries = service.list_entries_in_backlog(backlog.id)
            print(f"\n📋 {backlog.title} ({len(entries)} games)")
            print("-" * 50)

            if not entries:
                print(
                    "  No games in this backlog yet. Add some with 'add <game> <backlog>'"
                )
                return

            for e in entries:
                md = service.metadata_repo.get_by_id(e.meta_data or 0)
                if md:
                    status_str = format_status_priority(e.status, e.priority)
                    print(f"  {e.id}: {md.title}")
                    print(f"      {status_str}")

        elif main_cmd == "delete":
            if not args:
                print("Usage: delete <backlog_id_or_name>")
                return

            backlog = service.get_backlog_by_fuzzy_match(args[0])
            if not backlog:
                return

            if confirm(
                f"Delete backlog '{backlog.title}'? This will remove all entries."
            ):
                success = service.delete_backlog(backlog.id)
                print("✅ Deleted backlog" if success else "❌ Failed to delete")

        # Game management
        elif main_cmd == "add-game":
            title = " ".join(args) if args else prompt("Game title: ")
            if not title.strip():
                print("❌ Title cannot be empty")
                return

            metadata = service.create_game_metadata(title=title)
            print(f"✅ Added game: {metadata.id} - {metadata.title}")

            # Ask if they want to add more details
            if confirm("Add more details? (description, etc.)"):
                handle_command(f"edit-game {metadata.id}")

        elif main_cmd == "games":
            games = service.list_all_game_metadata()
            if not games:
                print("🎮 No games found. Add some with 'add-game <title>'")
                return

            print(f"\n🎮 Your Games ({len(games)}):")
            for g in games:
                desc = f" - {g.description[:50]}..." if g.description else ""
                print(f"  {g.id}: {g.title}{desc}")

        elif main_cmd == "game-info":
            if not args:
                print("Usage: game-info <game_id_or_name>")
                return

            game = service.get_game_by_fuzzy_match(args[0])
            if not game:
                return

            print(f"\n🎮 {game.title}")
            print("-" * 50)
            print(f"ID: {game.id}")
            if game.description:
                print(f"Description: {game.description}")
            if game.developer:
                print(f"Developer: {game.developer}")
            if game.publisher:
                print(f"Publisher: {game.publisher}")
            if game.avg_completion_time:
                print(f"Completion Time: {game.avg_completion_time} hours")

        elif main_cmd == "edit-game":
            if not args:
                print("Usage: edit-game <game_id_or_name>")
                return

            game = service.get_game_by_fuzzy_match(args[0])
            if not game:
                return

            print(f"Editing: {game.title}")
            title = prompt("Title: ", default=game.title)
            desc = prompt("Description: ", default=game.description or "")
            developer = prompt("Developer: ", default=game.developer or "")
            publisher = prompt("Publisher: ", default=game.publisher or "")

            try:
                completion_time = prompt(
                    "Avg completion time (hours): ",
                    default=str(game.avg_completion_time)
                    if game.avg_completion_time
                    else "",
                )
                completion_time = float(completion_time) if completion_time else 0
            except ValueError:
                completion_time = game.avg_completion_time

            updated = service.update_game_metadata(
                game.id,
                {
                    "title": title,
                    "description": desc,
                    "developer": developer,
                    "publisher": publisher,
                    "avg_completion_time": completion_time,
                },
            )
            print(f"✅ Updated: {updated.title}")

        elif main_cmd == "remove-game":
            if not args:
                print("Usage: remove-game <game_id_or_name>")
                return

            game = service.get_game_by_fuzzy_match(args[0])
            if not game:
                return

            if confirm(f"Remove game '{game.title}'?"):
                success = service.delete_game_metadata(game.id)
                print("✅ Removed game" if success else "❌ Failed to remove")

        # Entry management
        elif main_cmd == "add":
            if len(args) < 2:
                print("Usage: add <game> <backlog>")
                print("Example: add 'Zelda' 'My Backlog'")
                return

            game = service.get_game_by_fuzzy_match(args[0])
            backlog = service.get_backlog_by_fuzzy_match(args[1])

            if not game or not backlog:
                return

            service.add_game_to_backlog(backlog.id, game.id)
            print(f"✅ Added '{game.title}' to '{backlog.title}'")

        elif main_cmd == "entries":
            if not args:
                # Show Default Backlog
                backlogs = service.backlog_repo.list_all()
                if len(backlogs) == 0:
                    print("No Backlogs found")
                    return

                default_backlog = backlogs[0]
                handle_command(f"show {default_backlog.id}")
                return

            backlog = service.get_backlog_by_fuzzy_match(args[0])
            if not backlog:
                return

            handle_command(f"show {backlog.id}")

        elif main_cmd == "done":
            if not args:
                print("Usage: done <entry_id>")
                return

            try:
                entry = int(args[0])
                updated = service.update_entry_status(entry, BacklogStatus.FINISHED)
                print("✅ Marked as completed!" if updated else "❌ Entry not found")
            except ValueError:
                print("❌ Invalid entry ID")

        elif main_cmd == "playing":
            if not args:
                print("Usage: playing <entry_id>")
                return

            try:
                entry = int(args[0])
                updated = service.update_entry_status(entry, BacklogStatus.PLAYING)
                print("🎮 Started playing!" if updated else "❌ Entry not found")
            except ValueError:
                print("❌ Invalid entry ID")

        elif main_cmd == "priority":
            if len(args) < 2:
                print("Usage: priority <entry_id> <1-4>")
                print("Priority levels: 1=High, 2=Medium, 3=Normal, 4=Low")
                return

            try:
                entry = int(args[0])
                priority_num = int(args[1])
                priority_map = {
                    0: BacklogPriority.P0,
                    1: BacklogPriority.P1,
                    2: BacklogPriority.P2,
                    3: BacklogPriority.P3,
                }

                if priority_num not in priority_map:
                    print("❌ Priority must be 1-4")
                    return

                updated = service.update_entry_priority(
                    entry, priority_map[priority_num]
                )
                print("✅ Priority updated!" if updated else "❌ Entry not found")
            except ValueError:
                print("❌ Invalid entry ID or priority")

        # Session management
        elif main_cmd == "session":
            if len(args) < 1:
                print("Usage: session <backlog_entry>")
                print("Example: session 'Zelda'")
                return

            try:
                entry = args[0]

                entry = service.get_entry_by_fuzzy_match(entry)

                if not entry:
                    print(f"Entry {entry} not found")
                    return

                s = play_session_service.start_session(entry.id)
                print(f"⏱️ Started session {s.id} at {s.session_start}")
            except Exception as e:
                print(f"❌ Error: {e}")

        elif main_cmd == "stop":
            if not args:
                # Find active session
                sessions = play_session_service.get_all_sessions()
                active = [s for s in sessions if s.session_end is None]
                if not active:
                    print("No active session to stop")
                    return
                session_id = active[0].id
            else:
                try:
                    session_id = int(args[0])
                except ValueError:
                    print("❌ Invalid session ID")
                    return

            try:
                s = play_session_service.stop_session(session_id)
                print(f"⏹️ Stopped session {s.id} at {s.session_end}")
            except PlaySessionError as e:
                print(f"❌ Error: {e}")

        elif main_cmd == "sessions":
            sessions = play_session_service.get_all_sessions()
            if not sessions:
                print("📊 No sessions found. Start one with 'session'")
                return

            print(f"\n📊 Play Sessions ({len(sessions)}):")
            for s in sessions:
                entry = service.get_entry(s.backlog_entry)
                if not entry:  # Can't we avoid constant checking?
                    return
                meta_data = service.get_game_metadata(entry.meta_data)
                if not meta_data:
                    return
                print(f"Game:{meta_data.title}|{s}")

        # Utility commands
        elif main_cmd == "help":
            print_help()

        elif main_cmd == "clear":
            import os

            os.system("cls" if os.name == "nt" else "clear")

        elif main_cmd == "exit":
            if confirm("Exit GameBacklog CLI?"):
                print("👋 Thanks for using GameBacklog CLI!")
                return "EXIT"

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Type 'help' if you need assistance with commands")


def main_loop():
    """Enhanced main loop with better error handling"""
    print_welcome()

    while True:
        try:
            command = session.prompt(
                HTML("<ansi color='cyan'>gback></ansi> "), completer=cli_completer
            )

            result = handle_command(command)
            if result == "EXIT":
                break

        except KeyboardInterrupt:
            print("\n(Use 'exit' to quit)")
            continue
        except EOFError:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("Please report this issue if it persists.")


if __name__ == "__main__":
    main_loop()
