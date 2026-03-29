# Technical Dossier

## Social Mini-Games Platform

## 1. Scope of this dossier

This dossier defines:

* the core domain model
* aggregate boundaries
* state machines
* service boundaries
* API surface draft
* realtime event contracts
* persistence schema draft
* authorization model
* implementation sequencing
* explicit V1 / later split

It is intended to guide roughly 90% of the implementation decisions.

---

# 2. System statement

The platform is a **room-centric realtime social gaming system** in which:

* users enter a room first
* a room contains participants, tables, chats, matches, and optionally a tournament
* multiple matches may coexist in the same room
* one participant cannot play in multiple matches at the same time
* tournaments are first-class but do not freeze all other room activity
* guests are supported first
* reconnect and state recovery are mandatory
* all important domain actions are logged

---

# 3. Context map and bounded contexts

The recommended bounded contexts are:

## 3.1 Identity & Session

Responsibilities:

* guest identity creation
* session durability
* reconnect token handling
* future account attachment

Core objects:

* UserIdentity
* GuestSession

## 3.2 Room Management

Responsibilities:

* room lifecycle
* participant membership
* host management
* room configuration
* expiration
* table management

Core objects:

* Room
* Participant
* Table
* ParticipantRoleAssignment

## 3.3 Match Runtime

Responsibilities:

* match lifecycle
* player seat assignment
* action submission
* pause/resume/interruption
* result finalization
* snapshots and action history

Core objects:

* Match
* MatchSeat
* MatchAction
* MatchSnapshot

## 3.4 Game Catalog & Game Modules

Responsibilities:

* supported game definitions
* rules and capabilities per game
* game state transitions
* game-specific validation

Core objects:

* GameDefinition
* GameModule interface

## 3.5 Tournament Engine

Responsibilities:

* tournament lifecycle
* entry registration
* pairing/bracket generation
* tournament progression

Core objects:

* Tournament
* TournamentEntry
* TournamentMatch

## 3.6 Chat & Visibility

Responsibilities:

* scoped chat channels
* message creation
* history retrieval
* visibility rules
* system messages

Core objects:

* ChatChannel
* ChatMessage

## 3.7 Governance & Decision

Responsibilities:

* proposals
* votes
* future collaborative room actions

Core objects:

* Proposal
* ProposalResponse

## 3.8 Logging, Analytics & Audit

Responsibilities:

* domain event log
* admin audit
* future stats pipeline

Core objects:

* DomainEventLog
* AdminAuditLog

## 3.9 Admin & Moderation

Responsibilities:

* inspect rooms
* force-close rooms
* configure inactivity timeout
* future moderation actions

---

# 4. Core domain model

## 4.1 UserIdentity

Represents a human user known to the system.

### Attributes

* `identity_id: UUID`
* `identity_type: enum(guest, registered)`
* `display_name: string`
* `avatar_url: string?`
* `account_id: UUID?`
* `status: enum(active, inactive, deleted, merged)`
* `created_at: timestamp`
* `updated_at: timestamp`
* `last_seen_at: timestamp`
* `metadata_json: jsonb`

### Invariants

* guest identities may exist without account
* registered identities must be linked to account
* one active guest session key maps to at most one current guest identity

---

## 4.2 GuestSession

Tracks reconnect-safe guest continuity.

### Attributes

* `guest_session_id: UUID`
* `identity_id: UUID`
* `session_token_hash: string`
* `issued_at: timestamp`
* `expires_at: timestamp`
* `last_seen_at: timestamp`
* `client_fingerprint: string?`
* `metadata_json: jsonb`

### Purpose

Used for:

* reload recovery
* reconnect
* long-lived guest continuity until session ends

---

## 4.3 Room

The main social container.

### Attributes

* `room_id: UUID`
* `public_code: string`
* `invite_token: string`
* `status: enum(created, open, active, idle, closing, closed, expired, archived)`
* `visibility: enum(private, public_future)`
* `host_participant_id: UUID`
* `created_by_identity_id: UUID`
* `created_at: timestamp`
* `updated_at: timestamp`
* `last_activity_at: timestamp`
* `expires_at: timestamp?`
* `closed_at: timestamp?`
* `close_reason: enum(host_closed, admin_closed, inactivity_expired, error, unknown)?`
* `settings_json: jsonb`

### Room settings examples

* join policy
* newcomer history visibility
* inactivity timeout
* max participants
* default vote policy
* allowed games
* spectator permissions
* chat policy

### Invariants

* exactly one active host participant at a time
* private in V1
* always has at least one default lobby table

---

