<template>
  <nav class="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 py-3 rounded-t-3xl"
       style="background: rgba(255,255,255,0.9); backdrop-filter: blur(20px); box-shadow: 0 -1px 0 #E5E5EA">
    <RouterLink v-for="tab in tabs" :key="tab.name"
      :to="tab.path"
      class="flex flex-col items-center gap-1 px-5 py-1 rounded-2xl transition active:scale-90"
      :style="isActive(tab.path) ? 'color: #007AFF' : 'color: #8E8E93'">
      <component :is="tab.icon" :size="22"
                 :style="isActive(tab.path) ? 'color: #007AFF' : 'color: #8E8E93'" />
      <span class="text-[10px] font-bold uppercase tracking-widest">{{ tab.name }}</span>
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Home, DoorOpen, BarChart2, User } from 'lucide-vue-next'

const route = useRoute()

const tabs = [
  { name: 'Home',    path: '/home',    icon: Home },
  { name: 'Rooms',   path: '/rooms',   icon: DoorOpen },
  { name: 'Stats',   path: '/stats',   icon: BarChart2 },
  { name: 'Profile', path: '/profile', icon: User },
]

const isActive = (path: string) => route.path === path
</script>
