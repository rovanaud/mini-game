import secrets
import string
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

import apps.adminops.types as event_types
from apps.adminops.events import log_event
from apps.identities.models import IdentityType, UserIdentity
from apps.rooms.errors import (
    GuestNotAllowedError,
    RoomJoinNotAllowedError,
)
from apps.rooms.models import (
    ConnectionStatus,
    Participant,
    ParticipantRoleAssignment,
    ParticipantStatus,
    Proposal,
    ProposalResponse,
    ProposalResponseChoice,
    ProposalState,
    RoleScopeType,
    RoleType,
    Room,
    RoomStatus,
    RoomTable,
    RoomVisibility,
    TableStatus,
    TableType,
    VoteMode,
)
from apps.rooms.selectors import get_participant_room_id

DEFAULT_ROOM_INACTIVITY_MINUTES = 15
DEFAULT_PROPOSAL_TIMEOUT_SECONDS = 90


def _generate_room_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_invite_token() -> str:
    return secrets.token_urlsafe(24)


def _generate_unique_room_code() -> str:
    while True:
        code = _generate_room_code()
        if not Room.objects.filter(public_code=code).exists():
            return code


def _generate_unique_invite_token() -> str:
    while True:
        token = _generate_invite_token()
        if not Room.objects.filter(invite_token=token).exists():
            return token


@transaction.atomic
def create_room(
    identity: UserIdentity,
    *,
    settings: dict | None = None,
    visibility: str = RoomVisibility.PRIVATE,
) -> tuple[Room, Participant, RoomTable]:
    now = timezone.now()
    room_settings = settings or {}

    room = Room.objects.create(
        public_code=_generate_unique_room_code(),
        invite_token=_generate_unique_invite_token(),
        status=RoomStatus.OPEN,
        visibility=visibility,
        created_by_identity=identity,
        last_activity_at=now,
        expires_at=now + timedelta(minutes=DEFAULT_ROOM_INACTIVITY_MINUTES),
        settings_json=room_settings,
    )

    lobby_table = RoomTable.objects.create(
        room=room,
        table_type=TableType.LOBBY,
        name="Lobby",
        status=TableStatus.OPEN,
    )

    participant = Participant.objects.create(
        room=room,
        identity=identity,
        status=ParticipantStatus.IDLE,
        connection_status=ConnectionStatus.CONNECTED,
        current_table=lobby_table,
        is_host=True,
        last_active_at=now,
    )

    room.host_participant = participant
    room.save(update_fields=["host_participant", "updated_at"])

    log_event(
        event_types.ROOM_CREATED,
        room_id=room.room_id,
        participant_id=participant.participant_id,
        actor_identity_id=identity.identity_id,
        payload={"public_code": room.public_code},
    )

    ParticipantRoleAssignment.objects.create(
        participant=participant,
        role_type=RoleType.HOST,
        scope_type=RoleScopeType.ROOM,
        scope_id=room.room_id,
        granted_by_participant=None,  # self-granted at creation
    )

    return room, participant, lobby_table


@transaction.atomic
def join_room(
    identity: UserIdentity,
    room: Room,
) -> Participant:
    if room.is_permanent:
        raise RoomJoinNotAllowedError(
            "Permanent rooms cannot be joined by public code. "
            "You must be added by the host."
        )

    now = timezone.now()

    existing = (
        Participant.objects.select_for_update()
        .filter(
            room=room,
            identity=identity,
            status__in=[
                ParticipantStatus.JOINING,
                ParticipantStatus.IDLE,
                ParticipantStatus.SPECTATING,
                ParticipantStatus.WAITING,
                ParticipantStatus.PLAYING,
            ],
        )
        .first()
    )
    if existing:
        existing.connection_status = ConnectionStatus.CONNECTED
        existing.last_active_at = now
        if existing.status == ParticipantStatus.JOINING:
            existing.status = ParticipantStatus.IDLE
        existing.save(update_fields=["connection_status", "last_active_at", "status"])
        log_event(
            event_types.ROOM_JOINED,
            room_id=room.room_id,
            participant_id=existing.participant_id,
            actor_identity_id=identity.identity_id,
            payload={"reconnect": True},
        )
        return existing

    lobby_table = (
        RoomTable.objects.select_for_update()
        .filter(
            room=room,
            table_type=TableType.LOBBY,
            status__in=[TableStatus.OPEN, TableStatus.ACTIVE],
        )
        .first()
    )
    if lobby_table is None:
        lobby_table = RoomTable.objects.create(
            room=room,
            table_type=TableType.LOBBY,
            name="Lobby",
            status=TableStatus.OPEN,
        )

    participant = Participant.objects.create(
        room=room,
        identity=identity,
        status=ParticipantStatus.IDLE,
        connection_status=ConnectionStatus.CONNECTED,
        current_table=lobby_table,
        is_host=False,
        last_active_at=now,
    )

    room.last_activity_at = now
    room.status = (
        RoomStatus.ACTIVE
        if room.status in [RoomStatus.OPEN, RoomStatus.IDLE]
        else room.status
    )
    room.expires_at = now + timedelta(minutes=DEFAULT_ROOM_INACTIVITY_MINUTES)
    room.save(update_fields=["last_activity_at", "status", "expires_at", "updated_at"])

    ParticipantRoleAssignment.objects.create(
        participant=participant,
        role_type=RoleType.SPECTATOR,
        scope_type=RoleScopeType.ROOM,
        scope_id=room.room_id,
        granted_by_participant=None,
    )

    log_event(
        event_types.ROOM_JOINED,
        room_id=room.room_id,
        participant_id=participant.participant_id,
        actor_identity_id=identity.identity_id,
        payload={"reconnect": False},
    )

    return participant


