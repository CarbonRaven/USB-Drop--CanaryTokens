<script setup>
import { ref, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import { reportsApi, campaignsApi } from '@/services/api'
import { useToast } from 'primevue/usetoast'
import Select from 'primevue/select'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import ProgressSpinner from 'primevue/progressspinner'

Chart.register(...registerables)

// Set dark defaults for Chart.js
Chart.defaults.color = '#94a3b8'
Chart.defaults.borderColor = '#334155'

const toast = useToast()
const campaigns = ref([])
const selectedCampaign = ref('')
const report = ref(null)
const loading = ref(true)

const statusChart = ref(null)
const triggerChart = ref(null)
let statusChartInstance = null
let triggerChartInstance = null

const campaignOptions = ref([])

onMounted(async () => {
  await loadCampaigns()
})

const loadCampaigns = async () => {
  loading.value = true
  try {
    const response = await campaignsApi.list()
    campaigns.value = response.data
    campaignOptions.value = campaigns.value.map(c => ({
      label: `${c.name} (${c.status})`,
      value: c.id
    }))
    if (campaigns.value.length > 0) {
      selectedCampaign.value = campaigns.value[0].id
      await loadReport()
    }
  } finally {
    loading.value = false
  }
}

const loadReport = async () => {
  if (!selectedCampaign.value) return

  loading.value = true
  try {
    const response = await reportsApi.campaign(selectedCampaign.value)
    report.value = response.data
    updateCharts()
  } finally {
    loading.value = false
  }
}

const updateCharts = () => {
  // Status distribution chart
  if (statusChartInstance) statusChartInstance.destroy()
  if (statusChart.value && report.value?.status_distribution) {
    statusChartInstance = new Chart(statusChart.value, {
      type: 'doughnut',
      data: {
        labels: Object.keys(report.value.status_distribution),
        datasets: [{
          data: Object.values(report.value.status_distribution),
          backgroundColor: [
            '#64748b', // created - slate
            '#38bdf8', // prepared - sky
            '#22c55e', // deployed - green
            '#ef4444', // triggered - red
            '#f59e0b'  // recovered - amber
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#94a3b8'
            }
          }
        }
      }
    })
  }

  // Triggers over time chart
  if (triggerChartInstance) triggerChartInstance.destroy()
  if (triggerChart.value && report.value?.triggers_by_day) {
    const days = Object.keys(report.value.triggers_by_day).sort()
    triggerChartInstance = new Chart(triggerChart.value, {
      type: 'line',
      data: {
        labels: days.map(d => new Date(d).toLocaleDateString()),
        datasets: [{
          label: 'Triggers',
          data: days.map(d => report.value.triggers_by_day[d]),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
              color: '#94a3b8'
            },
            grid: {
              color: '#334155'
            }
          },
          x: {
            ticks: {
              color: '#94a3b8'
            },
            grid: {
              color: '#334155'
            }
          }
        }
      }
    })
  }
}

const exportCsv = async () => {
  try {
    const response = await reportsApi.exportCsv(selectedCampaign.value)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `campaign-${selectedCampaign.value}-report.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    toast.add({ severity: 'success', summary: 'CSV Exported', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to export CSV', life: 5000 })
  }
}

const getCampaignName = (id) => {
  return campaigns.value.find(c => c.id === id)?.name || ''
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-surface-0">Reports</h1>
      <Button
        v-if="selectedCampaign"
        label="Export CSV"
        icon="pi pi-download"
        @click="exportCsv"
      />
    </div>

    <!-- Campaign Selector -->
    <div class="bg-surface-900 border border-surface-700 rounded-lg p-4 mb-6">
      <div class="flex items-end gap-4">
        <div class="flex-1">
          <label class="block text-sm font-medium text-surface-300 mb-1">Select Campaign</label>
          <Select v-model="selectedCampaign" :options="campaignOptions" @change="loadReport"
            optionLabel="label" optionValue="value" class="w-full" />
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <div v-else-if="report">
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Total Drives</div>
          <div class="text-2xl font-bold text-surface-0">{{ report.total_drives }}</div>
        </div>
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Deployed</div>
          <div class="text-2xl font-bold text-green-400">{{ report.deployed }}</div>
        </div>
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Triggered</div>
          <div class="text-2xl font-bold text-red-400">{{ report.triggered }}</div>
        </div>
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Total Triggers</div>
          <div class="text-2xl font-bold text-surface-0">{{ report.total_triggers }}</div>
        </div>
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Success Rate</div>
          <div class="text-2xl font-bold text-surface-0">
            {{ report.deployed ? Math.round((report.triggered / report.deployed) * 100) : 0 }}%
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-6">
          <h2 class="text-lg font-medium text-surface-0 mb-4">Drive Status Distribution</h2>
          <div class="aspect-square max-w-xs mx-auto">
            <canvas ref="statusChart"></canvas>
          </div>
        </div>

        <div class="bg-surface-900 border border-surface-700 rounded-lg p-6">
          <h2 class="text-lg font-medium text-surface-0 mb-4">Triggers Over Time</h2>
          <canvas ref="triggerChart"></canvas>
        </div>
      </div>

      <!-- Token Type Breakdown -->
      <div class="bg-surface-900 border border-surface-700 rounded-lg p-6 mb-6">
        <h2 class="text-lg font-medium text-surface-0 mb-4">Triggers by Token Type</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="(count, type) in report.triggers_by_type" :key="type"
            class="text-center p-4 bg-surface-800 border border-surface-700 rounded-lg">
            <div class="text-2xl font-bold text-primary-400">{{ count }}</div>
            <div class="text-sm text-surface-400 capitalize">{{ type }}</div>
          </div>
        </div>
        <div v-if="Object.keys(report.triggers_by_type || {}).length === 0"
          class="text-center text-surface-400 py-4">
          No triggers recorded yet
        </div>
      </div>

      <!-- Top Triggered Drives -->
      <div class="bg-surface-900 border border-surface-700 rounded-lg overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-700">
          <h2 class="text-lg font-medium text-surface-0">Top Triggered Drives</h2>
        </div>
        <DataTable :value="report.top_drives || []" :rowHover="true"
          emptyMessage="No triggered drives yet">
          <Column field="unique_code" header="Code">
            <template #body="{ data }">
              <router-link :to="`/drives/${data.id}`" class="text-primary-400 hover:underline font-mono">
                {{ data.unique_code }}
              </router-link>
            </template>
          </Column>
          <Column field="label" header="Label">
            <template #body="{ data }">
              <span class="text-surface-300">{{ data.label || '-' }}</span>
            </template>
          </Column>
          <Column field="location" header="Location">
            <template #body="{ data }">
              <span class="text-surface-300">{{ data.location || '-' }}</span>
            </template>
          </Column>
          <Column field="trigger_count" header="Triggers">
            <template #body="{ data }">
              <span class="font-medium text-red-400">{{ data.trigger_count }}</span>
            </template>
          </Column>
          <Column field="first_trigger" header="First Trigger">
            <template #body="{ data }">
              <span class="text-surface-300">
                {{ data.first_trigger ? new Date(data.first_trigger).toLocaleString() : '-' }}
              </span>
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <div v-else class="text-center py-12 text-surface-400">
      <p>Select a campaign to view its report</p>
    </div>
  </div>
</template>
