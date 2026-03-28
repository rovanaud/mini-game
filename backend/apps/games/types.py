from dataclasses import dataclass, field


@dataclass
class GameActorContext:
    participant_id: str
    seat_index: int
    actor_type: str = "human"


@dataclass
class GameSetupContext:
    match_id: str
    room_id: str
    seat_participant_ids: list[str]


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
