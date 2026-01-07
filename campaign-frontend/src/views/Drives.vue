<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { drivesApi, campaignsApi, profilesApi, settingsApi } from '@/services/api'

const router = useRouter()
const drives = ref([])
const campaigns = ref([])
const profiles = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const showDeleteModal = ref(false)
const driveToDelete = ref(null)
const preparingId = ref(null)
const deletingId = ref(null)
const errorMessage = ref('')

// URL shortener config
const domains = ref([])
const showUrlConfig = ref(false)
const loadingProfile = ref(false)

const filters = ref({
  campaign_id: '',
  status: ''
})

const newDrive = ref({
  campaign_id: '',
  profile_id: '',
  label: '',
  url_config: {
    enabled: false,
    domain: '',
    base_slug: '',
    suffix_mode: 'random',
    suffix_length: 4
  }
})

const suffixModes = [
  { value: 'random', label: 'Random' },
  { value: 'drive_code', label: 'Drive Code' },
  { value: 'sequential', label: 'Sequential' },
  { value: 'custom', label: 'Custom' }
]

// Watch for profile changes to pre-fill URL config
watch(() => newDrive.value.profile_id, async (profileId) => {
  if (profileId) {
    loadingProfile.value = true
    try {
      const response = await profilesApi.get(profileId)
      const profileUrlConfig = response.data.url_config || {}
      // Pre-fill from profile defaults
      newDrive.value.url_config = {
        enabled: profileUrlConfig.enabled || false,
        domain: profileUrlConfig.domain || (domains.value[0]?.domain || ''),
        base_slug: profileUrlConfig.base_slug || '',
        suffix_mode: profileUrlConfig.suffix_mode || 'random',
        suffix_length: profileUrlConfig.suffix_length || 4
      }
      // Auto-expand URL config section if profile has it enabled
      if (profileUrlConfig.enabled) {
        showUrlConfig.value = true
      }
    } catch (err) {
      console.error('Failed to load profile:', err)
    } finally {
      loadingProfile.value = false
    }
  }
})

const statusColors = {
  created: 'bg-gray-100 text-gray-800',
  prepared: 'bg-blue-100 text-blue-800',
  deployed: 'bg-green-100 text-green-800',
  triggered: 'bg-red-100 text-red-800',
  recovered: 'bg-yellow-100 text-yellow-800'
}

// Organize profiles by category (system profiles only in standard categories)
const profileCategories = computed(() => {
  const corporate = ['it_department', 'hr_documents', 'finance', 'executive', 'network_admin']
  const personal = ['personal_backup', 'training_compliance', 'social_creator', 'project_client']
  const technical = ['developer', 'security_audit', 'contractor']
  const allStandard = [...corporate, ...personal, ...technical]

  // Only show system profiles in standard categories
  const systemProfiles = profiles.value.filter(p => p.is_system === 'true')

  return {
    corporate: systemProfiles.filter(p => corporate.includes(p.scenario_type)),
    personal: systemProfiles.filter(p => personal.includes(p.scenario_type)),
    technical: systemProfiles.filter(p => technical.includes(p.scenario_type)),
    // Custom = non-system profiles OR system profiles with non-standard scenario_type
    custom: profiles.value.filter(p =>
      p.is_system !== 'true' || !allStandard.includes(p.scenario_type)
    )
  }
})

onMounted(async () => {
  await Promise.all([
    loadDrives(),
    loadCampaigns(),
    loadProfiles(),
    loadDomains()
  ])
})

const loadDomains = async () => {
  try {
    const response = await settingsApi.listDomains()
    domains.value = response.data.domains || []
  } catch (err) {
    console.error('Failed to load domains:', err)
    domains.value = []
  }
}

const loadDrives = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.campaign_id) params.campaign_id = filters.value.campaign_id
    if (filters.value.status) params.status = filters.value.status

    const response = await drivesApi.list(params)
    drives.value = response.data
  } finally {
    loading.value = false
  }
}

const loadCampaigns = async () => {
  const response = await campaignsApi.list()
  campaigns.value = response.data
}

const loadProfiles = async () => {
  // Only load active profiles for drive creation
  const response = await profilesApi.listActive()
  profiles.value = response.data
}

const createDrive = async () => {
  const driveData = {
    campaign_id: newDrive.value.campaign_id,
    profile_id: newDrive.value.profile_id,
    label: newDrive.value.label
  }
  // Only include url_config if enabled
  if (newDrive.value.url_config.enabled) {
    driveData.url_config = newDrive.value.url_config
  }
  await drivesApi.create(driveData)
  showCreateModal.value = false
  resetForm()
  await loadDrives()
}

const prepareDrive = async (id) => {
  preparingId.value = id
  errorMessage.value = ''
  try {
    await drivesApi.prepare(id)
    await loadDrives()
  } catch (error) {
    const detail = error.response?.data?.detail || 'Failed to prepare drive'
    errorMessage.value = detail
  } finally {
    preparingId.value = null
  }
}

