<template>
  <div class="min-h-screen flex flex-col" style="background-color: #F2F2F7">

    <!-- Top Bar -->
    <header class="sticky top-0 z-50 px-4 py-3 flex justify-between items-center"
            style="background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); border-bottom: 1px solid #E5E5EA">
      <div class="flex items-center gap-3">
        <button @click="goBackToRooms" class="p-1 transition active:scale-90">
          <ChevronLeft :size="24" style="color: #007AFF" />
        </button>
        <button @click="showSheet = true" class="flex flex-col text-left transition active:opacity-60">
          <span class="font-bold text-base leading-tight" style="color: #1C1C1E">{{ roomName }}</span>
          <span class="text-[11px] font-semibold" style="color: #34C759">{{ participants.length }} online</span>
        </button>
      </div>
      <button @click="showSheet = true" class="p-1 transition active:scale-90">
        <MoreHorizontal :size="22" style="color: #8E8E93" />
      </button>
    </header>

    <!-- error display (add near top of sheet content) -->
    <p v-if="errorMsg" class="text-sm text-red-500 font-medium mb-3">{{ errorMsg }}</p>

    <!-- Pending proposal card -->
    <section v-if="myPendingProposal" class="mx-4 mt-3 rounded-2xl p-4"
             style="background-color: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.08)">
      <p class="text-[10px] font-bold uppercase tracking-widest mb-2" style="color: #8E8E93">
        Proposal
      </p>
      <p class="text-sm font-semibold mb-3" style="color: #1C1C1E">
        {{ proposalSummaryText }}
      </p>
      <div class="flex gap-2">
        <button @click="respondProposal('yes')" :disabled="respondingProposal"
                class="flex-1 h-10 rounded-xl font-semibold text-sm text-white transition active:scale-95"
                style="background-color: #34C759">
          Accept
        </button>
        <button @click="respondProposal('no')" :disabled="respondingProposal"
                class="flex-1 h-10 rounded-xl font-semibold text-sm text-white transition active:scale-95"
                style="background-color: #FF3B30">
          Decline
        </button>
      </div>
    </section>

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

    <!-- Active match resume -->
    <button
      v-if="showActiveMatchChip"
      @click="resumeMatch"
      class="fixed z-[55] px-4 py-2 h-12 rounded-2xl flex items-center gap-2 shadow-lg transition active:scale-90"
      style="bottom: 136px; right: 72px; background-color: #007AFF; color: #FFFFFF"
    >
      <span
        v-if="showActiveMatchAttention"
        class="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full border-2"
        style="background-color: #FF3B30; border-color: #FFFFFF"
      />
      <Swords :size="14" />
      <span class="text-[11px] font-bold uppercase tracking-wider">Resume Match</span>
    </button>
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
            <div class="flex items-center gap-2 flex-1">
              <template v-if="editingName">
                <input
                  v-model="nameInput"
                  @keyup.enter="saveName"
                  @keyup.escape="editingName = false"
                  @blur="saveName"
                  autofocus
                  class="text-lg font-bold bg-transparent border-b-2 outline-none flex-1"
                  style="color: #1C1C1E; border-color: #007AFF" />
              </template>
              <template v-else>
                <h2 class="text-lg font-bold" style="color: #1C1C1E">{{ roomName }}</h2>
                <button v-if="isHost" @click="startEditName" class="p-1 transition active:scale-90">
                  <Pencil :size="14" style="color: #8E8E93" />
                </button>
              </template>
            </div>
            <span class="text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full"
                  style="background-color: #EAFAF0; color: #34C759">{{ participants.length }} Online</span>
          </div>

          <!-- Participants -->
          <div class="flex gap-4 overflow-x-auto pb-4 mb-5">
            <div v-for="(p, i) in participants" :key="p.participant_id"
                 class="flex flex-col items-center gap-1 flex-shrink-0">
              <div class="relative">
                <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-white font-bold text-lg"
                     :style="`background-color: ${participantColor(i)}`">
                  {{ (p.display_name ?? '?')[0].toUpperCase() }}
                </div>
                <!-- Status dot -->
                <div class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white"
                     :style="`background-color: ${p.is_me ? '#007AFF' : '#34C759'}`" />
              </div>
              <span class="text-[10px] font-bold uppercase tracking-wide w-14 text-center truncate"
                    style="color: #8E8E93">{{ p.display_name ?? 'Unknown' }}</span>
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

          <p v-if="errorMsg" class="text-sm font-medium mb-3" style="color: #FF3B30">{{ errorMsg }}</p>

          <!-- Action Grid -->
          <div class="grid grid-cols-2 gap-3 pb-8">
            <button v-if="activeMatchId" @click="goToActiveMatch"
                    class="col-span-2 flex items-center justify-center gap-2 p-4 rounded-2xl text-white transition active:scale-95"
                    style="background-color: #34C759">
              <Rocket :size="20" />
              <span class="text-xs font-bold uppercase tracking-wide">Resume Active Match</span>
            </button>
            <!-- Launch Game button: wire it up -->
            <button @click="openSetup" :disabled="!isHost"
                    class="flex flex-col items-center justify-center p-4 rounded-2xl text-white transition active:scale-95"
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

    <!-- Game Setup Modal -->
    <Transition name="fade">
      <div v-if="showSetup"
          class="fixed inset-0 z-[70] flex items-end justify-center"
          style="background: rgba(0,0,0,0.4); backdrop-filter: blur(4px)"
          @click.self="showSetup = false">

        <div class="w-full rounded-t-3xl px-6 pt-5 pb-10"
            style="background-color: #FFFFFF; max-height: 75vh; overflow-y: auto">

          <!-- Handle -->
          <div class="w-10 h-1 rounded-full mx-auto mb-5" style="background-color: #E5E5EA" />

          <h3 class="text-lg font-black mb-5" style="color: #1C1C1E">New Game</h3>

          <!-- Game picker -->
          <p class="text-[11px] font-bold uppercase tracking-wider mb-2" style="color: #8E8E93">Game</p>
          <div class="flex flex-col gap-2 mb-6">
            <button v-for="g in availableGames" :key="g.game_id"
                    @click="selectedGameId = g.game_id"
                    class="flex items-center justify-between px-4 py-3 rounded-2xl transition active:scale-95"
                    :style="selectedGameId === g.game_id
                      ? 'background-color: #007AFF; color: white'
                      : 'background-color: #F2F2F7; color: #1C1C1E'">
              <span class="font-semibold text-sm">{{ g.display_name }}</span>
              <CheckCircle v-if="selectedGameId === g.game_id" :size="18" />
            </button>
          </div>

          <!-- Player picker -->
          <p class="text-[11px] font-bold uppercase tracking-wider mb-2" style="color: #8E8E93">
            Players ({{ selectedPlayerIds.length }} selected)
          </p>
          <div class="flex flex-col gap-2 mb-6">
            <button v-for="(p, i) in participants" :key="p.participant_id"
                    @click="togglePlayer(p.participant_id)"
                    class="flex items-center gap-3 px-4 py-3 rounded-2xl transition active:scale-95"
                    :style="selectedPlayerIds.includes(p.participant_id)
                      ? 'background-color: #EBF4FF; color: #007AFF'
                      : 'background-color: #F2F2F7; color: #1C1C1E'">
              <div class="w-8 h-8 rounded-xl flex items-center justify-center text-white text-xs font-bold"
                  :style="`background-color: ${participantColor(i)}`">
                {{ (p.display_name ?? '?')[0].toUpperCase() }}
              </div>
              <span class="font-semibold text-sm flex-1 text-left">
                {{ p.display_name ?? 'Unknown' }}
                <span v-if="p.is_me" class="text-[10px] font-normal ml-1" style="color: #8E8E93">(you)</span>
              </span>
              <CheckCircle v-if="selectedPlayerIds.includes(p.participant_id)" :size="18" />
            </button>
          </div>

          <p v-if="errorMsg" class="text-sm font-medium mb-3" style="color: #FF3B30">{{ errorMsg }}</p>

          <!-- Launch -->
          <button @click="launchGame" :disabled="launching"
                  class="w-full h-14 rounded-2xl font-black text-white text-base transition active:scale-95"
                  style="background-color: #007AFF">
            {{ launching ? 'Launching…' : '🚀 Launch' }}
          </button>
        </div>
      </div>
    </Transition>


    <BottomNav />
  </div>
