import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRoomStore = defineStore('room', () => {
    // ── State ───────────────────────────────────────────────────
    const currentRoomId = ref<string | null>(null)
    const room = ref({
        id: '',
        name: '',
        onlineCount: 0,
    })

    const participants = ref([
        { id: 1, name: 'You', color: '#007AFF', status: 'online' as const },
        { id: 2, name: 'Sarah', color: '#34C759', status: 'playing' as const },
        { id: 3, name: 'Mike', color: '#8E8E93', status: 'idle' as const },
    ])

    const messages = ref([
        { id: 1, isMine: false, author: 'Alex', text: 'Is everyone ready?', time: '18:42' },
        { id: 2, isMine: true, author: 'You', text: 'Count me in! 🍕', time: '18:45' },
    ])

    // ── Actions ─────────────────────────────────────────────────
    const enterRoom = (roomId: string, roomData: any) => {
        currentRoomId.value = roomId
        room.value = roomData
    }

    const leaveRoom = () => {
        currentRoomId.value = null
        room.value = { id: '', name: '', onlineCount: 0 }
        messages.value = []
    }

    const sendMessage = (text: string) => {
        messages.value.push({
            id: Date.now(),
            isMine: true,
            author: 'You',
            text,
            time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        })
    }

    return {
        currentRoomId,
        room,
        participants,
        messages,
        enterRoom,
        leaveRoom,
        sendMessage,
    }
})
