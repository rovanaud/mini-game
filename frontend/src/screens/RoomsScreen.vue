<template>
  <div class="min-h-screen" style="background-color: #F2F2F7">

    <!-- Top Bar -->
    <header class="sticky top-0 z-50 px-4 py-4 flex justify-between items-center"
            style="background: rgba(255,255,255,0.85); backdrop-filter: blur(20px); border-bottom: 1px solid #E5E5EA">
      <div class="flex items-center gap-2">
        <button @click="$router.back()"
                class="w-9 h-9 rounded-full flex items-center justify-center transition active:scale-90"
                style="background-color: #F2F2F7">
          <ChevronLeft :size="20" style="color: #1C1C1E" />
        </button>
        <h1 class="text-lg font-bold leading-tight" style="color: #1C1C1E">Rooms</h1>
      </div>
      <button @click="showQuickActions = true"
              class="w-10 h-10 rounded-full flex items-center justify-center transition active:scale-90"
              style="background-color: #F2F2F7">
        <Plus :size="20" style="color: #1C1C1E" />
      </button>
    </header>

    <p v-if="errorMsg" class="mx-4 mt-2 text-sm text-red-500 font-medium">{{ errorMsg }}</p>

    <main class="px-4 py-4 space-y-4 pb-24">

      <!-- Quick Actions -->
      <section class="space-y-3">
        <button @click="createRoom"
                class="w-full h-20 rounded-3xl flex items-center gap-4 px-5 text-left transition active:scale-[0.98]"
                style="background-color: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.08)">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0"
              style="background-color: #EAF3FF">
            <Plus :size="22" style="color: #007AFF" />
          </div>
          <div class="flex-1">
            <p class="font-bold text-base leading-tight" style="color: #1C1C1E">Create Room</p>
            <p class="text-sm mt-0.5" style="color: #8E8E93">Private lobby with friends</p>
          </div>
          <ChevronRight :size="20" style="color: #C7C7CC" />
        </button>

        <button @click="showJoinSheet = true"
                class="w-full h-20 rounded-3xl flex items-center gap-4 px-5 text-left transition active:scale-[0.98]"
                style="background-color: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.08)">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0"
              style="background-color: #EAFAF0">
            <QrCode :size="22" style="color: #34C759" />
          </div>
          <div class="flex-1">
            <p class="font-bold text-base leading-tight" style="color: #1C1C1E">Join Room</p>
            <p class="text-sm mt-0.5" style="color: #8E8E93">By code or link</p>
          </div>
          <ChevronRight :size="20" style="color: #C7C7CC" />
        </button>
      </section>

      <!-- Active Room (if any) -->
      <section v-if="activeRoom">
        <div class="flex justify-between items-center mb-3">
          <p class="text-xs font-bold uppercase tracking-widest" style="color: #8E8E93">Active</p>
          <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                style="background-color: #FF9500; color: #FFFFFF">In Room</span>
        </div>
        <button @click="goToActiveRoom"
                class="w-full rounded-2xl p-4 flex items-center gap-3 transition active:scale-[0.98]"
                style="background-color: #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.08)">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
               style="background-color: #FF9500">
            {{ activeRoom.name[0] }}
          </div>
          <div class="flex-1 text-left">
            <p class="font-bold text-base leading-tight" style="color: #1C1C1E">{{ activeRoom.name }}</p>
            <p class="text-sm" style="color: #8E8E93">{{ activeRoom.onlineCount }} online</p>
          </div>
          <div class="flex items-center gap-1">
            <Circle :size="12" style="color: #34C759" />
            <ChevronRight :size="18" style="color: #C7C7CC" />
          </div>
        </button>
      </section>

      <!-- Permanent Rooms -->
      <section>
        <div class="flex justify-between items-center mb-3">
          <p class="text-xs font-bold uppercase tracking-widest" style="color: #8E8E93">Permanent Rooms</p>
          <button class="text-xs font-semibold" style="color: #007AFF">Manage</button>
        </div>
        <div v-if="permanentRooms.length === 0"
             class="text-center py-12"
             style="color: #8E8E93">
          <div class="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-2"
               style="background-color: #F2F2F7">
            <Users :size="32" style="color: #C7C7CC" />
          </div>
          <p class="text-sm font-medium">No permanent rooms</p>
          <p class="text-[12px] mt-1">Create your first one later</p>
        </div>
        <div v-else class="space-y-2">
          <button v-for="room in permanentRooms" :key="room.id"
                  @click="goToPermanentRoom(room)"
                  class="w-full rounded-xl p-3 flex items-center gap-3 transition active:scale-[0.98]"
                  style="background-color: #FFFFFF; box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                 :style="`background-color: ${room.color}`">
              {{ room.name[0] }}
            </div>
            <div class="flex-1 text-left">
              <p class="font-semibold text-sm leading-tight" style="color: #1C1C1E">{{ room.name }}</p>
              <p class="text-[12px]" style="color: #8E8E93">{{ room.lastActivity }}</p>
            </div>
            <ChevronRight :size="16" style="color: #C7C7CC" />
          </button>
        </div>
      </section>

    </main>

    <!-- Quick Actions Sheet -->
    <Transition name="slide-up">
      <div v-if="showJoinSheet"
           class="fixed bottom-0 left-0 w-full z-[60] rounded-t-3xl flex flex-col"
           style="background-color: #FFFFFF; max-height: 70vh; box-shadow: 0 -8px 40px rgba(0,0,0,0.12)">
        <div class="w-10 h-1 rounded-full mx-auto mt-3 mb-1" style="background-color: #E5E5EA" />
        <div class="px-6 py-4">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-lg font-bold" style="color: #1C1C1E">Join Room</h2>
            <button @click="showJoinSheet = false"
                    class="text-sm font-semibold" style="color: #007AFF">
              Cancel
            </button>
          </div>

          <!-- By code -->
          <div class="space-y-3 mb-6">
            <label class="block text-xs font-semibold uppercase tracking-widest mb-1"
                   style="color: #8E8E93">Room code</label>
            <div class="flex gap-2">
              <input v-model="joinCode"
                     class="flex-1 px-4 py-3 rounded-2xl text-sm font-semibold"
                     style="background-color: #F2F2F7; color: #1C1C1E"
                     placeholder="XXXXX"
                     maxlength="7"
                     @keyup.enter="joinByCode" />
              <button @click="joinByCode"
                      class="px-6 py-3 rounded-2xl font-semibold text-sm text-white transition active:scale-[0.98]"
                      style="background-color: #007AFF">
                Join
              </button>
            </div>
          </div>

          <!-- By link -->
          <div class="space-y-3">
            <label class="block text-xs font-semibold uppercase tracking-widest mb-1"
                   style="color: #8E8E93">Room link</label>
            <div class="flex gap-2">
              <input v-model="joinLink"
                     class="flex-1 px-4 py-3 rounded-2xl text-sm font-semibold"
                     style="background-color: #F2F2F7; color: #1C1C1E"
                     placeholder="uriverse.app/room/abcde"
                     @keyup.enter="joinByLink" />
              <button @click="joinByLink"
                      class="px-6 py-3 rounded-2xl font-semibold text-sm text-white transition active:scale-[0.98]"
                      style="background-color: #007AFF">
                Join
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <BottomNav />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Plus, Users, QrCode, ChevronRight, ChevronLeft, Circle } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { roomApi, type RoomSummary } from '@/api'
import { useRoomsUpdatesSocket, type RoomsEvent } from '@/composables/useRoomSocket'
import BottomNav from '@/components/BottomNav.vue'

