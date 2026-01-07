<script setup>
import { ref, onMounted } from 'vue'
import { campaignsApi, targetsApi } from '@/services/api'

const campaigns = ref([])
const targets = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const showDeleteModal = ref(false)
const deleteStep = ref(1)
const deletePreview = ref(null)
const deletingCampaign = ref(null)
const deleting = ref(false)
const newCampaign = ref({
  name: '',
  client_name: '',
  description: '',
  target_id: '',
  landing_page_config: {
    mode: 'disabled',
    included_theme: 'corporate',
    custom_url: ''
  }
})

// Available landing page themes
const LANDING_PAGE_THEMES = [
  { id: 'corporate', name: 'Corporate Portal', description: 'Professional secure document portal' },
  { id: 'login', name: 'Login Page', description: 'Corporate login form (Gmail-style)' },
  { id: 'maintenance', name: 'Maintenance', description: 'System maintenance notice' },
  { id: 'helpdesk', name: 'IT Helpdesk', description: 'IT support portal with ticket system' },
  { id: 'hrportal', name: 'HR Portal', description: 'HR/Payroll portal' },
  { id: 'fileshare', name: 'File Share', description: 'File sharing/download interface' },
  { id: 'training', name: 'Training Portal', description: 'Learning management system' },
  { id: 'banking', name: 'Banking Portal', description: 'Banking verification page' },
  { id: 'document', name: 'Document Viewer', description: 'Document viewer page' },
  { id: 'survey', name: 'Survey', description: 'Survey/feedback form' },
  { id: 'onlyfans', name: 'Premium Content', description: 'Premium/exclusive content access' },
]

// Preview URL base - rickroll server
const PREVIEW_BASE_URL = 'https://rick.subproject55.com/preview'

const openPreview = (theme) => {
  window.open(`${PREVIEW_BASE_URL}/${theme}`, '_blank')
}

onMounted(async () => {
  await Promise.all([loadCampaigns(), loadTargets()])
})

const loadCampaigns = async () => {
  loading.value = true
  try {
    const response = await campaignsApi.list()
    campaigns.value = response.data
  } finally {
    loading.value = false
  }
}

const loadTargets = async () => {
  try {
    const response = await targetsApi.list()
    targets.value = response.data
  } catch (e) {
    console.error('Failed to load targets', e)
  }
}

const createCampaign = async () => {
  const data = { ...newCampaign.value }
  if (!data.target_id) delete data.target_id
  await campaignsApi.create(data)
  showCreateModal.value = false
  newCampaign.value = {
    name: '',
    client_name: '',
    description: '',
    target_id: '',
    landing_page_config: {
      mode: 'disabled',
      included_theme: 'corporate',
      custom_url: ''
    }
  }
  await loadCampaigns()
}

const openDeleteModal = async (campaign) => {
  deletingCampaign.value = campaign
  deleteStep.value = 1
  deletePreview.value = null
  showDeleteModal.value = true

  try {
    const response = await campaignsApi.deletePreview(campaign.id)
    deletePreview.value = response.data
  } catch (e) {
    console.error('Failed to load delete preview', e)
  }
}

const proceedToConfirm = () => {
  deleteStep.value = 2
}

