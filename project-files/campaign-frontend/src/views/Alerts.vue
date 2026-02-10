<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { alertsApi, campaignsApi } from '@/services/api'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'

const alerts = ref([])
const campaigns = ref([])
const stats = ref(null)
const loading = ref(true)
const autoRefresh = ref(true)
let refreshInterval = null

const filters = ref({
  campaign_id: '',
  hours: 24
})

const hourOptions = [
  { value: 1, label: 'Last hour' },
  { value: 6, label: 'Last 6 hours' },
  { value: 24, label: 'Last 24 hours' },
  { value: 72, label: 'Last 3 days' },
  { value: 168, label: 'Last 7 days' },
  { value: 720, label: 'Last 30 days' }
]

const campaignFilterOptions = ref([{ label: 'All Campaigns', value: '' }])

onMounted(async () => {
  await Promise.all([loadCampaigns(), loadAlerts()])
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

const startAutoRefresh = () => {
  if (autoRefresh.value) {
    refreshInterval = setInterval(loadAlerts, 30000)
  }
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

const onAutoRefreshChange = () => {
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const loadCampaigns = async () => {
  const response = await campaignsApi.list()
  campaigns.value = response.data
  campaignFilterOptions.value = [
    { label: 'All Campaigns', value: '' },
    ...campaigns.value.map(c => ({ label: c.name, value: c.id }))
  ]
}

const loadAlerts = async () => {
  loading.value = true
  try {
    const [alertsRes, statsRes] = await Promise.all([
      alertsApi.recent(filters.value.hours),
      alertsApi.stats(filters.value.campaign_id || undefined)
    ])

    let data = alertsRes.data
    if (filters.value.campaign_id) {
      data = data.filter(a => a.campaign_id === filters.value.campaign_id)
    }
    alerts.value = data
    stats.value = statsRes.data
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  loadAlerts()
}

const formatTime = (dateStr) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return date.toLocaleString()
}

const getTokenTypeSeverity = (type) => {
  const severities = {
    dns: 'secondary',
    word: 'info',
    excel: 'success',
    pdf: 'danger',
    folder: 'warn',
    qr: 'secondary'
  }
  return severities[type] || 'secondary'
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-surface-0">Alerts</h1>
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <ToggleSwitch v-model="autoRefresh" @update:modelValue="onAutoRefreshChange" />
          <span class="text-sm" :class="autoRefresh ? 'text-green-400' : 'text-surface-400'">
            {{ autoRefresh ? 'Live' : 'Paused' }}
          </span>
          <span v-if="autoRefresh" class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
        </div>
        <Button label="Refresh" icon="pi pi-refresh" text @click="loadAlerts" />
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
        <div class="text-sm text-surface-400">Total Triggers</div>
        <div class="text-2xl font-bold text-red-400">{{ stats?.total || 0 }}</div>
      </div>
      <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
        <div class="text-sm text-surface-400">Today</div>
        <div class="text-2xl font-bold text-surface-0">{{ stats?.today || 0 }}</div>
      </div>
      <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
        <div class="text-sm text-surface-400">This Week</div>
        <div class="text-2xl font-bold text-surface-0">{{ stats?.this_week || 0 }}</div>
      </div>
      <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
        <div class="text-sm text-surface-400">Unique IPs</div>
        <div class="text-2xl font-bold text-surface-0">{{ stats?.unique_ips || 0 }}</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-surface-900 border border-surface-700 rounded-lg p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Campaign</label>
          <Select v-model="filters.campaign_id" :options="campaignFilterOptions"
            optionLabel="label" optionValue="value" class="w-48" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Time Range</label>
          <Select v-model="filters.hours" :options="hourOptions"
            optionLabel="label" optionValue="value" class="w-40" />
        </div>

        <Button label="Apply" icon="pi pi-filter" @click="applyFilters" />
      </div>
    </div>

    <!-- Alerts List -->
    <div class="bg-surface-900 border border-surface-700 rounded-lg overflow-hidden">
      <div class="divide-y divide-surface-700">
        <div
          v-for="alert in alerts"
          :key="alert.id"
          class="p-4 hover:bg-surface-800 transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3">
                <router-link :to="`/drives/${alert.drive_id}`"
                  class="font-mono font-medium text-primary-400 hover:underline">
                  {{ alert.drive_code }}
                </router-link>
                <Tag :value="alert.token_type" :severity="getTokenTypeSeverity(alert.token_type)" />
                <span v-if="alert.token_filename" class="text-sm text-surface-400">
                  {{ alert.token_filename }}
                </span>
              </div>

              <div class="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-surface-300">
                <div class="flex items-center">
                  <i class="pi pi-globe mr-2 text-surface-400"></i>
                  {{ alert.source_ip || 'Unknown IP' }}
                </div>
                <div v-if="alert.geo_city || alert.geo_country" class="flex items-center">
                  <i class="pi pi-map-marker mr-2 text-surface-400"></i>
                  {{ alert.geo_city }}{{ alert.geo_city && alert.geo_country ? ', ' : '' }}{{ alert.geo_country }}
                </div>
                <div v-if="alert.user_agent" class="flex items-center max-w-xs truncate" :title="alert.user_agent">
                  <i class="pi pi-desktop mr-2 text-surface-400"></i>
                  <span class="truncate">{{ alert.user_agent }}</span>
                </div>
              </div>
            </div>

            <div class="text-right ml-4">
              <div class="text-sm font-medium text-surface-0">{{ formatTime(alert.triggered_at) }}</div>
              <div class="text-xs text-surface-400">{{ new Date(alert.triggered_at).toLocaleString() }}</div>
            </div>
          </div>
        </div>

        <div v-if="alerts.length === 0" class="p-8 text-center text-surface-400">
          <i class="pi pi-bell text-4xl text-surface-600 mb-4 block"></i>
          <p>No alerts in the selected time range</p>
        </div>
      </div>
    </div>
  </div>
</template>
