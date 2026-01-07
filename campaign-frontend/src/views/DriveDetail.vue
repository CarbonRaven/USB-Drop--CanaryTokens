<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { drivesApi, profilesApi } from '@/services/api'

const route = useRoute()
const router = useRouter()

const drive = ref(null)
const tokens = ref([])
const deploymentInfo = ref(null)
const profiles = ref([])
const loading = ref(true)
const showDeployModal = ref(false)
const deploying = ref(false)
const gettingLocation = ref(false)
const isEditingDeployment = ref(false)
const selectedProfileId = ref('')
const savingProfile = ref(false)
const prepareError = ref('')
const preparing = ref(false)
const showDeleteModal = ref(false)
const deleting = ref(false)

// Photo upload state
const selectedPhoto = ref(null)
const photoPreview = ref(null)
const extractedMetadata = ref(null)
const uploadMethod = ref('photo') // 'photo' or 'manual'

const deployment = ref({
  latitude: null,
  longitude: null,
  location_name: '',
  location_description: '',
  location_type: '',
  deployed_by: '',
  deployment_notes: ''
})

const locationTypes = [
  { value: 'parking_lot', label: 'Parking Lot' },
  { value: 'lobby', label: 'Building Lobby' },
  { value: 'cafe', label: 'Cafe/Restaurant' },
  { value: 'office', label: 'Office Area' },
  { value: 'restroom', label: 'Restroom' },
  { value: 'elevator', label: 'Elevator Area' },
  { value: 'stairwell', label: 'Stairwell' },
  { value: 'reception', label: 'Reception' },
  { value: 'other', label: 'Other' }
]

const statusColors = {
  created: 'bg-gray-100 text-gray-800',
  prepared: 'bg-blue-100 text-blue-800',
  deployed: 'bg-green-100 text-green-800',
  triggered: 'bg-red-100 text-red-800',
  recovered: 'bg-yellow-100 text-yellow-800'
}

onMounted(async () => {
  await Promise.all([loadDrive(), loadProfiles()])
  if (route.query.action === 'deploy') {
    showDeployModal.value = true
  }
})

const loadProfiles = async () => {
  try {
    const response = await profilesApi.list()
    profiles.value = response.data
  } catch (error) {
    console.error('Failed to load profiles:', error)
  }
}

const loadDrive = async () => {
  loading.value = true
  try {
    const [driveRes, tokensRes] = await Promise.all([
      drivesApi.get(route.params.id),
      drivesApi.tokens(route.params.id)
    ])
    drive.value = driveRes.data
    tokens.value = tokensRes.data
    selectedProfileId.value = drive.value.profile_id || ''

    // Load deployment info if deployed or triggered
    if (['deployed', 'triggered', 'recovered'].includes(drive.value.status) || drive.value.deployed_at) {
      try {
        const deployRes = await drivesApi.deployment(route.params.id)
        deploymentInfo.value = deployRes.data
      } catch (e) {
        // Deployment info not available
      }
    }
  } catch (error) {
    console.error('Failed to load drive:', error)
    router.push('/drives')
  } finally {
    loading.value = false
  }
}

const prepareDrive = async () => {
  preparing.value = true
  prepareError.value = ''
  try {
    await drivesApi.prepare(drive.value.id)
    await loadDrive()
  } catch (error) {
    prepareError.value = error.response?.data?.detail || 'Failed to prepare drive'
  } finally {
    preparing.value = false
  }
}

const saveProfile = async () => {
  if (!selectedProfileId.value) return
  savingProfile.value = true
  prepareError.value = ''
  try {
    await drivesApi.update(drive.value.id, { profile_id: selectedProfileId.value })
    await loadDrive()
  } catch (error) {
    prepareError.value = error.response?.data?.detail || 'Failed to assign profile'
  } finally {
    savingProfile.value = false
  }
}

const getProfileName = (id) => {
  const profile = profiles.value.find(p => p.id === id)
  return profile?.name || '-'
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

const onPhotoSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    alert('Please select an image file')
    return
  }

  selectedPhoto.value = file

  // Create preview URL
  photoPreview.value = URL.createObjectURL(file)

  // Note: EXIF extraction happens server-side
  // We'll show the extracted data after upload
  extractedMetadata.value = null
}