## 4.4 Participant

A user’s presence inside a room.

### Attributes

* `participant_id: UUID`
* `room_id: UUID`
* `identity_id: UUID`
* `status: enum(joining, idle, spectating, waiting, playing, left, kicked)`
* `connection_status: enum(connected, disconnected_recoverable, disconnected_expired)`
* `joined_at: timestamp`
* `last_active_at: timestamp`
* `left_at: timestamp?`
* `current_table_id: UUID?`
* `current_match_id: UUID?`
* `is_host: boolean`
* `metadata_json: jsonb`

### Invariants

* one identity may not be active participant in two rooms simultaneously
* a participant may spectate without playing
* a participant may hold multiple scoped roles
* a participant may not be in playing state for two simultaneous matches

---

## 4.5 ParticipantRoleAssignment

Extensible multi-scope role model.

### Attributes

* `participant_role_assignment_id: UUID`
* `participant_id: UUID`
* `role_type: string`
* `scope_type: enum(room, table, match, tournament, game)`
* `scope_id: UUID`
* `granted_by_participant_id: UUID?`
* `created_at: timestamp`
* `expires_at: timestamp?`
* `metadata_json: jsonb`

### Examples

* host for room
* player for match
* spectator for match
* referee for tournament
* moderator for room
* narrator for werewolf game later

---

## 4.6 Table

A room subdivision used to anchor activity.

### Attributes

* `table_id: UUID`
* `room_id: UUID`
* `table_type: enum(lobby, match, tournament, custom)`
* `name: string`
* `status: enum(open, active, idle, closed)`
* `created_at: timestamp`
* `closed_at: timestamp?`
* `settings_json: jsonb`

### Use

* lobby table for inactive/spectating users
* one table per active match by default
* future table-specific voice/text channels

---

## 4.7 GameDefinition

Static metadata about a supported game.

### Attributes

* `game_key: string`
* `display_name: string`
* `version: string`
* `category: string`
* `min_players: int`
* `max_players: int`
* `supports_spectators: boolean`
* `supports_pause: boolean`
* `supports_resume: boolean`
* `supports_bots: boolean`
* `supports_tournament: boolean`
* `supports_save_resume: boolean`
* `parameter_schema_json: jsonb`
* `communication_policy_schema_json: jsonb`
* `metadata_json: jsonb`

### V1 example

* `connect_four`

---

## 4.8 Match

A concrete playable session.

### Attributes

* `match_id: UUID`
* `room_id: UUID`
* `table_id: UUID`
* `game_key: string`
* `tournament_id: UUID?`
* `state: enum(draft, waiting_for_players, ready, starting, active, paused, interrupted, completed, cancelled, abandoned, archived)`
* `created_by_participant_id: UUID`
* `started_at: timestamp?`
* `ended_at: timestamp?`
* `paused_at: timestamp?`
* `resumable: boolean`
* `termination_reason: string?`
* `winner_summary_json: jsonb?`
* `config_json: jsonb`
* `snapshot_state_json: jsonb?`
* `metadata_json: jsonb`

### Invariants

* every match belongs to one room
* every match belongs to one table
* every match uses exactly one game
* server is source of truth for state

---

## 4.9 MatchSeat

A playable or reserved slot in a match.

### Attributes

* `match_seat_id: UUID`
* `match_id: UUID`
* `seat_index: int`
* `team_index: int?`
* `actor_type: enum(human, bot)`
* `participant_id: UUID?`
* `bot_id: UUID?`
* `seat_status: enum(reserved, filled, vacated, replaced)`
* `joined_at: timestamp`
* `left_at: timestamp?`
* `metadata_json: jsonb`

### Invariants

* either participant_id or bot_id must be set depending on actor_type
* one participant cannot fill multiple active seats across simultaneous matches

---

## 4.10 MatchAction

Stores atomic game actions.

### Attributes

* `match_action_id: UUID`
* `match_id: UUID`
* `sequence_number: bigint`
* `actor_type: enum(human, bot)`
* `participant_id: UUID?`
* `bot_id: UUID?`
* `action_type: string`
* `action_payload_json: jsonb`
* `validated: boolean`
* `applied_at: timestamp`
* `resulting_state_hash: string?`

### Purpose

* replay
* debugging
* analytics
* resumability
* bot training

---

## 4.11 MatchSnapshot

Optional periodic snapshots for fast recovery.

### Attributes

* `match_snapshot_id: UUID`
* `match_id: UUID`
* `snapshot_version: bigint`
* `state_json: jsonb`
* `created_at: timestamp`

---