const confirmDelete = async () => {
  deleting.value = true
  try {
    await campaignsApi.delete(deletingCampaign.value.id, true)
    showDeleteModal.value = false
    deletingCampaign.value = null
    deletePreview.value = null
    await loadCampaigns()
  } catch (e) {
    alert('Failed to delete campaign: ' + (e.response?.data?.detail || e.message))
  } finally {
    deleting.value = false
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
  deletingCampaign.value = null
  deletePreview.value = null
  deleteStep.value = 1
}

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800',
  completed: 'bg-blue-100 text-blue-800',
  archived: 'bg-yellow-100 text-yellow-800',
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        Campaigns
      </h1>
      <button
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        @click="showCreateModal = true"
      >
        New Campaign
      </button>
    </div>

    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Name
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Target
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Drives
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Triggers
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="campaign in campaigns"
            :key="campaign.id"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4">
              <router-link
                :to="`/campaigns/${campaign.id}`"
                class="text-primary-600 hover:underline"
              >
                {{ campaign.name }}
              </router-link>
              <div
                v-if="campaign.client_name"
                class="text-xs text-gray-500"
              >
                {{ campaign.client_name }}
              </div>
            </td>
            <td class="px-6 py-4">
              <router-link
                v-if="campaign.target"
                :to="`/targets/${campaign.target.id}`"
                class="text-primary-600 hover:underline text-sm"
              >
                {{ campaign.target.company_name }}
              </router-link>
              <span
                v-else
                class="text-gray-400 text-sm"
              >No target</span>
            </td>
            <td class="px-6 py-4">
              <span :class="[statusColors[campaign.status], 'px-2 py-1 text-xs rounded-full']">
                {{ campaign.status }}
              </span>
            </td>
            <td class="px-6 py-4 text-gray-500">
              {{ campaign.drive_count }}
            </td>
            <td class="px-6 py-4 text-gray-500">
              {{ campaign.triggered_count }}
            </td>
            <td class="px-6 py-4 space-x-2">
              <router-link
                :to="`/campaigns/${campaign.id}`"
                class="text-primary-600 hover:underline text-sm"
              >
                View
              </router-link>
              <button
                class="text-red-600 hover:underline text-sm"
                @click="openDeleteModal(campaign)"
              >
                Delete
              </button>
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
          Create Campaign
        </h2>
        <form
          class="space-y-4"
          @submit.prevent="createCampaign"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700">Name</label>
            <input
              v-model="newCampaign.name"
              type="text"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Target Organization</label>
            <select
              v-model="newCampaign.target_id"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">
                No target selected
              </option>
              <option
                v-for="target in targets"
                :key="target.id"
                :value="target.id"
              >
                {{ target.company_name }} ({{ target.industry }})
              </option>
            </select>
            <p class="mt-1 text-xs text-gray-500">
              Link to a target for AI-powered recommendations
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Client Name</label>
            <input
              v-model="newCampaign.client_name"
              type="text"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              v-model="newCampaign.description"
              rows="3"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <!-- Landing Page Settings -->
          <div class="border-t pt-4 mt-4">
            <h3 class="text-sm font-medium text-gray-900 mb-3">
              Landing Page Settings
            </h3>
            <p class="text-xs text-gray-500 mb-3">
              Configure the landing page shown when canary tokens are triggered.
            </p>

            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700">Mode</label>
                <select
                  v-model="newCampaign.landing_page_config.mode"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="disabled">
                    Disabled (use profile settings)
                  </option>
                  <option value="included">
                    Use Included Theme
                  </option>
                  <option value="custom_url">
                    Custom URL
                  </option>
                </select>
              </div>

              <div v-if="newCampaign.landing_page_config.mode === 'included'">
                <label class="block text-sm font-medium text-gray-700">Theme</label>
                <div class="mt-1 flex space-x-2">
                  <select
                    v-model="newCampaign.landing_page_config.included_theme"
                    class="block w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option
                      v-for="theme in LANDING_PAGE_THEMES"
                      :key="theme.id"
                      :value="theme.id"
                    >
                      {{ theme.name }} - {{ theme.description }}
                    </option>
                  </select>
                  <button
                    type="button"
                    class="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-md whitespace-nowrap"
                    @click="openPreview(newCampaign.landing_page_config.included_theme)"
                  >
                    Preview
                  </button>
                </div>
              </div>

              <div v-if="newCampaign.landing_page_config.mode === 'custom_url'">
                <label class="block text-sm font-medium text-gray-700">Custom URL</label>
                <input
                  v-model="newCampaign.landing_page_config.custom_url"
                  type="url"
                  placeholder="https://example.com/landing"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                >
              </div>
            </div>
          </div>

          <div class="flex justify-end space-x-3">
            <button
              type="button"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="showCreateModal = false"
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

    <!-- Delete Modal - Two Steps -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-lg">
        <!-- Step 1: Preview -->
        <div v-if="deleteStep === 1">
          <h2 class="text-lg font-medium mb-4 text-red-600">
            Delete Campaign
          </h2>

          <div
            v-if="!deletePreview"
            class="text-center py-4 text-gray-500"
          >
            Loading preview...
          </div>

          <div v-else>
            <p class="text-gray-700 mb-4">
              You are about to delete <strong>{{ deletePreview.campaign_name }}</strong>.
              This will permanently remove:
            </p>

            <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <ul class="space-y-2 text-sm">
                <li class="flex justify-between">
                  <span>USB Drives:</span>
                  <span class="font-medium">{{ deletePreview.drive_count }}</span>
                </li>
                <li class="flex justify-between">
                  <span>Deployed Drives:</span>
                  <span class="font-medium">{{ deletePreview.deployed_count }}</span>
                </li>
                <li class="flex justify-between">
                  <span>Triggered Drives:</span>
                  <span class="font-medium">{{ deletePreview.triggered_count }}</span>
                </li>
                <li class="flex justify-between">
                  <span>Canary Tokens:</span>
                  <span class="font-medium">{{ deletePreview.token_count }}</span>
                </li>
              </ul>
            </div>

            <div
              v-if="deletePreview.drives.length > 0"
              class="mb-4"
            >
              <p class="text-sm font-medium text-gray-700 mb-2">
                Drives to be deleted:
              </p>
              <div class="max-h-32 overflow-y-auto bg-gray-50 rounded p-2 text-xs font-mono">
                <div
                  v-for="drive in deletePreview.drives"
                  :key="drive.id"
                  class="py-1"
                >
                  {{ drive.unique_code }} - {{ drive.status }}
                  <span v-if="drive.label">({{ drive.label }})</span>
                </div>
              </div>
            </div>

            <div
              v-if="deletePreview.triggered_count > 0"
              class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4"
            >
              <p class="text-yellow-800 text-sm">
                <strong>Warning:</strong> This campaign has {{ deletePreview.triggered_count }} triggered drive(s).
                Deleting will remove all trigger history and forensic data.
              </p>
            </div>
          </div>

          <div class="flex justify-end space-x-3">
            <button
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="cancelDelete"
            >
              Cancel
            </button>
            <button
              :disabled="!deletePreview"
              class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              @click="proceedToConfirm"
            >
              Continue
            </button>
          </div>
        </div>

        <!-- Step 2: Confirm -->
        <div v-if="deleteStep === 2">
          <h2 class="text-lg font-medium mb-4 text-red-600">
            Confirm Deletion
          </h2>

          <div class="bg-red-100 border border-red-300 rounded-lg p-4 mb-4">
            <p class="text-red-800 font-medium">
              This action cannot be undone!
            </p>
            <p class="text-red-700 text-sm mt-2">
              You are permanently deleting "{{ deletePreview?.campaign_name }}"
              along with {{ deletePreview?.drive_count }} drive(s) and {{ deletePreview?.token_count }} token(s).
            </p>
          </div>

          <p class="text-gray-700 mb-4">
            Click "Delete Forever" to permanently remove this campaign and all associated data.
          </p>

          <div class="flex justify-end space-x-3">
            <button
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="deleteStep = 1"
            >
              Back
            </button>
            <button
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="cancelDelete"
            >
              Cancel
            </button>
            <button
              :disabled="deleting"
              class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              @click="confirmDelete"
            >
              {{ deleting ? 'Deleting...' : 'Delete Forever' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
