from __future__ import annotations

from apps.games.types import (
    GameActorContext,
    GameExecutionContext,
    GameMetadata,
    GameOutcome,
    GameSetupContext,
)


class GameBaseModule:
    """
    Default implementations for optional SPI methods.
    Concrete game modules should inherit this and override what they need.
    """

    game_id: str = ""

    def get_metadata(self) -> GameMetadata:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_metadata()"
        )

    def validate_config(self, config: dict) -> None:
        pass  # No config constraints by default

    def build_initial_state(self, config: dict, context: GameSetupContext) -> dict:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build_initial_state()"
        )

    def validate_action(
        self, state, action_type, action_payload, actor, context
    ) -> None:
        # resign is a universal action type — always structurally valid
        # games may override to restrict it (e.g. forbidden in tournament finals)
        if action_type == "resign":
            return
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement validate_action()"
        )

    def apply_action(self, state, action_type, action_payload, actor, context):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement apply_action()"
        )

    def resolve_outcome(
        self,
        state: dict,
        last_action_type: str,
        last_actor: GameActorContext,
    ) -> GameOutcome | None:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement resolve_outcome()"
        )

    # --- InterruptionPolicy defaults ---

    def can_pause(self, state: dict, actor: GameActorContext) -> bool:
        return False

    def can_resume(self, state: dict, actor: GameActorContext) -> bool:
        return False

    def can_abandon(self, state: dict, actor: GameActorContext) -> bool:
        return True  # abandon is always allowed by default

    # --- VisibilityPolicy default: full state, no hidden info ---

    def filter_state_for_actor(self, state: dict, actor: GameActorContext) -> dict:
        return state  # override in games with hidden information

    # --- BotAdapter default: unsupported ---

    def generate_bot_action(
        self,
        state: dict,
        bot_seat: GameActorContext,
        context: GameExecutionContext,
    ) -> tuple[str, dict]:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support bot actions."
        )
