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
                     maxlength="5"
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
  import {ref} from 'vue'
  import { Plus, Users, QrCode, ChevronRight, ChevronLeft, Circle, Wifi, Link2 } from 'lucide-vue-next'
  import {useRouter} from 'vue-router'
  import { useRoomStore } from '@/stores/room'
  import { useUserStore } from '@/stores/user'
  import BottomNav from '@/components/BottomNav.vue'


  const roomStore = useRoomStore()
  const userStore = useUserStore()

  // ── State ────────────────────────────────────────────────────
  const showQuickActions = ref(false)
  const showJoinCode = ref(false)
  const showJoinSheet = ref(false)
  const joinCode = ref('')
  const joinLink = ref('')
  const router = useRouter()
  // ── Demo data ────────────────────────────────────────────────
  const activeRoom = ref({
    id: 'active-1',
    name: 'Friday Game Night',
    onlineCount: 8,
    isPermanent: false,
  })

  const permanentRooms = ref([
    {
      id: 'perm-1',
      name: 'Family Hub',
      lastActivity: '2 days ago',
      color: '#FF9500',
      isPermanent: true,
    },
    {
      id: 'perm-2',
      name: 'Work Crew',
      lastActivity: '1 week ago',
      color: '#FF3B30',
      isPermanent: true,
    },
  ])

  // ── Actions ──────────────────────────────────────────────────
  const createRoom = () => {
    showQuickActions.value = false
    // TODO: create ephemeral room via API
    roomStore.enterRoom('ephemeral-123', {
      id: 'ephemeral-123',
      name: 'New Room',
      onlineCount: 1,
      isPermanent: false,
    })
    router.push('/room/ephemeral-123')
  }

  const joinRoom = () => {
    if (!joinCode.value.trim()) return
    showJoinCode.value = false
    // TODO: join via API
    roomStore.enterRoom('joined-456', {
      id: 'joined-456',
      name: `Room ${joinCode.value.toUpperCase()}`,
      onlineCount: 5,
      isPermanent: false,
    })
    router.push('/room/joined-456')
  }

  const joinByCode = () => {
    if (joinCode.value.length !== 5) return
    // TODO: join by code API
    console.log('joining by code:', joinCode.value)
  }

  const joinByLink = () => {
    // TODO: extract room ID from link
    console.log('joining by link:', joinLink.value)
  }

  const goToActiveRoom = () => {
    router.push(`/room/${activeRoom.value.id}`)
  }

  const goToPermanentRoom = (room: any) => {
    // TODO: navigate to permanent room screen (different from ephemeral)
    console.log('go to permanent room:', room)
  }

  const onCloseJoinCode = () => {
    showJoinCode.value = false
    joinCode.value = ''
  }
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
