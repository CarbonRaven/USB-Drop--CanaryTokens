<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Toast from 'primevue/toast'

const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)

const navItems = [
  { name: 'Dashboard', path: '/', icon: 'pi pi-chart-bar' },
  { name: 'Campaigns', path: '/campaigns', icon: 'pi pi-folder' },
  { name: 'Profiles', path: '/profiles', icon: 'pi pi-clipboard' },
  { name: 'Drives', path: '/drives', icon: 'pi pi-database' },
  { name: 'Map', path: '/map', icon: 'pi pi-map' },
  { name: 'Alerts', path: '/alerts', icon: 'pi pi-bell' },
  { name: 'Reports', path: '/reports', icon: 'pi pi-chart-line' },
]

const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
const mobileOpen = ref(false)
const isMobile = ref(false)

const toggleCollapse = () => {
  collapsed.value = !collapsed.value
  localStorage.setItem('sidebar-collapsed', collapsed.value)
}

const closeMobile = () => {
  mobileOpen.value = false
}

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) mobileOpen.value = false
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-surface-950">
    <Toast />
    <template v-if="isAuthenticated">
      <!-- Mobile overlay -->
      <div
        v-if="mobileOpen"
        class="fixed inset-0 bg-black/50 z-40 md:hidden"
        @click="closeMobile"
      ></div>

      <!-- Sidebar -->
      <aside
        :class="[
          'fixed top-0 left-0 h-full bg-surface-900 border-r border-surface-700 z-50 flex flex-col transition-all duration-200',
          isMobile
            ? (mobileOpen ? 'w-64 translate-x-0' : 'w-64 -translate-x-full')
            : (collapsed ? 'w-16' : 'w-64')
        ]"
      >
        <!-- Logo area -->
        <div class="flex items-center h-16 px-4 border-b border-surface-700">
          <span v-if="!collapsed || isMobile" class="text-lg font-bold text-primary-400 truncate">USB Drop</span>
          <span v-else class="text-lg font-bold text-primary-400 mx-auto">UD</span>
        </div>

        <!-- Nav items -->
        <nav class="flex-1 py-4 overflow-y-auto">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            @click="closeMobile"
            v-slot="{ isActive }"
            custom
          >
            <a
              :href="item.path"
              @click.prevent="router.push(item.path); closeMobile()"
              :class="[
                'flex items-center px-4 py-2.5 mx-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-surface-800 text-primary-400'
                  : 'text-surface-300 hover:bg-surface-800 hover:text-surface-100'
              ]"
              :title="collapsed && !isMobile ? item.name : undefined"
            >
              <i :class="[item.icon, 'text-base']" :style="collapsed && !isMobile ? 'margin: 0 auto' : ''"></i>
              <span v-if="!collapsed || isMobile" class="ml-3">{{ item.name }}</span>
            </a>
          </router-link>
        </nav>

        <!-- User area -->
        <div class="border-t border-surface-700 p-4">
          <div v-if="!collapsed || isMobile" class="flex items-center justify-between">
            <div class="flex items-center min-w-0">
              <i class="pi pi-user text-surface-400 mr-2"></i>
              <span class="text-sm text-surface-300 truncate">{{ authStore.user?.username }}</span>
            </div>
            <button @click="logout" class="text-surface-400 hover:text-red-400 ml-2" title="Logout">
              <i class="pi pi-sign-out"></i>
            </button>
          </div>
          <div v-else class="flex justify-center">
            <button @click="logout" class="text-surface-400 hover:text-red-400" title="Logout">
              <i class="pi pi-sign-out"></i>
            </button>
          </div>
        </div>
      </aside>

      <!-- Main content -->
      <div
        :class="[
          'transition-all duration-200',
          isMobile ? 'ml-0' : (collapsed ? 'ml-16' : 'ml-64')
        ]"
      >
        <!-- Mobile header bar -->
        <div class="md:hidden flex items-center h-14 px-4 bg-surface-900 border-b border-surface-700">
          <button @click="mobileOpen = true" class="text-surface-300 hover:text-surface-100">
            <i class="pi pi-bars text-xl"></i>
          </button>
          <span class="ml-3 text-lg font-bold text-primary-400">USB Drop</span>
        </div>

        <!-- Desktop collapse toggle -->
        <div class="hidden md:flex items-center h-10 px-4">
          <button
            @click="toggleCollapse"
            class="text-surface-400 hover:text-surface-200 transition-colors"
            :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          >
            <i :class="collapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'" class="text-sm"></i>
          </button>
        </div>

        <!-- Page content -->
        <main class="p-6">
          <router-view />
        </main>
      </div>
    </template>

    <!-- Unauthenticated: no sidebar -->
    <template v-else>
      <router-view />
    </template>
  </div>
</template>