## 4.12 Tournament

Structured competition inside a room.

### Attributes

* `tournament_id: UUID`
* `room_id: UUID`
* `state: enum(draft, registration_open, ready, in_progress, paused, completed, cancelled, archived)`
* `tournament_type: enum(single_elimination, double_elimination, round_robin, swiss, custom)`
* `game_selection_mode: enum(fixed_game, game_pool, player_choice, host_choice)`
* `default_game_key: string?`
* `created_by_participant_id: UUID`
* `started_at: timestamp?`
* `ended_at: timestamp?`
* `rules_json: jsonb`
* `metadata_json: jsonb`

### V1 recommendation

Implement single elimination first, but keep the enum open.

---

## 4.13 TournamentEntry

### Attributes

* `tournament_entry_id: UUID`
* `tournament_id: UUID`
* `participant_id: UUID`
* `seed: int?`
* `status: enum(registered, active, eliminated, withdrawn, disqualified, completed)`
* `score_summary_json: jsonb`
* `created_at: timestamp`

---

## 4.14 TournamentMatch

Connects tournament scheduling to a real match.

### Attributes

* `tournament_match_id: UUID`
* `tournament_id: UUID`
* `match_id: UUID?`
* `phase: string`
* `round_number: int`
* `bracket_position: string?`
* `status: enum(pending, scheduled, ready, in_progress, completed, cancelled)`
* `depends_on_json: jsonb`
* `scheduled_at: timestamp?`
* `resolved_at: timestamp?`
* `metadata_json: jsonb`

---

## 4.15 ChatChannel

Scoped communication container.

### Attributes

* `channel_id: UUID`
* `room_id: UUID`
* `scope_type: enum(room, table, match, tournament)`
* `scope_id: UUID`
* `channel_policy_json: jsonb`
* `created_at: timestamp`

---

## 4.16 ChatMessage

### Attributes

* `message_id: UUID`
* `channel_id: UUID`
* `sender_type: enum(participant, system)`
* `sender_id: UUID?`
* `message_type: enum(text, emoji, reaction, system)`
* `visibility_policy_json: jsonb`
* `payload_json: jsonb`
* `created_at: timestamp`
* `edited_at: timestamp?`
* `deleted_at: timestamp?`

---

## 4.17 Proposal

Future-proof collaboration/voting model.

### Attributes

* `proposal_id: UUID`
* `room_id: UUID`
* `scope_type: enum(room, table, match, tournament)`
* `scope_id: UUID`
* `proposal_type: string`
* `state: enum(proposed, open, accepted, rejected, expired, cancelled)`
* `created_by_participant_id: UUID`
* `rules_json: jsonb`
* `payload_json: jsonb`
* `created_at: timestamp`
* `expires_at: timestamp?`
* `resolved_at: timestamp?`

---

## 4.18 ProposalResponse

### Attributes

* `proposal_response_id: UUID`
* `proposal_id: UUID`
* `participant_id: UUID`
* `response_value: enum(yes, no, abstain)`
* `responded_at: timestamp`

---

## 4.19 BotDefinition

### Attributes

* `bot_id: UUID`
* `game_key: string`
* `name: string`
* `version: string`
* `difficulty: string`
* `config_json: jsonb`
* `metadata_json: jsonb`

### Note

Bot is game-level, not room-level.

---

## 4.20 DomainEventLog

### Attributes

* `event_id: UUID`
* `event_type: string`
* `room_id: UUID?`
* `participant_id: UUID?`
* `table_id: UUID?`
* `match_id: UUID?`
* `tournament_id: UUID?`
* `actor_identity_id: UUID?`
* `payload_json: jsonb`
* `occurred_at: timestamp`

---

## 4.21 AdminAuditLog

### Attributes

* `admin_audit_log_id: UUID`
* `admin_actor_id: UUID`
* `action_type: string`
* `target_type: string`
* `target_id: UUID?`
* `payload_json: jsonb`
* `occurred_at: timestamp`

---

# 5. UML-ready relationships

These are the key class relationships.

## 5.1 Core associations

* `UserIdentity 1 --- * Participant`
* `Room 1 --- * Participant`
* `Room 1 --- * Table`
* `Room 1 --- * Match`
* `Room 1 --- * ChatChannel`
* `Room 1 --- * Proposal`
* `Room 1 --- * DomainEventLog`
* `Room 1 --- * Tournament`

## 5.2 Match associations

* `Table 1 --- * Match`
* `Match 1 --- * MatchSeat`
* `Match 1 --- * MatchAction`
* `Match 1 --- * MatchSnapshot`
* `GameDefinition 1 --- * Match`
* `Tournament 1 --- * Match` through `TournamentMatch`

