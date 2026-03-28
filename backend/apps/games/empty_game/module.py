from __future__ import annotations

from copy import deepcopy

from apps.games.types import (
    GameActionResult,
    GameActorContext,
    GameExecutionContext,
    GameSetupContext,
)


class EmptyGameGameModule:
    game_id = "empty_game"

    def validate_config(self, config: dict) -> None:
        # Keep it simple for now: no special config
        return None

    def build_initial_state(self, config: dict, context: GameSetupContext) -> dict:
        return {}

    def validate_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> None:
        return None

    def apply_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> GameActionResult:
        return GameActionResult(new_state=deepcopy(state))
