# LEGACY: This module predates the full GameModule SPI.
# It does not implement: get_metadata, resolve_outcome,
# GameInterruptionPolicy, GameVisibilityPolicy, GameBotAdapter.
# Use connect_four as the reference implementation instead.

from __future__ import annotations

from copy import deepcopy

from apps.games.base import GameBaseModule
from apps.games.spi import (
    GameActionResult,
    GameActorContext,
    GameExecutionContext,
    GameSetupContext,
)
from apps.games.types import GameMetadata, GameOutcome


class VowelGameModule(GameBaseModule):
    game_id = "vowel_game"
    ALLOWED_VOWELS = ("A", "E", "I", "O", "U")

    def get_metadata(self) -> GameMetadata:
        return GameMetadata(
            game_id=self.game_id,
            display_name="Vowel Game",
            min_players=2,
            max_players=2,
            supports_spectators=True,
        )

    def validate_config(self, config: dict) -> None:
        # Keep it simple for now: no special config
        return None

    def build_initial_state(self, config: dict, context: GameSetupContext) -> dict:
        if len(context.seat_participant_ids) != 2:
            raise ValueError(
                f"Vowel Game requires exactly 2 players."
                f" Got: {len(context.seat_participant_ids)}"
            )
        return {
            "game_id": self.game_id,
            "status": "active",
            "allowed_vowels": self.ALLOWED_VOWELS[:],
            "played_vowels": [],
            "played_by": {},
            "prev_turn_seat": context.seat_participant_ids[0],
            "winner_seat": None,
            "outcome": None,
            "last_move": None,
        }

    def validate_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> None:
        if state.get("status") != "active":
            raise ValueError("Game is not active.")

        if action_type != "play_vowel":
            raise ValueError(f"Unsupported action type: {action_type}")

        if actor.participant_id == state.get("prev_turn_seat"):
            raise ValueError("It is not this actor's turn.")

        raw_vowel = action_payload.get("vowel")
        if not isinstance(raw_vowel, str):
            raise ValueError("Action payload must contain a string vowel.")

        vowel = raw_vowel.strip().upper()
        if vowel not in self.ALLOWED_VOWELS:
            raise ValueError(f"Invalid vowel: {raw_vowel}")

    def apply_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> GameActionResult:
        # Assume action has already been validated before this method is called,
        # so we can skip re-validating and just apply the game logic.
        # self.validate_action(state, action_type, action_payload, actor, context)

        new_state = deepcopy(state)
        vowel = action_payload["vowel"].strip().upper()

        played_vowels: list[str] = new_state["played_vowels"]
        played_by: dict[str, str] = new_state["played_by"]

        played_vowels.append(vowel)
        played_by[vowel] = actor.participant_id

        if len(played_vowels) == len(self.ALLOWED_VOWELS):
            # All vowels exhausted with no invalid repeat
            new_state["status"] = "completed"
            new_state["winner_seat"] = None
            new_state["outcome"] = "draw_exhausted"

        # new_state["prev_turn_seat"] = actor.participant_id
        new_state["last_move"] = vowel

        return GameActionResult(
            new_state=new_state,
        )

    def resolve_outcome(
        self,
        state: dict,
        last_action_type: str,
        last_actor: GameActorContext,
    ) -> GameOutcome | None:
        if state.get("outcome") == "resign":
            resigned_seat = state["resigned_seat"]
            winner_seat = 1 - resigned_seat
            return GameOutcome(
                outcome_type="win",
                winner_summary={
                    "winner_seat": winner_seat,
                    "loser_seat": resigned_seat,
                    "reason": "resignation",
                    "move_count": state["move_count"],
                },
            )

        vowel = state.get("last_move", None)
        played_vowels = state.get("played_vowels", [])

        if vowel in played_vowels:
            # Invalid repeated proposal => acting player loses immediately
            winner_seat = state.get("prev_turn_seat")
            state["status"] = "completed"
            state["winner_seat"] = winner_seat
            state["outcome"] = "invalid_repeat_loss"
            return GameOutcome(
                outcome_type="win",
                winner_summary={
                    "winner_seat": winner_seat,
                    "loser_seat": last_actor.participant_id,
                    "reason": "invalid_repeat",
                    "move_count": len(played_vowels),
                },
            )

        state["prev_turn_seat"] = last_actor.participant_id

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