const downloadDrive = async (id) => {
  const response = await drivesApi.download(id)
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `drive-${id}.zip`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const confirmDelete = (drive) => {
  driveToDelete.value = drive
  showDeleteModal.value = true
}

const deleteDrive = async () => {
  if (!driveToDelete.value) return

  deletingId.value = driveToDelete.value.id
  errorMessage.value = ''
  try {
    await drivesApi.delete(driveToDelete.value.id)
    showDeleteModal.value = false
    driveToDelete.value = null
    await loadDrives()
  } catch (error) {
    const detail = error.response?.data?.detail || 'Failed to delete drive'
    errorMessage.value = detail
  } finally {
    deletingId.value = null
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
  driveToDelete.value = null
}

const resetForm = () => {
  newDrive.value = {
    campaign_id: '',
    profile_id: '',
    label: '',
    url_config: {
      enabled: false,
      domain: '',
      base_slug: '',
      suffix_mode: 'random',
      suffix_length: 4
    }
  }
  showUrlConfig.value = false
}

const applyFilters = () => {
  loadDrives()
}

const clearFilters = () => {
  filters.value = { campaign_id: '', status: '' }
  loadDrives()
}

const getCampaignName = (id) => {
  const campaign = campaigns.value.find(c => c.id === id)
  return campaign?.name || '-'
}

const getProfileName = (id) => {
  const profile = profiles.value.find(p => p.id === id)
  return profile?.name || '-'
}

const filteredDrives = computed(() => {
  return drives.value
})
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        USB Drives
      </h1>
      <button
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        @click="showCreateModal = true"
      >
        New Drive
      </button>
    </div>

    <!-- Error Message -->
    <div
      v-if="errorMessage"
      class="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center"
    >
      <span>{{ errorMessage }}</span>
      <button
        class="text-red-500 hover:text-red-700"
        @click="errorMessage = ''"
      >
        &times;
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white shadow rounded-lg p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Campaign</label>
          <select
            v-model="filters.campaign_id"
            class="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">
              All Campaigns
            </option>
            <option
              v-for="c in campaigns"
              :key="c.id"
              :value="c.id"
            >
              {{ c.name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            v-model="filters.status"
            class="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">
              All Statuses
            </option>
            <option value="created">
              Created
            </option>
            <option value="prepared">
              Prepared
            </option>
            <option value="deployed">
              Deployed
            </option>
            <option value="triggered">
              Triggered
            </option>
            <option value="recovered">
              Recovered
            </option>
          </select>
        </div>

        <button
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          @click="applyFilters"
        >
          Filter
        </button>
        <button
          class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
          @click="clearFilters"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Drives Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Code
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Label
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Campaign
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Profile
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Tokens
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="drive in filteredDrives"
            :key="drive.id"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4">
              <router-link
                :to="`/drives/${drive.id}`"
                class="text-primary-600 hover:underline font-mono"
              >
                {{ drive.unique_code }}
              </router-link>
            </td>
            <td class="px-6 py-4 text-gray-700">
              {{ drive.label || '-' }}
            </td>
            <td class="px-6 py-4 text-gray-500">
              {{ getCampaignName(drive.campaign_id) }}
            </td>
            <td class="px-6 py-4 text-gray-500">
              {{ getProfileName(drive.profile_id) }}
            </td>
            <td class="px-6 py-4">
              <span :class="[statusColors[drive.status], 'px-2 py-1 text-xs rounded-full']">
                {{ drive.status }}
              </span>
            </td>
            <td class="px-6 py-4 text-gray-500">
              {{ drive.token_count || 0 }}
            </td>
            <td class="px-6 py-4">
              <div class="flex space-x-3">
                <button
                  v-if="drive.status === 'created'"
                  :disabled="preparingId === drive.id"
                  class="text-sm text-primary-600 hover:text-primary-700 disabled:opacity-50"
                  @click="prepareDrive(drive.id)"
                >
                  {{ preparingId === drive.id ? 'Preparing...' : 'Prepare' }}
                </button>
                <button
                  v-if="drive.status === 'prepared'"
                  class="text-sm text-green-600 hover:text-green-700"
                  @click="downloadDrive(drive.id)"
                >
                  Download
                </button>
                <router-link
                  v-if="drive.status === 'prepared'"
                  :to="`/drives/${drive.id}?action=deploy`"
                  class="text-sm text-blue-600 hover:text-blue-700"
                >
                  Deploy
                </router-link>
                <router-link
                  :to="`/drives/${drive.id}`"
                  class="text-sm text-gray-600 hover:text-gray-700"
                >
                  View
                </router-link>
                <button
                  class="text-sm text-red-600 hover:text-red-700"
                  @click="confirmDelete(drive)"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="drives.length === 0">
            <td
              colspan="7"
              class="px-6 py-8 text-center text-gray-500"
            >
              No drives found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">
          Create Drive
        </h2>
        <form
          class="space-y-4"
          @submit.prevent="createDrive"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700">Campaign</label>
            <select
              v-model="newDrive.campaign_id"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option
                value=""
                disabled
              >
                Select a campaign
              </option>
              <option
                v-for="c in campaigns"
                :key="c.id"
                :value="c.id"
              >
                {{ c.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Profile</label>
            <select
              v-model="newDrive.profile_id"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option
                value=""
                disabled
              >
                Select a profile
              </option>
              <optgroup
                v-if="profileCategories.corporate.length"
                label="Corporate"
              >
                <option
                  v-for="p in profileCategories.corporate"
                  :key="p.id"
                  :value="p.id"
                >
                  {{ p.name }}
                </option>
              </optgroup>
              <optgroup
                v-if="profileCategories.personal.length"
                label="Personal/Social"
              >
                <option
                  v-for="p in profileCategories.personal"
                  :key="p.id"
                  :value="p.id"
                >
                  {{ p.name }}
                </option>
              </optgroup>
              <optgroup
                v-if="profileCategories.technical.length"
                label="Technical"
              >
                <option
                  v-for="p in profileCategories.technical"
                  :key="p.id"
                  :value="p.id"
                >
                  {{ p.name }}
                </option>
              </optgroup>
              <optgroup
                v-if="profileCategories.custom.length"
                label="Custom"
              >
                <option
                  v-for="p in profileCategories.custom"
                  :key="p.id"
                  :value="p.id"
                >
                  {{ p.name }}
                </option>
              </optgroup>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Label (optional)</label>
            <input
              v-model="newDrive.label"
              type="text"
              placeholder="e.g., HR Payroll Q4"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
          </div>

          <!-- URL Shortener Settings -->
          <div class="border-t pt-4 mt-4">
            <button
              type="button"
              class="flex items-center justify-between w-full text-left text-sm font-medium text-gray-700 hover:text-gray-900"
              @click="showUrlConfig = !showUrlConfig"
            >
              <span class="flex items-center gap-2">
                <span>URL Shortener Settings</span>
                <span
                  v-if="newDrive.url_config.enabled"
                  class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded"
                >
                  Enabled
                </span>
              </span>
              <svg
                :class="['h-5 w-5 transition-transform', showUrlConfig ? 'rotate-180' : '']"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <div
              v-if="showUrlConfig"
              class="mt-4 space-y-4 bg-gray-50 p-4 rounded-lg"
            >
              <!-- Loading indicator -->
              <div
                v-if="loadingProfile"
                class="text-sm text-gray-500 italic"
              >
                Loading profile settings...
              </div>

              <!-- Enable checkbox -->
              <div class="flex items-center">
                <input
                  id="url-enabled"
                  v-model="newDrive.url_config.enabled"
                  type="checkbox"
                  class="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                >
                <label
                  for="url-enabled"
                  class="ml-2 text-sm text-gray-700"
                >
                  Enable short URLs for this drive
                </label>
              </div>

              <!-- Config fields (only show when enabled) -->
              <template v-if="newDrive.url_config.enabled">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Domain</label>
                  <select
                    v-model="newDrive.url_config.domain"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option
                      value=""
                      disabled
                    >
                      Select a domain
                    </option>
                    <option
                      v-for="d in domains"
                      :key="d.domain"
                      :value="d.domain"
                    >
                      {{ d.domain }}{{ d.is_default ? ' (default)' : '' }}
                    </option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700">Base Slug</label>
                  <input
                    v-model="newDrive.url_config.base_slug"
                    type="text"
                    placeholder="e.g., hr-docs"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                  <p class="mt-1 text-xs text-gray-500">
                    Short URLs will look like: {{ newDrive.url_config.domain || 'domain.com' }}/{{ newDrive.url_config.base_slug || 'slug' }}-xxxx
                  </p>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700">Suffix Mode</label>
                    <select
                      v-model="newDrive.url_config.suffix_mode"
                      class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option
                        v-for="mode in suffixModes"
                        :key="mode.value"
                        :value="mode.value"
                      >
                        {{ mode.label }}
                      </option>
                    </select>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700">Suffix Length</label>
                    <input
                      v-model.number="newDrive.url_config.suffix_length"
                      type="number"
                      min="2"
                      max="12"
                      class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                  </div>
                </div>
              </template>

              <p
                v-if="!newDrive.url_config.enabled"
                class="text-xs text-gray-500"
              >
                Enable to create short URLs for token tracking links when this drive is prepared.
              </p>
            </div>
          </div>

          <div class="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="showCreateModal = false; resetForm()"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            >
              Create
            </button>
          </div>
        </form>
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
          Are you sure you want to delete drive <strong class="font-mono">{{ driveToDelete?.unique_code }}</strong>?
        </p>
        <p class="text-sm text-gray-500 mb-4">
          This will permanently delete the drive and all associated tokens from both the database and CanaryTokens service.
        </p>
        <div class="flex justify-end space-x-3">
          <button
            :disabled="deletingId"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md disabled:opacity-50"
            @click="cancelDelete"
          >
            Cancel
          </button>
          <button
            :disabled="deletingId"
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
            @click="deleteDrive"
          >
            {{ deletingId ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
