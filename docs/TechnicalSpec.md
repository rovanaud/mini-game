# Technical Specification

## Social Mini-Games Platform

### Domain Model, State Model, System Architecture, Persistence, and Delivery Plan

## 1. Purpose

This document translates the product specification into a technical blueprint intended to guide most of the implementation.

It is designed to support:

* domain-driven design
* UML class/state/sequence diagrams
* database schema design
* API and realtime contract design
* backend modularization
* phased implementation planning

This document assumes:

* private rooms first
* guest users first
* strong extensibility
* room-centric interaction model
* multiple concurrent matches in a room
* tournaments as first-class domain objects
* reconnect-safe state
* rich event logging for stats and future analytics

---

# 2. System Vision

The platform is a **room-centric realtime social game system**.

A user does not primarily “start a game”.
They first enter a **room**, then from that room they may:

* chat
* spectate
* join a table
* play a match
* create or join another match
* participate in a tournament
* remain present while others play

This distinction is central to the architecture.

## 2.1 Core architectural principles

1. **Room is the primary aggregate of social presence.**
2. **Match is the primary aggregate of gameplay.**
3. **Tournament is the primary aggregate of structured competition.**
4. **Games are pluggable modules attached to matches.**
5. **Server is authoritative for all business-critical state.**
6. **Clients are presentation and interaction layers, not sources of truth.**
7. **Realtime communication is event-driven.**
8. **All meaningful actions should be loggable.**
9. **State must survive refresh and transient disconnects.**
10. **The first implementation must stay simple without damaging long-term extensibility.**

---

# 3. High-Level Architecture

## 3.1 Recommended logical modules

Split the backend into the following subdomains/modules:

### Identity & Session

Handles:

* guest identity
* future registered accounts
* session durability
* reconnect logic
* account linking later

### Room Management

Handles:

* room creation and closure
* room join/leave
* host assignment and transfer
* participant membership
* room policies
* room expiration
* room tables

### Presence & Realtime

Handles:

* connection lifecycle
* online/offline status
* room subscriptions
* match subscriptions
* reconnect and resync
* event fanout

### Match Engine

Handles:

* match creation
* match lifecycle
* seat/player assignment
* pause/resume
* completion/interruption
* interaction with game modules

### Game Runtime / Game Plugins

Handles:

* game-specific rules
* action validation
* game state transitions
* supported configuration
* match result resolution
* compatibility with bots/tournaments/spectators

### Tournament Engine

Handles:

* tournament creation
* entry registration
* bracket/scheduling model
* match generation
* tournament progress
* tournament-specific policies

### Chat & Communication

Handles:

* channels
* room chat
* match chat
* table chat
* tournament chat
* system messages
* visibility policies

### Logging / Analytics

Handles:

* event log
* operational logs
* future stats aggregation
* replay/debug support
* audit-ready data

### Administration / Moderation

Handles:

* active room inspection
* system controls
* timeout configuration
* force-close
* moderation-ready hooks

---

# 4. Domain Model

## 4.1 Main entities

Below is the recommended core domain model.

---

## 4.2 Identity

### UserIdentity

Represents a human identity known to the system, whether guest or registered.

**Fields**

* `identity_id`
* `identity_type` (`guest`, `registered`)
* `display_name`
* `avatar_url` nullable
* `account_id` nullable
* `created_at`
* `updated_at`
* `last_seen_at`
* `status`
* `metadata_json`

**Notes**

* In V1, most identities are guests.
* A guest identity should persist long enough to survive reload/reconnect.
* Later, a guest identity may be linked to an account.

---

## 4.3 Room

### Room

A social container where participants interact.

**Fields**

* `room_id`
* `public_code`
* `invite_token`
* `status`
* `visibility` (`private`, future `public`)
* `host_participant_id`
* `created_by_identity_id`
* `created_at`
* `updated_at`
* `last_activity_at`
* `expires_at` nullable
* `closed_at` nullable
* `close_reason` nullable
* `settings_json`

**Examples inside `settings_json`**

* join policy
* allow chat history visibility for newcomers
* inactivity timeout override
* vote policy defaults
* allowed games
* tournament options
* spectator visibility policy

---

## 4.4 Participant

### Participant

Represents an identity inside a room.

**Fields**

* `participant_id`
* `room_id`
* `identity_id`
* `status`
* `connection_status`
* `joined_at`
* `last_active_at`
* `left_at` nullable
* `current_table_id` nullable
* `current_match_id` nullable
* `is_host`
* `metadata_json`

