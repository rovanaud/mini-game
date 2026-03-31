from __future__ import annotations

from apps.games.base import GameBaseModule
from apps.games.types import (
    GameActionResult,
    GameActorContext,
    GameExecutionContext,
    GameMetadata,
    GameOutcome,
    GameSetupContext,
)


class EmptyGameModule(GameBaseModule):
    game_id: str = "empty_game"

    # GameDefinitionProvider
    def get_metadata(self) -> GameMetadata:
        return GameMetadata(
            game_id=self.game_id,
            display_name="Empty Game",
            min_players=1,
            max_players=400,
        )

    # GameConfigValidator
    def validate_config(self, config: dict) -> None: ...

    # GameStateFactory
    def build_initial_state(self, config: dict, context: GameSetupContext) -> dict: ...

    # GameActionValidator
    def validate_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> None: ...

    # GameActionReducer
    def apply_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> GameActionResult: ...

    # GameOutcomeResolver
    def resolve_outcome(
        self,
        state: dict,
        last_action_type: str,
        last_actor: GameActorContext,
    ) -> GameOutcome | None: ...

    # GameInterruptionPolicy
    def can_pause(self, state: dict, actor: GameActorContext) -> bool: ...
    def can_resume(self, state: dict, actor: GameActorContext) -> bool: ...
    def can_abandon(self, state: dict, actor: GameActorContext) -> bool: ...

    # GameVisibilityPolicy
    def filter_state_for_actor(self, state: dict, actor: GameActorContext) -> dict: ...

    # GameBotAdapter (optional — raise NotImplementedError if unsupported)
    def generate_bot_action(
        self,
        state: dict,
        bot_seat: GameActorContext,
        context: GameExecutionContext,
    ) -> tuple[str, dict]: ...
