<template>
  <div class="min-h-screen pb-24" style="background-color: #F2F2F7">

    <!-- Top Bar -->
    <header class="sticky top-0 z-50 px-6 py-4 flex justify-between items-center"
            style="background: rgba(242,242,247,0.85); backdrop-filter: blur(20px)">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm"
             style="background-color: #007AFF">
          {{ initials }}
        </div>
        <div>
          <p class="text-xs font-semibold uppercase tracking-widest" style="color: #8E8E93">Welcome back</p>
          <p class="text-base font-bold leading-tight" style="color: #1C1C1E">{{ displayName }}</p>
        </div>
      </div>
      <button @click="$router.push('/profile')"
              class="w-10 h-10 rounded-full flex items-center justify-center transition active:scale-90"
              style="background-color: #FFFFFF">
        <Settings :size="20" style="color: #8E8E93" />
      </button>
    </header>

    <main class="px-6 pt-6 space-y-8">

      <!-- Main Action Cards -->
      <section class="space-y-4">
        <!-- Play -->
        <button @click="$router.push('/play')"
                class="w-full rounded-2xl p-5 flex items-center gap-4 text-left transition active:scale-[0.98]"
                style="background-color: #FFFFFF; box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
               style="background-color: #EAF3FF">
            <Gamepad2 :size="24" style="color: #007AFF" />
          </div>
          <div class="flex-1">
            <p class="font-bold text-base" style="color: #1C1C1E">Play</p>
            <p class="text-sm" style="color: #8E8E93">Solo or 1v1 — against humans or bots</p>
          </div>
          <ChevronRight :size="18" style="color: #C7C7CC" />
        </button>

        <!-- Start a Room -->
        <button @click="$router.push('/rooms')"
                class="w-full rounded-2xl p-5 flex items-center gap-4 text-left transition active:scale-[0.98]"
                style="background-color: #FFFFFF; box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
               style="background-color: #EAFAF0">
            <Users :size="24" style="color: #34C759" />
          </div>
          <div class="flex-1">
            <p class="font-bold text-base" style="color: #1C1C1E">Start a Room</p>
            <p class="text-sm" style="color: #8E8E93">Host a private lobby with friends</p>
          </div>
          <ChevronRight :size="18" style="color: #C7C7CC" />
        </button>

        <!-- Statistics -->
        <button @click="$router.push('/stats')"
                class="w-full rounded-2xl p-5 flex items-center gap-4 text-left transition active:scale-[0.98]"
                style="background-color: #FFFFFF; box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
               style="background-color: #FFF0F0">
            <BarChart2 :size="24" style="color: #FF3B30" />
          </div>
          <div class="flex-1">
            <p class="font-bold text-base" style="color: #1C1C1E">Statistics</p>
            <p class="text-sm" style="color: #8E8E93">Your performance per game</p>
          </div>
          <ChevronRight :size="18" style="color: #C7C7CC" />
        </button>
      </section>

      <!-- Recent Activity -->
      <section>
        <div class="flex justify-between items-center mb-3">
          <p class="text-xs font-bold uppercase tracking-widest" style="color: #8E8E93">Recent Activity</p>
          <button class="text-xs font-semibold" style="color: #007AFF">View all</button>
        </div>

        <div class="rounded-2xl overflow-hidden" style="background-color: #FFFFFF; box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
          <!-- Activity item -->
          <div v-for="(item, index) in recentActivity" :key="item.id"
               class="flex items-center gap-4 px-5 py-4"
               :style="index < recentActivity.length - 1 ? 'border-bottom: 1px solid #E5E5EA' : ''">
            <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                 :style="`background-color: ${item.iconBg}`">
              <component :is="item.icon" :size="18" :style="`color: ${item.iconColor}`" />
            </div>
            <div class="flex-1">
              <p class="text-sm font-semibold" style="color: #1C1C1E">{{ item.title }}</p>
              <p class="text-xs" style="color: #8E8E93">{{ item.subtitle }}</p>
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="recentActivity.length === 0" class="px-5 py-8 text-center">
            <p class="text-sm" style="color: #8E8E93">No activity yet</p>
          </div>
        </div>
      </section>

    </main>

    <!-- Bottom Nav -->
    <BottomNav />

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Gamepad2, Users, BarChart2, ChevronRight, Settings, Trophy, MessageSquare } from 'lucide-vue-next'
import BottomNav from '@/components/BottomNav.vue'

// TODO: replace with real user from auth store
const displayName = 'Alex'
const initials = computed(() => displayName.slice(0, 2).toUpperCase())

// TODO: replace with real data from API
const recentActivity = [
  {
    id: 1,
    title: 'Connect Four — Victory',
    subtitle: 'vs. Sarah · 2 hours ago',
    icon: Trophy,
    iconBg: '#FFFAEB',
    iconColor: '#FF9500',
  },
  {
    id: 2,
    title: 'Sarah invited you to a room',
    subtitle: 'Game Night · 5 hours ago',
    icon: MessageSquare,
    iconBg: '#EAF3FF',
    iconColor: '#007AFF',
  },
]
</script>
