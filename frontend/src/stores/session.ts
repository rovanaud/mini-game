import { defineStore } from 'pinia'


/* TODO: extend this with multi game session data
 * recording all matches results in the room
 */
interface SessionScore {
    [roomId: string]: { mine: number; opponent: number }
}

export const useSessionStore = defineStore('session', {
    state: (): { scores: SessionScore } => ({
        scores: {},
    }),
    actions: {
        recordWin(roomId: string) {
            if (!this.scores[roomId]) this.scores[roomId] = { mine: 0, opponent: 0 }
            this.scores[roomId].mine++
        },
        recordLoss(roomId: string) {
            if (!this.scores[roomId]) this.scores[roomId] = { mine: 0, opponent: 0 }
            this.scores[roomId].opponent++
        },
        getScore(roomId: string) {
            return this.scores[roomId] ?? { mine: 0, opponent: 0 }
        },
        clearScore(roomId: string) {
            delete this.scores[roomId]
        },
    },
})
