<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import { reportsApi, campaignsApi } from '@/services/api'

Chart.register(...registerables)

// State
const campaigns = ref([])
const selectedCampaign = ref('')
const activeTab = ref('executive')
const loading = ref(true)

// Report data
const executiveReport = ref(null)
const temporalReport = ref(null)
const geographicReport = ref(null)
const behavioralReport = ref(null)
const comparativeReport = ref(null)

// Chart refs
const hourlyChart = ref(null)
const dayOfWeekChart = ref(null)
const heatmapChart = ref(null)
const timeToTriggerChart = ref(null)
const trendChart = ref(null)
const osChart = ref(null)
const browserChart = ref(null)
const fileTypeChart = ref(null)
const comparisonChart = ref(null)
const monthlyTrendChart = ref(null)

// Chart instances
let chartInstances = {}

const tabs = [
  { id: 'executive', name: 'Executive Summary', icon: '📊' },
  { id: 'temporal', name: 'Temporal Analysis', icon: '⏱️' },
  { id: 'geographic', name: 'Geographic Intelligence', icon: '🗺️' },
  { id: 'behavioral', name: 'Behavioral Analysis', icon: '🧠' },
  { id: 'comparative', name: 'Comparative Trends', icon: '📈' },
]

const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

onMounted(async () => {
  await loadCampaigns()
})

watch(activeTab, async () => {
  await loadActiveReport()
})

const loadCampaigns = async () => {
  loading.value = true
  try {
    const response = await campaignsApi.list()
    campaigns.value = response.data
    if (campaigns.value.length > 0) {
      selectedCampaign.value = campaigns.value[0].id
      await loadActiveReport()
    }
  } finally {
    loading.value = false
  }
}

const loadActiveReport = async () => {
  if (activeTab.value === 'comparative') {
    await loadComparativeReport()
  } else if (selectedCampaign.value) {
    loading.value = true
    try {
      switch (activeTab.value) {
        case 'executive':
          await loadExecutiveReport()
          break
        case 'temporal':
          await loadTemporalReport()
          break
        case 'geographic':
          await loadGeographicReport()
          break
        case 'behavioral':
          await loadBehavioralReport()
          break
      }
    } finally {
      loading.value = false
    }
  }
}

const loadExecutiveReport = async () => {
  const response = await reportsApi.executiveSummary(selectedCampaign.value)
  executiveReport.value = response.data
}

const loadTemporalReport = async () => {
  const response = await reportsApi.temporal(selectedCampaign.value)
  temporalReport.value = response.data
  await nextTick()
  renderTemporalCharts()
}

const loadGeographicReport = async () => {
  const response = await reportsApi.geographic(selectedCampaign.value)
  geographicReport.value = response.data
}

const loadBehavioralReport = async () => {
  const response = await reportsApi.behavioral(selectedCampaign.value)
  behavioralReport.value = response.data
  await nextTick()
  renderBehavioralCharts()
}

const loadComparativeReport = async () => {
  loading.value = true
  try {
    const response = await reportsApi.comparative()
    comparativeReport.value = response.data
    await nextTick()
    renderComparativeCharts()
  } finally {
    loading.value = false
  }
}

const destroyChart = (name) => {
  if (chartInstances[name]) {
    chartInstances[name].destroy()
    chartInstances[name] = null
  }
}

