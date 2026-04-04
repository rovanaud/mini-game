import { onUnmounted, ref } from 'vue'

function defaultWsBase(): string {
    if (typeof window === 'undefined') {
        return 'ws://localhost:8000'
    }
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${wsProtocol}//${window.location.host}`
}

const WS_BASE = import.meta.env.VITE_WS_URL ?? defaultWsBase()
const MAX_RETRIES = 5
const BACKOFF_BASE_MS = 1000

export interface RoomEvent {
    type: 'room_event'
    event: string
    room_code: string
    payload: Record<string, unknown>
}

export interface RoomChatMessage {
    id: string
    sender_id: string | null
    display_name: string | null
    text: string
    created_at: string
}

export interface RoomChatMessageEvent {
    type: 'room_chat_message'
    message: RoomChatMessage
}

export interface RoomChatHistoryEvent {
    type: 'room_chat_history'
    messages: RoomChatMessage[]
}

export interface RoomSocketErrorEvent {
    type: 'error'
    message: string
}

export type RoomSocketEvent =
    | RoomEvent
    | RoomChatMessageEvent
    | RoomChatHistoryEvent
    | RoomSocketErrorEvent

export interface RoomsEvent {
    type: 'rooms_event'
    event: string
    room_code?: string
    payload: Record<string, unknown>
}

export function useRoomSocket(roomCode: string) {
    const isConnected = ref(false)
    const error = ref<string | null>(null)

    let ws: WebSocket | null = null
    let retries = 0
    let retryTimeout: ReturnType<typeof setTimeout> | null = null

    const listeners: {
        [K in RoomSocketEvent['type']]: Array<
            (event: Extract<RoomSocketEvent, { type: K }>) => void
        >
    } = {
        room_event: [],
        room_chat_message: [],
        room_chat_history: [],
        error: [],
    }

    function on<K extends RoomSocketEvent['type']>(
        type: K,
        handler: (event: Extract<RoomSocketEvent, { type: K }>) => void,
    ) {
        ; (
            listeners[type] as Array<
                (event: Extract<RoomSocketEvent, { type: K }>) => void
            >
        ).push(handler)
    }

    function off<K extends RoomSocketEvent['type']>(
        type: K,
        handler: (event: Extract<RoomSocketEvent, { type: K }>) => void,
    ) {
        const arr = listeners[type] as Array<unknown>
        const idx = arr.indexOf(handler)
        if (idx !== -1) arr.splice(idx, 1)
    }

    function emit<K extends RoomSocketEvent['type']>(
        type: K,
        event: Extract<RoomSocketEvent, { type: K }>,
    ) {
        ; (
            listeners[type] as Array<
                (event: Extract<RoomSocketEvent, { type: K }>) => void
            >
        ).forEach((h) => h(event))
    }

    function connect() {
        if (ws && ws.readyState === WebSocket.OPEN) return

        ws = new WebSocket(`${WS_BASE}/ws/rooms/${encodeURIComponent(roomCode)}/`)

        ws.onopen = () => {
            isConnected.value = true
            error.value = null
            retries = 0
        }

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data) as RoomSocketEvent
                emit(data.type as RoomSocketEvent['type'], data as never)
            } catch {
                console.error('[RoomSocket] Failed to parse message', event.data)
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
            ws.onclose = null
            ws.close()
            ws = null
        }
        isConnected.value = false
    }

    function send(payload: Record<string, unknown>) {
        if (!ws || ws.readyState !== WebSocket.OPEN) return
        ws.send(JSON.stringify(payload))
    }

    function sendChat(text: string) {
        send({ type: 'chat', text })
    }

    connect()
    onUnmounted(disconnect)

    return {
        isConnected,
        error,
        on,
        off,
        disconnect,
        sendChat,
    }
}

export function useRoomsUpdatesSocket() {
    const isConnected = ref(false)
    const error = ref<string | null>(null)
    const listeners: Array<(event: RoomsEvent) => void> = []

    let ws: WebSocket | null = null
    let retries = 0
    let retryTimeout: ReturnType<typeof setTimeout> | null = null

    function on(handler: (event: RoomsEvent) => void) {
        listeners.push(handler)
    }

    function off(handler: (event: RoomsEvent) => void) {
        const index = listeners.indexOf(handler)
        if (index >= 0) listeners.splice(index, 1)
    }

    function emit(event: RoomsEvent) {
        listeners.forEach((handler) => handler(event))
    }

    function connect() {
        if (ws && ws.readyState === WebSocket.OPEN) return

        ws = new WebSocket(`${WS_BASE}/ws/rooms/updates/`)

        ws.onopen = () => {
            isConnected.value = true
            error.value = null
            retries = 0
        }

        ws.onmessage = (event) => {
            try {
                emit(JSON.parse(event.data) as RoomsEvent)
            } catch {
                console.error('[RoomsUpdatesSocket] Failed to parse message', event.data)
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
            ws.onclose = null
            ws.close()
            ws = null
        }
        isConnected.value = false
    }

    connect()
    onUnmounted(disconnect)

    return {
        isConnected,
        error,
        on,
        off,
        disconnect,
    }
}
