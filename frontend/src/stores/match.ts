import { defineStore } from 'pinia'
import { ref } from 'vue'
import { matchApi } from '@/api'
import type { MatchDetail } from '@/api'

export const useMatchStore = defineStore('match', () => {
    const matchId = ref<string | null>(null)
    const detail = ref<MatchDetail | null>(null)
    const loading = ref(false)
    const error = ref<string | null>(null)

    // Initial HTTP load — fetches config + seats (also provided by WS on connect,
    // but HTTP gives us something to render before the socket opens)
    const fetchMatch = async (id: string) => {
        loading.value = true
        error.value = null
        try {
            detail.value = await matchApi.detail(id)
            matchId.value = id
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Unknown error'
        } finally {
            loading.value = false
        }
    }

    // Called by useMatchSocket when a state_update event arrives
    const applyStateUpdate = (
        gameState: Record<string, unknown>,
        matchState: string,
    ) => {
        if (detail.value) {
            detail.value.game_state = gameState
            detail.value.match_state = matchState
        }
    }

    // Kept as HTTP fallback (e.g. reconnect after network loss)
    const refreshMatch = async () => {
        if (!matchId.value) return
        await fetchMatch(matchId.value)
    }

    const clear = () => {
        matchId.value = null
        detail.value = null
        error.value = null
    }

    return { matchId, detail, loading, error, fetchMatch, applyStateUpdate, refreshMatch, clear }
})