const renderTemporalCharts = () => {
  if (!temporalReport.value) return

  // Hourly chart
  destroyChart('hourly')
  if (hourlyChart.value) {
    const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
    chartInstances.hourly = new Chart(hourlyChart.value, {
      type: 'bar',
      data: {
        labels: hours,
        datasets: [{
          label: 'Triggers',
          data: Object.values(temporalReport.value.triggers_by_hour),
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    })
  }

  // Day of week chart
  destroyChart('dayOfWeek')
  if (dayOfWeekChart.value) {
    chartInstances.dayOfWeek = new Chart(dayOfWeekChart.value, {
      type: 'bar',
      data: {
        labels: dayNames,
        datasets: [{
          label: 'Triggers',
          data: Object.values(temporalReport.value.triggers_by_day_of_week),
          backgroundColor: 'rgba(16, 185, 129, 0.7)',
          borderColor: 'rgb(16, 185, 129)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    })
  }

  // Time-to-trigger distribution
  destroyChart('timeToTrigger')
  if (timeToTriggerChart.value) {
    const distribution = temporalReport.value.time_to_trigger_distribution
    chartInstances.timeToTrigger = new Chart(timeToTriggerChart.value, {
      type: 'bar',
      data: {
        labels: Object.keys(distribution).map(k => k + ' min'),
        datasets: [{
          label: 'Drives',
          data: Object.values(distribution),
          backgroundColor: 'rgba(239, 68, 68, 0.7)',
          borderColor: 'rgb(239, 68, 68)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    })
  }

  // Daily trend
  destroyChart('trend')
  if (trendChart.value && Object.keys(temporalReport.value.triggers_by_date).length > 0) {
    const dates = Object.keys(temporalReport.value.triggers_by_date).sort()
    chartInstances.trend = new Chart(trendChart.value, {
      type: 'line',
      data: {
        labels: dates.map(d => new Date(d).toLocaleDateString()),
        datasets: [{
          label: 'Triggers',
          data: dates.map(d => temporalReport.value.triggers_by_date[d]),
          borderColor: 'rgb(139, 92, 246)',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    })
  }
}

const renderBehavioralCharts = () => {
  if (!behavioralReport.value) return

  // OS distribution
  destroyChart('os')
  if (osChart.value && Object.keys(behavioralReport.value.os_distribution).length > 0) {
    chartInstances.os = new Chart(osChart.value, {
      type: 'doughnut',
      data: {
        labels: Object.keys(behavioralReport.value.os_distribution),
        datasets: [{
          data: Object.values(behavioralReport.value.os_distribution),
          backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#6B7280']
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'right' } }
      }
    })
  }

  // Browser distribution
  destroyChart('browser')
  if (browserChart.value && Object.keys(behavioralReport.value.browser_distribution).length > 0) {
    chartInstances.browser = new Chart(browserChart.value, {
      type: 'doughnut',
      data: {
        labels: Object.keys(behavioralReport.value.browser_distribution),
        datasets: [{
          data: Object.values(behavioralReport.value.browser_distribution),
          backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#6B7280']
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'right' } }
      }
    })
  }

  // File type popularity
  destroyChart('fileType')
  if (fileTypeChart.value && Object.keys(behavioralReport.value.file_type_popularity).length > 0) {
    chartInstances.fileType = new Chart(fileTypeChart.value, {
      type: 'bar',
      data: {
        labels: Object.keys(behavioralReport.value.file_type_popularity),
        datasets: [{
          label: 'Opens',
          data: Object.values(behavioralReport.value.file_type_popularity),
          backgroundColor: 'rgba(59, 130, 246, 0.7)'
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    })
  }
}

const renderComparativeCharts = () => {
  if (!comparativeReport.value) return

  // Campaign comparison
  destroyChart('comparison')
  if (comparisonChart.value && comparativeReport.value.campaigns.length > 0) {
    const campaigns = comparativeReport.value.campaigns.slice(0, 10)
    chartInstances.comparison = new Chart(comparisonChart.value, {
      type: 'bar',
      data: {
        labels: campaigns.map(c => c.campaign_name.length > 15 ? c.campaign_name.substring(0, 15) + '...' : c.campaign_name),
        datasets: [{
          label: 'Plug-in Rate %',
          data: campaigns.map(c => c.plug_in_rate),
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true, max: 100 } }
      }
    })
  }

  // Monthly trend
  destroyChart('monthlyTrend')
  if (monthlyTrendChart.value && Object.keys(comparativeReport.value.monthly_trigger_counts).length > 0) {
    const months = Object.keys(comparativeReport.value.monthly_trigger_counts).sort()
    chartInstances.monthlyTrend = new Chart(monthlyTrendChart.value, {
      type: 'line',
      data: {
        labels: months,
        datasets: [
          {
            label: 'Triggers',
            data: months.map(m => comparativeReport.value.monthly_trigger_counts[m]),
            borderColor: 'rgb(239, 68, 68)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            fill: true,
            yAxisID: 'y'
          },
          {
            label: 'Plug-in Rate %',
            data: months.map(m => comparativeReport.value.monthly_plug_in_rates[m]),
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: false,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          y: { type: 'linear', position: 'left', beginAtZero: true },
          y1: { type: 'linear', position: 'right', beginAtZero: true, max: 100, grid: { drawOnChartArea: false } }
        }
      }
    })
  }
}

const getRiskColor = (level) => {
  const colors = {
    'Critical': 'text-red-600 bg-red-100',
    'High': 'text-orange-600 bg-orange-100',
    'Medium': 'text-yellow-600 bg-yellow-100',
    'Low': 'text-green-600 bg-green-100'
  }
  return colors[level] || 'text-gray-600 bg-gray-100'
}

const formatDuration = (minutes) => {
  if (!minutes) return '-'
  if (minutes < 60) return `${Math.round(minutes)} min`
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return `${hours}h ${mins}m`
}

const exportCsv = async () => {
  const response = await reportsApi.exportCsv(selectedCampaign.value)
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `campaign-report.csv`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Reports</h1>
      <button
        v-if="selectedCampaign && activeTab !== 'comparative'"
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        @click="exportCsv"
      >
        Export CSV
      </button>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="-mb-px flex space-x-8">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="[
            activeTab === tab.id
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
          ]"
          @click="activeTab = tab.id"
        >
          <span class="mr-2">{{ tab.icon }}</span>
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- Campaign Selector (not shown for comparative) -->
    <div v-if="activeTab !== 'comparative'" class="bg-white shadow rounded-lg p-4 mb-6">
      <div class="flex items-end gap-4">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700 mb-1">Select Campaign</label>
          <select
            v-model="selectedCampaign"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            @change="loadActiveReport"
          >
            <option v-for="c in campaigns" :key="c.id" :value="c.id">
              {{ c.name }} ({{ c.status }})
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
    </div>

    <!-- Executive Summary Tab -->
    <div v-else-if="activeTab === 'executive' && executiveReport">
      <!-- Risk Assessment Banner -->
      <div :class="['rounded-lg p-6 mb-6', getRiskColor(executiveReport.risk_level)]">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-xl font-bold">Risk Level: {{ executiveReport.risk_level }}</h2>
            <p class="mt-1">{{ executiveReport.campaign_name }} - {{ executiveReport.client_name || 'No client' }}</p>
          </div>
          <div class="text-4xl font-bold">{{ executiveReport.risk_score }}/100</div>
        </div>
      </div>

      <!-- Key Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Plug-in Rate</div>
          <div class="text-3xl font-bold text-primary-600">{{ executiveReport.plug_in_rate }}%</div>
          <div class="text-xs text-gray-400">{{ executiveReport.drives_triggered }}/{{ executiveReport.drives_deployed }} drives</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Avg Time to Trigger</div>
          <div class="text-3xl font-bold">{{ formatDuration(executiveReport.avg_time_to_trigger_minutes) }}</div>
          <div class="text-xs text-gray-400">Min: {{ formatDuration(executiveReport.min_time_to_trigger_minutes) }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Total Triggers</div>
          <div class="text-3xl font-bold text-red-600">{{ executiveReport.total_triggers }}</div>
          <div class="text-xs text-gray-400">{{ executiveReport.unique_ips }} unique IPs</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Campaign Duration</div>
          <div class="text-xl font-bold">{{ executiveReport.campaign_start || 'Not started' }}</div>
          <div class="text-xs text-gray-400">{{ executiveReport.campaign_end || 'Ongoing' }}</div>
        </div>
      </div>

      <!-- Key Findings -->
      <div class="bg-white shadow rounded-lg p-6 mb-6">
        <h3 class="text-lg font-medium mb-4">Key Findings</h3>
        <ul class="space-y-2">
          <li v-for="(finding, i) in executiveReport.key_findings" :key="i" class="flex items-start">
            <span class="text-primary-600 mr-2">•</span>
            {{ finding }}
          </li>
        </ul>
      </div>

      <!-- Best Performers -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Most Effective Profile</h3>
          <div class="text-2xl font-bold text-primary-600">
            {{ executiveReport.most_effective_profile || 'N/A' }}
          </div>
        </div>
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Most Effective Location</h3>
          <div class="text-2xl font-bold text-primary-600">
            {{ executiveReport.most_effective_location || 'N/A' }}
          </div>
        </div>
      </div>
    </div>

    <!-- Temporal Analysis Tab -->
    <div v-else-if="activeTab === 'temporal' && temporalReport">
      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Avg Time to Trigger</div>
          <div class="text-2xl font-bold">{{ formatDuration(temporalReport.avg_time_to_trigger_minutes) }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Median Time</div>
          <div class="text-2xl font-bold">{{ formatDuration(temporalReport.median_time_to_trigger_minutes) }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Peak Hour</div>
          <div class="text-2xl font-bold">{{ temporalReport.peak_hour !== null ? temporalReport.peak_hour + ':00' : 'N/A' }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Peak Day</div>
          <div class="text-2xl font-bold">{{ temporalReport.peak_day !== null ? dayNames[temporalReport.peak_day] : 'N/A' }}</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Triggers by Hour</h3>
          <canvas ref="hourlyChart" />
        </div>
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Triggers by Day of Week</h3>
          <canvas ref="dayOfWeekChart" />
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Time to First Trigger Distribution</h3>
          <canvas ref="timeToTriggerChart" />
        </div>
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Daily Trigger Trend</h3>
          <canvas ref="trendChart" />
        </div>
      </div>
    </div>

    <!-- Geographic Intelligence Tab -->
    <div v-else-if="activeTab === 'geographic' && geographicReport">
      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Total Locations</div>
          <div class="text-2xl font-bold">{{ geographicReport.locations.length }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Triggered On-Site</div>
          <div class="text-2xl font-bold text-green-600">{{ geographicReport.drives_triggered_onsite }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Triggered Off-Site</div>
          <div class="text-2xl font-bold text-orange-600">{{ geographicReport.drives_triggered_offsite }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Countries</div>
          <div class="text-2xl font-bold">{{ Object.keys(geographicReport.trigger_countries).length }}</div>
        </div>
      </div>

      <!-- Location Table -->
      <div class="bg-white shadow rounded-lg mb-6">
        <div class="px-6 py-4 border-b">
          <h3 class="text-lg font-medium">Location Performance</h3>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Deployed</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Triggered</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rate</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Time</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="loc in geographicReport.locations" :key="loc.location_name" class="hover:bg-gray-50">
              <td class="px-6 py-4 font-medium">{{ loc.location_name || 'Unknown' }}</td>
              <td class="px-6 py-4">{{ loc.drives_deployed }}</td>
              <td class="px-6 py-4 text-red-600 font-medium">{{ loc.drives_triggered }}</td>
              <td class="px-6 py-4">
                <span :class="[
                  'px-2 py-1 rounded text-sm font-medium',
                  loc.trigger_rate >= 50 ? 'bg-red-100 text-red-700' :
                  loc.trigger_rate >= 25 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-green-100 text-green-700'
                ]">
                  {{ loc.trigger_rate }}%
                </span>
              </td>
              <td class="px-6 py-4 text-gray-500">{{ formatDuration(loc.avg_time_to_trigger_minutes) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Cities & Countries -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Trigger Sources by City</h3>
          <div v-if="Object.keys(geographicReport.trigger_cities).length > 0" class="space-y-2">
            <div v-for="(count, city) in geographicReport.trigger_cities" :key="city" class="flex justify-between">
              <span>{{ city }}</span>
              <span class="font-medium">{{ count }}</span>
            </div>
          </div>
          <div v-else class="text-gray-500">No city data available</div>
        </div>
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Trigger Sources by Country</h3>
          <div v-if="Object.keys(geographicReport.trigger_countries).length > 0" class="space-y-2">
            <div v-for="(count, country) in geographicReport.trigger_countries" :key="country" class="flex justify-between">
              <span>{{ country }}</span>
              <span class="font-medium">{{ count }}</span>
            </div>
          </div>
          <div v-else class="text-gray-500">No country data available</div>
        </div>
      </div>
    </div>

    <!-- Behavioral Analysis Tab -->
    <div v-else-if="activeTab === 'behavioral' && behavioralReport">
      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Unique IPs</div>
          <div class="text-2xl font-bold">{{ behavioralReport.unique_ips }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Single File Openers</div>
          <div class="text-2xl font-bold text-green-600">{{ behavioralReport.single_file_openers }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Multi-File Openers</div>
          <div class="text-2xl font-bold text-orange-600">{{ behavioralReport.multi_file_openers }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Avg Files per IP</div>
          <div class="text-2xl font-bold">{{ behavioralReport.avg_files_per_ip }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Repeat Offenders</div>
          <div class="text-2xl font-bold text-red-600">{{ behavioralReport.repeat_trigger_ips }}</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Operating Systems</h3>
          <canvas ref="osChart" />
        </div>
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Browsers</h3>
          <canvas ref="browserChart" />
        </div>
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">File Type Popularity</h3>
          <canvas ref="fileTypeChart" />
        </div>
      </div>

      <!-- First File Opened -->
      <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-lg font-medium mb-4">First File Opened (per drive)</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div
            v-for="(count, type) in behavioralReport.first_file_opened"
            :key="type"
            class="text-center p-4 bg-gray-50 rounded-lg"
          >
            <div class="text-2xl font-bold text-primary-600">{{ count }}</div>
            <div class="text-sm text-gray-500 capitalize">{{ type }}</div>
          </div>
        </div>
        <div v-if="Object.keys(behavioralReport.first_file_opened).length === 0" class="text-center text-gray-500 py-4">
          No data available
        </div>
      </div>
    </div>

    <!-- Comparative Analysis Tab -->
    <div v-else-if="activeTab === 'comparative' && comparativeReport">
      <!-- Aggregate Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Total Campaigns</div>
          <div class="text-2xl font-bold">{{ comparativeReport.total_campaigns }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Avg Plug-in Rate</div>
          <div class="text-2xl font-bold text-primary-600">{{ comparativeReport.avg_plug_in_rate }}%</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Best Campaign</div>
          <div class="text-lg font-bold text-green-600">{{ comparativeReport.best_campaign || 'N/A' }}</div>
        </div>
        <div class="bg-white shadow rounded-lg p-4">
          <div class="text-sm text-gray-500">Needs Improvement</div>
          <div class="text-lg font-bold text-orange-600">{{ comparativeReport.worst_campaign || 'N/A' }}</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Campaign Comparison (Top 10)</h3>
          <canvas ref="comparisonChart" />
        </div>
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium mb-4">Monthly Trends</h3>
          <canvas ref="monthlyTrendChart" />
        </div>
      </div>

      <!-- Campaign Table -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b">
          <h3 class="text-lg font-medium">All Campaigns</h3>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Campaign</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Deployed</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Triggered</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rate</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Time</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="c in comparativeReport.campaigns" :key="c.campaign_id" class="hover:bg-gray-50">
              <td class="px-6 py-4 font-medium">{{ c.campaign_name }}</td>
              <td class="px-6 py-4">
                <span :class="[
                  'px-2 py-1 rounded text-xs font-medium',
                  c.status === 'active' ? 'bg-green-100 text-green-700' :
                  c.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                ]">
                  {{ c.status }}
                </span>
              </td>
              <td class="px-6 py-4">{{ c.drives_deployed }}</td>
              <td class="px-6 py-4 text-red-600 font-medium">{{ c.drives_triggered }}</td>
              <td class="px-6 py-4">
                <span :class="[
                  'px-2 py-1 rounded text-sm font-medium',
                  c.plug_in_rate >= 50 ? 'bg-red-100 text-red-700' :
                  c.plug_in_rate >= 25 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-green-100 text-green-700'
                ]">
                  {{ c.plug_in_rate }}%
                </span>
              </td>
              <td class="px-6 py-4 text-gray-500">{{ formatDuration(c.avg_time_to_trigger_minutes) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- No Data -->
    <div v-else class="text-center py-12 text-gray-500">
      <p>Select a campaign to view its report</p>
    </div>
  </div>
</template>
