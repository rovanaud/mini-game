from apps.matches.models import GameMatch
from apps.rooms.models import Participant, Room, RoomTable


def get_room_participants(room: Room):
    return Participant.objects.filter(room=room).order_by("joined_at")


def get_room_participants_count(room: Room):
    return get_room_participants(room).count()


def get_room_participants_ids(room: Room):
    return get_room_participants(room).values_list("participant_id", flat=True)


def get_room_participants_identities(room: Room):
    return (
        get_room_participants(room)
        .select_related("identity")
        .values_list("identity", flat=True)
    )


def get_participant_room_id(participant: Participant) -> int:
    return participant.room_id  # type: ignore[attr-defined]


def get_room_table_room_id(room_table: RoomTable) -> int:
    return room_table.room_id  # type: ignore[attr-defined]


def get_room_matches(room: Room):
    return GameMatch.objects.filter(room=room).order_by("-started_at")


def get_room_matches_count(room: Room):
    return get_room_matches(room).count()


def get_participant_current_game_match_id(participant: Participant):
    return participant.current_game_match_id  # type: ignore[attr-defined]


def get_participant_current_table_id(participant: Participant):
    return participant.current_table_id  # type: ignore[attr-defined]