def get_room_for_join(
    *, public_code: str | None = None, invite_token: str | None = None
) -> Room | None:
    if invite_token:
        return Room.objects.filter(invite_token=invite_token).first()
    if public_code:
        return Room.objects.filter(public_code=public_code).first()
    return None


@transaction.atomic
def leave_room(participant: Participant) -> Participant:
    now = timezone.now()

    participant.status = ParticipantStatus.LEFT
    participant.is_host = False
    participant.connection_status = ConnectionStatus.DISCONNECTED_EXPIRED
    participant.left_at = now
    participant.save(
        update_fields=["status", "is_host", "connection_status", "left_at"]
    )

    room = participant.room
    active_participants = list(
        Participant.objects.filter(
            room=room,
            status__in=[
                ParticipantStatus.JOINING,
                ParticipantStatus.IDLE,
                ParticipantStatus.SPECTATING,
                ParticipantStatus.WAITING,
                ParticipantStatus.PLAYING,
            ],
        ).order_by("joined_at")
    )
    if active_participants:
        new_host = active_participants[0]
        if room.host_participant_id != new_host.participant_id:
            Participant.objects.filter(participant_id=new_host.participant_id).update(
                is_host=True
            )
            room.host_participant = new_host
    else:
        room.host_participant = None
        room.status = RoomStatus.IDLE

    room.last_activity_at = now
    room.save(
        update_fields=["host_participant", "status", "last_activity_at", "updated_at"]
    )

    if active_participants:
        ParticipantRoleAssignment.objects.get_or_create(
            participant=active_participants[0],
            role_type=RoleType.HOST,
            scope_type=RoleScopeType.ROOM,
            scope_id=room.room_id,
            defaults={"granted_by_participant": None},
        )

    log_event(
        event_types.ROOM_LEFT,
        room_id=get_participant_room_id(participant),
        participant_id=participant.participant_id,
        actor_identity_id=participant.identity.identity_id,
    )

    return participant


@transaction.atomic
def create_permanent_room(
    identity: UserIdentity,
    *,
    name: str = "New Room",
) -> tuple[Room, Participant, RoomTable]:
    if identity.identity_type == IdentityType.GUEST:
        raise GuestNotAllowedError("Guests cannot create permanent rooms.")

    now = timezone.now()

    room = Room.objects.create(
        public_code=_generate_unique_room_code(),
        invite_token=_generate_unique_invite_token(),
        name=name,
        is_permanent=True,
        status=RoomStatus.OPEN,
        visibility=RoomVisibility.PRIVATE,
        created_by_identity=identity,
        last_activity_at=now,
        expires_at=None,  # permanent rooms never expire
        settings_json={},
    )

    lobby_table = RoomTable.objects.create(
        room=room,
        table_type=TableType.LOBBY,
        name="Lobby",
        status=TableStatus.OPEN,
    )

    participant = Participant.objects.create(
        room=room,
        identity=identity,
        status=ParticipantStatus.IDLE,
        connection_status=ConnectionStatus.CONNECTED,
        current_table=lobby_table,
        is_host=True,
        last_active_at=now,
    )

    room.host_participant = participant
    room.save(update_fields=["host_participant", "updated_at"])

    ParticipantRoleAssignment.objects.create(
        participant=participant,
        role_type=RoleType.HOST,
        scope_type=RoleScopeType.ROOM,
        scope_id=room.room_id,
        granted_by_participant=None,
    )

    log_event(
        event_types.ROOM_CREATED,
        room_id=room.room_id,
        participant_id=participant.participant_id,
        actor_identity_id=identity.identity_id,
        payload={"public_code": room.public_code, "is_permanent": True, "name": name},
    )

    return room, participant, lobby_table


