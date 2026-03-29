from apps.games.types import GameActorContext
from apps.matches.errors import ActorNotInMatchError
from apps.matches.models import GameMatch, GameMatchSeat


def get_match_seats(game_match: GameMatch):
    return GameMatchSeat.objects.filter(game_match=game_match).order_by("seat_index")


def get_match_seats_with_participant_identity(game_match: GameMatch):
    return get_match_seats(game_match).select_related(
        "participant", "participant__identity"
    )


def get_match_seat_participant_ids(game_match: GameMatch) -> list[str]:
    return list(
        map(str, get_match_seats(game_match).values_list("participant", flat=True))
    )


def get_match_seat(game_match: GameMatch, participant_id: str) -> GameMatchSeat | None:
    return (
        GameMatchSeat.objects.filter(
            game_match=game_match,
            participant_id=participant_id,
        )
        .only("seat_index", "participant")
        .first()
    )


def get_actor_context(game_match: GameMatch, participant_id: str) -> GameActorContext:
    seat = (
        GameMatchSeat.objects.select_related("participant__identity")
        .filter(game_match=game_match, participant_id=participant_id)
        .first()
    )
    if seat is None:
        raise ActorNotInMatchError("Participant is not a player in this match.")

    return GameActorContext(
        participant_id=participant_id,
        seat_index=seat.seat_index,
        actor_type=seat.actor_type,
        identity_id=str(seat.participant.identity_id) if seat.participant else None,
    )


def get_game_match_room_id(game_match: GameMatch) -> int:
    return game_match.room_id  # type: ignore[attr-defined]


def get_game_match_game_id(game_match: GameMatch) -> str:
    # game_id is a foreign key to GameDefinition, and is equivalent to game_id
    return game_match.game_id  # type: ignore[attr-defined]
