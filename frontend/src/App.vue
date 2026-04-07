<template>
  <ToastStack />
  <RouterView :key="$route.fullPath"/>
</template>

<script setup lang="ts">
import ToastStack from '@/components/ToastStack.vue'
</script>
