<template>
  <div class="w-full max-w-sm">
    <!-- Board -->
    <div class="rounded-3xl p-3"
         style="background-color: #FFFFFF; box-shadow: 0 4px 24px rgba(0,0,0,0.08)">
      <div class="grid gap-1.5" :style="`grid-template-columns: repeat(${config.cols}, 1fr)`">
        <button
          v-for="col in config.cols" :key="`col-${col}`"
          class="flex flex-col gap-1.5 transition active:scale-95"
          :disabled="!isMyTurn"
          @click="$emit('action', { type: 'drop_disc', payload: { col: col - 1 } })">
          <div
            v-for="row in config.rows" :key="`cell-${row}-${col}`"
            class="aspect-square rounded-full transition-all duration-300"
            :style="cellStyle(row - 1, col - 1)" />
        </button>
      </div>
    </div>

    <!-- Win length note (only shown if not standard) -->
    <p v-if="config.win_length !== 4"
       class="text-center text-[11px] mt-2 font-medium"
       style="color: #8E8E93">
       {{ config.win_length }} in a row to win
    </p>
  </div>
</template>

<script setup lang="ts">
import type { ConnectFourConfig, ConnectFourState } from '@/types'

const props = defineProps<{
  state: ConnectFourState
  config: ConnectFourConfig
  isMyTurn: boolean
  myPlayerIndex: number
}>()

defineEmits<{
  action: [payload: { type: string; payload: Record<string, unknown> }]
}>()

const cellStyle = (row: number, col: number) => {
  const val = props.state.board[row]?.[col] ?? 0
  if (val === props.myPlayerIndex)
    return 'background-color: #007AFF; box-shadow: 0 2px 8px rgba(0,122,255,0.35)'
  if (val !== 0)
    return 'background-color: #34C759; box-shadow: 0 2px 8px rgba(52,199,89,0.35)'
  return 'background-color: #F2F2F7; box-shadow: inset 0 1px 3px rgba(0,0,0,0.08)'
}
</script>
