from modules.enums.enums import BacklogPriority, BacklogStatus


class StatusPriorityFormatter:
    STATUS_ICONS = {
        BacklogStatus.INBOX: "📥",
        BacklogStatus.PLAYING: "🎮",
        BacklogStatus.FINISHED: "✅",
        BacklogStatus.ABANDONED: "❌",
        BacklogStatus.PAUSED: "⏸️",
    }

    PRIORITY_ICONS = {
        BacklogPriority.P0: "🔴",
        BacklogPriority.P1: "🟡",
        BacklogPriority.P2: "🟢",
        BacklogPriority.P3: "⚪",
    }

    @staticmethod
    def fmt(status: BacklogStatus, priority: BacklogPriority) -> str:
        return f"{StatusPriorityFormatter.STATUS_ICONS.get(status, '❓')} {status.name} | {StatusPriorityFormatter.PRIORITY_ICONS.get(priority, '❓')} {priority.name}"
