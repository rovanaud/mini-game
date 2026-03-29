// ── Timer ─────────────────────────────────────────────────────
export interface TimerConfig {
    enabled: boolean
    mode: 'per_move' | 'total'
    seconds_per_move?: number
    total_seconds?: number
    allow_time_request: boolean
    time_request_seconds?: number
    max_time_requests?: number
}

// ── Generic match shell ───────────────────────────────────────
export interface MatchConfig {
    timer: TimerConfig
    [key: string]: unknown   // allows game-specific fields to coexist
}

export interface Match {
    id: string
    game_key: string
    game_config: Record<string, unknown>  // typed per-game (see below)
    game_state: Record<string, unknown>   // typed per-game
    config: MatchConfig
}
