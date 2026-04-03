import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const TERMINAL_MATCH_STATES = new Set(['completed', 'cancelled', 'abandoned'])

export const useActiveMatchStore = defineStore('activeMatch', () => {
    const matchId = ref<string | null>(null)
    const roomCode = ref<string | null>(null)
    const matchState = ref<string | null>(null)
    const hasUnreadAttention = ref(false)

    const hasActiveMatch = computed(
        () =>
            !!matchId.value &&
            !!matchState.value &&
            !TERMINAL_MATCH_STATES.has(matchState.value),
    )

    const setActiveMatch = (payload: {
        matchId: string
        roomCode?: string
        matchState?: string
    }) => {
        matchId.value = payload.matchId
        if (payload.roomCode) roomCode.value = payload.roomCode
        matchState.value = payload.matchState ?? 'in_progress'
    }

    const updateMatchState = (state: string) => {
        matchState.value = state
        if (TERMINAL_MATCH_STATES.has(state)) clear()
    }

    const markAttention = () => {
        if (!hasActiveMatch.value) return
        hasUnreadAttention.value = true
    }

    const clearAttention = () => {
        hasUnreadAttention.value = false
    }

    const clear = () => {
        matchId.value = null
        roomCode.value = null
        matchState.value = null
        hasUnreadAttention.value = false
    }

    return {
        matchId,
        roomCode,
        matchState,
        hasActiveMatch,
        hasUnreadAttention,
        setActiveMatch,
        updateMatchState,
        markAttention,
        clearAttention,
        clear,
    }
})
