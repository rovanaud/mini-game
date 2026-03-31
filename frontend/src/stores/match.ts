import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Match } from '@/types'

export const useMatchStore = defineStore('match', () => {
    // ── State ───────────────────────────────────────────────────
    const currentMatchId = ref<string | null>(null)
    const match = ref<Match>({
        id: '',
        game_key: '',
        game_config: {},
        game_state: {},
        config: {
            timer: {
                enabled: false,
                mode: 'per_move',
                allow_time_request: false,

            },
        }
    })

    // ── Actions ─────────────────────────────────────────────────
    const enterMatch = (matchId: string, matchData: Match) => {
        currentMatchId.value = matchId
        match.value = matchData
    }

    const leaveMatch = () => {
        currentMatchId.value = null
        match.value = {
            id: '',
            game_key: '',
            game_config: {},
            game_state: {},
            config: {
                timer: {
                    enabled: false,
                    mode: 'per_move',
                    allow_time_request: false,

                },
            }
        }
    }

    const submitAction = (action: { type: string; payload: Record<string, unknown> }) => {
        // TODO: send to WebSocket
        console.log('Match action:', action)
    }

    return {
        currentMatchId,
        match,
        enterMatch,
        leaveMatch,
        submitAction,
    }
})
