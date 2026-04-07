<template>
  <div class="min-h-screen flex flex-col items-center justify-between px-6 py-12"
       style="background-color: #F2F2F7">

    <!-- Logo + Branding -->
    <div class="flex-1 flex flex-col items-center justify-center space-y-5">
      <div class="w-24 h-24 rounded-[28%] flex items-center justify-center"
           style="background-color: #007AFF; box-shadow: 0 8px 24px rgba(0,122,255,0.25); transform: rotate(3deg)">
        <Globe2 :size="44" color="white" :stroke-width="1.5" />
      </div>

      <div class="text-center space-y-2">
        <h1 class="text-4xl font-black tracking-tight" style="color: #1C1C1E">
          <span style="color: #007AFF">U</span>riverse
        </h1>
        <p class="text-base font-medium" style="color: #8E8E93">
          Where every game has its place.
        </p>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="w-full max-w-sm space-y-3">
      <div class="space-y-2">
        <label class="text-xs font-semibold uppercase tracking-widest block" style="color: #8E8E93">
          Display name
        </label>
        <input
          v-model="displayName"
          class="w-full h-12 rounded-xl px-4 text-sm font-semibold"
          style="background-color: #FFFFFF; color: #1C1C1E"
          placeholder="Your name"
          maxlength="100"
          @keyup.enter="createGuestProfile" />
      </div>

      <button
        @click="createGuestProfile"
        :disabled="loading"
        class="w-full h-14 rounded-xl font-semibold text-base text-white transition-transform active:scale-[0.98]"
        style="background-color: #007AFF">
        {{ loading ? 'Creating profile...' : 'Create profile' }}
      </button>

      <button
        @click="createGuestProfile"
        :disabled="loading"
        class="w-full h-14 rounded-xl font-semibold text-base transition-transform active:scale-[0.98]"
        style="border: 2px solid #007AFF; color: #007AFF; background: transparent">
        Continue
      </button>

      <div class="flex justify-center pt-1">
        <button
          @click="quickGuest"
          :disabled="loading"
          class="text-sm font-medium py-2 px-4"
          style="color: #8E8E93">
          Quick guest
        </button>
      </div>
      <p v-if="errorMsg" class="text-sm font-semibold text-center" style="color: #FF3B30">{{ errorMsg }}</p>
    </div>

    <!-- Footer -->
    <div class="pt-8 text-center">
      <p class="text-[10px] font-bold uppercase tracking-widest"
         style="color: #C7C7CC">
        Uriverse Engine
      </p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Globe2 } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const displayName = ref('')
const loading = ref(false)
const errorMsg = ref('')

const createGuestProfile = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    await userStore.createGuestProfile(displayName.value)
    router.push('/home')
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : 'Failed to create profile'
  } finally {
    loading.value = false
  }
}

const quickGuest = async () => {
  displayName.value = ''
  await createGuestProfile()
}
</script>
