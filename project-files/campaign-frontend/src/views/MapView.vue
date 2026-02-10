<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { alertsApi, campaignsApi } from '@/services/api'
import Select from 'primevue/select'
import ProgressSpinner from 'primevue/progressspinner'

const route = useRoute()
const mapContainer = ref(null)
const map = ref(null)
const campaigns = ref([])
const mapData = ref([])
const loading = ref(true)

const filters = ref({
  campaign_id: route.query.campaign_id || '',
  type: 'both'
})

const typeOptions = [
  { label: 'Deployments & Triggers', value: 'both' },
  { label: 'Deployments Only', value: 'deployments' },
  { label: 'Triggers Only', value: 'triggers' },
]

// Fix for default marker icons in Leaflet with bundlers
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const deploymentIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const triggerIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

L.Marker.prototype.options.icon = defaultIcon

const campaignFilterOptions = ref([{ label: 'All Campaigns', value: '' }])

onMounted(async () => {
  await loadCampaigns()
  initMap()
  await loadMapData()
})

watch(filters, async () => {
  await loadMapData()
}, { deep: true })

const initMap = () => {
  map.value = L.map(mapContainer.value).setView([39.8283, -98.5795], 4)

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
  }).addTo(map.value)
}

const loadCampaigns = async () => {
  const response = await campaignsApi.list()
  campaigns.value = response.data
  campaignFilterOptions.value = [
    { label: 'All Campaigns', value: '' },
    ...campaigns.value.map(c => ({ label: c.name, value: c.id }))
  ]
}

const loadMapData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.campaign_id) {
      params.campaign_id = filters.value.campaign_id
    }

    const response = await alertsApi.map(params)
    mapData.value = response.data
    updateMarkers()
  } finally {
    loading.value = false
  }
}

const updateMarkers = () => {
  // Clear existing markers
  map.value.eachLayer((layer) => {
    if (layer instanceof L.Marker) {
      map.value.removeLayer(layer)
    }
  })

  const bounds = []

  // Add deployment markers
  if (filters.value.type === 'deployments' || filters.value.type === 'both') {
    mapData.value.deployments?.forEach((d) => {
      if (d.latitude && d.longitude) {
        const marker = L.marker([d.latitude, d.longitude], { icon: deploymentIcon })
          .addTo(map.value)
          .bindPopup(`
            <div class="text-sm">
              <div class="font-bold text-cyan-400">Deployed: ${d.drive_code}</div>
              <div class="text-slate-300">${d.location_description || 'No description'}</div>
              <div class="text-slate-400">${new Date(d.deployed_at).toLocaleString()}</div>
            </div>
          `)
        bounds.push([d.latitude, d.longitude])
      }
    })
  }

  // Add trigger markers
  if (filters.value.type === 'triggers' || filters.value.type === 'both') {
    mapData.value.triggers?.forEach((t) => {
      if (t.geo_latitude && t.geo_longitude) {
        const marker = L.marker([t.geo_latitude, t.geo_longitude], { icon: triggerIcon })
          .addTo(map.value)
          .bindPopup(`
            <div class="text-sm">
              <div class="font-bold text-red-400">Triggered: ${t.drive_code}</div>
              <div class="text-slate-300">${t.token_type} - ${t.filename || 'DNS'}</div>
              <div class="text-slate-300">${t.geo_city || ''}${t.geo_city && t.geo_country ? ', ' : ''}${t.geo_country || ''}</div>
              <div class="text-slate-400">IP: ${t.source_ip || 'Unknown'}</div>
              <div class="text-slate-400">${new Date(t.triggered_at).toLocaleString()}</div>
            </div>
          `)
        bounds.push([t.geo_latitude, t.geo_longitude])
      }
    })
  }

  // Fit map to markers
  if (bounds.length > 0) {
    map.value.fitBounds(bounds, { padding: [20, 20] })
  }
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold text-surface-0">Map View</h1>
    </div>

    <!-- Filters -->
    <div class="bg-surface-900 border border-surface-700 rounded-lg p-4 mb-4">
      <div class="flex flex-wrap gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Campaign</label>
          <Select v-model="filters.campaign_id" :options="campaignFilterOptions"
            optionLabel="label" optionValue="value" class="w-48" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Show</label>
          <Select v-model="filters.type" :options="typeOptions"
            optionLabel="label" optionValue="value" class="w-56" />
        </div>

        <div class="flex items-center space-x-4 text-sm">
          <div class="flex items-center">
            <span class="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
            <span class="text-surface-300">Deployment</span>
          </div>
          <div class="flex items-center">
            <span class="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
            <span class="text-surface-300">Trigger</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Map -->
    <div class="flex-1 bg-surface-900 border border-surface-700 rounded-lg overflow-hidden relative">
      <div v-if="loading" class="absolute inset-0 bg-surface-900/75 flex items-center justify-center z-10">
        <ProgressSpinner />
      </div>
      <div ref="mapContainer" class="h-full min-h-[500px]"></div>
    </div>

    <!-- Stats -->
    <div class="mt-4 grid grid-cols-2 gap-4">
      <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
        <div class="text-sm text-surface-400">Deployments Shown</div>
        <div class="text-xl font-bold text-blue-400">
          {{ mapData.deployments?.length || 0 }}
        </div>
      </div>
      <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
        <div class="text-sm text-surface-400">Triggers Shown</div>
        <div class="text-xl font-bold text-red-400">
          {{ mapData.triggers?.length || 0 }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.leaflet-container {
  font-family: inherit;
}
</style>