**Status examples**

* `joining`
* `idle`
* `spectating`
* `playing`
* `waiting`
* `left`
* `kicked`

**Connection status**

* `connected`
* `disconnected_recoverable`
* `disconnected_expired`

---

## 4.5 Role model

You want cumulative and extensible roles, so avoid encoding them into one enum.

### ParticipantRoleAssignment

**Fields**

* `participant_role_assignment_id`
* `participant_id`
* `role_type`
* `scope_type` (`room`, `match`, `tournament`, `game`)
* `scope_id`
* `granted_by_participant_id` nullable
* `created_at`
* `expires_at` nullable
* `metadata_json`

**Examples**

* host at room scope
* moderator at room scope
* player at match scope
* spectator at match scope
* narrator at game scope
* referee at tournament scope

This model is much safer than a flat role field.

---

## 4.6 Table

### Table

A subspace within a room used to organize local activities.

**Fields**

* `table_id`
* `room_id`
* `table_type` (`lobby`, `match`, `tournament`, `custom`)
* `name`
* `status`
* `created_at`
* `closed_at` nullable
* `settings_json`

**Design note**
A room should always have at least one default lobby table.

---

## 4.7 Game catalog

### GameDefinition

Defines the capabilities and constraints of a game module.

**Fields**

* `game_key`
* `display_name`
* `version`
* `category`
* `min_players`
* `max_players`
* `supports_spectators`
* `supports_pause`
* `supports_resume`
* `supports_bots`
* `supports_tournament`
* `supports_save_resume`
* `parameter_schema_json`
* `communication_policy_schema_json`
* `metadata_json`

**Examples**

* connect_four
* werewolf
* uno
* mental_arithmetic
* sequence_guessing
* digit_memory

---

## 4.8 Match

### Match

A concrete playable game session.

**Fields**

* `match_id`
* `room_id`
* `table_id`
* `game_key`
* `tournament_id` nullable
* `state`
* `created_by_participant_id`
* `started_at` nullable
* `ended_at` nullable
* `paused_at` nullable
* `resumable`
* `termination_reason` nullable
* `winner_summary_json` nullable
* `config_json`
* `snapshot_state_json` nullable
* `metadata_json`

**State examples**

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

---

## 4.9 Match seats / players

### MatchSeat

Represents a playable slot in a match.

**Fields**

* `match_seat_id`
* `match_id`
* `seat_index`
* `team_index` nullable
* `actor_type` (`human`, `bot`)
* `participant_id` nullable
* `bot_id` nullable
* `seat_status`
* `joined_at`
* `left_at` nullable
* `metadata_json`

**Seat status**

* `reserved`
* `filled`
* `vacated`
* `replaced`

This is more robust than assuming “player = participant directly”.

---

## 4.10 Match actions

### MatchAction

Stores every action/coup if the game supports it.

**Fields**

* `match_action_id`
* `match_id`
* `sequence_number`
* `actor_type`
* `participant_id` nullable
* `bot_id` nullable
* `action_type`
* `action_payload_json`
* `validated`
* `applied_at`
* `resulting_state_hash` nullable

This becomes critical for:

* replay
* debugging
* analytics
* future bots
* cheat detection
* resumability

---

## 4.11 Tournament

### Tournament

First-class competition object.

**Fields**

* `tournament_id`
* `room_id`
* `state`
* `tournament_type`
* `game_selection_mode`
* `default_game_key` nullable
* `created_by_participant_id`
* `started_at` nullable
* `ended_at` nullable
* `rules_json`
* `metadata_json`

**Tournament types**

* `single_elimination`
* `double_elimination`
* `round_robin`
* `swiss`
* `custom`

**Game selection modes**

* `fixed_game`
* `game_pool`
* `player_choice`
* `host_choice`

---

## 4.12 Tournament entries

### TournamentEntry

A participant’s registration in a tournament.

**Fields**

* `tournament_entry_id`
* `tournament_id`
* `participant_id`
* `seed` nullable
* `status`
* `score_summary_json`
* `created_at`

**Status**

* `registered`
* `active`
* `eliminated`
* `withdrawn`
* `disqualified`
* `completed`

---

## 4.13 Tournament-match link

### TournamentMatch

Connects a generated competitive pairing to a match.

**Fields**

* `tournament_match_id`
* `tournament_id`
* `match_id` nullable
* `phase`
* `round_number`
* `bracket_position`
* `status`
* `depends_on_json`
* `scheduled_at` nullable
* `resolved_at` nullable
* `metadata_json`

