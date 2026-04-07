import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from '@/router'
import { useUserStore } from '@/stores/user'
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const userStore = useUserStore(pinia)
const PUBLIC_ROUTES = new Set(['auth'])

router.beforeEach(async (to) => {
    await userStore.ensureHydrated()
    const hasProfile = userStore.hasProfile

    if (to.name === 'auth' && hasProfile) {
        return { name: 'home' }
    }
    if (!PUBLIC_ROUTES.has(String(to.name ?? '')) && !hasProfile) {
        return { name: 'auth' }
    }
    return true
})

app.use(router)
app.mount('#app')
