from modules.backlog.models import (
    GameBacklog,
    GameBacklogEntry,
    GameBacklogEntryPersistenceModel,
    GameBacklogPersistenceModel,
    GameMetadata,
    GameMetadataPersistenceModel,
)


class GameBacklogEntryMapper:
    @staticmethod
    def to_persistence(
        game_backlog_entry: GameBacklogEntry,
    ) -> GameBacklogEntryPersistenceModel:
        return GameBacklogEntryPersistenceModel(
            **game_backlog_entry.model_dump(exclude_unset=True)
        )

    @staticmethod
    def to_domain(
        game_backlog_entry: GameBacklogEntryPersistenceModel,
    ) -> GameBacklogEntry:
        return GameBacklogEntry(**game_backlog_entry.model_dump())


class GameBacklogMapper:
    @staticmethod
    def to_persistence(backlog: GameBacklog) -> GameBacklogPersistenceModel:
        return GameBacklogPersistenceModel(**backlog.model_dump(exclude_unset=True))

    @staticmethod
    def to_domain(backlog: GameBacklogPersistenceModel) -> GameBacklog:
        return GameBacklog(**backlog.model_dump())


class GameMetadataMapper:
    @staticmethod
    def to_persistence(
        game_metadata: GameMetadata,
    ) -> GameMetadataPersistenceModel:
        return GameMetadataPersistenceModel(
            **game_metadata.model_dump(exclude_unset=True)
        )

    @staticmethod
    def to_domain(game_metadata: GameMetadataPersistenceModel) -> GameMetadata:
        return GameMetadata(**game_metadata.model_dump())
