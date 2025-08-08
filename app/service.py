from modules.play_session.models import PlaySession
from modules.play_session.sqlmodels import PlaySessionModel
from modules.play_session.services import (
    PlaySessionService,
)
from modules.backlog.services import GameBacklogService
from modules.repositories.in_memory_repository import InMemoryRepository
from modules.backlog.models import (
    GameBacklog,
    GameBacklogEntry,
    GameMetadata,
)
from modules.backlog.sqlmodels import (
    GameBacklogEntryModel,
    GameBacklogModel,
    GameMetadataModel,
)
from modules.repositories.smol_sql_repository import SmolORMRepository

STORAGE = "smol_orm"

# Initialize repositories and services
if STORAGE == "smol_orm":
    backlog_repo = SmolORMRepository(GameBacklogModel, GameBacklog)
    entry_repo = SmolORMRepository(GameBacklogEntryModel, GameBacklogEntry)
    metadata_repo = SmolORMRepository(GameMetadataModel, GameMetadata)
    session_repo = SmolORMRepository(PlaySessionModel, PlaySession)
else:
    backlog_repo = InMemoryRepository()
    entry_repo = InMemoryRepository()
    metadata_repo = InMemoryRepository()
    session_repo = InMemoryRepository()

backlog_service = GameBacklogService(
    backlog_repo=backlog_repo,
    entry_repo=entry_repo,
    metadata_repo=metadata_repo,
)

play_session_service = PlaySessionService(session_repo)
