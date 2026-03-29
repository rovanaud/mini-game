from __future__ import annotations

from apps.adminops.models import DomainEventLog


def log_event(
    event_type: str,
    *,
    room_id=None,
    participant_id=None,
    table_id=None,
    match_id=None,
    tournament_id=None,
    actor_identity_id=None,
    payload: dict | None = None,
) -> DomainEventLog:
    return DomainEventLog.objects.create(
        event_type=event_type,
        room_id=room_id,
        participant_id=participant_id,
        table_id=table_id,
        match_id=match_id,
        tournament_id=tournament_id,
        actor_identity_id=actor_identity_id,
        payload_json=payload or {},
    )
