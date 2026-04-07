import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { identityApi, type IdentityProfile } from '@/api'

function initialsFor(name: string): string {
    const trimmed = name.trim()
    if (!trimmed) return '??'
    const parts = trimmed.split(/\s+/).filter(Boolean)
    if (parts.length >= 2) {
        return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
    }
    return trimmed.slice(0, 2).toUpperCase()
}

export const useUserStore = defineStore('user', () => {
    const identity = ref<IdentityProfile | null>(null)
    const hydrated = ref(false)
    const loading = ref(false)
    const error = ref<string | null>(null)
    const avatarColor = ref('#007AFF')

    const hasProfile = computed(() => identity.value !== null)
    const displayName = computed(() => identity.value?.display_name ?? '')
    const initials = computed(() => initialsFor(displayName.value))
    const isGuest = computed(() => (identity.value?.identity_type ?? 'guest') === 'guest')

    const setIdentity = (value: IdentityProfile | null) => {
        identity.value = value
    }

    const fetchMe = async () => {
        loading.value = true
        error.value = null
        try {
            const result = await identityApi.me()
            setIdentity(result.identity)
            hydrated.value = true
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Failed to load profile'
            hydrated.value = true
        } finally {
            loading.value = false
        }
    }

    const ensureHydrated = async () => {
        if (hydrated.value) return
        await fetchMe()
    }

    const createGuestProfile = async (name?: string) => {
        loading.value = true
        error.value = null
        try {
            const result = await identityApi.createGuest(name?.trim() || undefined)
            setIdentity(result.identity)
            hydrated.value = true
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Failed to create profile'
            throw e
        } finally {
            loading.value = false
        }
    }

    const updateDisplayName = async (name: string) => {
        const trimmed = name.trim()
        if (!trimmed) throw new Error('Display name is required.')
        loading.value = true
        error.value = null
        try {
            const result = await identityApi.updateMe(trimmed)
            setIdentity(result.identity)
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Failed to update profile'
            throw e
        } finally {
            loading.value = false
        }
    }

    const deleteProfile = async () => {
        loading.value = true
        error.value = null
        try {
            await identityApi.deleteMe()
            setIdentity(null)
            hydrated.value = true
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Failed to delete profile'
            throw e
        } finally {
            loading.value = false
        }
    }

    return {
        identity,
        hydrated,
        loading,
        error,
        displayName,
        initials,
        isGuest,
        hasProfile,
        avatarColor,
        fetchMe,
        ensureHydrated,
        createGuestProfile,
        updateDisplayName,
        deleteProfile,
    }
})
