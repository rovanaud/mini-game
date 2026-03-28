from __future__ import annotations

from copy import deepcopy

from apps.games.spi import (
    GameActionResult,
    GameActorContext,
    GameExecutionContext,
    GameSetupContext,
)


class VowelGameModule:
    game_id = "vowel_game"
    ALLOWED_VOWELS = ("A", "E", "I", "O", "U")

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

        if vowel in played_vowels:
            # Invalid repeated proposal => acting player loses immediately
            winner_seat = state.get("prev_turn_seat")
            new_state["status"] = "completed"
            new_state["winner_seat"] = winner_seat
            new_state["outcome"] = "invalid_repeat_loss"

            return GameActionResult(
                new_state=new_state,
                is_terminal=True,
                outcome_type="win",
                winner_summary={
                    "winner_seat": winner_seat,
                    "loser_seat": actor.participant_id,
                    "reason": "invalid_repeat_loss",
                },
            )

        played_vowels.append(vowel)
        played_by[vowel] = actor.participant_id

        if len(played_vowels) == len(self.ALLOWED_VOWELS):
            # All vowels exhausted with no invalid repeat
            new_state["status"] = "completed"
            new_state["winner_seat"] = None
            new_state["outcome"] = "draw_exhausted"

            return GameActionResult(
                new_state=new_state,
                is_terminal=True,
                outcome_type="draw",
                winner_summary={
                    "winner_seat": None,
                    "reason": "draw_exhausted",
                },
            )

        new_state["prev_turn_seat"] = actor.participant_id

        return GameActionResult(
            new_state=new_state,
            is_terminal=False,
            outcome_type=None,
            winner_summary=None,
        )
