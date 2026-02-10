<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { drivesApi } from '@/services/api'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

const route = useRoute()
const router = useRouter()

const drive = ref(null)
const tokens = ref([])
const loading = ref(true)
const showDeployModal = ref(false)
const deploying = ref(false)
const gettingLocation = ref(false)

const deployment = ref({
  latitude: null,
  longitude: null,
  location_description: '',
  deployed_by: ''
})

const driveStatusSeverity = {
  created: 'secondary',
  prepared: 'info',
  deployed: 'success',
  triggered: 'danger',
  recovered: 'warn',
}

onMounted(async () => {
  await loadDrive()
  if (route.query.action === 'deploy') {
    showDeployModal.value = true
  }
})

const loadDrive = async () => {
  loading.value = true
  try {
    const [driveRes, tokensRes] = await Promise.all([
      drivesApi.get(route.params.id),
      drivesApi.tokens(route.params.id)
    ])
    drive.value = driveRes.data
    tokens.value = tokensRes.data
  } catch (error) {
    console.error('Failed to load drive:', error)
    router.push('/drives')
  } finally {
    loading.value = false
  }
}

const prepareDrive = async () => {
  await drivesApi.prepare(drive.value.id)
  await loadDrive()
}

const downloadDrive = async () => {
  const response = await drivesApi.download(drive.value.id)
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${drive.value.unique_code}.zip`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const getCurrentLocation = () => {
  if (!navigator.geolocation) {
    alert('Geolocation is not supported by your browser')
    return
  }

  gettingLocation.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      deployment.value.latitude = position.coords.latitude
      deployment.value.longitude = position.coords.longitude
      gettingLocation.value = false
    },
    (error) => {
      console.error('Geolocation error:', error)
      alert('Failed to get current location')
      gettingLocation.value = false
    }
  )
}

const deployDrive = async () => {
  if (!deployment.value.latitude || !deployment.value.longitude) {
    alert('Please provide location coordinates')
    return
  }

  deploying.value = true
  try {
    await drivesApi.deploy(drive.value.id, deployment.value)
    showDeployModal.value = false
    await loadDrive()
  } finally {
    deploying.value = false
  }
}

const tokenTypeLabels = {
  dns: 'DNS Token',
  word: 'Word Document',
  excel: 'Excel Spreadsheet',
  pdf: 'PDF Document',
  folder: 'Windows Folder',
  qr: 'QR Code'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}
</script>

<template>
  <div>
    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <div v-else-if="drive">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center space-x-4">
          <router-link to="/drives" class="text-surface-400 hover:text-surface-200">
            &larr; Back to Drives
          </router-link>
        </div>
        <div class="mt-4 flex justify-between items-start">
          <div>
            <h1 class="text-2xl font-bold text-surface-0 font-mono">{{ drive.unique_code }}</h1>
            <p v-if="drive.label" class="mt-1 text-surface-400">{{ drive.label }}</p>
          </div>
          <Tag :value="drive.status" :severity="driveStatusSeverity[drive.status]" class="text-sm" />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mb-6 flex gap-3">
        <Button v-if="drive.status === 'created'" label="Prepare Drive" icon="pi pi-cog"
          @click="prepareDrive" />
        <Button v-if="drive.status === 'prepared'" label="Download ZIP" icon="pi pi-download"
          severity="success" @click="downloadDrive" />
        <Button v-if="drive.status === 'prepared'" label="Record Deployment" icon="pi pi-map-marker"
          severity="info" @click="showDeployModal = true" />
      </div>

      <!-- Drive Info -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-6">
          <h2 class="text-lg font-medium text-surface-0 mb-4">Drive Information</h2>
          <dl class="space-y-3">
            <div class="flex justify-between">
              <dt class="text-surface-400">Unique Code</dt>
              <dd class="font-mono text-surface-200">{{ drive.unique_code }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-surface-400">Status</dt>
              <dd class="text-surface-200">{{ drive.status }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-surface-400">Created</dt>
              <dd class="text-surface-200">{{ formatDate(drive.created_at) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-surface-400">Prepared</dt>
              <dd class="text-surface-200">{{ formatDate(drive.prepared_at) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-surface-400">Deployed</dt>
              <dd class="text-surface-200">{{ formatDate(drive.deployed_at) }}</dd>
            </div>
          </dl>
        </div>

        <div class="bg-surface-900 border border-surface-700 rounded-lg p-6">
          <h2 class="text-lg font-medium text-surface-0 mb-4">Deployment Details</h2>
          <div v-if="drive.deployment">
            <dl class="space-y-3">
              <div class="flex justify-between">
                <dt class="text-surface-400">Location</dt>
                <dd class="text-surface-200">{{ drive.deployment.location_description || 'Not specified' }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-surface-400">Coordinates</dt>
                <dd class="font-mono text-sm text-surface-200">
                  {{ drive.deployment.latitude?.toFixed(6) }}, {{ drive.deployment.longitude?.toFixed(6) }}
                </dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-surface-400">Deployed By</dt>
                <dd class="text-surface-200">{{ drive.deployment.deployed_by || '-' }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-surface-400">Deployed At</dt>
                <dd class="text-surface-200">{{ formatDate(drive.deployment.deployed_at) }}</dd>
              </div>
            </dl>
          </div>
          <div v-else class="text-surface-400">
            Not yet deployed
          </div>
        </div>
      </div>

      <!-- Tokens -->
      <div class="bg-surface-900 border border-surface-700 rounded-lg">
        <div class="px-6 py-4 border-b border-surface-700">
          <h2 class="text-lg font-medium text-surface-0">Tokens ({{ tokens.length }})</h2>
        </div>
        <div class="divide-y divide-surface-700">
          <div v-for="token in tokens" :key="token.id" class="px-6 py-4">
            <div class="flex justify-between items-start">
              <div>
                <div class="flex items-center space-x-2">
                  <Tag :value="tokenTypeLabels[token.token_type] || token.token_type" severity="info" />
                  <span class="font-medium text-surface-0">{{ token.filename || 'DNS Token' }}</span>
                </div>
                <div class="mt-1 text-sm text-surface-400">
                  {{ token.memo || 'No description' }}
                </div>
              </div>
              <div class="text-right">
                <div class="text-sm text-surface-400">
                  {{ token.trigger_count || 0 }} triggers
                </div>
              </div>
            </div>
          </div>
          <div v-if="tokens.length === 0" class="px-6 py-8 text-center text-surface-400">
            No tokens created yet. Prepare the drive to generate tokens.
          </div>
        </div>
      </div>
    </div>

    <!-- Deploy Dialog -->
    <Dialog v-model:visible="showDeployModal" header="Record Deployment" modal :style="{ width: '28rem' }">
      <form @submit.prevent="deployDrive" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Location</label>
          <div class="flex gap-2">
            <InputNumber v-model="deployment.latitude" placeholder="Latitude" :minFractionDigits="1" :maxFractionDigits="6"
              mode="decimal" class="flex-1" />
            <InputNumber v-model="deployment.longitude" placeholder="Longitude" :minFractionDigits="1" :maxFractionDigits="6"
              mode="decimal" class="flex-1" />
          </div>
          <Button
            type="button"
            :label="gettingLocation ? 'Getting location...' : 'Use current location'"
            text size="small"
            :loading="gettingLocation"
            @click="getCurrentLocation"
            class="mt-2"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Description</label>
          <InputText v-model="deployment.location_description"
            placeholder="e.g., Building A lobby, near elevators" class="w-full" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Deployed By</label>
          <InputText v-model="deployment.deployed_by" placeholder="Your name" class="w-full" />
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <Button label="Cancel" severity="secondary" text @click="showDeployModal = false" />
          <Button type="submit" :label="deploying ? 'Recording...' : 'Record Deployment'" :loading="deploying" />
        </div>
      </form>
    </Dialog>
  </div>
</template>