const clearPhoto = () => {
  selectedPhoto.value = null
  if (photoPreview.value) {
    URL.revokeObjectURL(photoPreview.value)
    photoPreview.value = null
  }
  extractedMetadata.value = null
}

const openDeployModal = (editMode = false) => {
  isEditingDeployment.value = editMode

  if (editMode && deploymentInfo.value) {
    // Populate form with existing deployment data
    deployment.value = {
      latitude: deploymentInfo.value.latitude,
      longitude: deploymentInfo.value.longitude,
      location_name: deploymentInfo.value.location_name || '',
      location_description: deploymentInfo.value.location_description || '',
      location_type: deploymentInfo.value.location_type || '',
      deployed_by: deploymentInfo.value.deployed_by || '',
      deployment_notes: deploymentInfo.value.deployment_notes || ''
    }
    uploadMethod.value = 'manual' // Default to manual when editing
  } else {
    // Reset form for new deployment
    deployment.value = {
      latitude: null,
      longitude: null,
      location_name: '',
      location_description: '',
      location_type: '',
      deployed_by: '',
      deployment_notes: ''
    }
    uploadMethod.value = 'photo'
  }
  clearPhoto()
  showDeployModal.value = true
}

const closeDeployModal = () => {
  showDeployModal.value = false
  clearPhoto()
}

const deployDrive = async () => {
  if (uploadMethod.value === 'photo') {
    if (!selectedPhoto.value) {
      alert('Please select a deployment photo')
      return
    }
    await deployWithPhoto()
  } else {
    if (!deployment.value.latitude || !deployment.value.longitude) {
      alert('Please provide location coordinates')
      return
    }
    await deployManual()
  }
}

const deployWithPhoto = async () => {
  deploying.value = true
  try {
    const formData = new FormData()
    formData.append('photo', selectedPhoto.value)

    if (deployment.value.location_name) {
      formData.append('location_name', deployment.value.location_name)
    }
    if (deployment.value.location_description) {
      formData.append('location_description', deployment.value.location_description)
    }
    if (deployment.value.location_type) {
      formData.append('location_type', deployment.value.location_type)
    }
    if (deployment.value.deployed_by) {
      formData.append('deployed_by', deployment.value.deployed_by)
    }
    if (deployment.value.deployment_notes) {
      formData.append('deployment_notes', deployment.value.deployment_notes)
    }

    const response = await drivesApi.deployWithPhoto(drive.value.id, formData)
    extractedMetadata.value = response.data

    closeDeployModal()
    await loadDrive()
  } catch (error) {
    console.error('Deployment failed:', error)
    alert('Failed to record deployment: ' + (error.response?.data?.detail || error.message))
  } finally {
    deploying.value = false
  }
}

const deployManual = async () => {
  deploying.value = true
  try {
    if (isEditingDeployment.value) {
      // Update existing deployment
      await drivesApi.updateDeployment(drive.value.id, deployment.value)
    } else {
      // Create new deployment
      await drivesApi.deploy(drive.value.id, deployment.value)
    }
    closeDeployModal()
    await loadDrive()
  } catch (error) {
    console.error('Deployment failed:', error)
    alert('Failed to ' + (isEditingDeployment.value ? 'update' : 'record') + ' deployment')
  } finally {
    deploying.value = false
  }
}

const confirmDelete = () => {
  showDeleteModal.value = true
}

