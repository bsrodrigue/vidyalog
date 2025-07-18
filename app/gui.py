import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Import your existing modules
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


class GameBacklogGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Backlog Manager")
        self.root.geometry("1000x700")

        # Initialize service
        self.setup_service()

        # Create GUI
        self.create_widgets()

        # Load initial data
        self.refresh_all_lists()

    def setup_service(self):
        """Initialize the service with repositories"""
        backlog_repo = LocalStorageRepository(InputGameBacklog, GameBacklog, "backlogs")
        entry_repo = LocalStorageRepository(
            InputGameBacklogEntry, GameBacklogEntry, "entries"
        )
        metadata_repo = LocalStorageRepository(
            InputGameMetadata, GameMetadata, "metadata"
        )

        self.service = GameBacklogService(
            backlog_repo=backlog_repo,
            entry_repo=entry_repo,
            metadata_repo=metadata_repo,
        )

    def create_widgets(self):
        """Create the main GUI layout"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_backlogs_tab()
        self.create_metadata_tab()
        self.create_entries_tab()

    def create_backlogs_tab(self):
        """Create the backlogs management tab"""
        # Backlogs tab
        backlogs_frame = ttk.Frame(self.notebook)
        self.notebook.add(backlogs_frame, text="Backlogs")

        # Top frame for controls
        controls_frame = ttk.Frame(backlogs_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            controls_frame, text="Create Backlog", command=self.create_backlog
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            controls_frame, text="Delete Backlog", command=self.delete_backlog
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Refresh", command=self.refresh_backlogs).pack(
            side=tk.LEFT, padx=5
        )

        # Backlogs listbox with scrollbar
        list_frame = ttk.Frame(backlogs_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.backlogs_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.backlogs_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.backlogs_listbox.yview)

        # Bind double-click to show details
        self.backlogs_listbox.bind("<Double-1>", self.show_backlog_details)

    def create_metadata_tab(self):
        """Create the game metadata management tab"""
        # Metadata tab
        metadata_frame = ttk.Frame(self.notebook)
        self.notebook.add(metadata_frame, text="Game Metadata")

        # Top frame for controls
        controls_frame = ttk.Frame(metadata_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            controls_frame, text="Create Metadata", command=self.create_metadata
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            controls_frame, text="Delete Metadata", command=self.delete_metadata
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Refresh", command=self.refresh_metadata).pack(
            side=tk.LEFT, padx=5
        )

        # Metadata listbox with scrollbar
        list_frame = ttk.Frame(metadata_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.metadata_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.metadata_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.metadata_listbox.yview)

        # Bind double-click to show details
        self.metadata_listbox.bind("<Double-1>", self.show_metadata_details)

    def create_entries_tab(self):
        """Create the entries management tab"""
        # Entries tab
        entries_frame = ttk.Frame(self.notebook)
        self.notebook.add(entries_frame, text="Backlog Entries")

        # Top frame for backlog selection
        selection_frame = ttk.Frame(entries_frame)
        selection_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(selection_frame, text="Select Backlog:").pack(side=tk.LEFT, padx=5)
        self.backlog_var = tk.StringVar()
        self.backlog_combo = ttk.Combobox(
            selection_frame, textvariable=self.backlog_var, state="readonly", width=30
        )
        self.backlog_combo.pack(side=tk.LEFT, padx=5)
        self.backlog_combo.bind("<<ComboboxSelected>>", self.on_backlog_selected)

        # Controls frame
        controls_frame = ttk.Frame(entries_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(controls_frame, text="Add Entry", command=self.add_entry).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            controls_frame, text="Update Status", command=self.update_entry_status
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            controls_frame, text="Update Priority", command=self.update_entry_priority
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Delete Entry", command=self.delete_entry).pack(
            side=tk.LEFT, padx=5
        )

        # Entries treeview
        tree_frame = ttk.Frame(entries_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview with columns
        self.entries_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Game", "Priority", "Status"),
            show="headings",
            height=15,
        )

        # Define column headings
        self.entries_tree.heading("ID", text="Entry ID")
        self.entries_tree.heading("Game", text="Game Title")
        self.entries_tree.heading("Priority", text="Priority")
        self.entries_tree.heading("Status", text="Status")

        # Configure column widths
        self.entries_tree.column("ID", width=80)
        self.entries_tree.column("Game", width=300)
        self.entries_tree.column("Priority", width=100)
        self.entries_tree.column("Status", width=100)

        # Add scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.entries_tree.yview
        )
        self.entries_tree.configure(yscrollcommand=tree_scrollbar.set)

        # Pack treeview and scrollbar
        self.entries_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_all_lists(self):
        """Refresh all data lists"""
        self.refresh_backlogs()
        self.refresh_metadata()
        self.refresh_backlog_combo()

    def refresh_backlogs(self):
        """Refresh the backlogs list"""
        self.backlogs_listbox.delete(0, tk.END)
        backlogs = self.service.list_all_backlogs()
        for backlog in backlogs:
            self.backlogs_listbox.insert(tk.END, f"ID: {backlog.id} | {backlog.title}")

    def refresh_metadata(self):
        """Refresh the metadata list"""
        self.metadata_listbox.delete(0, tk.END)
        metadata_list = self.service.list_all_game_metadata()
        for metadata in metadata_list:
            self.metadata_listbox.insert(
                tk.END, f"ID: {metadata.id} | {metadata.title}"
            )

    def refresh_backlog_combo(self):
        """Refresh the backlog selection combobox"""
        backlogs = self.service.list_all_backlogs()
        backlog_options = [f"ID: {b.id} | {b.title}" for b in backlogs]
        self.backlog_combo["values"] = backlog_options

    def create_backlog(self):
        """Create a new backlog"""
        title = simpledialog.askstring("Create Backlog", "Enter backlog title:")
        if title:
            try:
                backlog = self.service.create_backlog(title)
                messagebox.showinfo("Success", f"Backlog created with ID {backlog.id}")
                self.refresh_backlogs()
                self.refresh_backlog_combo()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create backlog: {e}")

    def delete_backlog(self):
        """Delete selected backlog"""
        selection = self.backlogs_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a backlog to delete")
            return

        selected_text = self.backlogs_listbox.get(selection[0])
        backlog_id = int(selected_text.split("|")[0].split(":")[1].strip())

        if messagebox.askyesno("Confirm", f"Delete backlog with ID {backlog_id}?"):
            try:
                success = self.service.delete_backlog(backlog_id)
                if success:
                    messagebox.showinfo("Success", "Backlog deleted")
                    self.refresh_backlogs()
                    self.refresh_backlog_combo()
                else:
                    messagebox.showerror("Error", "Backlog not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete backlog: {e}")

    def show_backlog_details(self, event):
        """Show details of selected backlog"""
        selection = self.backlogs_listbox.curselection()
        if not selection:
            return

        selected_text = self.backlogs_listbox.get(selection[0])
        backlog_id = int(selected_text.split("|")[0].split(":")[1].strip())

        try:
            backlog = self.service.get_backlog(backlog_id)
            if backlog:
                details = f"Backlog ID: {backlog.id}\nTitle: {backlog.title}\nEntries: {len(backlog.entries)}"
                messagebox.showinfo("Backlog Details", details)
            else:
                messagebox.showerror("Error", "Backlog not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get backlog details: {e}")

    def create_metadata(self):
        """Create new game metadata"""
        title = simpledialog.askstring("Create Metadata", "Enter game title:")
        if title:
            try:
                metadata = self.service.create_game_metadata(title=title)
                messagebox.showinfo(
                    "Success", f"Metadata created with ID {metadata.id}"
                )
                self.refresh_metadata()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create metadata: {e}")

    def delete_metadata(self):
        """Delete selected metadata"""
        selection = self.metadata_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select metadata to delete")
            return

        selected_text = self.metadata_listbox.get(selection[0])
        metadata_id = int(selected_text.split("|")[0].split(":")[1].strip())

        if messagebox.askyesno("Confirm", f"Delete metadata with ID {metadata_id}?"):
            try:
                success = self.service.delete_game_metadata(metadata_id)
                if success:
                    messagebox.showinfo("Success", "Metadata deleted")
                    self.refresh_metadata()
                else:
                    messagebox.showerror("Error", "Metadata not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete metadata: {e}")

    def show_metadata_details(self, event):
        """Show details of selected metadata"""
        selection = self.metadata_listbox.curselection()
        if not selection:
            return

        selected_text = self.metadata_listbox.get(selection[0])
        metadata_id = int(selected_text.split("|")[0].split(":")[1].strip())

        try:
            metadata = self.service.get_game_metadata(metadata_id)
            if metadata:
                details = f"Metadata ID: {metadata.id}\nTitle: {metadata.title}\nDescription: {metadata.description or 'No description'}"
                messagebox.showinfo("Metadata Details", details)
            else:
                messagebox.showerror("Error", "Metadata not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get metadata details: {e}")

    def on_backlog_selected(self, event):
        """Handle backlog selection change"""
        if self.backlog_var.get():
            self.refresh_entries()

    def refresh_entries(self):
        """Refresh entries for selected backlog"""
        # Clear current entries
        for item in self.entries_tree.get_children():
            self.entries_tree.delete(item)

        if not self.backlog_var.get():
            return

        # Get backlog ID from selection
        backlog_id = int(self.backlog_var.get().split("|")[0].split(":")[1].strip())

        try:
            entries = self.service.list_entries_in_backlog(backlog_id)
            for entry in entries:
                # Get game title from metadata
                metadata = self.service.get_game_metadata(entry.meta_data)
                game_title = metadata.title if metadata else "Unknown Game"

                # Insert entry into treeview
                self.entries_tree.insert(
                    "",
                    tk.END,
                    values=(
                        entry.id,
                        game_title,
                        entry.priority.name,
                        entry.status.name,
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load entries: {e}")

    def add_entry(self):
        """Add new entry to selected backlog"""
        if not self.backlog_var.get():
            messagebox.showwarning("Warning", "Please select a backlog first")
            return

        # Get backlog ID
        backlog_id = int(self.backlog_var.get().split("|")[0].split(":")[1].strip())

        # Create dialog for entry details
        dialog = EntryDialog(self.root, self.service)
        if dialog.result:
            try:
                entry = self.service.add_game_to_backlog(
                    backlog_id,
                    dialog.result["metadata_id"],
                    dialog.result["priority"],
                    dialog.result["status"],
                )
                messagebox.showinfo("Success", f"Entry added with ID {entry.id}")
                self.refresh_entries()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add entry: {e}")

    def update_entry_status(self):
        """Update status of selected entry"""
        selection = self.entries_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to update")
            return

        item = self.entries_tree.item(selection[0])
        entry_id = int(item["values"][0])

        # Create status selection dialog
        status_dialog = StatusDialog(self.root)
        if status_dialog.result:
            try:
                success = self.service.update_entry_status(
                    entry_id, status_dialog.result
                )
                if success:
                    messagebox.showinfo("Success", "Entry status updated")
                    self.refresh_entries()
                else:
                    messagebox.showerror("Error", "Entry not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update status: {e}")

    def update_entry_priority(self):
        """Update priority of selected entry"""
        selection = self.entries_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to update")
            return

        item = self.entries_tree.item(selection[0])
        entry_id = int(item["values"][0])

        # Create priority selection dialog
        priority_dialog = PriorityDialog(self.root)
        if priority_dialog.result:
            try:
                success = self.service.update_entry_priority(
                    entry_id, priority_dialog.result
                )
                if success:
                    messagebox.showinfo("Success", "Entry priority updated")
                    self.refresh_entries()
                else:
                    messagebox.showerror("Error", "Entry not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update priority: {e}")

    def delete_entry(self):
        """Delete selected entry"""
        selection = self.entries_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to delete")
            return

        item = self.entries_tree.item(selection[0])
        entry_id = int(item["values"][0])

        if messagebox.askyesno("Confirm", f"Delete entry with ID {entry_id}?"):
            try:
                success = self.service.delete_entry(entry_id)
                if success:
                    messagebox.showinfo("Success", "Entry deleted")
                    self.refresh_entries()
                else:
                    messagebox.showerror("Error", "Entry not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete entry: {e}")


class EntryDialog:
    """Dialog for creating new entries"""

    def __init__(self, parent, service):
        self.service = service
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Entry")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")

        self.create_widgets()

    def create_widgets(self):
        """Create dialog widgets"""
        # Game selection
        ttk.Label(self.dialog, text="Select Game:").pack(pady=5)
        self.game_var = tk.StringVar()
        self.game_combo = ttk.Combobox(
            self.dialog, textvariable=self.game_var, state="readonly", width=40
        )
        self.game_combo.pack(pady=5)

        # Load games
        metadata_list = self.service.list_all_game_metadata()
        game_options = [f"ID: {m.id} | {m.title}" for m in metadata_list]
        self.game_combo["values"] = game_options

        # Priority selection
        ttk.Label(self.dialog, text="Priority:").pack(pady=5)
        self.priority_var = tk.StringVar(value="P2")
        priority_frame = ttk.Frame(self.dialog)
        priority_frame.pack(pady=5)

        for priority in BacklogPriority:
            ttk.Radiobutton(
                priority_frame,
                text=priority.name,
                variable=self.priority_var,
                value=priority.name,
            ).pack(side=tk.LEFT, padx=5)

        # Status selection
        ttk.Label(self.dialog, text="Status:").pack(pady=5)
        self.status_var = tk.StringVar(value="INBOX")
        status_frame = ttk.Frame(self.dialog)
        status_frame.pack(pady=5)

        for status in BacklogStatus:
            ttk.Radiobutton(
                status_frame,
                text=status.name,
                variable=self.status_var,
                value=status.name,
            ).pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Add", command=self.add_entry).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

    def add_entry(self):
        """Add the entry"""
        if not self.game_var.get():
            messagebox.showwarning("Warning", "Please select a game")
            return

        metadata_id = int(self.game_var.get().split("|")[0].split(":")[1].strip())
        priority = BacklogPriority[self.priority_var.get()]
        status = BacklogStatus[self.status_var.get()]

        self.result = {
            "metadata_id": metadata_id,
            "priority": priority,
            "status": status,
        }

        self.dialog.destroy()


class StatusDialog:
    """Dialog for selecting status"""

    def __init__(self, parent):
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Status")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"300x200+{x}+{y}")

        self.create_widgets()

    def create_widgets(self):
        """Create dialog widgets"""
        ttk.Label(self.dialog, text="Select Status:").pack(pady=10)

        self.status_var = tk.StringVar(value="INBOX")
        status_frame = ttk.Frame(self.dialog)
        status_frame.pack(pady=10)

        for status in BacklogStatus:
            ttk.Radiobutton(
                status_frame,
                text=status.name,
                variable=self.status_var,
                value=status.name,
            ).pack(anchor=tk.W, padx=10)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

    def ok_clicked(self):
        """Handle OK button click"""
        self.result = BacklogStatus[self.status_var.get()]
        self.dialog.destroy()


class PriorityDialog:
    """Dialog for selecting priority"""

    def __init__(self, parent):
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Priority")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"300x200+{x}+{y}")

        self.create_widgets()

    def create_widgets(self):
        """Create dialog widgets"""
        ttk.Label(self.dialog, text="Select Priority:").pack(pady=10)

        self.priority_var = tk.StringVar(value="P2")
        priority_frame = ttk.Frame(self.dialog)
        priority_frame.pack(pady=10)

        for priority in BacklogPriority:
            ttk.Radiobutton(
                priority_frame,
                text=priority.name,
                variable=self.priority_var,
                value=priority.name,
            ).pack(anchor=tk.W, padx=10)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

    def ok_clicked(self):
        """Handle OK button click"""
        self.result = BacklogPriority[self.priority_var.get()]
        self.dialog.destroy()


def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = GameBacklogGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