## 5.3 Tournament associations

* `Tournament 1 --- * TournamentEntry`
* `Tournament 1 --- * TournamentMatch`

## 5.4 Chat associations

* `ChatChannel 1 --- * ChatMessage`

## 5.5 Role associations

* `Participant 1 --- * ParticipantRoleAssignment`

---

# 6. Aggregate design

## 6.1 Room aggregate

Aggregate root:

* Room

Includes consistency around:

* participant membership
* host ownership
* room-level settings
* room closure
* room expiration
* creation of default lobby table

Room aggregate should not directly own all match internals transactionally.

---

## 6.2 Match aggregate

Aggregate root:

* Match

Includes:

* match seats
* current match state
* action sequencing
* pause/resume/interruption
* completion rules
* snapshots

This is the core gameplay aggregate.

---

## 6.3 Tournament aggregate

Aggregate root:

* Tournament

Includes:

* entries
* pairing/progression metadata
* tournament state

---

## 6.4 ChatChannel aggregate

Aggregate root:

* ChatChannel

Includes:

* messages
* visibility policy resolution

---

# 7. State machine definitions

## 7.1 Room state machine

### States

* `created`
* `open`
* `active`
* `idle`
* `closing`
* `closed`
* `expired`
* `archived`

### Transitions

* `created -> open`: room initialized and joinable
* `open -> active`: first meaningful activity
* `active -> idle`: no active presence/match/chat activity
* `idle -> active`: activity resumes
* `idle -> expired`: inactivity timeout reached
* `active -> closing`: host/admin initiates close
* `closing -> closed`
* `closed -> archived`
* `expired -> archived`

### Notes

`last_activity_at` should be refreshed by:

* participant join/leave
* chat messages
* match creation/start/action
* tournament events

---

## 7.2 Participant state machine

### States

* `joining`
* `idle`
* `spectating`
* `waiting`
* `playing`
* `disconnected_recoverable`
* `left`
* `kicked`

### Transitions

* `joining -> idle`
* `idle -> spectating`
* `idle -> waiting`
* `waiting -> playing`
* `spectating -> playing`
* `playing -> spectating`
* `idle/spectating/playing -> disconnected_recoverable`
* `disconnected_recoverable -> restored prior state`
* `any -> left`
* `any -> kicked`

---

## 7.3 Match state machine

### States

* `draft`
* `waiting_for_players`
* `ready`
* `starting`
* `active`
* `paused`
* `interrupted`
* `completed`
* `cancelled`
* `abandoned`
* `archived`

### Transitions

* `draft -> waiting_for_players`
* `waiting_for_players -> ready`
* `ready -> starting`
* `starting -> active`
* `active -> paused`
* `paused -> active`
* `active -> interrupted`
* `interrupted -> active`
* `active -> completed`
* `active -> abandoned`
* `waiting_for_players -> cancelled`
* `completed/cancelled/abandoned -> archived`

---

## 7.4 Tournament state machine

### States

* `draft`
* `registration_open`
* `ready`
* `in_progress`
* `paused`
* `completed`
* `cancelled`
* `archived`

### Transitions

* `draft -> registration_open`
* `registration_open -> ready`
* `ready -> in_progress`
* `in_progress -> paused`
* `paused -> in_progress`
* `in_progress -> completed`
* `registration_open -> cancelled`
* `in_progress -> cancelled`
* `completed -> archived`

---

## 7.5 Proposal state machine

### States

* `proposed`
* `open`
* `accepted`
* `rejected`
* `expired`
* `cancelled`

### Transitions

* `proposed -> open`
* `open -> accepted`
* `open -> rejected`
* `open -> expired`
* `open -> cancelled`

---

# 8. Permissions model

## 8.1 Authorization philosophy

Do not hardcode authorization only by UI role labels.
Use:

* actor identity
* participant binding
* scoped role assignments
* room settings
* match state
* game module rules

## 8.2 Permission resolution inputs

For any action, authorization should consider:

* who is acting
* room context
* participant status
* scoped roles
* action target
* match/tournament state
* game policy if action is game-specific

## 8.3 Suggested permission categories

### Room permissions

* create_room
* join_room
* leave_room
* close_room
* transfer_host
* expel_participant
* update_room_settings
* create_table

### Match permissions

* create_match
* volunteer_for_match
* invite_to_match
* assign_player
* start_match
* pause_match
* resume_match
* abandon_match
* spectate_match