</template>

<script setup lang="ts">

import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
    ChevronLeft, MoreHorizontal, Plus, PlusCircle,
    Send, Smile, CheckCheck, Rocket, Trophy,
    UserPlus, Settings, LogOut, Pencil, CheckCircle, Swords
} from 'lucide-vue-next'
import { roomApi, type ProposalResponseChoice, type RoomProposal } from '@/api'
import { useRoomStore } from '@/stores/room'
import { useActiveMatchStore } from '@/stores/activeMatch'
import {
    useRoomSocket,
    type RoomEvent,
    type RoomChatMessageEvent,
    type RoomChatHistoryEvent,
} from '@/composables/useRoomSocket'
import BottomNav from '@/components/BottomNav.vue'

const route = useRoute()
const router = useRouter()
const roomStore = useRoomStore()
const activeMatchStore = useActiveMatchStore()
const roomCode = route.params.roomCode as string
const roomSocket = useRoomSocket(roomCode)

const showSheet = ref(false)
const inputText = ref('')
const errorMsg = ref('')
const launching = ref(false)
const respondingProposal = ref(false)

const goBackToRooms = () => router.push('/rooms')

// Derive display values from store
const roomName = computed(() => roomStore.detail?.name ?? '…')
const editingName = ref(false)
const nameInput = ref(roomName.value)
const startEditName = () => {
  nameInput.value = roomName.value ?? ''
  editingName.value = true
}
const saveName = async () => {
    editingName.value = false
    const trimmed = nameInput.value.trim()
    if (!trimmed || trimmed === roomStore.detail?.name) return
    try {
        await roomApi.rename(route.params.roomCode as string, trimmed)
        // Patch store directly — no need for full re-fetch
        if (roomStore.detail) roomStore.detail.name = trimmed
    } catch (e: unknown) {
        errorMsg.value = e instanceof Error ? e.message : 'Failed to rename'
    }
}
const participants = computed(() => roomStore.detail?.participants ?? [])
const isHost = computed(() => roomStore.detail?.is_host ?? false)
const activeMatchId = computed(() => roomStore.detail?.active_match_id ?? null)
const availableGames = computed(() => roomStore.detail?.available_games ?? [])
const pendingProposals = computed(() => roomStore.detail?.pending_proposals ?? [])
const myPendingProposal = computed(
  () => pendingProposals.value.find((p) => p.can_respond && p.proposal_type === 'match_start') ?? null,
)
const proposalSummaryText = computed(() => {
  const p = myPendingProposal.value
  if (!p) return ''
  const payload = p.payload as { game_id?: string }
  const gameId = payload.game_id ?? 'game'
  return `You are invited to a ${String(gameId).replace('_', ' ')} match.`
})

