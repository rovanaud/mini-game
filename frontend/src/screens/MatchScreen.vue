<template>
  <div class="h-screen flex flex-col overflow-hidden" style="background-color: #F2F2F7">

    <!-- Top Bar -->
    <header class="px-4 py-3 flex justify-between items-center flex-shrink-0"
            style="background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); border-bottom: 1px solid #E5E5EA">
      <div class="flex items-center gap-3">
        <button @click="$router.back()"
                class="w-9 h-9 rounded-full flex items-center justify-center transition active:scale-90"
                style="background-color: #F2F2F7">
          <ChevronLeft :size="22" style="color: #1C1C1E" />
        </button>
        <div class="flex items-center gap-2">
          <div class="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold"
               :style="`background-color: ${opponent.color}`">
            {{ opponent.name[0] }}
          </div>
          <div>
            <p class="text-sm font-bold leading-tight" style="color: #1C1C1E">{{ opponent.name }}</p>
            <p class="text-[10px] font-bold uppercase tracking-wide"
               :style="`color: ${isMyTurn ? '#34C759' : '#8E8E93'}`">
              {{ isMyTurn ? 'Your turn' : 'Their turn' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Timer (only if enabled) -->
      <div v-if="timerConfig.enabled"
           class="flex items-center gap-2 px-3 py-1.5 rounded-full"
           :style="timerWarning ? 'background-color: #FFF0F0' : 'background-color: #F2F2F7'">
        <Timer :size="14" :style="`color: ${timerWarning ? '#FF3B30' : '#007AFF'}`" />
        <span class="text-sm font-black tabular-nums"
              :style="`color: ${timerWarning ? '#FF3B30' : '#1C1C1E'}`">
          {{ formattedTime }}
        </span>

        <!-- Request time button -->
        <button v-if="timerConfig.allow_time_request && timeRequestsLeft > 0"
                @click="requestTime"
                class="ml-1 px-2 py-0.5 rounded-full text-[10px] font-bold transition active:scale-90"
                style="background-color: #EAF3FF; color: #007AFF">
          +{{ timerConfig.time_request_seconds }}s
        </button>
        <span v-else-if="timerConfig.allow_time_request && timeRequestsLeft === 0"
              class="ml-1 text-[10px]" style="color: #C7C7CC">
          No requests left
        </span>
      </div>

      <!-- No timer indicator -->
      <div v-else class="px-3 py-1.5 rounded-full" style="background-color: #F2F2F7">
        <span class="text-[10px] font-semibold" style="color: #8E8E93">No timer</span>
      </div>
    </header>

    <!-- Game Board Area — generic slot -->
    <main class="flex-1 flex flex-col items-center justify-center px-4 py-4 min-h-0">

      <div class="flex items-center gap-2 px-3 py-1 rounded-full mb-4"
           style="background-color: #EAF3FF">
        <div class="w-2 h-2 rounded-full animate-pulse" style="background-color: #007AFF" />
        <span class="text-[10px] font-bold uppercase tracking-widest" style="color: #007AFF">
          {{ gameKey.replace('_', ' ') }}
        </span>
      </div>

      <!-- Dynamic game component -->
      <component
        :is="gameBoardComponent"
        :state="gameState as unknown as ConnectFourState"
        :config="gameConfig as unknown as ConnectFourConfig"
        :is-my-turn="isMyTurn"
        :my-player-index="myPlayerIndex"
        @action="submitAction"
      />

      <!-- Unknown game fallback -->
      <div v-if="!gameBoardComponent"
           class="flex flex-col items-center gap-3 p-8 rounded-3xl"
           style="background-color: #FFFFFF">
        <Puzzle :size="40" style="color: #C7C7CC" />
        <p class="text-sm font-semibold" style="color: #8E8E93">
          Game "{{ gameKey }}" not yet available.
        </p>
      </div>

      <!-- Player indicators -->
      <div class="flex items-center gap-6 mt-5">
        <div class="flex flex-col items-center gap-1">
          <div class="w-10 h-10 rounded-full transition-all duration-300"
               :style="`background-color: #007AFF;
                        box-shadow: ${isMyTurn ? '0 0 0 4px rgba(0,122,255,0.2)' : 'none'};
                        opacity: ${isMyTurn ? '1' : '0.4'}`" />
          <span class="text-[10px] font-bold uppercase tracking-wide" style="color: #007AFF">You</span>
        </div>
        <div style="width: 24px; height: 1px; background-color: #E5E5EA" />
        <div class="flex flex-col items-center gap-1 transition-all duration-300"
             :style="`opacity: ${!isMyTurn ? '1' : '0.4'}`">
          <div class="w-10 h-10 rounded-full"
               :style="`background-color: ${opponent.color};
                        box-shadow: ${!isMyTurn ? '0 0 0 4px rgba(52,199,89,0.2)' : 'none'}`" />
          <span class="text-[10px] font-bold uppercase tracking-wide"
                :style="`color: ${opponent.color}`">{{ opponent.name }}</span>
        </div>
      </div>
    </main>

    <!-- Bottom Action Bar -->
    <footer class="flex-shrink-0 flex justify-between items-center px-8 py-4"
            style="background-color: #FFFFFF; border-top: 1px solid #E5E5EA">
      <div class="flex gap-5">
        <button @click="showChat = true"
                class="flex flex-col items-center gap-1 transition active:scale-90">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center relative"
               style="background-color: #F2F2F7">
            <MessageSquare :size="20" style="color: #1C1C1E" />
            <span v-if="unreadCount > 0"
                  class="absolute -top-1 -right-1 w-4 h-4 rounded-full text-white text-[9px] font-bold flex items-center justify-center"
                  style="background-color: #FF3B30">
              {{ unreadCount }}
            </span>
          </div>
          <span class="text-[9px] font-bold uppercase tracking-wide" style="color: #8E8E93">Chat</span>
        </button>

        <button @click="showReactions = true"
                class="flex flex-col items-center gap-1 transition active:scale-90">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center"
               style="background-color: #F2F2F7">
            <Smile :size="20" style="color: #1C1C1E" />
          </div>
          <span class="text-[9px] font-bold uppercase tracking-wide" style="color: #8E8E93">React</span>
        </button>

        <button class="flex flex-col items-center gap-1 transition active:scale-90">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center"
               style="background-color: #F2F2F7">
            <Zap :size="20" style="color: #1C1C1E" />
          </div>
          <span class="text-[9px] font-bold uppercase tracking-wide" style="color: #8E8E93">Actions</span>
        </button>
      </div>

      <button @click="confirmResign"
              class="flex flex-col items-center gap-1 transition active:scale-90">
        <div class="w-12 h-12 rounded-2xl flex items-center justify-center"
             style="background-color: #FFF0F0">
          <Flag :size="20" style="color: #FF3B30" />
        </div>
        <span class="text-[9px] font-bold uppercase tracking-wide" style="color: #FF3B30">Resign</span>
      </button>
    </footer>

    <!-- ── Overlays ────────────────────────────────── -->

    <!-- Chat -->
    <Transition name="fade">
      <div v-if="showChat" class="fixed inset-0 z-50"
           style="background: rgba(0,0,0,0.3); backdrop-filter: blur(2px)"
           @click="showChat = false" />
    </Transition>
    <Transition name="slide-up">
      <div v-if="showChat"
           class="fixed bottom-0 left-0 w-full z-[60] rounded-t-3xl flex flex-col"
           style="background-color: #FFFFFF; max-height: 60vh; box-shadow: 0 -8px 40px rgba(0,0,0,0.12)">
        <div class="w-10 h-1 rounded-full mx-auto mt-3 mb-1" style="background-color: #E5E5EA" />
        <p class="text-xs font-bold uppercase tracking-widest text-center py-2" style="color: #8E8E93">
          Game Chat
        </p>
        <div class="flex-1 overflow-y-auto px-4 py-2 space-y-3">
          <div v-for="msg in chatMessages" :key="msg.id"
               class="flex" :class="msg.isMine ? 'justify-end' : 'justify-start'">
            <div class="rounded-2xl px-3 py-2 max-w-[75%]"
                 :style="msg.isMine ? 'background-color: #007AFF' : 'background-color: #F2F2F7'">
              <p class="text-sm" :style="msg.isMine ? 'color: #FFFFFF' : 'color: #1C1C1E'">
                {{ msg.text }}
              </p>
            </div>
          </div>
        </div>
        <div class="px-4 py-3 flex items-center gap-2"
             style="border-top: 1px solid #E5E5EA">
          <div class="flex-1 flex items-center rounded-full px-4 py-2"
               style="background-color: #F2F2F7">
            <input v-model="chatInput" @keyup.enter="sendChatMessage"
                   type="text" placeholder="Message..."
                   class="flex-1 bg-transparent border-none outline-none text-sm"
                   style="color: #1C1C1E" />
          </div>
          <button @click="sendChatMessage"
                  class="w-9 h-9 rounded-full flex items-center justify-center transition-all duration-150"
                  :class="sendPulse ? 'scale-125' : 'scale-100 active:scale-90'"
                  style="background-color: #007AFF">
            <Send :size="14" color="white" />
          </button>
        </div>
      </div>
    </Transition>

    <!-- Reactions -->
    <Transition name="fade">
      <div v-if="showReactions" class="fixed inset-0 z-50"
           style="background: rgba(0,0,0,0.2)" @click="showReactions = false" />
    </Transition>
    <Transition name="slide-up">
      <div v-if="showReactions"
           class="fixed bottom-0 left-0 w-full z-[60] rounded-t-3xl px-6 py-6"
           style="background-color: #FFFFFF; box-shadow: 0 -8px 40px rgba(0,0,0,0.12)">
        <div class="w-10 h-1 rounded-full mx-auto mb-5" style="background-color: #E5E5EA" />
        <div class="flex justify-around">
          <button v-for="emoji in reactions" :key="emoji"
                  @click="sendReaction(emoji)"
                  class="text-4xl transition active:scale-75 hover:scale-125 duration-150">
            {{ emoji }}
          </button>
        </div>
      </div>
    </Transition>

    <!-- Resign confirm -->
    <Transition name="fade">
      <div v-if="showResignConfirm"
           class="fixed inset-0 z-[70] flex items-center justify-center px-8"
           style="background: rgba(0,0,0,0.4)">
        <div class="w-full max-w-xs rounded-3xl p-6 text-center"
             style="background-color: #FFFFFF; box-shadow: 0 8px 40px rgba(0,0,0,0.15)">
          <p class="text-base font-bold mb-1" style="color: #1C1C1E">Resign?</p>
          <p class="text-sm mb-6" style="color: #8E8E93">
            You'll forfeit this match. This can't be undone.
          </p>
          <div class="flex gap-3">
            <button @click="showResignConfirm = false"
                    class="flex-1 h-11 rounded-2xl font-semibold text-sm transition active:scale-95"
                    style="background-color: #F2F2F7; color: #1C1C1E">
              Cancel
            </button>
            <button @click="resign"
                    class="flex-1 h-11 rounded-2xl font-semibold text-sm text-white transition active:scale-95"
                    style="background-color: #FF3B30">
              Resign
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Floating Reactions Layer -->
    <TransitionGroup name="reaction-float" tag="div" class="fixed inset-0 z-30 pointer-events-none">
      <div v-for="r in activeReactions" :key="r.id"
          class="absolute text-5xl select-none"
          :style="`left: ${r.x}%; bottom: 20%`">
        {{ r.emoji }}
      </div>
    </TransitionGroup>

  </div>
</template>

<script setup lang="ts">

  import { ref, computed, onMounted, onUnmounted, type Component } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChevronLeft, Timer, MessageSquare,
  Smile, Zap, Flag, Send, Puzzle
} from 'lucide-vue-next'
import type { TimerConfig } from '@/types'
import type { ConnectFourState, ConnectFourConfig } from '@/types'
import ConnectFourBoard from '@/components/games/ConnectFourBoard.vue'
import { useMatchStore } from '@/stores/match'

const gameRegistry: Record<string, Component> = {
  connect_four: ConnectFourBoard,
}

const route = useRoute()
const matchStore = useMatchStore()

// ── Data from store ───────────────────────────────────────────
const gameState = computed(() => matchStore.detail?.game_state ?? {})
const gameConfig = computed(() => matchStore.detail?.game_config ?? {})
const gameKey = computed(() => matchStore.detail?.game_key ?? '')
const myPlayerIndex = computed(() => matchStore.detail?.my_seat_index ?? 0)

const isMyTurn = computed(() => {
  const state = gameState.value as Partial<ConnectFourState>
  return state.current_turn_seat === myPlayerIndex.value
})

const gameBoardComponent = computed(() => gameRegistry[gameKey.value] ?? null)

// Opponent: the seat that is not mine
const opponent = computed(() => {
  const seats = matchStore.detail?.seats ?? []
  const opp = seats.find(s => s.seat_index !== myPlayerIndex.value)
  return {
    name: opp?.display_name ?? 'Opponent',
    color: '#34C759',
  }
})

// ── Actions ───────────────────────────────────────────────────
const submitAction = (action: { type: string; payload: Record<string, unknown> }) => {
  matchStore.submitAction(action.type, action.payload)
}

// ── Timer ─────────────────────────────────────────────────────
const timerConfig = computed<TimerConfig>(() => {
  const cfg = matchStore.detail?.game_config as any
  return cfg?.timer ?? { enabled: false, mode: 'per_move', allow_time_request: false }
})
const seconds = ref(0)
const timeRequestsLeft = ref(timerConfig.value.max_time_requests ?? 0)
const timerWarning = computed(() =>
  timerConfig.value.enabled &&
  timerConfig.value.mode === 'per_move' &&
  ((timerConfig.value.seconds_per_move ?? 60) - seconds.value) <= 10
)
const formattedTime = computed(() => {
  const s = timerConfig.value.mode === 'per_move'
    ? Math.max(0, (timerConfig.value.seconds_per_move ?? 60) - seconds.value)
    : seconds.value
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const sec = (s % 60).toString().padStart(2, '0')
  return `${m}:${sec}`
})
const requestTime = () => {
  if (timeRequestsLeft.value <= 0) return
  timeRequestsLeft.value--
  seconds.value = Math.max(0, seconds.value - (timerConfig.value.time_request_seconds ?? 15))
}

let timerInterval: ReturnType<typeof setInterval>
onMounted(async () => {
  await matchStore.fetchMatch(route.params.id as string)
  timerInterval = setInterval(() => {
    if (isMyTurn.value && timerConfig.value.enabled) seconds.value++
  }, 1000)
})
onUnmounted(() => {
  clearInterval(timerInterval)
  matchStore.clear()
})

// ── Chat ─────────────────────────────────────────────────────
const showChat = ref(false)
const chatInput = ref('')
const unreadCount = ref(0)
const chatMessages = ref<{ id: number; isMine: boolean; text: string }[]>([])
const sendPulse = ref(false)
const sendChatMessage = () => {
  if (!chatInput.value.trim()) return
  chatMessages.value.push({ id: Date.now(), isMine: true, text: chatInput.value.trim() })
  chatInput.value = ''
  sendPulse.value = true
  setTimeout(() => { sendPulse.value = false }, 150)
}

// ── Reactions ─────────────────────────────────────────────────
const showReactions = ref(false)
const reactions = ['👏', '🔥', '😂', '😮', '❤️', '👎']
interface ActiveReaction { id: number; emoji: string; x: number }
const activeReactions = ref<ActiveReaction[]>([])
const sendReaction = (emoji: string) => {
  showReactions.value = false
  chatMessages.value.push({ id: Date.now(), isMine: true, text: emoji + ' reacted' })
  unreadCount.value += showChat.value ? 0 : 1
  const id = Date.now()
  activeReactions.value.push({ id, emoji, x: 20 + Math.random() * 60 })
  setTimeout(() => {
    activeReactions.value = activeReactions.value.filter(r => r.id !== id)
  }, 1600)
}

// ── Resign ────────────────────────────────────────────────────
const showResignConfirm = ref(false)
const confirmResign = () => { showResignConfirm.value = true }
const resign = () => {
  showResignConfirm.value = false
  matchStore.submitAction('resign', {})
}

</script>

<style scoped>
  .fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
  .fade-enter-from, .fade-leave-to { opacity: 0; }
  .slide-up-enter-active, .slide-up-leave-active { transition: transform 0.3s ease; }
  .slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); }
  /* Floating reaction animation */
  .reaction-float-enter-active {
    animation: floatUp 1.6s ease-out forwards;
  }
  .reaction-float-leave-active {
    display: none;
  }

  @keyframes floatUp {
    0%   { transform: translateY(0)    scale(1);   opacity: 1; }
    40%  { transform: translateY(-80px) scale(1.3); opacity: 1; }
    100% { transform: translateY(-160px) scale(0.8); opacity: 0; }
  }
</style>