### Game permissions

* submit_game_action
* request_save
* request_replace_with_bot

### Tournament permissions

* create_tournament
* register_tournament_entry
* start_tournament
* generate_tournament_match
* resolve_tournament_match

### Chat permissions

* send_message
* react_message
* read_history

---

# 9. API dossier

This is an implementation-oriented contract outline.
You can expose it as REST + websocket, or HTTP + event transport.

---

## 9.1 Identity & session API

### `POST /guest-sessions`

Creates guest identity and guest session.

**Response**

* identity summary
* guest session token
* expiry info

### `POST /sessions/restore`

Restores guest identity from token.

**Response**

* identity summary
* active room participation list if any

---

## 9.2 Room API

### `POST /rooms`

Create room.

**Request**

* room settings
* optional host display preferences

**Response**

* room summary
* invite token
* public code
* participant summary for creator as host

### `POST /rooms/{roomId}/join`

Join room by invite/code.

**Request**

* guest session token
* room code and/or invite token

**Response**

* participant summary
* room snapshot
* subscribed channels info

### `POST /rooms/{roomId}/leave`

Leave room.

### `POST /rooms/{roomId}/close`

Host/admin close room.

### `POST /rooms/{roomId}/transfer-host`

Transfer host.

**Request**

* target participant id

### `PATCH /rooms/{roomId}`

Update room settings.

### `GET /rooms/{roomId}`

Fetch room snapshot.

### `GET /rooms/{roomId}/participants`

Fetch room participants.

### `POST /rooms/{roomId}/tables`

Create table.

---

## 9.3 Match API

### `POST /rooms/{roomId}/matches`

Create match draft.

**Request**

* game key
* optional table id
* config
* invited participants / initial volunteers

### `POST /matches/{matchId}/volunteer`

Mark willingness to play.

### `POST /matches/{matchId}/invite`

Invite inactive participant.

### `POST /matches/{matchId}/assign-seat`

Assign participant to seat.

### `POST /matches/{matchId}/start`

Start match.

### `POST /matches/{matchId}/pause`

Pause match.

### `POST /matches/{matchId}/resume`

Resume match.

### `POST /matches/{matchId}/abandon`

Abandon match.

### `POST /matches/{matchId}/actions`

Submit game action.

**Request**

* action type
* action payload
* client sequence hint optional

### `GET /matches/{matchId}`

Get match snapshot.

### `GET /matches/{matchId}/actions`

Get match action history.

---

## 9.4 Tournament API

### `POST /rooms/{roomId}/tournaments`

Create tournament.

### `POST /tournaments/{tournamentId}/entries`

Register participant.

### `POST /tournaments/{tournamentId}/start`

Start tournament.

### `POST /tournaments/{tournamentId}/generate-round`

Generate next round or pairings.

### `GET /tournaments/{tournamentId}`

Get tournament snapshot.

### `GET /tournaments/{tournamentId}/matches`

Get tournament match list.

---

## 9.5 Chat API

### `POST /channels/{channelId}/messages`

Send message.

### `GET /channels/{channelId}/messages`

Fetch message history.

### `POST /messages/{messageId}/reactions`

Add reaction.

---

## 9.6 Proposal API

### `POST /rooms/{roomId}/proposals`

Create proposal.

### `POST /proposals/{proposalId}/responses`

Respond to proposal.

### `GET /proposals/{proposalId}`

Get proposal state.

---

## 9.7 Admin API

### `GET /admin/rooms/active`

List active rooms.

### `GET /admin/rooms/{roomId}`

Inspect room.

### `POST /admin/rooms/{roomId}/force-close`

Force close room.

### `PATCH /admin/config/inactivity-timeout`

Adjust global inactivity timeout.

---

# 10. Realtime event dossier

## 10.1 Subscription scopes

Clients should subscribe to:

* `room:{roomId}`
* `table:{tableId}`
* `match:{matchId}`
* `tournament:{tournamentId}`
* optionally `participant:{participantId}` for direct invites/notices

---

## 10.2 Envelope format

All realtime events should share a common envelope:

```json
{
  "event_id": "uuid",
  "event_type": "match_action_applied",
  "occurred_at": "2026-03-25T12:00:00Z",
  "scope_type": "match",
  "scope_id": "uuid",
  "room_id": "uuid",
  "sequence": 184,
  "payload": {}
}
```

Recommended fields:

* event_id
* event_type
* occurred_at
* scope_type
* scope_id
* room_id
* sequence
* payload

---

## 10.3 Room events

* `room_updated`
* `room_closing`
* `room_closed`
* `room_expired`
* `host_transferred`