@transaction.atomic
def add_member_to_permanent_room(
    room: Room,
    identity: UserIdentity,
    *,
    added_by: Participant,
) -> Participant:
    """
    Directly adds a registered identity as a permanent member.
    This is the placeholder for the future invite flow —
    when RoomInvite is built, this becomes the acceptance step.
    """
    if not room.is_permanent:
        raise ValueError("add_member_to_permanent_room called on a non-permanent room.")

    if identity.identity_type == IdentityType.GUEST:
        raise GuestNotAllowedError("Guests cannot be members of permanent rooms.")

    # Idempotent — if already a member, return existing participant
    existing = Participant.objects.filter(
        room=room,
        identity=identity,
        status__in=[
            ParticipantStatus.IDLE,
            ParticipantStatus.JOINING,
            ParticipantStatus.WAITING,
            ParticipantStatus.PLAYING,
            ParticipantStatus.SPECTATING,
        ],
    ).first()
    if existing:
        return existing

    now = timezone.now()

    lobby_table = RoomTable.objects.filter(
        room=room,
        table_type=TableType.LOBBY,
        status__in=[TableStatus.OPEN, TableStatus.ACTIVE],
    ).first()

    participant = Participant.objects.create(
        room=room,
        identity=identity,
        status=ParticipantStatus.IDLE,
        connection_status=ConnectionStatus.DISCONNECTED_EXPIRED,  # not online yet
        current_table=lobby_table,
        is_host=False,
        last_active_at=now,
    )

    ParticipantRoleAssignment.objects.create(
        participant=participant,
        role_type=RoleType.PLAYER,
        scope_type=RoleScopeType.ROOM,
        scope_id=room.room_id,
        granted_by_participant=added_by,
    )

    log_event(
        event_types.ROOM_JOINED,
        room_id=room.room_id,
        participant_id=participant.participant_id,
        actor_identity_id=identity.identity_id,
        payload={"added_by": str(added_by.participant_id), "is_permanent": True},
    )

    return participant


def _normalize_vote_mode(rules: dict) -> str:
    mode = (rules.get("mode") or VoteMode.ALL_OR_NOTHING).strip()
    if mode not in {VoteMode.ALL_OR_NOTHING, VoteMode.MAJORITY}:
        raise ValueError(f"Unsupported vote mode: {mode}")
    return mode