// Participant colours (stable per index)
const COLORS = ['#007AFF', '#34C759', '#FF9500', '#FF3B30', '#AF52DE', '#5AC8FA']
const participantColor = (index: number) => COLORS[index % COLORS.length]
// Add after participantColor:
const statusLegend = [
    { label: 'Online',  color: '#34C759' },
    { label: 'Playing', color: '#007AFF' },
    { label: 'Idle',    color: '#C7C7CC' },
]

// Chat (local only for now — WebSocket in next step)
type RoomUiMessage = {
    id: string
    type: 'chat' | 'system'
    isMine: boolean
    author: string
    avatarColor: string
    text: string
    time: string
}

const messages = ref<RoomUiMessage[]>([])
const chatContainer = ref<HTMLElement | null>(null)

const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

const colorFromName = (name: string) => {
    let hash = 0
    for (let i = 0; i < name.length; i++) hash = (hash << 5) - hash + name.charCodeAt(i)
    const palette = COLORS
    return palette[Math.abs(hash) % palette.length]
}

const pushRoomChatMessage = (message: {
    id: string
    sender_id: string | null
    display_name: string | null
    text: string
    created_at: string
}) => {
    const me = roomStore.detail?.my_participant_id
    const author = message.display_name ?? 'Unknown'
    messages.value.push({
        id: message.id,
        type: 'chat',
        isMine: !!me && message.sender_id === me,
        author,
        avatarColor: colorFromName(author),
        text: message.text,
        time: formatTime(message.created_at),
    })
    nextTick(() => {
        chatContainer.value?.scrollTo({
            top: chatContainer.value.scrollHeight,
            behavior: 'smooth',
        })
    })
}

const sendMessage = () => {
    const text = inputText.value.trim()
    if (!text) return
    roomSocket.sendChat(text)
    inputText.value = ''
}

// If there's already an active match, go straight to it
const goToActiveMatch = () => {
    if (!activeMatchId.value) return
    activeMatchStore.setActiveMatch({
        matchId: activeMatchId.value,
        roomCode,
    })
    activeMatchStore.clearAttention()
    router.push(`/match/${activeMatchId.value}`)
}

// ── Game setup ──────────────────────────────────────────────────
const showSetup = ref(false)
const selectedGameId = ref<string>('')
const selectedPlayerIds = ref<string[]>([])

const openSetup = () => {
  // Pre-fill defaults: first available game, all participants
  selectedGameId.value = availableGames.value[0]?.game_id ?? ''
  selectedPlayerIds.value = participants.value.map(p => p.participant_id)
  showSetup.value = true
}

