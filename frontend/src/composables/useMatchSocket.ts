import { onUnmounted, ref } from 'vue'

function defaultWsBase(): string {
    if (typeof window === 'undefined') {
        return 'ws://localhost:8000'
    }
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${wsProtocol}//${window.location.host}`
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface WsOutcome {
    termination_reason: string          // 'resign', 'checkmate', 'draw', etc.
    winner_summary: Record<string, unknown>
    actor_participant_id: string | null // who triggered the end
}

export interface WsStateUpdate {
    type: 'state_update'
    game_state: Record<string, unknown>
    match_state: string
    seats?: Array<{
        seat_index: number
        participant_id: string | null
        display_name: string | null
        actor_type: string
    }>
    my_seat_index?: number | null
    outcome?: WsOutcome                 // present only when match_state === 'completed'
}

export interface WsChatMessage {
    type: 'chat_message'
    message: {
        id: string
        sender_id: string
        display_name: string | null
        text: string
        created_at: string
    }
}

export interface WsReaction {
    type: 'reaction'
    sender_id: string
    emoji: string
}

export interface WsError {
    type: 'error'
    message: string
}

export interface WsRematch {
    type: 'rematch_request'
    rematch_match_id: string
}

export type WsEvent = WsStateUpdate | WsChatMessage | WsReaction | WsError | WsRematch

// ── Composable ─────────────────────────────────────────────────────────────

const WS_BASE = import.meta.env.VITE_WS_URL ?? defaultWsBase()
const MAX_RETRIES = 5
const BACKOFF_BASE_MS = 1000

export function useMatchSocket(matchId: string) {
    const isConnected = ref(false)
    const error = ref<string | null>(null)

    let ws: WebSocket | null = null
    let retries = 0
    let retryTimeout: ReturnType<typeof setTimeout> | null = null

    // Typed event listeners
    const listeners: { [K in WsEvent['type']]: Array<(e: Extract<WsEvent, { type: K }>) => void> } = {
        state_update: [],
        chat_message: [],
        reaction: [],
        error: [],
        rematch_request: [],
    }

    function on<K extends WsEvent['type']>(
        type: K,
        handler: (e: Extract<WsEvent, { type: K }>) => void,
    ) {
        ; (listeners[type] as Array<(e: Extract<WsEvent, { type: K }>) => void>).push(handler)
    }

    function off<K extends WsEvent['type']>(
        type: K,
        handler: (e: Extract<WsEvent, { type: K }>) => void,
    ) {
        const arr = listeners[type] as Array<unknown>
        const idx = arr.indexOf(handler)
        if (idx !== -1) arr.splice(idx, 1)
    }

    function emit<K extends WsEvent['type']>(type: K, event: Extract<WsEvent, { type: K }>) {
        ; (listeners[type] as Array<(e: Extract<WsEvent, { type: K }>) => void>).forEach((h) =>
            h(event),
        )
    }

    // ── Connection management ──────────────────────────────────────────────

    function connect() {
        if (ws && ws.readyState === WebSocket.OPEN) return

        ws = new WebSocket(`${WS_BASE}/ws/matches/${matchId}/`)

        ws.onopen = () => {
            isConnected.value = true
            error.value = null
            retries = 0
        }

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data) as WsEvent
                emit(data.type as WsEvent['type'], data as never)
            } catch {
                console.error('[MatchSocket] Failed to parse message', event.data)
            }
        }

        ws.onerror = () => {
            error.value = 'WebSocket error'
        }

        ws.onclose = () => {
            isConnected.value = false
            ws = null
            if (retries < MAX_RETRIES) {
                const delay = BACKOFF_BASE_MS * 2 ** retries
                retries++
                retryTimeout = setTimeout(connect, delay)
            } else {
                error.value = 'Connection lost. Please refresh.'
            }
        }
    }

    function disconnect() {
        if (retryTimeout) {
            clearTimeout(retryTimeout)
            retryTimeout = null
        }
        if (ws) {
            ws.onclose = null // prevent reconnect loop on intentional close
            ws.close()
            ws = null
        }
        isConnected.value = false
    }

    // ── Send helpers ───────────────────────────────────────────────────────

    function send(payload: Record<string, unknown>) {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.warn('[MatchSocket] Cannot send — socket not open')
            return
        }
        ws.send(JSON.stringify(payload))
    }

    function sendAction(actionType: string, actionPayload: Record<string, unknown>) {
        send({ type: 'action', action_type: actionType, action_payload: actionPayload })
    }

    function sendChat(text: string) {
        send({ type: 'chat', text })
    }

    function sendReaction(emoji: string) {
        send({ type: 'reaction', emoji })
    }

    function sendRematchRequest() {
        send({ type: 'request_rematch' })
    }

    // ── Auto-cleanup ───────────────────────────────────────────────────────

    connect()
    onUnmounted(disconnect)

    return {
        isConnected,
        error,
        on,
        off,
        disconnect,
        sendAction,
        sendChat,
        sendReaction,
        sendRematchRequest,
    }
}
