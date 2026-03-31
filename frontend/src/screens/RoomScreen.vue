<template>
  <div class="min-h-screen flex flex-col" style="background-color: #F2F2F7">

    <!-- Top Bar -->
    <header class="sticky top-0 z-50 px-4 py-3 flex justify-between items-center"
            style="background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); border-bottom: 1px solid #E5E5EA">
      <div class="flex items-center gap-3">
        <button @click="$router.back()" class="p-1 transition active:scale-90">
          <ChevronLeft :size="24" style="color: #007AFF" />
        </button>
        <button @click="showSheet = true" class="flex flex-col text-left transition active:opacity-60">
          <span class="font-bold text-base leading-tight" style="color: #1C1C1E">{{ room.name }}</span>
          <span class="text-[11px] font-semibold" style="color: #34C759">{{ room.onlineCount }} online</span>
        </button>
      </div>
      <button @click="showSheet = true" class="p-1 transition active:scale-90">
        <MoreHorizontal :size="22" style="color: #8E8E93" />
      </button>
    </header>

    <!-- Chat Messages -->
    <main ref="chatContainer"
      class="flex-1 overflow-y-auto px-4 py-4 space-y-4"
      style="padding-bottom: 140px">

      <!-- Date separator -->
      <div class="flex justify-center">
        <span class="text-[11px] font-semibold px-3 py-1 rounded-full"
              style="background-color: #E5E5EA; color: #8E8E93">Today</span>
      </div>

      <!-- Messages -->
      <template v-for="msg in messages" :key="msg.id">

        <!-- System message -->
        <div v-if="msg.type === 'system'" class="flex justify-center">
          <span class="text-[11px] font-medium px-3 py-1 rounded-full"
                style="background-color: #E5E5EA; color: #8E8E93">{{ msg.text }}</span>
        </div>

        <!-- Others' message -->
        <div v-else-if="!msg.isMine" class="flex gap-2 items-end">
          <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
               :style="`background-color: ${msg.avatarColor}`">
            {{ (msg.author || '?')[0].toUpperCase() }}
          </div>
          <div class="flex flex-col max-w-[75%]">
            <span class="text-[10px] font-bold uppercase tracking-wide mb-1 ml-1"
                  style="color: #8E8E93">{{ msg.author }}</span>
            <div class="rounded-2xl rounded-bl-none px-4 py-3"
                 style="background-color: #FFFFFF; box-shadow: 0 1px 2px rgba(0,0,0,0.06)">
              <p class="text-sm leading-relaxed" style="color: #1C1C1E">{{ msg.text }}</p>
            </div>
            <span class="text-[10px] mt-1 ml-1" style="color: #C7C7CC">{{ msg.time }}</span>
          </div>
        </div>

        <!-- Own message -->
        <div v-else class="flex flex-col items-end max-w-[75%] ml-auto">
          <div class="rounded-2xl rounded-br-none px-4 py-3"
               style="background-color: #007AFF">
            <p class="text-sm leading-relaxed text-white">{{ msg.text }}</p>
          </div>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-[10px]" style="color: #C7C7CC">{{ msg.time }}</span>
            <CheckCheck :size="12" style="color: #007AFF" />
          </div>
        </div>

      </template>
    </main>

    <!-- FAB -->
    <button @click="showSheet = true"
            class="fixed z-40 w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg transition active:scale-90"
            style="bottom: 136px; right: 16px; background-color: #007AFF">
      <Plus :size="22" color="white" />
    </button>

    <!-- Chat Input -->
    <div class="fixed left-0 w-full z-40 px-4 py-3"
        style="bottom: 64px; background: rgba(255,255,255,0.9); backdrop-filter: blur(20px); border-top: 1px solid #E5E5EA">
      <div class="flex items-center gap-2">
        <button class="p-1 transition active:scale-90">
          <PlusCircle :size="24" style="color: #007AFF" />
        </button>
        <div class="flex-1 flex items-center rounded-full px-4 py-2 gap-2"
            style="background-color: #F2F2F7">
          <input v-model="inputText"
                @keyup.enter="sendMessage"
                type="text"
                placeholder="Message..."
                class="flex-1 bg-transparent border-none outline-none text-sm"
                style="color: #1C1C1E" />
          <button class="transition active:scale-90">
            <Smile :size="18" style="color: #8E8E93" />
          </button>
        </div>
        <button @click="sendMessage"
                class="w-9 h-9 rounded-full flex items-center justify-center shadow-md transition active:scale-90"
                style="background-color: #007AFF">
          <Send :size="15" color="white" />
        </button>
      </div>
    </div>

    <!-- Bottom Sheet Overlay -->
    <Transition name="fade">
      <div v-if="showSheet"
           class="fixed inset-0 z-50"
           style="background: rgba(0,0,0,0.3); backdrop-filter: blur(2px)"
           @click="showSheet = false" />
    </Transition>

    <!-- Bottom Sheet -->
    <Transition name="slide-up">
      <div v-if="showSheet"
           class="fixed bottom-0 left-0 w-full z-[60] rounded-t-3xl flex flex-col"
           style="background-color: #FFFFFF; max-height: 80vh; box-shadow: 0 -8px 40px rgba(0,0,0,0.12)">

        <!-- Handle -->
        <div class="w-10 h-1 rounded-full mx-auto mt-3 mb-1" style="background-color: #E5E5EA" />

        <div class="px-6 py-4 overflow-y-auto">
          <!-- Sheet Header -->
          <div class="flex justify-between items-center mb-5">
            <h2 class="text-lg font-bold" style="color: #1C1C1E">{{ room.name }}</h2>
            <span class="text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full"
                  style="background-color: #EAFAF0; color: #34C759">{{ room.onlineCount }} Online</span>
          </div>

          <!-- Participants -->
          <div class="flex gap-4 overflow-x-auto pb-4 mb-5">
            <div v-for="p in participants" :key="p.id"
                 class="flex flex-col items-center gap-1 flex-shrink-0">
              <div class="relative">
                <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-white font-bold text-lg"
                     :style="`background-color: ${p.color}`">
                  {{ p.name[0].toUpperCase() }}
                </div>
                <!-- Status dot -->
                <div class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white"
                     :style="`background-color: ${statusColor(p.status)}`" />
              </div>
              <span class="text-[10px] font-bold uppercase tracking-wide w-14 text-center truncate"
                    style="color: #8E8E93">{{ p.name }}</span>
            </div>
          </div>

          <!-- Status legend -->
          <div class="flex gap-4 mb-6">
            <div v-for="s in statusLegend" :key="s.label" class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full" :style="`background-color: ${s.color}`" />
              <span class="text-[10px]" style="color: #8E8E93">{{ s.label }}</span>
            </div>
          </div>

          <!-- Divider -->
          <div class="mb-4" style="border-top: 1px solid #E5E5EA" />

          <!-- Action Grid -->
          <div class="grid grid-cols-2 gap-3 pb-8">
            <button class="flex flex-col items-center justify-center p-4 rounded-2xl text-white transition active:scale-95"
                    style="background-color: #007AFF">
              <Rocket :size="22" class="mb-2" />
              <span class="text-xs font-bold uppercase tracking-wide">Launch Game</span>
            </button>
            <button class="flex flex-col items-center justify-center p-4 rounded-2xl transition active:scale-95"
                    style="background-color: #EAFAF0; color: #34C759">
              <Trophy :size="22" class="mb-2" />
              <span class="text-xs font-bold uppercase tracking-wide text-center">Tournament</span>
            </button>
            <button class="flex flex-col items-center justify-center p-4 rounded-2xl transition active:scale-95"
                    style="background-color: #F2F2F7; color: #1C1C1E">
              <UserPlus :size="22" class="mb-2" />
              <span class="text-xs font-bold uppercase tracking-wide">Invite</span>
            </button>
            <button class="flex flex-col items-center justify-center p-4 rounded-2xl transition active:scale-95"
                    style="background-color: #F2F2F7; color: #1C1C1E">
              <Settings :size="22" class="mb-2" />
              <span class="text-xs font-bold uppercase tracking-wide">Settings</span>
            </button>
            <button class="col-span-2 flex items-center justify-center gap-2 p-4 rounded-2xl transition active:scale-95 mt-1"
                    style="background-color: #FFF0F0; color: #FF3B30">
              <LogOut :size="20" />
              <span class="text-xs font-bold uppercase tracking-wide">Leave Room</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <BottomNav />
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import {
    ChevronLeft, MoreHorizontal, Plus, PlusCircle,
    Send, Smile, CheckCheck, Rocket, Trophy,
    UserPlus, Settings, LogOut
  } from 'lucide-vue-next'
  import BottomNav from '@/components/BottomNav.vue'

  // TODO: fetch from API via route param (route.params.id)
  const room = ref({ name: 'Friday Game Night', onlineCount: 8 })

  const showSheet = ref(false)
  const inputText = ref('')

  const participants = ref([
    { id: 1, name: 'You',   color: '#007AFF', status: 'online' },
    { id: 2, name: 'Sarah', color: '#34C759', status: 'playing' },
    { id: 3, name: 'Mike',  color: '#8E8E93', status: 'idle' },
    { id: 4, name: 'Léa',   color: '#FF9500', status: 'online' },
  ])

  const statusColor = (status: string) => {
    if (status === 'online')  return '#34C759'
    if (status === 'playing') return '#007AFF'
    if (status === 'idle')    return '#C7C7CC'
    return '#C7C7CC'
  }

  const statusLegend = [
    { label: 'Online',  color: '#34C759' },
    { label: 'Playing', color: '#007AFF' },
    { label: 'Idle',    color: '#C7C7CC' },
  ]

  // TODO: fetch from API
  const messages = ref([
    { id: 1, type: 'chat', isMine: false, author: 'Alex', avatarColor: '#FF9500', text: 'Is everyone ready for tonight?', time: '18:42' },
    { id: 2, type: 'chat', isMine: true,  author: 'You',  avatarColor: '#007AFF', text: 'Count me in! 🍕', time: '18:45' },
    { id: 3, type: 'system', text: 'Sarah joined the room' },
    { id: 4, type: 'chat', isMine: false, author: 'Sarah', avatarColor: '#34C759', text: 'Board is looking legendary! 🎲', time: '18:47' },
  ])

  const chatContainer = ref<HTMLElement | null>(null)

  const sendMessage = () => {
    if (!inputText.value.trim()) return
    messages.value.push({
      id: Date.now(),
      type: 'chat',
      isMine: true,
      author: 'You',
      avatarColor: '#007AFF',
      text: inputText.value.trim(),
      time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
    })
    inputText.value = ''
  }
</script>

<style scoped>
  .fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
  .fade-enter-from, .fade-leave-to { opacity: 0; }

  .slide-up-enter-active, .slide-up-leave-active { transition: transform 0.3s ease; }
  .slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); }
</style>
