<template>
  <div class="fixed top-4 left-0 right-0 z-[120] px-4 pointer-events-none">
    <TransitionGroup name="toast" tag="div" class="mx-auto w-full max-w-md space-y-2">
      <div
        v-for="toast in toasts.items"
        :key="toast.id"
        class="rounded-2xl px-4 py-3 shadow-lg border pointer-events-auto"
        :style="toastStyle(toast.variant)"
      >
        <p class="text-sm font-bold">{{ toast.title }}</p>
        <p v-if="toast.body" class="text-xs mt-0.5 opacity-90">{{ toast.body }}</p>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useToastStore, type ToastItem } from '@/stores/toast'

const toasts = useToastStore()

const toastStyle = (variant: ToastItem['variant']) => {
  if (variant === 'success') {
    return 'background-color: #EAFAF0; color: #1C1C1E; border-color: #B9E8C6'
  }
  if (variant === 'warning') {
    return 'background-color: #FFF7E8; color: #1C1C1E; border-color: #F7D7A6'
  }
  return 'background-color: #F2F2F7; color: #1C1C1E; border-color: #E5E5EA'
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.24s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.98);
}
</style>