This should not replace `Match`; it should wrap it.

---

## 4.14 Chat model

### ChatChannel

**Fields**

* `channel_id`
* `room_id`
* `scope_type` (`room`, `table`, `match`, `tournament`)
* `scope_id`
* `channel_policy_json`
* `created_at`

### ChatMessage

**Fields**

* `message_id`
* `channel_id`
* `sender_type` (`participant`, `system`)
* `sender_id` nullable
* `message_type` (`text`, `emoji`, `reaction`, `system`)
* `visibility_policy_json`
* `payload_json`
* `created_at`
* `edited_at` nullable
* `deleted_at` nullable

---

## 4.15 Votes / proposals

Since you want votes eventually, model them now.

### Proposal

**Fields**

* `proposal_id`
* `room_id`
* `scope_type`
* `scope_id`
* `proposal_type`
* `state`
* `created_by_participant_id`
* `rules_json`
* `payload_json`
* `created_at`
* `expires_at` nullable
* `resolved_at` nullable

### ProposalResponse

**Fields**

* `proposal_response_id`
* `proposal_id`
* `participant_id`
* `response_value`
* `responded_at`

---

## 4.16 Bots

### BotDefinition

**Fields**

* `bot_id`
* `game_key`
* `name`
* `version`
* `difficulty`
* `config_json`
* `metadata_json`

Important: bot is not a room participant in the default model.

---

## 4.17 Event log

### DomainEventLog

Universal event stream for business-relevant occurrences.

**Fields**

* `event_id`
* `event_type`
* `room_id` nullable
* `participant_id` nullable
* `table_id` nullable
* `match_id` nullable
* `tournament_id` nullable
* `actor_identity_id` nullable
* `payload_json`
* `occurred_at`

This is one of the most important tables in the whole platform.

---

# 5. Aggregate Boundaries

A practical aggregate strategy is needed so the system stays coherent.

## 5.1 Room aggregate

Root:

* `Room`

Includes transactional consistency around:

* participant membership
* host transfer
* room lifecycle
* room-level settings
* room tables

Do not force every match state update to go through the whole room aggregate if you want decent scalability.

## 5.2 Match aggregate

Root:

* `Match`

Includes:

* seats
* gameplay state
* action application
* pause/resume
* result resolution

This aggregate should be authoritative for gameplay.

## 5.3 Tournament aggregate

Root:

* `Tournament`

Includes:

* entries
* generated competition structure
* tournament progression logic

## 5.4 Chat channel aggregate

Root:

* `ChatChannel`

Includes:

* messages
* message visibility policy

---

# 6. State Machines

These are suitable starting points for UML state diagrams.

---

## 6.1 Room state machine

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

* `created -> open` when room becomes joinable
* `open -> active` when meaningful presence/activity exists
* `active -> idle` when no relevant activity remains
* `idle -> active` when activity resumes
* `idle -> expired` after inactivity timeout
* `active -> closing` when host/admin closes room
* `closing -> closed`
* `closed -> archived`
* `expired -> archived`

### Notes

Room state should depend on:

* participant presence
* open matches
* tournament activity
* last room activity timestamp

---

## 6.2 Participant state machine

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
* `playing -> disconnected_recoverable`
* `spectating -> disconnected_recoverable`
* `idle -> disconnected_recoverable`
* `disconnected_recoverable -> previous active state`
* `any -> left`
* `any -> kicked`

---

## 6.3 Match state machine

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
* `completed -> archived`
* `cancelled -> archived`
* `abandoned -> archived`

### Technical distinction

* `paused`: intentional pause
* `interrupted`: external disturbance such as disconnection
* `abandoned`: match cannot continue meaningfully
* `completed`: normal terminal state

---

## 6.4 Tournament state machine

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

## 6.5 Proposal/Vote state machine

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

# 7. Core Business Rules

## 7.1 Room rules

1. Every room has one host.
2. A room is private in V1.
3. Access is through invite link and code.
4. Host can configure join policy.
5. A room expires automatically after inactivity.
6. Expiration timeout is configurable by superadmin.
7. A room may contain multiple tables.
8. A room may contain multiple matches.
9. A room may have at most one active tournament in V1 unless later expanded.

## 7.2 Participant rules

1. A participant belongs to exactly one room at a time.
2. A participant may spectate without playing.
3. A participant may hold multiple roles.
4. A participant may not play in two matches simultaneously.
5. A participant may disconnect and recover.

