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
      <button
        @click="$router.push('/home')"
        class="w-full h-14 rounded-xl font-semibold text-base text-white transition-transform active:scale-[0.98]"
        style="background-color: #007AFF">
        Create account
      </button>

      <button
        @click="$router.push('/home')"
        class="w-full h-14 rounded-xl font-semibold text-base transition-transform active:scale-[0.98]"
        style="border: 2px solid #007AFF; color: #007AFF; background: transparent">
        Sign in
      </button>

      <div class="flex justify-center pt-1">
        <button
          @click="$router.push('/home')"
          class="text-sm font-medium py-2 px-4"
          style="color: #8E8E93">
          Play as guest
        </button>
      </div>
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
import { Globe2 } from 'lucide-vue-next'
</script>
