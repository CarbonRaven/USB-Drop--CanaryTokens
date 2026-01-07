<script setup>
import { ref, onMounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import api from '@/services/api'

const mapContainer = ref(null)
const map = ref(null)
const loading = ref(true)
const error = ref(null)
const stats = ref({ deployments: 0, triggers: 0 })

// Marker icons
const blueIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const redIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

onMounted(async () => {
  // Initialize map
  map.value = L.map(mapContainer.value).setView([39.8283, -98.5795], 4)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map.value)

  // Load data
  await loadData()
})

async function loadData() {
  loading.value = true
  error.value = null

  try {
    const response = await api.get('/alerts/mapdata')
    const data = response.data

    console.log('Map API response:', data)

    const bounds = []
    let depCount = 0
    let trigCount = 0

    // Handle new format: { deployments: [], triggers: [] }
    if (data.deployments && Array.isArray(data.deployments)) {
      data.deployments.forEach(d => {
        if (d.latitude && d.longitude) {
          addMarker(d.latitude, d.longitude, blueIcon, `
            <b>Deployment: ${d.drive_code}</b><br>
            ${d.location_description || 'No description'}<br>
            <small>${new Date(d.deployed_at).toLocaleString()}</small>
          `)
          bounds.push([d.latitude, d.longitude])
          depCount++
        }
      })
    }

    if (data.triggers && Array.isArray(data.triggers)) {
      data.triggers.forEach(t => {
        const lat = t.geo_latitude || t.latitude
        const lng = t.geo_longitude || t.longitude
        if (lat && lng) {
          addMarker(lat, lng, redIcon, `
            <b style="color:red">Trigger: ${t.drive_code}</b><br>
            ${t.token_type} - ${t.filename || 'DNS'}<br>
            ${t.geo_city || ''}${t.geo_city && t.geo_country ? ', ' : ''}${t.geo_country || ''}<br>
            <small>IP: ${t.source_ip || 'Unknown'}</small><br>
            <small>${new Date(t.triggered_at).toLocaleString()}</small>
          `)
          bounds.push([lat, lng])
          trigCount++
        }
      })
    }

    // Handle old format: array with type field
    if (Array.isArray(data)) {
      data.forEach(item => {
        if (item.latitude && item.longitude) {
          const isDeployment = item.type === 'deployment'
          addMarker(item.latitude, item.longitude, isDeployment ? blueIcon : redIcon, `
            <b>${item.label || item.drive_code}</b><br>
            <small>${new Date(item.timestamp).toLocaleString()}</small>
          `)
          bounds.push([item.latitude, item.longitude])
          if (isDeployment) depCount++
          else trigCount++
        }
      })
    }

    stats.value = { deployments: depCount, triggers: trigCount }

    // Fit map to markers
    if (bounds.length > 0) {
      map.value.fitBounds(bounds, { padding: [50, 50] })
    }

  } catch (err) {
    console.error('Map load error:', err)
    error.value = err.response?.data?.detail || err.message || 'Failed to load map data'
  } finally {
    loading.value = false
  }
}

function addMarker(lat, lng, icon, popupContent) {
  L.marker([lat, lng], { icon })
    .addTo(map.value)
    .bindPopup(popupContent)
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-4">Map View</h1>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>

    <!-- Legend -->
    <div class="bg-white shadow rounded-lg p-4 mb-4 flex items-center gap-6">
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 bg-blue-500 rounded-full"></span>
        <span>Deployments ({{ stats.deployments }})</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 bg-red-500 rounded-full"></span>
        <span>Triggers ({{ stats.triggers }})</span>
      </div>
      <button
        @click="loadData"
        class="ml-auto px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
      >
        Refresh
      </button>
    </div>

    <!-- Map -->
    <div class="bg-white shadow rounded-lg overflow-hidden relative" style="height: 600px;">
      <div v-if="loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
      <div ref="mapContainer" style="height: 100%; width: 100%;"></div>
    </div>
  </div>
</template>

<style scoped>
.leaflet-container {
  height: 100%;
  width: 100%;
}
</style>