## 7.3 Host rules

1. Host is the primary room authority.
2. Host may create tournaments.
3. Host may validate room-wide game changes.
4. Host may select players from volunteers.
5. Host may transfer host role.
6. If host disappears, system may auto-transfer host according to deterministic rule.

## 7.4 Match rules

1. Every match belongs to a room.
2. Every match belongs to a table.
3. A match uses exactly one game module.
4. A player quitting mid-match may trigger pause or interruption.
5. Match continuation depends on game support and room decision.
6. Match actions must be validated server-side.

## 7.5 Tournament rules

1. Tournaments are room-scoped.
2. Tournaments are created by host in V1.
3. Tournament matches are still ordinary matches underneath.
4. Players may continue other room activities while not currently playing.
5. Players may not be assigned to concurrent active matches.

## 7.6 Chat rules

1. Chat is stratified by scope.
2. Visibility depends on role and policy.
3. System messages are first-class messages.
4. Chat history visibility can be host-controlled.

---

# 8. Game Plugin Architecture

This is one of the most important technical decisions.

## 8.1 Why plugin architecture is needed

Your future game list is heterogeneous:

* Connect Four
* Werewolf
* UNO
* card games
* arithmetic games
* memory games
* sequence/pattern games

These cannot be cleanly modeled with one monolithic game engine.
They need a shared contract with game-specific implementations.

---

## 8.2 Game module contract

Each game should implement a contract like this conceptually:

### `GameModule`

Responsibilities:

* expose metadata
* validate configuration
* initialize match state
* validate player assignment
* validate actions
* apply actions
* determine terminal conditions
* determine winner/result
* expose spectator policy
* expose pause/reconnect support
* expose bot support
* serialize/deserialize state

---

## 8.3 Suggested interfaces

### `GameDefinitionProvider`

Returns static game capabilities and parameter schema.

### `GameConfigValidator`

Validates match setup options.

### `GameStateFactory`

Creates initial game state.

### `GameActionValidator`

Checks whether an action is legal in current state.

### `GameActionReducer`

Returns new state from current state + action.

### `GameOutcomeResolver`

Detects win/loss/draw/completion.

### `GameInterruptionPolicy`

Defines what to do on disconnect, pause, resume, abandonment.

### `GameVisibilityPolicy`

Defines who may see what chat/information.

### `GameBotAdapter`

Optional integration point for bots.

---

## 8.4 Match runtime contract

For any incoming action:

1. load current match state
2. load game module by `game_key`
3. validate actor eligibility
4. validate action through game module
5. apply action through game module
6. persist action log
7. persist new snapshot / derived state
8. detect terminal or pause condition
9. publish realtime events
10. write domain event log

---

# 9. Realtime Architecture

## 9.1 Required realtime channels

At minimum, the server should support logical subscription scopes:

* `room:{roomId}`
* `table:{tableId}`
* `match:{matchId}`
* `tournament:{tournamentId}`
* optionally `participant:{participantId}` for private invitations/notifications

## 9.2 Realtime event categories

### Presence events

* participant_joined
* participant_left
* participant_disconnected
* participant_reconnected
* host_transferred

### Room events

* room_updated
* room_closing
* room_closed
* room_expiring

### Table events

* table_created
* table_closed
* table_updated

### Match events

* match_created
* match_ready
* match_started
* match_paused
* match_interrupted
* match_resumed
* match_completed
* match_cancelled
* match_action_applied

### Tournament events

* tournament_created
* tournament_registration_opened
* tournament_started
* tournament_round_advanced
* tournament_match_assigned
* tournament_completed

### Chat events

* message_created
* message_updated
* reaction_added
* system_message_created

### Proposal events

* proposal_created
* proposal_opened
* proposal_resolved

---

## 9.3 Reconnect strategy

On reconnect:

1. authenticate session/guest token
2. restore identity
3. restore participant binding in room
4. resubscribe client to relevant channels
5. send state resync payload:

   * room snapshot
   * participant snapshot
   * current match snapshot if relevant
   * missed events since last known sequence if available

### Recommendation

Use:

* server-side sequence numbers
* per-channel event ordering
* idempotent client reducers

---

# 10. Persistence Strategy

## 10.1 Recommended storage pattern

Use a hybrid model:

### Current-state tables

For operational reads and normal UI rendering:

* rooms
* participants
* tables
* matches
* match_seats
* tournaments
* chat_channels
* chat_messages

### Event log tables

For analytics, audit, replay, debugging:

