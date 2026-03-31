import { defineStore } from 'pinia'
import { ref } from 'vue'
import { roomApi } from '@/api'
import type { RoomDetail } from '@/api'

export const useRoomStore = defineStore('room', () => {
    const detail = ref<RoomDetail | null>(null)
    const loading = ref(false)
    const error = ref<string | null>(null)

    const fetchRoom = async (roomCode: string) => {
        loading.value = true
        error.value = null
        try {
            detail.value = await roomApi.detail(roomCode)
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Unknown error'
        } finally {
            loading.value = false
        }
    }

    const clear = () => {
        detail.value = null
        error.value = null
    }

    return { detail, loading, error, fetchRoom, clear }
})
