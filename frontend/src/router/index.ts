import { createRouter, createWebHistory } from 'vue-router'

import AuthScreen from '@/screens/AuthScreen.vue'
import HomeScreen from '@/screens/HomeScreen.vue'
import RoomsScreen from '@/screens/RoomsScreen.vue'
import StatsScreen from '@/screens/StatsScreen.vue'
import ProfileScreen from '@/screens/ProfileScreen.vue'
import RoomScreen from '@/screens/RoomScreen.vue'
import MatchScreen from '@/screens/MatchScreen.vue'

const routes = [
    { path: '/', name: 'auth', component: AuthScreen },
    { path: '/home', name: 'home', component: HomeScreen },
    { path: '/rooms', name: 'rooms', component: RoomsScreen },
    { path: '/stats', name: 'stats', component: StatsScreen },
    { path: '/profile', name: 'profile', component: ProfileScreen },
    { path: '/room/:roomCode', name: 'room', component: RoomScreen },
    { path: '/match/:id', name: 'match', component: MatchScreen },
]

export default createRouter({
    history: createWebHistory(),
    routes,
})