* domain_event_log
* match_actions

This is better than full event sourcing for V1, while still giving you historical richness.

---

## 10.2 Suggested relational schema groups

### Identity/session tables

* `user_identity`
* `guest_session`
* future `account`

### Room tables

* `room`
* `participant`
* `participant_role_assignment`
* `room_table`

### Match tables

* `match`
* `match_seat`
* `match_action`

### Tournament tables

* `tournament`
* `tournament_entry`
* `tournament_match`

### Chat tables

* `chat_channel`
* `chat_message`

### Governance tables

* `proposal`
* `proposal_response`

### Logging/admin tables

* `domain_event_log`
* `admin_audit_log`

---

## 10.3 Snapshot policy

For matches, store both:

* fine-grained actions
* occasional full state snapshots

Why:

* replay from zero every time becomes expensive
* debugging and reconnect become simpler
* later bot analysis benefits from both representations

For Connect Four, snapshots are cheap and easy.

---

# 11. API / Service Contract Outline

This is not a full REST or websocket spec, but a technical structure.

## 11.1 Room service operations

* create room
* join room
* leave room
* transfer host
* close room
* list room participants
* create table
* update room settings

## 11.2 Match service operations

* create match
* volunteer for match
* assign players
* invite player
* start match
* pause match
* resume match
* abandon match
* archive match
* submit action

## 11.3 Tournament service operations

* create tournament
* open registration
* register participant
* start tournament
* generate round/matches
* resolve match result
* advance bracket
* cancel tournament

## 11.4 Chat service operations

* send message
* react to message
* fetch channel history
* create system message

## 11.5 Presence service operations

* connect
* disconnect
* heartbeat
* reconnect
* resync state

## 11.6 Proposal service operations

* create proposal
* respond to proposal
* resolve proposal

---

# 12. Implementation Guidance for Connect Four V1

Connect Four should be used as the reference implementation of the game plugin model.

## 12.1 Connect Four capabilities

* 2 players
* spectators allowed
* pause supported
* resume supported
* full action history supported
* tournament compatible
* bot-compatible later

## 12.2 Connect Four state model

Store:

* board matrix
* current turn
* player seat mapping
* move count
* match status
* winner nullable
* winning alignment nullable

## 12.3 Connect Four action model

Action:

* `drop_disc(column_index)`

Validation:

* actor must be current player
* column must be valid
* column must not be full
* match must be active

Reducer:

* place disc
* switch turn if not terminal
* detect win/draw

## 12.4 Why Connect Four is ideal as first implementation

It exercises:

* player assignment
* turn logic
* state snapshotting
* action logs
* reconnect
* spectators
* tournament compatibility

---

# 13. Tournament Technical Design

## 13.1 V1 recommendation

Model tournaments broadly, implement one format concretely:

* `single_elimination`

## 13.2 Why this is the best compromise

You want tournaments to be major, but V1 should remain deliverable.

So:

* model all types
* fully implement one type
* keep `tournament_type` abstract

## 13.3 Tournament scheduling policy

Since you want players to be able to delay or roam socially:

* tournament match assignment should not assume strict immediate execution
* tournament match objects should allow `scheduled`, `waiting`, `ready`, `in_progress`, `completed`

This prevents over-coupling tournament logic to immediate match launch.

---

# 14. Host Transfer Policy

You explicitly asked what to do when the host disconnects.

## Recommended technical policy

### For private rooms in V1

If host disconnects:

1. mark host as `disconnected_recoverable`
2. start host grace timer
3. if reconnects in time, keep host
4. if not, auto-transfer to best eligible participant

### Default eligibility rule

Pick:

* connected participant
* longest continuously present
* not already leaving
* deterministic tie-breaker by join timestamp then participant_id

This is much safer than instant transfer.

---

# 15. Chat Visibility Model

Because your communication model is layered and permission-sensitive, the message visibility policy must not be hardcoded only in frontend logic.

## 15.1 Recommended visibility policy structure

Each message/channel should resolve visibility using:

* room-level default policy
* game-specific override
* match-specific override
* sender role
* recipient role

## 15.2 Simple V1 implementation

V1 may implement only:

* room chat visible to all room participants
* system messages visible to all room participants

But the model should already support:

* players only
* spectators read-only
* host/moderator-only
* tournament-only

---

# 16. Logging and Analytics Design

You clearly want rich stats later, so this must be designed from the start.

## 16.1 Operational logging

Used for engineering:

* errors
* websocket disconnects
* failed actions
* performance timings

## 16.2 Domain event logging

Used for product/business:

* room created
* participant joined
* match started
* move played
* match paused
* tournament advanced

## 16.3 Future analytics examples

Later, this can support:

* average session duration
* win rate by game
* abandonment rate
* reconnect frequency
* room survival time
* tournament participation rate
* player progression in cognitive games
* move pattern analysis
* bot training data

---

# 17. Security and Integrity Rules

## 17.1 Server authority

The client must never be allowed to:

* declare itself winner
* assign itself as player
* modify game state directly
* bypass host rules
* bypass room permissions

## 17.2 Required validations

For every critical action:

* identity valid
* participant valid in room
* permission valid
* match state valid
* game action valid
* action sequence valid

## 17.3 Invite/code security

Room access should use:

* hard-to-guess invite token
* human-friendly short code
* server-side access validation

---

# 18. Suggested UML Derivations

This document is now sufficient to derive the following UML artifacts.

## 18.1 Class diagrams

At minimum:

* UserIdentity
* Room
* Participant
* ParticipantRoleAssignment
* Table
* GameDefinition
* Match
* MatchSeat
* MatchAction
* Tournament
* TournamentEntry
* TournamentMatch
* ChatChannel
* ChatMessage
* Proposal
* ProposalResponse
* BotDefinition
* DomainEventLog

## 18.2 State diagrams

At minimum:

* Room
* Participant
* Match
* Tournament
* Proposal

## 18.3 Sequence diagrams

Highly recommended first:

* create room
* join room as guest
* reconnect after refresh
* create Connect Four match
* assign players and start match
* submit Connect Four move
* disconnect during match and resume
* create tournament
* assign tournament match
* auto-transfer host after timeout

---

# 19. Delivery Plan

## 19.1 Phase 0 — technical foundation

Build:

* backend project structure
* identity/session model
* room model
* realtime transport
* event log table
* base database migrations
* shared authorization helpers

## 19.2 Phase 1 — room core

Build:

* create/join/leave room
* host assignment
* participant presence
* room expiration
* lobby table
* basic room state sync

## 19.3 Phase 2 — chat core

Build:

* room chat
* system messages
* recent history retrieval
* realtime fanout

## 19.4 Phase 3 — match engine core

Build:

* generic match lifecycle
* seat assignment
* player volunteering/invitation
* pause/resume
* action submission pipeline

## 19.5 Phase 4 — Connect Four plugin

Build:

* game definition
* game state
* move validation
* result resolution
* snapshot persistence
* spectator updates

## 19.6 Phase 5 — reconnect and recovery

Build:

* reconnect token flow
* participant reattachment
* missed-event or snapshot resync
* interrupted match recovery

## 19.7 Phase 6 — tournament baseline

Build:

* tournament domain model
* host creates tournament
* simple single elimination
* tournament-to-match linkage
* room-visible tournament status

## 19.8 Phase 7 — admin baseline

Build:

* list active rooms
* inspect room state
* set inactivity timeout
* force close room

---

# 20. V1 Acceptance Criteria

A solid V1 should satisfy all of the following:

1. A guest can create a private room.
2. Another guest can join using link/code.
3. Participants remain visible in the room.
4. Host is clearly identified.
5. Room survives page refresh.
6. Participants can chat in room chat.
7. Host can create a Connect Four match.
8. Players can be assigned from available participants.
9. A Connect Four match can start and be played fully.
10. Actions are validated server-side.
11. Moves are persisted.
12. Spectators can observe the match.
13. A disconnect during match does not destroy state.
14. A reconnect can restore the match state.
15. Room inactivity eventually triggers expiration.
16. Core events are logged.

---

# 21. Technical Risks

## 21.1 Overbuilding too early

You want many advanced features.
The risk is not the model being too rich; the risk is implementing all of it immediately.

Mitigation:

* keep architecture broad
* keep first implementation narrow

## 21.2 Role explosion

Extensible roles can become messy fast.

Mitigation:

* role assignment table
* scope-based role semantics
* policy-driven checks

## 21.3 Tournament complexity

Tournament logic can easily dominate the whole system.

Mitigation:

* treat tournament as wrapper around matches
* implement one format first
* decouple scheduling from immediate gameplay launch

## 21.4 State synchronization bugs

Realtime + reconnect + multiple scopes create consistency risks.

Mitigation:

* server authoritative state
* monotonic event sequencing
* snapshot resync fallback
* strong domain logging