## 10.4 Participant events

* `participant_joined`
* `participant_left`
* `participant_disconnected`
* `participant_reconnected`
* `participant_status_changed`

## 10.5 Table events

* `table_created`
* `table_updated`
* `table_closed`

## 10.6 Match events

* `match_created`
* `match_waiting_for_players`
* `match_ready`
* `match_started`
* `match_paused`
* `match_interrupted`
* `match_resumed`
* `match_completed`
* `match_abandoned`
* `match_action_applied`

## 10.7 Tournament events

* `tournament_created`
* `tournament_registration_opened`
* `tournament_started`
* `tournament_match_scheduled`
* `tournament_round_advanced`
* `tournament_completed`

## 10.8 Chat events

* `message_created`
* `message_updated`
* `reaction_added`
* `system_message_created`

## 10.9 Proposal events

* `proposal_created`
* `proposal_opened`
* `proposal_resolved`

---

# 11. Reconnect and recovery model

## 11.1 Requirements

* refresh must not destroy participation state
* temporary disconnect must not erase gameplay state
* client must be able to resync authoritatively from server

## 11.2 Recommended flow

1. client reconnects with guest session token
2. backend resolves identity
3. backend resolves active participant binding
4. backend marks connection restored
5. backend returns:

   * room snapshot
   * participant snapshot
   * active match snapshot if any
   * recent events since last sequence if supported

## 11.3 Match recovery strategy

For active match resync:

* latest match snapshot
* latest action sequence
* optionally recent action tail

## 11.4 Host recovery grace policy

Recommended:

* if host disconnects, wait grace period
* if host does not return, deterministic auto-transfer

---

# 12. SQL-oriented schema draft

This is not final SQL syntax, but it is close enough for schema derivation.

## 12.1 identity tables

### `user_identity`

* identity_id PK
* identity_type
* display_name
* avatar_url
* account_id nullable
* status
* created_at
* updated_at
* last_seen_at
* metadata_json

### `guest_session`

* guest_session_id PK
* identity_id FK -> user_identity
* session_token_hash unique
* issued_at
* expires_at
* last_seen_at
* client_fingerprint nullable
* metadata_json

---

## 12.2 room tables

### `room`

* room_id PK
* public_code unique
* invite_token unique
* status
* visibility
* host_participant_id nullable
* created_by_identity_id FK -> user_identity
* created_at
* updated_at
* last_activity_at
* expires_at nullable
* closed_at nullable
* close_reason nullable
* settings_json

### `participant`

* participant_id PK
* room_id FK -> room
* identity_id FK -> user_identity
* status
* connection_status
* joined_at
* last_active_at
* left_at nullable
* current_table_id nullable
* current_match_id nullable
* is_host
* metadata_json

Unique constraints:

* one active participant per identity across active rooms
* one host participant per room

### `participant_role_assignment`

* participant_role_assignment_id PK
* participant_id FK -> participant
* role_type
* scope_type
* scope_id
* granted_by_participant_id nullable FK -> participant
* created_at
* expires_at nullable
* metadata_json

### `room_table`

* table_id PK
* room_id FK -> room
* table_type
* name
* status
* created_at
* closed_at nullable
* settings_json

---

## 12.3 game tables

### `game_definition`

* game_key PK
* display_name
* version
* category
* min_players
* max_players
* supports_spectators
* supports_pause
* supports_resume
* supports_bots
* supports_tournament
* supports_save_resume
* parameter_schema_json
* communication_policy_schema_json
* metadata_json

---

## 12.4 match tables

### `match`

* match_id PK
* room_id FK -> room
* table_id FK -> room_table
* game_key FK -> game_definition
* tournament_id nullable FK -> tournament
* state
* created_by_participant_id FK -> participant
* started_at nullable
* ended_at nullable
* paused_at nullable
* resumable
* termination_reason nullable
* winner_summary_json nullable
* config_json
* snapshot_state_json nullable
* metadata_json

### `match_seat`

* match_seat_id PK
* match_id FK -> match
* seat_index
* team_index nullable
* actor_type
* participant_id nullable FK -> participant
* bot_id nullable FK -> bot_definition
* seat_status
* joined_at
* left_at nullable
* metadata_json

Unique:

* one seat index per match

### `match_action`

* match_action_id PK
* match_id FK -> match
* sequence_number
* actor_type
* participant_id nullable FK -> participant
* bot_id nullable FK -> bot_definition
* action_type
* action_payload_json
* validated
* applied_at
* resulting_state_hash nullable