def _compute_required_yes_count(total_voters: int, rules: dict) -> int:
    explicit = rules.get("required_yes_count")
    if explicit is not None:
        required = int(explicit)
        if required < 1 or required > total_voters:
            raise ValueError("required_yes_count is out of range for this voter set.")
        return required

    mode = _normalize_vote_mode(rules)
    if mode == VoteMode.ALL_OR_NOTHING:
        return total_voters
    # strict majority: floor(n/2) + 1
    return (total_voters // 2) + 1


def serialize_proposal(proposal: Proposal) -> dict:
    responses = list(
        ProposalResponse.objects.filter(proposal=proposal)
        .select_related("participant__identity")
        .order_by("created_at")
    )
    return {
        "proposal_id": str(proposal.proposal_id),
        "proposal_type": proposal.proposal_type,
        "state": proposal.state,
        "payload": proposal.payload_json,
        "rules": proposal.rules_json,
        "result": proposal.result_json,
        "created_by_participant_id": str(proposal.created_by_participant_id),
        "created_at": proposal.created_at.isoformat(),
        "resolved_at": proposal.resolved_at.isoformat()
        if proposal.resolved_at
        else None,
        "expires_at": proposal.expires_at.isoformat() if proposal.expires_at else None,
        "responses": [
            {
                "participant_id": str(r.participant_id),
                "display_name": (
                    r.participant.identity.display_name
                    if r.participant and r.participant.identity
                    else None
                ),
                "response": r.response,
                "responded_at": r.responded_at.isoformat() if r.responded_at else None,
            }
            for r in responses
        ],
    }


def _execute_accepted_proposal(proposal: Proposal) -> dict:
    if proposal.proposal_type != "match_start":
        return {"executed": False}

    payload = proposal.payload_json or {}
    game_id = (payload.get("game_id") or "").strip()
    players_ids = payload.get("players_ids") or []

    if not game_id:
        raise ValueError("Proposal payload missing game_id.")

    from apps.matches.runtime import initialize_match
    from apps.matches.services import create_game_match

    match, _ = create_game_match(
        room=proposal.room,
        game_id=game_id,
        created_by_participant=proposal.created_by_participant,
        players_ids=players_ids,
    )
    initialize_match(match)
    return {
        "executed": True,
        "match_id": str(match.game_match_id),
        "game_id": game_id,
    }


@transaction.atomic
def create_proposal(
    *,
    room: Room,
    created_by_participant: Participant,
    proposal_type: str,
    payload: dict,
    rules: dict | None = None,
) -> Proposal:
    if created_by_participant.room_id != room.room_id:
        raise ValueError("Creator participant does not belong to room.")

    normalized_rules = rules or {}
    voters_ids = payload.get("voters_ids")
    if not isinstance(voters_ids, list) or not voters_ids:
        raise ValueError("Proposal payload must include non-empty voters_ids.")

    voters = list(
        Participant.objects.filter(
            room=room, participant_id__in=voters_ids
        ).select_related("identity")
    )
    if len(voters) != len(set(voters_ids)):
        raise ValueError("Some voters_ids do not belong to this room.")

    timeout_seconds = int(
        normalized_rules.get("timeout_seconds", DEFAULT_PROPOSAL_TIMEOUT_SECONDS)
    )
    if timeout_seconds < 5:
        timeout_seconds = 5

    now = timezone.now()
    proposal = Proposal.objects.create(
        room=room,
        created_by_participant=created_by_participant,
        proposal_type=proposal_type,
        state=ProposalState.OPEN,
        payload_json=payload,
        rules_json=normalized_rules,
        expires_at=now + timedelta(seconds=timeout_seconds),
    )

    for voter in voters:
        choice = (
            ProposalResponseChoice.YES
            if voter.participant_id == created_by_participant.participant_id
            else ProposalResponseChoice.PENDING
        )
        responded_at = now if choice == ProposalResponseChoice.YES else None
        ProposalResponse.objects.create(
            proposal=proposal,
            participant=voter,
            response=choice,
            responded_at=responded_at,
        )

    _evaluate_and_resolve_proposal(proposal)
    proposal.refresh_from_db()
    return proposal


@transaction.atomic
def respond_to_proposal(
    *,
    proposal: Proposal,
    participant: Participant,
    response: str,
) -> Proposal:
    if proposal.room_id != participant.room_id:
        raise ValueError("Participant does not belong to proposal room.")

    if proposal.state != ProposalState.OPEN:
        raise ValueError("Proposal is no longer open.")

    if proposal.expires_at and timezone.now() > proposal.expires_at:
        proposal.state = ProposalState.EXPIRED
        proposal.resolved_at = timezone.now()
        proposal.save(update_fields=["state", "resolved_at"])
        raise ValueError("Proposal has expired.")

    if response not in {
        ProposalResponseChoice.YES,
        ProposalResponseChoice.NO,
        ProposalResponseChoice.ABSTAIN,
    }:
        raise ValueError(f"Unsupported response: {response}")

    row = ProposalResponse.objects.filter(
        proposal=proposal, participant=participant
    ).first()
    if row is None:
        raise ValueError("Participant is not eligible to respond to this proposal.")
    if row.response != ProposalResponseChoice.PENDING:
        raise ValueError("Participant already responded.")

    row.response = response
    row.responded_at = timezone.now()
    row.save(update_fields=["response", "responded_at"])

    _evaluate_and_resolve_proposal(proposal)
    proposal.refresh_from_db()
    return proposal


def _evaluate_and_resolve_proposal(proposal: Proposal) -> Proposal:
    if proposal.state != ProposalState.OPEN:
        return proposal

    responses = list(ProposalResponse.objects.filter(proposal=proposal))
    total = len(responses)
    if total == 0:
        proposal.state = ProposalState.REJECTED
        proposal.resolved_at = timezone.now()
        proposal.result_json = {"reason": "no_voters"}
        proposal.save(update_fields=["state", "resolved_at", "result_json"])
        return proposal

    required_yes_count = _compute_required_yes_count(total, proposal.rules_json or {})
    yes_count = len([r for r in responses if r.response == ProposalResponseChoice.YES])
    no_count = len([r for r in responses if r.response == ProposalResponseChoice.NO])
    pending_count = len(
        [r for r in responses if r.response == ProposalResponseChoice.PENDING]
    )
    mode = _normalize_vote_mode(proposal.rules_json or {})

    accepted = yes_count >= required_yes_count
    rejected = False

    if mode == VoteMode.ALL_OR_NOTHING and no_count > 0:
        rejected = True
    elif not accepted and pending_count == 0:
        rejected = True

    if not accepted and not rejected:
        return proposal

    now = timezone.now()
    if accepted:
        proposal.state = ProposalState.ACCEPTED
        proposal.resolved_at = now
        execution = _execute_accepted_proposal(proposal)
        proposal.result_json = {
            "decision": "accepted",
            "yes_count": yes_count,
            "no_count": no_count,
            "pending_count": pending_count,
            "required_yes_count": required_yes_count,
            **execution,
        }
    else:
        proposal.state = ProposalState.REJECTED
        proposal.resolved_at = now
        proposal.result_json = {
            "decision": "rejected",
            "yes_count": yes_count,
            "no_count": no_count,
            "pending_count": pending_count,
            "required_yes_count": required_yes_count,
        }
    proposal.save(update_fields=["state", "resolved_at", "result_json"])
    return proposal
