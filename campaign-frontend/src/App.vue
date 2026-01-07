<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const openDropdown = ref(null)
const mobileMenuOpen = ref(false)
const mobileSubmenu = ref(null)

const campaignPaths = ['/campaigns', '/targets', '/profiles', '/drives']
const monitorPaths = ['/map', '/alerts', '/reports']

const isCampaignActive = computed(() => campaignPaths.some(p => route.path.startsWith(p)))
const isMonitorActive = computed(() => monitorPaths.some(p => route.path.startsWith(p)))

const toggleDropdown = (name) => {
  openDropdown.value = openDropdown.value === name ? null : name
}

const closeDropdowns = () => {
  openDropdown.value = null
}

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
  if (!mobileMenuOpen.value) {
    mobileSubmenu.value = null
  }
}

const toggleMobileSubmenu = (name) => {
  mobileSubmenu.value = mobileSubmenu.value === name ? null : name
}

const closeMobileMenu = () => {
  mobileMenuOpen.value = false
  mobileSubmenu.value = null
}

const handleClickOutside = (e) => {
  if (!e.target.closest('.dropdown-container')) {
    closeDropdowns()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav
      v-if="isAuthenticated"
      class="bg-white shadow-sm border-b"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <!-- Logo -->
            <div class="flex-shrink-0 flex items-center">
              <span class="text-xl font-bold text-primary-600">USB Drop</span>
            </div>
            <!-- Desktop Nav links -->
            <div class="hidden md:ml-6 md:flex md:items-center md:space-x-1">
              <!-- Dashboard -->
              <router-link
                to="/"
                class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 hover:bg-gray-50 rounded-md"
                :class="{ 'text-primary-600 bg-primary-50': route.path === '/' }"
              >
                <span class="mr-1">📊</span>
                Dashboard
              </router-link>

              <!-- Campaigns Dropdown -->
              <div class="relative dropdown-container">
                <button
                  class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 hover:bg-gray-50 rounded-md"
                  :class="{ 'text-primary-600 bg-primary-50': isCampaignActive }"
                  @click.stop="toggleDropdown('campaigns')"
                >
                  <span class="mr-1">📁</span>
                  Campaigns
                  <svg
                    class="ml-1 h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                <div
                  v-if="openDropdown === 'campaigns'"
                  class="absolute left-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50"
                >
                  <router-link
                    to="/campaigns"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    :class="{ 'bg-primary-50 text-primary-600': route.path.startsWith('/campaigns') }"
                    @click="closeDropdowns"
                  >
                    <span class="mr-2">📁</span>Campaigns
                  </router-link>
                  <router-link
                    to="/targets"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    :class="{ 'bg-primary-50 text-primary-600': route.path.startsWith('/targets') }"
                    @click="closeDropdowns"
                  >
                    <span class="mr-2">🎯</span>Targets
                  </router-link>
                  <router-link
                    to="/profiles"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    :class="{ 'bg-primary-50 text-primary-600': route.path.startsWith('/profiles') }"
                    @click="closeDropdowns"
                  >
                    <span class="mr-2">📋</span>Profiles
                  </router-link>
                  <router-link
                    to="/drives"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    :class="{ 'bg-primary-50 text-primary-600': route.path.startsWith('/drives') }"
                    @click="closeDropdowns"
                  >
                    <span class="mr-2">💾</span>Drives
                  </router-link>
                </div>
              </div>

              <!-- Monitor Dropdown -->
              <div class="relative dropdown-container">
                <button
                  class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 hover:bg-gray-50 rounded-md"
                  :class="{ 'text-primary-600 bg-primary-50': isMonitorActive }"
                  @click.stop="toggleDropdown('monitor')"
                >
                  <span class="mr-1">📡</span>
                  Monitor
                  <svg
                    class="ml-1 h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                <div
                  v-if="openDropdown === 'monitor'"
                  class="absolute left-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50"
                >
                  <router-link
                    to="/map"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    :class="{ 'bg-primary-50 text-primary-600': route.path === '/map' }"
                    @click="closeDropdowns"
                  >
                    <span class="mr-2">🗺️</span>Map
                  </router-link>
                  <router-link
                    to="/alerts"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    :class="{ 'bg-primary-50 text-primary-600': route.path === '/alerts' }"
                    @click="closeDropdowns"
                  >
                    <span class="mr-2">🚨</span>Alerts
                  </router-link>
                  <router-link
                    to="/reports"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    :class="{ 'bg-primary-50 text-primary-600': route.path === '/reports' }"
                    @click="closeDropdowns"
                  >
                    <span class="mr-2">📈</span>Reports
                  </router-link>
                </div>
              </div>

              <!-- Users (Admin only) -->
              <router-link
                v-if="authStore.isAdmin"
                to="/users"
                class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 hover:bg-gray-50 rounded-md"
                :class="{ 'text-primary-600 bg-primary-50': route.path === '/users' }"
              >
                <span class="mr-1">👥</span>
                Users
              </router-link>

              <!-- Settings (Admin only) -->
              <router-link
                v-if="authStore.isAdmin"
                to="/settings"
                class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 hover:bg-gray-50 rounded-md"
                :class="{ 'text-primary-600 bg-primary-50': route.path === '/settings' }"
              >
                <span class="mr-1">⚙️</span>
                Settings
              </router-link>
            </div>
          </div>

          <!-- Desktop User menu -->
          <div class="hidden md:flex items-center">
            <span class="text-sm text-gray-500 mr-2">{{ authStore.user?.username }}</span>
            <span
              v-if="authStore.isAdmin"
              class="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded-full mr-4"
            >Admin</span>
            <span
              v-else-if="authStore.userRole === 'operator'"
              class="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full mr-4"
            >Operator</span>
            <span
              v-else
              class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full mr-4"
            >Viewer</span>
            <button
              class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-md"
              @click="logout"
            >
              Logout
            </button>
          </div>

          <!-- Mobile menu button -->
          <div class="flex items-center md:hidden">
            <button
              class="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-primary-600 hover:bg-gray-100"
              @click="toggleMobileMenu"
            >
              <svg
                v-if="!mobileMenuOpen"
                class="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              <svg
                v-else
                class="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile menu -->
      <div
        v-if="mobileMenuOpen"
        class="md:hidden border-t border-gray-200"
      >
        <div class="px-2 pt-2 pb-3 space-y-1">
          <!-- Dashboard -->
          <router-link
            to="/"
            class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
            :class="{ 'bg-primary-50 text-primary-600': route.path === '/' }"
            @click="closeMobileMenu"
          >
            <span class="mr-2">📊</span>Dashboard
          </router-link>

          <!-- Campaigns submenu -->
          <div>
            <button
              class="w-full flex items-center justify-between px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
              :class="{ 'bg-primary-50 text-primary-600': isCampaignActive }"
              @click="toggleMobileSubmenu('campaigns')"
            >
              <span><span class="mr-2">📁</span>Campaigns</span>
              <svg
                class="h-5 w-5 transition-transform"
                :class="{ 'rotate-180': mobileSubmenu === 'campaigns' }"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            <div
              v-if="mobileSubmenu === 'campaigns'"
              class="pl-6 space-y-1"
            >
              <router-link
                to="/campaigns"
                class="block px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
                :class="{ 'bg-primary-50 text-primary-600': route.path.startsWith('/campaigns') }"
                @click="closeMobileMenu"
              >
                <span class="mr-2">📁</span>Campaigns
              </router-link>
              <router-link
                to="/targets"
                class="block px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
                :class="{ 'bg-primary-50 text-primary-600': route.path.startsWith('/targets') }"
                @click="closeMobileMenu"
              >
                <span class="mr-2">🎯</span>Targets
              </router-link>
              <router-link
                to="/profiles"
                class="block px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
                :class="{ 'bg-primary-50 text-primary-600': route.path.startsWith('/profiles') }"
                @click="closeMobileMenu"
              >
                <span class="mr-2">📋</span>Profiles
              </router-link>
              <router-link
                to="/drives"
                class="block px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
                :class="{ 'bg-primary-50 text-primary-600': route.path.startsWith('/drives') }"
                @click="closeMobileMenu"
              >
                <span class="mr-2">💾</span>Drives
              </router-link>
            </div>
          </div>

          <!-- Monitor submenu -->
          <div>
            <button
              class="w-full flex items-center justify-between px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
              :class="{ 'bg-primary-50 text-primary-600': isMonitorActive }"
              @click="toggleMobileSubmenu('monitor')"
            >
              <span><span class="mr-2">📡</span>Monitor</span>
              <svg
                class="h-5 w-5 transition-transform"
                :class="{ 'rotate-180': mobileSubmenu === 'monitor' }"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            <div
              v-if="mobileSubmenu === 'monitor'"
              class="pl-6 space-y-1"
            >
              <router-link
                to="/map"
                class="block px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
                :class="{ 'bg-primary-50 text-primary-600': route.path === '/map' }"
                @click="closeMobileMenu"
              >
                <span class="mr-2">🗺️</span>Map
              </router-link>
              <router-link
                to="/alerts"
                class="block px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
                :class="{ 'bg-primary-50 text-primary-600': route.path === '/alerts' }"
                @click="closeMobileMenu"
              >
                <span class="mr-2">🚨</span>Alerts
              </router-link>
              <router-link
                to="/reports"
                class="block px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
                :class="{ 'bg-primary-50 text-primary-600': route.path === '/reports' }"
                @click="closeMobileMenu"
              >
                <span class="mr-2">📈</span>Reports
              </router-link>
            </div>
          </div>

          <!-- Users (Admin only) -->
          <router-link
            v-if="authStore.isAdmin"
            to="/users"
            class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
            :class="{ 'bg-primary-50 text-primary-600': route.path === '/users' }"
            @click="closeMobileMenu"
          >
            <span class="mr-2">👥</span>Users
          </router-link>

          <!-- Settings (Admin only) -->
          <router-link
            v-if="authStore.isAdmin"
            to="/settings"
            class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
            :class="{ 'bg-primary-50 text-primary-600': route.path === '/settings' }"
            @click="closeMobileMenu"
          >
            <span class="mr-2">⚙️</span>Settings
          </router-link>
        </div>

        <!-- Mobile user info -->
        <div class="border-t border-gray-200 pt-4 pb-3 px-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                <span class="text-primary-600 font-medium">{{ authStore.user?.username?.charAt(0).toUpperCase() }}</span>
              </div>
            </div>
            <div class="ml-3">
              <div class="text-base font-medium text-gray-800">
                {{ authStore.user?.username }}
              </div>
              <div class="text-sm text-gray-500">
                {{ authStore.user?.email }}
              </div>
            </div>
            <span
              v-if="authStore.isAdmin"
              class="ml-auto text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded-full"
            >Admin</span>
            <span
              v-else-if="authStore.userRole === 'operator'"
              class="ml-auto text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full"
            >Operator</span>
            <span
              v-else
              class="ml-auto text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
            >Viewer</span>
          </div>
          <div class="mt-3">
            <button
              class="w-full px-3 py-2 text-base font-medium text-red-600 hover:bg-red-50 rounded-md text-left"
              @click="logout"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <router-view />
    </main>
  </div>
</template>