Unique:

* unique(match_id, sequence_number)

### `match_snapshot`

* match_snapshot_id PK
* match_id FK -> match
* snapshot_version
* state_json
* created_at

---

## 12.5 tournament tables

### `tournament`

* tournament_id PK
* room_id FK -> room
* state
* tournament_type
* game_selection_mode
* default_game_key nullable FK -> game_definition
* created_by_participant_id FK -> participant
* started_at nullable
* ended_at nullable
* rules_json
* metadata_json

### `tournament_entry`

* tournament_entry_id PK
* tournament_id FK -> tournament
* participant_id FK -> participant
* seed nullable
* status
* score_summary_json
* created_at

Unique:

* unique(tournament_id, participant_id)

### `tournament_match`

* tournament_match_id PK
* tournament_id FK -> tournament
* match_id nullable FK -> match
* phase
* round_number
* bracket_position nullable
* status
* depends_on_json
* scheduled_at nullable
* resolved_at nullable
* metadata_json

---

## 12.6 chat tables

### `chat_channel`

* channel_id PK
* room_id FK -> room
* scope_type
* scope_id
* channel_policy_json
* created_at

Unique:

* unique(scope_type, scope_id)

### `chat_message`

* message_id PK
* channel_id FK -> chat_channel
* sender_type
* sender_id nullable
* message_type
* visibility_policy_json
* payload_json
* created_at
* edited_at nullable
* deleted_at nullable

---

## 12.7 governance tables

### `proposal`

* proposal_id PK
* room_id FK -> room
* scope_type
* scope_id
* proposal_type
* state
* created_by_participant_id FK -> participant
* rules_json
* payload_json
* created_at
* expires_at nullable
* resolved_at nullable

### `proposal_response`

* proposal_response_id PK
* proposal_id FK -> proposal
* participant_id FK -> participant
* response_value
* responded_at

Unique:

* unique(proposal_id, participant_id)

---

## 12.8 analytics/admin tables

### `domain_event_log`

* event_id PK
* event_type
* room_id nullable FK -> room
* participant_id nullable FK -> participant
* table_id nullable FK -> room_table
* match_id nullable FK -> match
* tournament_id nullable FK -> tournament
* actor_identity_id nullable FK -> user_identity
* payload_json
* occurred_at

### `admin_audit_log`

* admin_audit_log_id PK
* admin_actor_id
* action_type
* target_type
* target_id nullable
* payload_json
* occurred_at

### `bot_definition`

* bot_id PK
* game_key FK -> game_definition
* name
* version
* difficulty
* config_json
* metadata_json

---

# 13. Game module contract dossier

## 13.1 GameModule interface

Every game implementation should provide:

* `getDefinition()`
* `validateConfig(config)`
* `buildInitialState(setup)`
* `validateSeatAssignment(setup, seats)`
* `validateAction(state, actor, action)`
* `applyAction(state, actor, action)`
* `resolveOutcome(state)`
* `getVisibilityPolicy(state)`
* `getInterruptionPolicy()`
* `supportsBotReplacement()`
* `serializeState(state)`
* `deserializeState(serialized)`

## 13.2 Result contract from action application

Each action application should return:

* new state
* accepted/rejected
* emitted domain effects
* updated turn / actor
* terminal status if any
* winner/result if any
* optional derived chat/system events

## 13.3 Connect Four reference implementation

Minimum Connect Four module:

* 2 seats
* board state
* turn tracking
* drop-disc action
* winner detection
* draw detection
* pause/resume support
* full action logging

---

# 14. Sequence dossier

These are the first sequence diagrams you should derive.

## 14.1 Create room

1. guest session exists or is created
2. user requests room creation
3. room created
4. creator inserted as participant
5. host role assigned
6. default lobby table created
7. room chat channel created
8. domain event written
9. room snapshot returned

## 14.2 Join room

1. guest token validated
2. invite/code validated
3. participant inserted
4. participant added to room
5. room snapshot loaded
6. participant_joined event emitted
7. room snapshot returned

## 14.3 Reconnect to room

1. guest token validated
2. participant recovered
3. connection_status updated
4. active match linkage checked
5. latest snapshots loaded
6. participant_reconnected emitted
7. resync payload returned

## 14.4 Create and start Connect Four match

1. host creates match draft
2. match and table created if needed
3. participants volunteer / are invited
4. host assigns seats
5. match enters ready
6. start requested
7. module initial state created
8. match enters active
9. match_started emitted

## 14.5 Submit Connect Four move

