from modules.backlog.services import GameBacklogService
from modules.repositories.repositories import LocalStorageRepository
from modules.backlog.models import (
    GameBacklog,
    GameBacklogEntry,
    GameMetadata,
    InputGameBacklog,
    InputGameBacklogEntry,
    InputGameMetadata,
)
from modules.backlog.models import BacklogPriority, BacklogStatus


def main():
    print("Welcome to Game Backlog Manager!")
    print("Type 'help' to see available commands.\n")

    backlog_repo = LocalStorageRepository(InputGameBacklog, GameBacklog, "backlogs")
    entry_repo = LocalStorageRepository(
        InputGameBacklogEntry, GameBacklogEntry, "entries"
    )
    metadata_repo = LocalStorageRepository(InputGameMetadata, GameMetadata, "metadata")

    service = GameBacklogService(
        backlog_repo=backlog_repo,
        entry_repo=entry_repo,
        metadata_repo=metadata_repo,
    )

    def show_help():
        print(
            "Commands:\n"
            "  create backlog <title>               - Create a new backlog\n"
            "  list backlogs                       - List all backlogs\n"
            "  show backlog <id>                   - Show backlog details\n"
            "  delete backlog <id>                 - Delete a backlog\n"
            "  create metadata <title>             - Create game metadata\n"
            "  list metadata                      - List all metadata\n"
            "  show metadata <id>                  - Show metadata details\n"
            "  delete metadata <id>                - Delete metadata\n"
            "  add entry <backlog_id> <metadata_id> [priority] [status] - Add entry to backlog\n"
            "  list entries <backlog_id>           - List all entries in backlog\n"
            "  update entry status <entry_id> <status>   - Update entry status\n"
            "  update entry priority <entry_id> <priority> - Update entry priority\n"
            "  delete entry <entry_id>             - Delete an entry\n"
            "  help                              - Show this message\n"
            "  exit                              - Exit\n"
        )

    while True:
        command = input("Enter command: ").strip()
        if not command:
            continue
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()

        try:
            if cmd == "exit":
                print("Exiting...")
                break

            elif cmd == "help":
                show_help()

            elif cmd == "create" and len(cmd_parts) >= 3:
                if cmd_parts[1].lower() == "backlog":
                    title = " ".join(cmd_parts[2:])
                    backlog = service.create_backlog(title)
                    print(f"Backlog created with ID {backlog.id}")

                elif cmd_parts[1].lower() == "metadata":
                    title = " ".join(cmd_parts[2:])
                    metadata = service.create_game_metadata(title=title)
                    print(f"Metadata created with ID {metadata.id}")

                else:
                    print(
                        "Unknown create target. Use 'create backlog <title>' or 'create metadata <title>'."
                    )

            elif cmd == "list" and len(cmd_parts) == 2:
                if cmd_parts[1].lower() == "backlogs":
                    backlogs = service.list_all_backlogs()
                    if not backlogs:
                        print("No backlogs found.")
                    else:
                        for b in backlogs:
                            print(f"ID: {b.id} | Title: {b.title}")

                elif cmd_parts[1].lower() == "metadata":
                    metadata_list = service.list_all_game_metadata()
                    if not metadata_list:
                        print("No metadata found.")
                    else:
                        for m in metadata_list:
                            print(f"ID: {m.id} | Title: {m.title}")

                else:
                    print(
                        "Unknown list target. Use 'list backlogs' or 'list metadata'."
                    )

            elif cmd == "show" and len(cmd_parts) == 3:
                target = cmd_parts[1].lower()
                try:
                    id_ = int(cmd_parts[2])
                except ValueError:
                    print("ID must be an integer.")
                    continue

                if target == "backlog":
                    backlog = service.get_backlog(id_)
                    if backlog:
                        print(
                            f"Backlog ID: {backlog.id}\nTitle: {backlog.title}\nEntries: {backlog.entries}"
                        )
                    else:
                        print("Backlog not found.")

                elif target == "metadata":
                    metadata = service.get_game_metadata(id_)
                    if metadata:
                        print(
                            f"Metadata ID: {metadata.id}\nTitle: {metadata.title}\nDescription: {metadata.description}"
                        )
                    else:
                        print("Metadata not found.")

                else:
                    print(
                        "Unknown show target. Use 'show backlog <id>' or 'show metadata <id>'."
                    )

            elif cmd == "delete" and len(cmd_parts) == 3:
                target = cmd_parts[1].lower()
                try:
                    id_ = int(cmd_parts[2])
                except ValueError:
                    print("ID must be an integer.")
                    continue

                if target == "backlog":
                    success = service.delete_backlog(id_)
                    print("Backlog deleted." if success else "Backlog not found.")

                elif target == "metadata":
                    success = service.delete_game_metadata(id_)
                    print("Metadata deleted." if success else "Metadata not found.")

                elif target == "entry":
                    success = service.delete_entry(id_)
                    print("Entry deleted." if success else "Entry not found.")

                else:
                    print(
                        "Unknown delete target. Use 'delete backlog <id>', 'delete metadata <id>', or 'delete entry <id>'."
                    )

            elif cmd == "add" and len(cmd_parts) >= 4:
                if cmd_parts[1].lower() == "entry":
                    try:
                        backlog_id = int(cmd_parts[2])
                        metadata_id = int(cmd_parts[3])
                    except ValueError:
                        print("Backlog ID and Metadata ID must be integers.")
                        continue

                    priority = BacklogPriority.P2
                    status = BacklogStatus.INBOX

                    if len(cmd_parts) > 4:
                        try:
                            priority = BacklogPriority[cmd_parts[4].upper()]
                        except KeyError:
                            print(
                                f"Unknown priority '{cmd_parts[4]}', using default P2."
                            )

                    if len(cmd_parts) > 5:
                        try:
                            status = BacklogStatus[cmd_parts[5].upper()]
                        except KeyError:
                            print(
                                f"Unknown status '{cmd_parts[5]}', using default INBOX."
                            )

                    try:
                        entry = service.add_game_to_backlog(
                            backlog_id, metadata_id, priority, status
                        )
                        print(f"Entry added with ID {entry.id}")
                    except ValueError as e:
                        print(str(e))

                else:
                    print(
                        "Unknown add target. Use 'add entry <backlog_id> <metadata_id> [priority] [status]'."
                    )

            elif (
                cmd == "list"
                and len(cmd_parts) == 3
                and cmd_parts[1].lower() == "entries"
            ):
                try:
                    backlog_id = int(cmd_parts[2])
                except ValueError:
                    print("Backlog ID must be an integer.")
                    continue

                entries = service.list_entries_in_backlog(backlog_id)
                if not entries:
                    print("No entries found or backlog does not exist.")
                else:
                    for e in entries:
                        print(
                            f"ID: {e.id} | MetaData ID: {e.meta_data} | Priority: {e.priority.name} | Status: {e.status.name}"
                        )

            elif cmd == "update" and len(cmd_parts) == 5:
                target = cmd_parts[1].lower()
                if target == "entry":
                    try:
                        entry_id = int(cmd_parts[3])
                    except ValueError:
                        print("Entry ID must be an integer.")
                        continue

                    field = cmd_parts[2].lower()
                    value = cmd_parts[4]

                    if field == "status":
                        try:
                            status = BacklogStatus[value.upper()]
                        except KeyError:
                            print(f"Unknown status '{value}'.")
                            continue
                        updated = service.update_entry_status(entry_id, status)
                        if updated:
                            print(f"Entry {entry_id} status updated to {status.name}.")
                        else:
                            print("Entry not found.")

                    elif field == "priority":
                        try:
                            priority = BacklogPriority[value.upper()]
                        except KeyError:
                            print(f"Unknown priority '{value}'.")
                            continue
                        updated = service.update_entry_priority(entry_id, priority)
                        if updated:
                            print(
                                f"Entry {entry_id} priority updated to {priority.name}."
                            )
                        else:
                            print("Entry not found.")

                    else:
                        print(
                            "Unknown update field. Use 'update entry status <entry_id> <status>' or 'update entry priority <entry_id> <priority>'."
                        )

                else:
                    print("Unknown update target. Use 'update entry ...'.")

            else:
                print("Unknown command. Type 'help' to see available commands.")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
