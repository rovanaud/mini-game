<template>
  <div class="min-h-[100dvh] pb-24" style="background-color: #F2F2F7">
    <header class="sticky top-0 z-50 px-4 py-4 flex items-center justify-between"
            style="background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); border-bottom: 1px solid #E5E5EA">
      <div class="flex items-center gap-2">
        <button @click="$router.back()"
                class="w-9 h-9 rounded-full flex items-center justify-center transition active:scale-90"
                style="background-color: #F2F2F7">
          <ChevronLeft :size="20" style="color: #1C1C1E" />
        </button>
        <h1 class="text-lg font-bold leading-tight" style="color: #1C1C1E">Profile</h1>
      </div>
      <span v-if="userStore.isGuest" class="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full"
            style="background-color: #FFF5E6; color: #FF9500">
        Guest
      </span>
    </header>

    <main class="px-4 py-5 space-y-4">
      <section class="rounded-3xl p-5" style="background-color: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.08)">
        <p class="text-xs font-bold uppercase tracking-widest mb-2" style="color: #8E8E93">Identity</p>
        <p class="text-lg font-black" style="color: #1C1C1E">
          {{ userStore.displayName || 'No profile yet' }}
        </p>
        <p class="text-xs mt-1" style="color: #8E8E93">
          {{ userStore.identity?.identity_id ?? 'Create a profile to continue.' }}
        </p>
      </section>

      <section class="rounded-3xl p-5 space-y-3"
               style="background-color: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.08)">
        <label class="block text-xs font-semibold uppercase tracking-widest" style="color: #8E8E93">
          Display name
        </label>
        <input
          v-model="displayName"
          class="w-full h-12 rounded-xl px-4 text-sm font-semibold"
          style="background-color: #F2F2F7; color: #1C1C1E"
          maxlength="100"
          placeholder="Your name"
          @keyup.enter="saveName" />

        <button
          @click="saveName"
          :disabled="saving"
          class="w-full h-12 rounded-xl font-semibold text-sm text-white transition active:scale-[0.98]"
          style="background-color: #007AFF">
          {{ saving ? 'Saving...' : userStore.hasProfile ? 'Update profile' : 'Create profile' }}
        </button>
      </section>

      <section v-if="userStore.hasProfile"
               class="rounded-3xl p-5 space-y-3"
               style="background-color: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.08)">
        <button
          @click="deleteProfile"
          :disabled="deleting"
          class="w-full h-12 rounded-xl font-semibold text-sm transition active:scale-[0.98]"
          style="background-color: #FFF0F0; color: #FF3B30">
          {{ deleting ? 'Deleting...' : 'Delete profile' }}
        </button>
      </section>

      <p v-if="errorMsg" class="text-sm font-semibold" style="color: #FF3B30">{{ errorMsg }}</p>
      <p v-if="successMsg" class="text-sm font-semibold" style="color: #34C759">{{ successMsg }}</p>
    </main>

    <BottomNav />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronLeft } from 'lucide-vue-next'
import BottomNav from '@/components/BottomNav.vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const displayName = ref('')
const saving = ref(false)
const deleting = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const syncDisplayName = () => {
  displayName.value = userStore.displayName
}

const saveName = async () => {
  const trimmed = displayName.value.trim()
  if (!trimmed) {
    errorMsg.value = 'Display name is required.'
    return
  }

  errorMsg.value = ''
  successMsg.value = ''
  saving.value = true
  try {
    if (userStore.hasProfile) {
      await userStore.updateDisplayName(trimmed)
      successMsg.value = 'Profile updated.'
    } else {
      await userStore.createGuestProfile(trimmed)
      successMsg.value = 'Profile created.'
    }
    syncDisplayName()
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : 'Failed to save profile'
  } finally {
    saving.value = false
  }
}

const deleteProfile = async () => {
  errorMsg.value = ''
  successMsg.value = ''
  deleting.value = true
  try {
    await userStore.deleteProfile()
    router.push('/')
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : 'Failed to delete profile'
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  syncDisplayName()
})
</script>