1. client submits action
2. actor authorization checked
3. match loaded
4. game module validates action
5. action persisted
6. new state produced
7. snapshot updated
8. terminal status checked
9. match_action_applied emitted
10. if completed, match_completed emitted

## 14.6 Host disconnect and transfer

1. host connection lost
2. participant marked disconnected_recoverable
3. grace timer starts
4. if not restored, eligible participant selected
5. host role reassigned
6. host_transferred emitted
7. audit/domain event stored

---

# 15. Service/component dossier

## 15.1 IdentityService

Methods:

* createGuestIdentity
* createGuestSession
* restoreGuestSession
* resolveIdentityFromSession
* attachAccountLater

## 15.2 RoomService

Methods:

* createRoom
* joinRoom
* leaveRoom
* closeRoom
* expireRoom
* transferHost
* createDefaultLobbyTable
* updateRoomSettings

## 15.3 ParticipantService

Methods:

* addParticipant
* removeParticipant
* markDisconnected
* markReconnected
* updateParticipantState
* assignScopedRole

## 15.4 MatchService

Methods:

* createMatchDraft
* volunteerParticipant
* inviteParticipant
* assignSeat
* startMatch
* pauseMatch
* resumeMatch
* abandonMatch
* archiveMatch

## 15.5 GameRuntimeService

Methods:

* loadGameModule
* validateAction
* applyAction
* resolveOutcome
* persistSnapshot

## 15.6 TournamentService

Methods:

* createTournament
* registerEntry
* startTournament
* generateNextRound
* bindMatchToTournamentNode
* resolveTournamentProgress

## 15.7 ChatService

Methods:

* ensureChannel
* sendMessage
* sendSystemMessage
* fetchHistory
* applyVisibilityRules

## 15.8 ProposalService

Methods:

* createProposal
* openProposal
* recordResponse
* resolveProposal

## 15.9 PresenceService

Methods:

* connectParticipant
* disconnectParticipant
* heartbeat
* resyncParticipant

## 15.10 EventPublisher

Methods:

* publishToRoom
* publishToTable
* publishToMatch
* publishToTournament
* publishToParticipant

## 15.11 DomainEventService

Methods:

* appendEvent
* fetchEventsSince
* projectAnalyticsEvents

---

# 16. Delivery plan

## 16.1 Milestone A — foundation

Deliver:

* project structure
* database migrations
* guest session support
* room entity
* participant entity
* domain event log
* websocket or equivalent realtime transport

## 16.2 Milestone B — room core

Deliver:

* create/join/leave room
* host assignment
* room snapshot endpoint
* lobby table
* room expiration
* participant reconnect

## 16.3 Milestone C — room chat

Deliver:

* room chat channel
* message posting
* history retrieval
* system messages for joins/leaves

## 16.4 Milestone D — match engine

Deliver:

* match draft creation
* seat assignment
* match start/pause/resume
* generic action submission pipeline

## 16.5 Milestone E — Connect Four

Deliver:

* Connect Four module
* board snapshots
* move history
* spectators
* completion/winner detection

## 16.6 Milestone F — recovery hardening

Deliver:

* reconnect resync
* interrupted match handling
* host grace timer and transfer

## 16.7 Milestone G — tournament baseline

Deliver:

* tournament creation
* registration
* single-elimination progression
* tournament match linkage

## 16.8 Milestone H — admin baseline

Deliver:

* list active rooms
* inspect room
* force close
* inactivity timeout configuration

---

# 17. V1 cut

## 17.1 Must be in V1

* guests
* room create/join/leave
* invite token + code
* host
* room persistence across refresh
* lobby table
* room chat
* Connect Four
* spectators
* move history
* pause/interruption support
* event logging
* room expiration
* basic admin timeout config

## 17.2 Can remain structurally modeled but not fully built in V1

* scoped role richness
* proposal/vote engine
* advanced tournament UX
* multi-game catalog beyond Connect Four
* bots
* match-specific/table-specific chat
* public rooms
* registered accounts
* moderation features
* cognitive analytics dashboards

---

# 18. Engineering risks and design safeguards

## 18.1 Overgeneralizing too soon

Safeguard:

* implement Connect Four first
* keep plugin interface small and clean

## 18.2 Role and permission complexity

Safeguard:

* centralize authorization checks
* use scope-aware role assignments
* keep V1 policy set small

## 18.3 Realtime synchronization bugs

Safeguard:

* server authoritative state
* sequence numbers on events
* snapshot-based resync fallback

## 18.4 Tournament feature creep

Safeguard:

* one real tournament type in V1
* tournament wraps matches instead of replacing them
