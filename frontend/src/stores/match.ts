import { defineStore } from 'pinia'
import { ref } from 'vue'
import { matchApi } from '@/api'
import type { MatchDetail } from '@/api'

export const useMatchStore = defineStore('match', () => {
    const matchId = ref<string | null>(null)
    const detail = ref<MatchDetail | null>(null)
    const loading = ref(false)
    const error = ref<string | null>(null)

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

    const submitAction = async (actionType: string, actionPayload: Record<string, unknown>) => {
        if (!matchId.value) return
        error.value = null
        try {
            const result = await matchApi.submitAction(matchId.value, actionType, actionPayload)
            // Patch game_state in place — no full re-fetch needed
            if (detail.value) {
                detail.value.game_state = result.game_state
                detail.value.match_state = result.match_state
            }
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Unknown error'
        }
    }

    const clear = () => {
        matchId.value = null
        detail.value = null
        error.value = null
    }

    return { matchId, detail, loading, error, fetchMatch, submitAction, clear }
})
