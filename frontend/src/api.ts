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

    startGame: (roomCode: string, gameId: string, playersIds: string[]) =>
        request<{ match_id: string; game_key: string }>(`/rooms/${roomCode}/start/`, {
            method: 'POST',
            body: JSON.stringify({ game_id: gameId, players_ids: playersIds }),
        }),
    rename: (roomCode: string, name: string) =>
        request<{ name: string }>(`/rooms/${roomCode}/rename/`, {
            method: 'POST',
            body: JSON.stringify({ name }),
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

// ── Types ─────────────────────────────────────────────────────
export interface RoomSummary {
    room_id: string
    public_code: string
    name: string
    created_at: string
}

export interface RoomParticipant {
    participant_id: string
    display_name: string | null
    is_me: boolean
}

export interface RoomDetail {
    room_id: string
    public_code: string
    name: string
    participants: RoomParticipant[]
    active_match_id: string | null
    my_participant_id: string | null
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

export interface MatchSeat {
    seat_index: number
    participant_id: string | null
    display_name: string | null
    actor_type: string
}

export interface MatchDetail {
    match_id: string
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
