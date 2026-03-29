from dataclasses import dataclass, field

# TODO: Add the metadata fields to the contexts managed by the game's modules


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
    seat_identity_ids: list[str] | None = field(default_factory=list)


@dataclass
class GameExecutionContext:
    match_id: str
    room_id: str
    sequence_number: int


@dataclass
class GameActionResult:
    new_state: dict
    is_terminal: bool = False
    outcome_type: str | None = None
    winner_summary: dict | None = None
    side_effects: list[dict] = field(default_factory=list)