const togglePlayer = (id: string) => {
  if (selectedPlayerIds.value.includes(id)) {
    selectedPlayerIds.value = selectedPlayerIds.value.filter(x => x !== id)
  } else {
    selectedPlayerIds.value.push(id)
  }
}

const launchGame = async () => {
  if (!isHost.value || launching.value) return
  if (!selectedGameId.value) { errorMsg.value = 'Pick a game.'; return }
  if (selectedPlayerIds.value.length < 2) { errorMsg.value = 'Select at least 2 players.'; return }

  errorMsg.value = ''
  launching.value = true
  try {
    const result = await roomApi.startGame(
      route.params.roomCode as string,
      selectedGameId.value,
      selectedPlayerIds.value,
    )
    if (result.match_id) {
      activeMatchStore.setActiveMatch({
        matchId: result.match_id,
        roomCode,
      })
    }
    showSetup.value = false
    showSheet.value = false
    if (result.match_id) {
      router.push(`/match/${result.match_id}`)
    } else {
      messages.value.push({
        id: `sys-${Date.now()}`,
        type: 'system',
        isMine: false,
        author: 'System',
        avatarColor: '#8E8E93',
        text: 'Match proposal sent. Waiting for approvals.',
        time: '',
      })
    }
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : 'Failed to start game'
  } finally {
    launching.value = false
  }
}

const respondProposal = async (response: ProposalResponseChoice) => {
  const proposal = myPendingProposal.value
  if (!proposal || respondingProposal.value) return
  respondingProposal.value = true
  errorMsg.value = ''
  try {
    await roomApi.respondProposal(roomCode, proposal.proposal_id, response)
    await refreshRoom()
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : 'Failed to respond to proposal'
  } finally {
    respondingProposal.value = false
  }
}

// ── Active match chip ─────────────────────────────────────────
const showActiveMatchChip = computed(
  () => activeMatchStore.hasActiveMatch && route.name !== 'match',
)

console.log('showActiveMatchChip', showActiveMatchChip.value, activeMatchStore.hasActiveMatch, route.name)

const showActiveMatchAttention = computed(
  () => showActiveMatchChip.value && activeMatchStore.hasUnreadAttention,
)

const resumeMatch = () => {
  if (!activeMatchStore.matchId) return
  activeMatchStore.clearAttention()
  router.push(`/match/${activeMatchStore.matchId}`)
}

// ── Room life cycle ─────────────────────────────────────────
const refreshRoom = async () => {
    await roomStore.fetchRoom(roomCode)
    if (roomStore.detail?.active_match_id) {
        activeMatchStore.setActiveMatch({
            matchId: roomStore.detail.active_match_id,
            roomCode,
        })
    } else if (activeMatchStore.roomCode === roomCode) {
        activeMatchStore.clear()
    }
}

const handleRoomEvent = async (event: RoomEvent) => {
  console.log('Received room event', event)
    if (event.event === 'subscribed') return
    if (event.event.startsWith('match_')) {
        activeMatchStore.markAttention()
    }
    await refreshRoom()
}

const handleRoomChatMessage = (event: RoomChatMessageEvent) => {
    pushRoomChatMessage(event.message)
}

const handleRoomChatHistory = (event: RoomChatHistoryEvent) => {
    const me = roomStore.detail?.my_participant_id
    messages.value = event.messages.map((message) => {
        const author = message.display_name ?? 'Unknown'
        return {
            id: message.id,
            type: 'chat' as const,
            isMine: !!me && message.sender_id === me,
            author,
            avatarColor: colorFromName(author),
            text: message.text,
            time: formatTime(message.created_at),
        }
    })
    nextTick(() => {
        chatContainer.value?.scrollTo({
            top: chatContainer.value.scrollHeight,
            behavior: 'auto',
        })
    })
}

onMounted(async () => {
    await refreshRoom()
    roomSocket.on('room_event', handleRoomEvent)
    roomSocket.on('room_chat_message', handleRoomChatMessage)
    roomSocket.on('room_chat_history', handleRoomChatHistory)
})
onUnmounted(() => {
    roomSocket.off('room_event', handleRoomEvent)
    roomSocket.off('room_chat_message', handleRoomChatMessage)
    roomSocket.off('room_chat_history', handleRoomChatHistory)
    roomSocket.disconnect()
    roomStore.clear()
})

</script>

<style scoped>
  .fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
  .fade-enter-from, .fade-leave-to { opacity: 0; }

  .slide-up-enter-active, .slide-up-leave-active { transition: transform 0.3s ease; }
  .slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); }
</style>
