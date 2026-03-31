from __future__ import annotations

from copy import deepcopy

from apps.games.base import GameBaseModule
from apps.games.types import (
    GameActionResult,
    GameActorContext,
    GameExecutionContext,
    GameMetadata,
    GameOutcome,
    GameSetupContext,
)

ROWS = 6
COLS = 7
WIN_LENGTH = 4


def _make_board() -> list[list[str | None]]:
    return [[None] * COLS for _ in range(ROWS)]


def _drop_disc(board: list, col: int, disc: str) -> int:
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] is None:
            board[row][col] = disc
            return row
    raise ValueError(f"Column {col} is full.")  # should never reach here after validate


def _check_win(board: list, row: int, col: int, disc: str) -> bool:
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        for sign in (1, -1):
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == disc:
                count += 1
                r += sign * dr
                c += sign * dc
        if count >= WIN_LENGTH:
            return True
    return False


def _is_draw(board: list) -> bool:
    return all(board[0][col] is not None for col in range(COLS))


class ConnectFourModule(GameBaseModule):
    game_id = "connect_four"

    def get_metadata(self) -> GameMetadata:
        return GameMetadata(
            game_id=self.game_id,
            display_name="Connect Four",
            min_players=2,
            max_players=2,
            supports_spectators=True,
            supports_pause=False,
            supports_resume=False,
            supports_bots=False,  # future: easy to add
            # supports_hidden_state=False,  # full board visible to all
        )

    def validate_config(self, config: dict) -> None:
        # Future: allow {"rows": int, "cols": int, "win_length": int}
        pass

    def build_initial_state(self, config: dict, context: GameSetupContext) -> dict:
        if len(context.seat_participant_ids) != 2:
            raise ValueError(
                f"Connect Four requires exactly 2 players. "
                f"Got: {len(context.seat_participant_ids)}"
            )
        return {
            "game_id": self.game_id,
            "status": "active",
            "board": _make_board(),
            "current_turn_seat": 0,
            "seat_discs": {"0": "R", "1": "Y"},
            "move_count": 0,
            "last_move": None,  # {row, col, disc, seat} — useful for UI highlighting
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

        if action_type == "resign":
            # Resigning is valid any time for a seated palyer - no turn check needed
            return

        if action_type != "drop_disc":
            raise ValueError(f"Unsupported action type: {action_type!r}")

        if actor.seat_index != state["current_turn_seat"]:
            raise ValueError(
                f"Not seat {actor.seat_index}'s turn. "
                f"Expected seat {state['current_turn_seat']}."
            )

        col = action_payload.get("column")
        if not isinstance(col, int) or not (0 <= col < COLS):
            raise ValueError(f"Invalid column: {col!r}. Must be integer 0–{COLS - 1}.")

        if state["board"][0][col] is not None:
            raise ValueError(f"Column {col} is full.")

    def apply_action(
        self,
        state: dict,
        action_type: str,
        action_payload: dict,
        actor: GameActorContext,
        context: GameExecutionContext,
    ) -> GameActionResult:
        new_state = deepcopy(state)

        if action_type == "resign":
            new_state["status"] = "finished"
            new_state["outcome"] = "resign"
            new_state["resigned_seat"] = actor.seat_index
            return GameActionResult(new_state=new_state)

        col = action_payload["column"]
        disc = new_state["seat_discs"][str(actor.seat_index)]

        row = _drop_disc(new_state["board"], col, disc)
        new_state["move_count"] += 1
        new_state["last_move"] = {
            "row": row,
            "col": col,
            "disc": disc,
            "seat": actor.seat_index,
        }

        # Determine whose turn is next (flipped) — outcome resolver decides terminal
        new_state["current_turn_seat"] = 1 - actor.seat_index

        return GameActionResult(new_state=new_state)

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

        last_move = state.get("last_move")
        if not last_move:
            return None

        board = state["board"]
        row, col, disc = last_move["row"], last_move["col"], last_move["disc"]

        if _check_win(board, row, col, disc):
            winner_seat = last_actor.seat_index
            return GameOutcome(
                outcome_type="win",
                winner_summary={
                    "winner_seat": winner_seat,
                    "loser_seat": 1 - winner_seat,
                    "reason": "four_in_a_row",
                    "move_count": state["move_count"],
                    "winning_disc": disc,
                },
            )

        if _is_draw(board):
            return GameOutcome(
                outcome_type="draw",
                winner_summary={
                    "winner_seat": None,
                    "reason": "board_full",
                    "move_count": state["move_count"],
                },
            )

        return None  # game continues

    # can_pause, can_resume inherited from GameBaseModule (both return False)
    # can_abandon inherited (returns True)
    # filter_state_for_actor inherited (returns full state — no hidden info)
    # generate_bot_action inherited (raises NotImplementedError)
