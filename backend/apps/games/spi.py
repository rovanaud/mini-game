from __future__ import annotations

from typing import Protocol

from apps.games.types import (
    GameActionResult,
    GameActorContext,
    GameExecutionContext,
    GameSetupContext,
)


class GameModule(Protocol):
    game_id: str

    def validate_config(self, config: dict) -> None: ...

    def build_initial_state(self, config: dict, context: GameSetupContext) -> dict: ...

    def validate_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> None: ...

    def apply_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> GameActionResult: ...
