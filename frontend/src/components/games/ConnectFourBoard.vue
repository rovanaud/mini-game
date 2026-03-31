<template>
  <div class="w-full max-w-sm">
    <!-- Board -->
    <div class="rounded-3xl p-3"
         style="background-color: #FFFFFF; box-shadow: 0 4px 24px rgba(0,0,0,0.08)">
      <div class="grid gap-1.5" :style="`grid-template-columns: repeat(${cols}, 1fr)`">
        <button
          v-for="col in cols" :key="`col-${col}`"
          class="flex flex-col gap-1.5 transition active:scale-95"
          :disabled="!isMyTurn || !!state.outcome"
          @click="dropDisc(col - 1)">
          <div
            v-for="row in rows" :key="`cell-${row}-${col}`"
            class="aspect-square rounded-full transition-all duration-300"
            :style="cellStyle(row - 1, col - 1)" />
        </button>
      </div>
    </div>

    <!-- Status banner -->
    <div v-if="state.outcome" class="mt-3 px-4 py-2 rounded-2xl text-center text-sm font-bold"
         :style="resultStyle">
      {{ resultLabel }}
    </div>

    <!-- Win length note (only shown if not standard) -->
    <p v-else-if="config.win_length !== 4"
       class="text-center text-[11px] mt-2 font-medium"
       style="color: #8E8E93">
       {{ config.win_length }} in a row to win
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ConnectFourConfig, ConnectFourState, Disc } from '@/types'

const props = defineProps<{
  state: ConnectFourState
  config: ConnectFourConfig
  isMyTurn: boolean
  myPlayerIndex: number   // seat index: 0 or 1
}>()

const emit = defineEmits<{
  action: [payload: { type: string; payload: Record<string, unknown> }]
}>()

const rows = computed(() => props.config.rows ?? 6)
const cols = computed(() => props.config.cols ?? 7)

// My disc based on my seat index
const myDisc = computed<Disc>(() => props.state.seat_discs?.[String(props.myPlayerIndex)] ?? null)

const dropDisc = (col: number) => {
  emit('action', { type: 'drop_disc', payload: { column: col } })
}

const cellStyle = (row: number, col: number): string => {
  const val = props.state.board[row]?.[col] ?? null
  const isLastMove =
    props.state.last_move?.row === row && props.state.last_move?.col === col

  if (val === null)
    return 'background-color: #F2F2F7; box-shadow: inset 0 1px 3px rgba(0,0,0,0.08)'
  if (val === myDisc.value)
    return `background-color: #007AFF; box-shadow: 0 2px 8px rgba(0,122,255,${isLastMove ? '0.6' : '0.35'})`
  return `background-color: #34C759; box-shadow: 0 2px 8px rgba(52,199,89,${isLastMove ? '0.6' : '0.35'})`
}

const resultLabel = computed(() => {
  if (!props.state.outcome) return ''
  if (props.state.outcome === 'board_full') return "It's a draw!"
  const iWon = props.state.winner_seat === props.myPlayerIndex
  if (props.state.outcome === 'resign') return iWon ? 'Opponent resigned — You win! 🎉' : 'You resigned'
  return iWon ? 'You win! 🎉' : 'You lose'
})

const resultStyle = computed(() => {
  if (props.state.outcome === 'board_full') return 'background-color: #F2F2F7; color: #1C1C1E'
  const iWon = props.state.winner_seat === props.myPlayerIndex
  return iWon
    ? 'background-color: #EAFAF0; color: #34C759'
    : 'background-color: #FFF0F0; color: #FF3B30'
})
</script>
