import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
    // ── State ───────────────────────────────────────────────────
    const displayName = ref('Alex')
    const initials = ref('AL')
    const isGuest = ref(true)
    const avatarColor = ref('#007AFF')

    // ── Actions ─────────────────────────────────────────────────
    const setUser = (name: string, guest: boolean = true, color: string = '#007AFF') => {
        displayName.value = name
        isGuest.value = guest
        initials.value = name.slice(0, 2).toUpperCase()
        avatarColor.value = color
    }

    const clearUser = () => {
        displayName.value = ''
        initials.value = ''
        isGuest.value = true
    }

    return {
        displayName,
        initials,
        isGuest,
        avatarColor,
        setUser,
        clearUser,
    }
})