const router = useRouter()
const showQuickActions = ref(false)
const showJoinSheet = ref(false)
const joinCode = ref('')
const joinLink = ref('')
const errorMsg = ref('')
const rooms = ref<RoomSummary[]>([])
const roomsSocket = useRoomsUpdatesSocket()

const fetchRooms = async () => {
    try {
        const result = await roomApi.list()
        rooms.value = result.rooms
    } catch (e: unknown) {
        errorMsg.value = e instanceof Error ? e.message : 'Failed to load rooms'
    }
}

const activeRoom = computed(() => {
    const room = rooms.value[0]
    if (!room) return null
    return {
        id: room.public_code,
        name: room.name,
        onlineCount: 'Unknown',
    }
})
const permanentRooms = ref<{ id: string; name: string; lastActivity: string; color: string }[]>([])

const handleRoomsEvent = async (event: RoomsEvent) => {
    if (event.event === 'subscribed') return
    await fetchRooms()
}

const goToActiveRoom = () => {
    if (activeRoom.value) router.push(`/room/${activeRoom.value.id}`)
}

const goToPermanentRoom = (room: { id: string }) => {
    router.push(`/room/${room.id}`)
}

const createRoom = async () => {
    errorMsg.value = ''
    try {
        const result = await roomApi.create()
        await fetchRooms()
        router.push(`/room/${result.public_code}`)
    } catch (e: unknown) {
        errorMsg.value = e instanceof Error ? e.message : 'Failed to create room'
    }
}

const joinByCode = async () => {
    if (joinCode.value.length < 4) return
    errorMsg.value = ''
    try {
        const result = await roomApi.join(joinCode.value)
        await fetchRooms()
        showJoinSheet.value = false
        router.push(`/room/${result.public_code}`)
    } catch (e: unknown) {
        errorMsg.value = e instanceof Error ? e.message : 'Failed to join room'
    }
}

const joinByLink = () => {
    const match = joinLink.value.match(/room\/([A-Z0-9]{4,8})/i)
    if (match) {
        joinCode.value = match[1].toUpperCase()
        joinByCode()
    }
}

onMounted(async () => {
    await fetchRooms()
    roomsSocket.on(handleRoomsEvent)
})

onUnmounted(() => {
    roomsSocket.off(handleRoomsEvent)
    roomsSocket.disconnect()
})

</script>

<style scoped>
  .slide-up-enter-active, .slide-up-leave-active {
    transition: transform 0.3s ease;
  }
  .slide-up-enter-from, .slide-up-leave-to {
    transform: translateY(100%);
  }
  .fade-enter-active, .fade-leave-active {
    transition: opacity 0.2s ease;
  }
  .fade-enter-from, .fade-leave-to {
    opacity: 0;
}
</style>
