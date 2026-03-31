from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GameActorContext:
    participant_id: str
    seat_index: int
    actor_type: str = "human"
    identity_id: str | None = None


@dataclass
class GameSetupContext:
    match_id: str
    room_id: str
    seat_participant_ids: list[str]
    seat_identity_ids: list[str | None] = field(default_factory=list)


@dataclass
class GameExecutionContext:
    match_id: str
    room_id: str
    sequence_number: int


@dataclass
class GameOutcome:
    outcome_type: str  # "win", "draw", "abandoned", etc.
    winner_summary: dict | None = None  # None for draws/abandonments
    side_effects: list[dict] = field(default_factory=list)


@dataclass
class GameActionResult:
    """
    Pure state transition result. Terminal detection is the
    responsibility of resolve_outcome(), not apply_action().
    """

    new_state: dict
    side_effects: list[dict] = field(default_factory=list)


@dataclass
class GameMetadata:
    game_id: str
    display_name: str
    min_players: int
    max_players: int
    supports_spectators: bool = True
    supports_pause: bool = False
    supports_resume: bool = False
    supports_bots: bool = False
    # supports_hidden_state: bool = False
