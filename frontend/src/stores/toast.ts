import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ToastItem {
    id: number
    title: string
    body?: string
    variant?: 'info' | 'success' | 'warning'
    ttlMs?: number
}

export const useToastStore = defineStore('toast', () => {
    const items = ref<ToastItem[]>([])

    const remove = (id: number) => {
        items.value = items.value.filter((item) => item.id !== id)
    }

    const push = (toast: Omit<ToastItem, 'id'>) => {
        const id = Date.now() + Math.floor(Math.random() * 1000)
        const ttlMs = toast.ttlMs ?? 2800
        items.value.push({ ...toast, id, ttlMs })
        setTimeout(() => remove(id), ttlMs)
    }

    return { items, push, remove }
})
