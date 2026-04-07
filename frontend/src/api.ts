// All calls go through /api/* which Vite proxies to http://localhost:8000
const BASE = '/api'

async function request<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
        credentials: 'include',   // sends guest_session_token cookie
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers ?? {}),
        },
        ...options,
    })
    if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${res.status}`)
    }
    return res.json() as Promise<T>
}

// ── Rooms ─────────────────────────────────────────────────────
export const roomApi = {
    list: () =>
        request<{ rooms: RoomSummary[] }>('/rooms/'),

    detail: (roomCode: string) =>
        request<RoomDetail>(`/rooms/${roomCode}/`),

    create: (displayName?: string) =>
        request<RoomCreated>('/rooms/create/', {
            method: 'POST',
            body: JSON.stringify({ display_name: displayName }),
        }),

    join: (roomCode: string, displayName?: string) =>
        request<RoomJoined>('/rooms/join/', {
            method: 'POST',
            body: JSON.stringify({ room_code: roomCode, display_name: displayName }),
        }),
    leave: (roomCode: string) =>
        request<{ ok: boolean; deleted: boolean }>(`/rooms/${roomCode}/leave/`, {
            method: 'POST',
        }),

    startGame: (roomCode: string, gameId: string, playersIds: string[]) =>
        request<StartGameResult>(`/rooms/${roomCode}/start/`, {
            method: 'POST',
            body: JSON.stringify({ game_id: gameId, players_ids: playersIds }),
        }),
    respondProposal: (roomCode: string, proposalId: string, response: ProposalResponseChoice) =>
        request<{ proposal: RoomProposal }>(`/rooms/${roomCode}/proposals/${proposalId}/respond/`, {
            method: 'POST',
            body: JSON.stringify({ response }),
        }),
    rename: (roomCode: string, name: string) =>
        request<{ name: string }>(`/rooms/${roomCode}/rename/`, {
            method: 'POST',
            body: JSON.stringify({ name }),
        }),
}

// ── Identities ───────────────────────────────────────────────
export const identityApi = {
    me: () => request<{ identity: IdentityProfile | null }>('/identities/me/'),
    createGuest: (displayName?: string) =>
        request<{ identity: IdentityProfile }>('/identities/guest/', {
            method: 'POST',
            body: JSON.stringify({ display_name: displayName }),
        }),
    updateMe: (displayName: string) =>
        request<{ identity: IdentityProfile }>('/identities/me/', {
            method: 'PATCH',
            body: JSON.stringify({ display_name: displayName }),
        }),
    deleteMe: () =>
        request<{ deleted: boolean }>('/identities/me/', {
            method: 'DELETE',
        }),
}

// ── Matches ───────────────────────────────────────────────────
export const matchApi = {
    detail: (matchId: string) =>
        request<MatchDetail>(`/matches/${matchId}/`),

    submitAction: (matchId: string, actionType: string, actionPayload: Record<string, unknown>) =>
        request<ActionResult>(`/matches/${matchId}/actions/`, {
            method: 'POST',
            body: JSON.stringify({ action_type: actionType, action_payload: actionPayload }),
        }),
}

// ── Chat ──────────────────────────────────────────────────────
export const chatApi = {
    getRoomChat: (roomCode: string) =>
        request<ChatHistory>(`/chat/rooms/${roomCode}/`),

    postRoomChat: (roomCode: string, text: string) =>
        request<{ message: ChatMessageDTO }>(`/chat/rooms/${roomCode}/`, {
            method: 'POST',
            body: JSON.stringify({ text }),
        }),
}

export interface ChatMessageDTO {
    id: string
    sender_type: string
    sender_id: string
    type: string
    status: string
    payload: Record<string, unknown>
    created_at: string
    edited_at: string | null
    deleted_at: string | null
}

export interface ChatHistory {
    channel_id: string | null
    messages: ChatMessageDTO[]
}

// ── Types ─────────────────────────────────────────────────────
export interface RoomSummary {
    room_id: string
    public_code: string
    name: string
    created_at: string
    participant_count?: number
}

export interface RoomParticipant {
    participant_id: string
    display_name: string | null
    is_me: boolean
    is_host?: boolean
}

export interface RoomDetail {
    room_id: string
    public_code: string
    name: string
    is_host: boolean
    available_games: { game_id: string; display_name: string }[]
    participants: RoomParticipant[]
    active_match_id: string | null
    my_participant_id: string | null
    pending_proposals: RoomProposal[]
}

export interface ProposalVote {
    participant_id: string
    display_name: string | null
    response: ProposalResponseChoice
    responded_at: string | null
}

export type ProposalResponseChoice = 'pending' | 'yes' | 'no' | 'abstain'

export interface RoomProposal {
    proposal_id: string
    proposal_type: string
    state: string
    payload: Record<string, unknown>
    rules: Record<string, unknown>
    result: Record<string, unknown>
    created_by_participant_id: string
    created_at: string
    resolved_at: string | null
    expires_at: string | null
    responses: ProposalVote[]
    my_response: ProposalResponseChoice | null
    can_respond: boolean
}

export interface RoomCreated {
    room_id: string
    public_code: string
    name: string
    participant_id: string
}

export interface RoomJoined {
    room_id: string
    public_code: string
    name: string
    participant_id: string
}

export interface StartGameResult {
    proposal_id: string
    state: string
    match_id: string | null
}

export interface MatchSeat {
    seat_index: number
    participant_id: string | null
    display_name: string | null
    actor_type: string
}

export interface MatchDetail {
    match_id: string
    room_id: string
    room_code: string
    game_key: string
    game_config: Record<string, unknown>
    game_state: Record<string, unknown>
    match_state: string
    seats: MatchSeat[]
    my_seat_index: number | null
}

export interface ActionResult {
    match_state: string
    game_state: Record<string, unknown>
}

export interface IdentityProfile {
    identity_id: string
    display_name: string
    identity_type: 'guest' | 'registered'
    status: string
    avatar_url: string | null
    created_at: string
}
