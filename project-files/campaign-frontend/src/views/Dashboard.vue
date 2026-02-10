<script setup>
import { ref, onMounted } from 'vue'
import { reportsApi, alertsApi } from '@/services/api'
import ProgressSpinner from 'primevue/progressspinner'

const stats = ref(null)
const recentAlerts = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [summaryRes, alertsRes] = await Promise.all([
      reportsApi.summary(),
      alertsApi.recent(24)
    ])
    stats.value = summaryRes.data
    recentAlerts.value = alertsRes.data.slice(0, 10)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-surface-0 mb-6">Dashboard</h1>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <div v-else>
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-6">
          <div class="text-sm font-medium text-surface-400">Total Campaigns</div>
          <div class="mt-2 text-3xl font-bold text-surface-0">{{ stats?.total_campaigns || 0 }}</div>
          <div class="mt-1 text-sm text-green-400">{{ stats?.active_campaigns || 0 }} active</div>
        </div>

        <div class="bg-surface-900 border border-surface-700 rounded-lg p-6">
          <div class="text-sm font-medium text-surface-400">Total Drives</div>
          <div class="mt-2 text-3xl font-bold text-surface-0">{{ stats?.total_drives || 0 }}</div>
          <div class="mt-1 text-sm text-surface-400">
            {{ stats?.drives_by_status?.deployed || 0 }} deployed
          </div>
        </div>

        <div class="bg-surface-900 border border-surface-700 rounded-lg p-6">
          <div class="text-sm font-medium text-surface-400">Total Triggers</div>
          <div class="mt-2 text-3xl font-bold text-red-400">{{ stats?.total_triggers || 0 }}</div>
          <div class="mt-1 text-sm text-surface-400">
            {{ stats?.drives_by_status?.triggered || 0 }} drives triggered
          </div>
        </div>

        <div class="bg-surface-900 border border-surface-700 rounded-lg p-6">
          <div class="text-sm font-medium text-surface-400">Ready to Deploy</div>
          <div class="mt-2 text-3xl font-bold text-primary-400">
            {{ stats?.drives_by_status?.prepared || 0 }}
          </div>
          <div class="mt-1 text-sm text-surface-400">prepared drives</div>
        </div>
      </div>

      <!-- Recent Alerts -->
      <div class="bg-surface-900 border border-surface-700 rounded-lg">
        <div class="px-6 py-4 border-b border-surface-700">
          <h2 class="text-lg font-medium text-surface-0">Recent Alerts (24h)</h2>
        </div>
        <div class="divide-y divide-surface-700">
          <div
            v-for="alert in recentAlerts"
            :key="alert.id"
            class="px-6 py-4 hover:bg-surface-800 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="font-medium text-surface-0">{{ alert.drive_code }}</span>
                <span class="mx-2 text-surface-600">|</span>
                <span class="text-sm text-surface-300">{{ alert.token_type }}</span>
                <span v-if="alert.token_filename" class="text-sm text-surface-400">
                  - {{ alert.token_filename }}
                </span>
              </div>
              <div class="text-right">
                <div class="text-sm text-surface-300">{{ alert.source_ip || 'Unknown IP' }}</div>
                <div class="text-xs text-surface-400">
                  {{ alert.geo_city }}{{ alert.geo_city && alert.geo_country ? ', ' : '' }}{{ alert.geo_country }}
                </div>
              </div>
            </div>
          </div>

          <div v-if="recentAlerts.length === 0" class="px-6 py-8 text-center text-surface-400">
            No alerts in the last 24 hours
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