const deleteDrive = async () => {
  deleting.value = true
  try {
    await drivesApi.delete(drive.value.id)
    router.push('/drives')
  } catch (error) {
    console.error('Failed to delete drive:', error)
    prepareError.value = error.response?.data?.detail || 'Failed to delete drive'
    showDeleteModal.value = false
  } finally {
    deleting.value = false
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
}

const tokenTypeLabels = {
  dns: 'DNS Token',
  word: 'Word Document',
  ms_word: 'Word Document',
  excel: 'Excel Spreadsheet',
  ms_excel: 'Excel Spreadsheet',
  pdf: 'PDF Document',
  folder: 'Windows Folder',
  windows_dir: 'Windows Folder',
  qr: 'QR Code',
  qr_code: 'QR Code',
  text: 'Text File',
  web: 'Web Token',
  aws_keys: 'AWS Credentials',
  template_image: 'Photo'
}

// Get files from manifest for display
const manifestFiles = computed(() => {
  if (!drive.value?.files_manifest?.files) return []
  return drive.value.files_manifest.files
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

const formatCoordinate = (coord) => {
  if (coord === null || coord === undefined) return '-'
  return Number(coord).toFixed(6)
}
</script>

<template>
  <div>
    <div
      v-if="loading"
      class="text-center py-12"
    >
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
    </div>

    <div v-else-if="drive">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center space-x-4">
          <router-link
            to="/drives"
            class="text-gray-500 hover:text-gray-700"
          >
            &larr; Back to Drives
          </router-link>
        </div>
        <div class="mt-4 flex justify-between items-start">
          <div>
            <h1 class="text-2xl font-bold text-gray-900 font-mono">
              {{ drive.unique_code }}
            </h1>
            <p
              v-if="drive.label"
              class="mt-1 text-gray-500"
            >
              {{ drive.label }}
            </p>
          </div>
          <span :class="[statusColors[drive.status], 'px-3 py-1 text-sm rounded-full']">
            {{ drive.status }}
          </span>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="prepareError"
        class="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center"
      >
        <span>{{ prepareError }}</span>
        <button
          class="text-red-500 hover:text-red-700"
          @click="prepareError = ''"
        >
          &times;
        </button>
      </div>

      <!-- Profile Assignment (for drives without profile) -->
      <div
        v-if="drive.status === 'created' && !drive.profile_id"
        class="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4"
      >
        <h3 class="text-sm font-medium text-yellow-800 mb-2">
          Profile Required
        </h3>
        <p class="text-sm text-yellow-700 mb-3">
          Assign a profile to this drive before preparing it.
        </p>
        <div class="flex items-center space-x-3">
          <select
            v-model="selectedProfileId"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
          >
            <option
              value=""
              disabled
            >
              Select a profile...
            </option>
            <option
              v-for="p in profiles"
              :key="p.id"
              :value="p.id"
            >
              {{ p.name }}
            </option>
          </select>
          <button
            :disabled="!selectedProfileId || savingProfile"
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            @click="saveProfile"
          >
            {{ savingProfile ? 'Saving...' : 'Assign Profile' }}
          </button>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mb-6 flex space-x-4">
        <button
          v-if="drive.status === 'created' && drive.profile_id"
          :disabled="preparing"
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
          @click="prepareDrive"
        >
          {{ preparing ? 'Preparing...' : 'Prepare Drive' }}
        </button>
        <button
          v-if="drive.status === 'prepared'"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          @click="downloadDrive"
        >
          Download ZIP
        </button>
        <button
          v-if="drive.status === 'prepared'"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          @click="openDeployModal(false)"
        >
          Record Deployment
        </button>
        <button
          v-if="['deployed', 'triggered', 'recovered'].includes(drive.status)"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          @click="openDeployModal(true)"
        >
          Edit Deployment
        </button>
        <button
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          @click="confirmDelete"
        >
          Delete Drive
        </button>
      </div>

      <!-- Drive Info -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium mb-4">
            Drive Information
          </h2>
          <dl class="space-y-3">
            <div class="flex justify-between">
              <dt class="text-gray-500">
                Unique Code
              </dt>
              <dd class="font-mono">
                {{ drive.unique_code }}
              </dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">
                Status
              </dt>
              <dd>{{ drive.status }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">
                Profile
              </dt>
              <dd>{{ drive.profile_id ? getProfileName(drive.profile_id) : 'Not assigned' }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">
                Created
              </dt>
              <dd>{{ formatDate(drive.created_at) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">
                Prepared
              </dt>
              <dd>{{ formatDate(drive.prepared_at) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">
                Deployed
              </dt>
              <dd>{{ formatDate(drive.deployed_at) }}</dd>
            </div>
          </dl>
        </div>

        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium mb-4">
            Deployment Details
          </h2>
          <div v-if="deploymentInfo">
            <dl class="space-y-3">
              <div class="flex justify-between">
                <dt class="text-gray-500">
                  Location
                </dt>
                <dd>{{ deploymentInfo.location_name || deploymentInfo.location_description || 'Not specified' }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">
                  Type
                </dt>
                <dd>{{ deploymentInfo.location_type || '-' }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">
                  Coordinates
                </dt>
                <dd class="font-mono text-sm">
                  {{ formatCoordinate(deploymentInfo.latitude) }}, {{ formatCoordinate(deploymentInfo.longitude) }}
                </dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">
                  Deployed By
                </dt>
                <dd>{{ deploymentInfo.deployed_by || '-' }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">
                  Deployed At
                </dt>
                <dd>{{ formatDate(deploymentInfo.deployed_at) }}</dd>
              </div>
              <div
                v-if="deploymentInfo.photo_taken_at"
                class="flex justify-between"
              >
                <dt class="text-gray-500">
                  Photo Taken
                </dt>
                <dd>{{ formatDate(deploymentInfo.photo_taken_at) }}</dd>
              </div>
            </dl>

            <!-- Deployment Photo -->
            <div
              v-if="deploymentInfo.photo_url"
              class="mt-4"
            >
              <p class="text-sm text-gray-500 mb-2">
                Deployment Photo
              </p>
              <img
                :src="deploymentInfo.photo_url"
                alt="Deployment photo"
                class="w-full rounded-lg shadow-sm max-h-64 object-cover cursor-pointer"
                @click="window.open(deploymentInfo.photo_url, '_blank')"
              >
            </div>
          </div>
          <div
            v-else
            class="text-gray-500"
          >
            Not yet deployed
          </div>
        </div>
      </div>

      <!-- Files -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b">
          <h2 class="text-lg font-medium">
            Files ({{ manifestFiles.length }})
          </h2>
        </div>
        <div class="divide-y">
          <div
            v-for="(file, index) in manifestFiles"
            :key="index"
            class="px-6 py-4"
          >
            <div class="flex justify-between items-start">
              <div>
                <div class="flex items-center space-x-2">
                  <span
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      file.token_type === 'template_image' ? 'bg-green-100 text-green-800' : 'bg-primary-100 text-primary-800'
                    ]"
                  >
                    {{ tokenTypeLabels[file.token_type] || file.token_type }}
                  </span>
                  <span class="font-medium">{{ file.path }}</span>
                </div>
                <div class="mt-1 text-sm text-gray-500">
                  <span v-if="file.size_bytes">{{ (file.size_bytes / 1024).toFixed(1) }} KB</span>
                  <span
                    v-if="file.token_type === 'template_image'"
                    class="text-green-600"
                  >AI-generated image</span>
                </div>
              </div>
              <div class="text-right">
                <div
                  v-if="file.token_id"
                  class="text-xs text-gray-400 font-mono"
                >
                  {{ file.token_id.substring(0, 8) }}...
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="manifestFiles.length === 0"
            class="px-6 py-8 text-center text-gray-500"
          >
            No files created yet. Prepare the drive to generate files.
          </div>
        </div>
      </div>
    </div>

    <!-- Deploy Modal -->
    <div
      v-if="showDeployModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <h2 class="text-lg font-medium mb-4">
            {{ isEditingDeployment ? 'Edit Deployment' : 'Record Deployment' }}
          </h2>

          <!-- Method Toggle -->
          <div class="mb-6">
            <div class="flex rounded-lg bg-gray-100 p-1">
              <button
                :class="[
                  'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors',
                  uploadMethod === 'photo'
                    ? 'bg-white text-primary-700 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                ]"
                @click="uploadMethod = 'photo'"
              >
                Upload Photo
              </button>
              <button
                :class="[
                  'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors',
                  uploadMethod === 'manual'
                    ? 'bg-white text-primary-700 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                ]"
                @click="uploadMethod = 'manual'"
              >
                Enter Manually
              </button>
            </div>
          </div>

          <form
            class="space-y-4"
            @submit.prevent="deployDrive"
          >
            <!-- Photo Upload Section -->
            <div v-if="uploadMethod === 'photo'">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Deployment Photo
                <span class="text-gray-400 font-normal">(GPS coordinates extracted automatically)</span>
              </label>

              <div
                v-if="!photoPreview"
                class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center"
              >
                <input
                  id="photo-upload"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="onPhotoSelect"
                >
                <label
                  for="photo-upload"
                  class="cursor-pointer"
                >
                  <svg
                    class="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  <p class="mt-2 text-sm text-gray-600">
                    <span class="text-primary-600 hover:text-primary-700 font-medium">Click to upload</span>
                    or drag and drop
                  </p>
                  <p class="mt-1 text-xs text-gray-500">
                    Photo with GPS metadata for automatic location extraction
                  </p>
                </label>
              </div>

              <div
                v-else
                class="relative"
              >
                <img
                  :src="photoPreview"
                  alt="Preview"
                  class="w-full h-48 object-cover rounded-lg"
                >
                <button
                  type="button"
                  class="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                  @click="clearPhoto"
                >
                  <svg
                    class="w-5 h-5"
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
                <p class="mt-2 text-sm text-gray-500">
                  {{ selectedPhoto?.name }}
                </p>
              </div>

              <p class="mt-2 text-xs text-gray-500">
                GPS coordinates and timestamp will be extracted from the photo's EXIF data.
                Make sure your phone's location services were enabled when taking the photo.
              </p>
            </div>

            <!-- Manual Location Entry -->
            <div v-if="uploadMethod === 'manual'">
              <label class="block text-sm font-medium text-gray-700">GPS Coordinates</label>
              <div class="mt-1 flex space-x-2">
                <input
                  v-model.number="deployment.latitude"
                  type="number"
                  step="any"
                  placeholder="Latitude"
                  required
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                >
                <input
                  v-model.number="deployment.longitude"
                  type="number"
                  step="any"
                  placeholder="Longitude"
                  required
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                >
              </div>
              <button
                type="button"
                :disabled="gettingLocation"
                class="mt-2 text-sm text-primary-600 hover:text-primary-700"
                @click="getCurrentLocation"
              >
                {{ gettingLocation ? 'Getting location...' : 'Use current location' }}
              </button>
            </div>

            <!-- Common Fields -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Location Name</label>
              <input
                v-model="deployment.location_name"
                type="text"
                placeholder="e.g., Building A, Office Park"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Location Type</label>
              <select
                v-model="deployment.location_type"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">
                  Select type...
                </option>
                <option
                  v-for="type in locationTypes"
                  :key="type.value"
                  :value="type.value"
                >
                  {{ type.label }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <input
                v-model="deployment.location_description"
                type="text"
                placeholder="e.g., Near elevators, left side of lobby"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Deployed By</label>
              <input
                v-model="deployment.deployed_by"
                type="text"
                placeholder="Your name"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Notes</label>
              <textarea
                v-model="deployment.deployment_notes"
                placeholder="Any additional notes about the deployment..."
                rows="2"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div class="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
                @click="closeDeployModal"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="deploying"
                class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
              >
                {{ deploying ? (isEditingDeployment ? 'Saving...' : 'Recording...') : (isEditingDeployment ? 'Save Changes' : 'Record Deployment') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-2 text-red-600">
          Delete Drive
        </h2>
        <p class="text-gray-600 mb-4">
          Are you sure you want to delete drive <strong class="font-mono">{{ drive?.unique_code }}</strong>?
        </p>
        <p class="text-sm text-gray-500 mb-4">
          This will permanently delete the drive and all associated tokens from both the database and CanaryTokens service.
        </p>
        <div class="flex justify-end space-x-3">
          <button
            :disabled="deleting"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md disabled:opacity-50"
            @click="cancelDelete"
          >
            Cancel
          </button>
          <button
            :disabled="deleting"
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
            @click="deleteDrive"
          >
            {{ deleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
