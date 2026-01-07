<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { targetsApi } from '@/services/api'

const route = useRoute()
const router = useRouter()
const target = ref(null)
const options = ref({ industries: [], company_sizes: [], departments: [], regions: [] })
const loading = ref(true)
const saving = ref(false)
const analyzing = ref(false)
const recommendation = ref(null)
const editMode = ref(false)
const showDeleteModal = ref(false)

const editTarget = ref({})

onMounted(async () => {
  await Promise.all([loadTarget(), loadOptions()])
})

const loadTarget = async () => {
  loading.value = true
  try {
    const response = await targetsApi.get(route.params.id)
    target.value = response.data
    editTarget.value = { ...response.data }
  } finally {
    loading.value = false
  }
}

const loadOptions = async () => {
  try {
    const response = await targetsApi.options()
    options.value = response.data
  } catch (e) {
    console.error('Failed to load options', e)
  }
}

const saveTarget = async () => {
  saving.value = true
  try {
    await targetsApi.update(route.params.id, editTarget.value)
    target.value = { ...editTarget.value }
    editMode.value = false
  } finally {
    saving.value = false
  }
}

const cancelEdit = () => {
  editTarget.value = { ...target.value }
  editMode.value = false
}

const analyzeTarget = async () => {
  analyzing.value = true
  try {
    const response = await targetsApi.recommendScenario(route.params.id)
    recommendation.value = response.data
    // Reload target to get cached recommendation
    await loadTarget()
  } catch (e) {
    console.error('Analysis failed', e)
    alert('AI analysis failed. Please check API key configuration.')
  } finally {
    analyzing.value = false
  }
}

const deleteTarget = async () => {
  try {
    await targetsApi.delete(route.params.id)
    router.push('/targets')
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to delete target')
  }
}

const sizeLabels = {
  startup: 'Startup (<50 employees)',
  smb: 'SMB (50-200 employees)',
  mid_market: 'Mid-Market (200-1000 employees)',
  enterprise: 'Enterprise (1000+ employees)',
}

const confidenceColors = {
  high: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-red-100 text-red-800',
}
</script>

<template>
  <div>
    <div
      v-if="loading"
      class="text-center py-8 text-gray-500"
    >
      Loading target...
    </div>

    <div v-else-if="target">
      <!-- Header -->
      <div class="flex justify-between items-start mb-6">
        <div>
          <router-link
            to="/targets"
            class="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block"
          >
            ← Back to Targets
          </router-link>
          <h1 class="text-2xl font-bold text-gray-900">
            {{ target.company_name }}
          </h1>
          <p class="text-sm text-gray-500">
            {{ target.name }}
          </p>
        </div>
        <div class="flex space-x-2">
          <button
            v-if="!editMode"
            class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm"
            @click="editMode = true"
          >
            Edit
          </button>
          <button
            class="px-4 py-2 border border-red-300 text-red-600 rounded-md hover:bg-red-50 text-sm"
            @click="showDeleteModal = true"
          >
            Delete
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Target Details -->
        <div class="lg:col-span-2 space-y-6">
          <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-medium mb-4">
              Organization Details
            </h2>

            <div
              v-if="editMode"
              class="space-y-4"
            >
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Internal Name</label>
                  <input
                    v-model="editTarget.name"
                    type="text"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Company Name</label>
                  <input
                    v-model="editTarget.company_name"
                    type="text"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Industry</label>
                  <select
                    v-model="editTarget.industry"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option
                      v-for="ind in options.industries"
                      :key="ind"
                      :value="ind"
                    >
                      {{ ind }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Company Size</label>
                  <select
                    v-model="editTarget.company_size"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option
                      v-for="size in options.company_sizes"
                      :key="size"
                      :value="size"
                    >
                      {{ sizeLabels[size] || size }}
                    </option>
                  </select>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Target Department</label>
                  <select
                    v-model="editTarget.target_department"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="">
                      Any
                    </option>
                    <option
                      v-for="dept in options.departments"
                      :key="dept"
                      :value="dept"
                    >
                      {{ dept }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Region</label>
                  <select
                    v-model="editTarget.geographic_region"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option
                      v-for="region in options.regions"
                      :key="region"
                      :value="region"
                    >
                      {{ region.replace('_', ' ').toUpperCase() }}
                    </option>
                  </select>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Email Domain</label>
                  <input
                    v-model="editTarget.email_domain"
                    type="text"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">Website</label>
                  <input
                    v-model="editTarget.website"
                    type="text"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">OSINT Notes</label>
                <textarea
                  v-model="editTarget.osint_notes"
                  rows="4"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>

              <div class="flex justify-end space-x-2 pt-4">
                <button
                  class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md text-sm"
                  @click="cancelEdit"
                >
                  Cancel
                </button>
                <button
                  :disabled="saving"
                  class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm disabled:opacity-50"
                  @click="saveTarget"
                >
                  {{ saving ? 'Saving...' : 'Save Changes' }}
                </button>
              </div>
            </div>

            <div
              v-else
              class="grid grid-cols-2 gap-4 text-sm"
            >
              <div>
                <span class="text-gray-500">Industry:</span>
                <span class="ml-2 capitalize">{{ target.industry }}</span>
              </div>
              <div>
                <span class="text-gray-500">Size:</span>
                <span class="ml-2">{{ sizeLabels[target.company_size] || target.company_size }}</span>
              </div>
              <div>
                <span class="text-gray-500">Department:</span>
                <span class="ml-2 capitalize">{{ target.target_department || 'Any' }}</span>
              </div>
              <div>
                <span class="text-gray-500">Region:</span>
                <span class="ml-2">{{ (target.geographic_region || 'N/A').replace('_', ' ').toUpperCase() }}</span>
              </div>
              <div>
                <span class="text-gray-500">Email Domain:</span>
                <span class="ml-2">{{ target.email_domain || 'Not set' }}</span>
              </div>
              <div>
                <span class="text-gray-500">Website:</span>
                <span class="ml-2">
                  <a
                    v-if="target.website"
                    :href="target.website"
                    target="_blank"
                    class="text-primary-600 hover:underline"
                  >
                    {{ target.website }}
                  </a>
                  <span v-else>Not set</span>
                </span>
              </div>
              <div
                v-if="target.osint_notes"
                class="col-span-2"
              >
                <span class="text-gray-500">OSINT Notes:</span>
                <p class="mt-1 text-gray-700 whitespace-pre-wrap">
                  {{ target.osint_notes }}
                </p>
              </div>
            </div>
          </div>

          <!-- AI Recommendation Results -->
          <div
            v-if="recommendation"
            class="bg-white shadow rounded-lg p-6"
          >
            <h2 class="text-lg font-medium mb-4">
              AI Analysis Results
            </h2>

            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <span class="text-sm text-gray-500">Recommended Profile:</span>
                  <span class="ml-2 px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
                    {{ recommendation.recommended_profile }}
                  </span>
                </div>
                <span :class="[confidenceColors[recommendation.confidence], 'px-2 py-1 text-xs rounded-full']">
                  {{ recommendation.confidence }} confidence
                </span>
              </div>

              <div>
                <span class="text-sm text-gray-500">Reasoning:</span>
                <p class="mt-1 text-gray-700">
                  {{ recommendation.reasoning }}
                </p>
              </div>

              <div v-if="recommendation.alternative_profiles?.length">
                <span class="text-sm text-gray-500">Alternatives:</span>
                <div class="mt-1 flex space-x-2">
                  <span
                    v-for="alt in recommendation.alternative_profiles"
                    :key="alt"
                    class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm"
                  >
                    {{ alt }}
                  </span>
                </div>
              </div>

              <div v-if="recommendation.suggested_labels?.length">
                <span class="text-sm text-gray-500">Suggested USB Labels:</span>
                <div class="mt-1 flex flex-wrap gap-2">
                  <span
                    v-for="label in recommendation.suggested_labels"
                    :key="label"
                    class="px-2 py-1 bg-yellow-50 border border-yellow-200 text-yellow-800 rounded text-sm"
                  >
                    {{ label }}
                  </span>
                </div>
              </div>

              <div v-if="recommendation.suggested_filenames?.length">
                <span class="text-sm text-gray-500">Suggested Filenames:</span>
                <div class="mt-1 font-mono text-sm text-gray-600">
                  <div
                    v-for="fname in recommendation.suggested_filenames"
                    :key="fname"
                  >
                    {{ fname }}
                  </div>
                </div>
              </div>

              <div v-if="recommendation.risk_factors?.length">
                <span class="text-sm text-gray-500">Risk Factors:</span>
                <ul class="mt-1 list-disc list-inside text-sm text-red-600">
                  <li
                    v-for="risk in recommendation.risk_factors"
                    :key="risk"
                  >
                    {{ risk }}
                  </li>
                </ul>
              </div>

              <div v-if="recommendation.tips?.length">
                <span class="text-sm text-gray-500">Tips:</span>
                <ul class="mt-1 list-disc list-inside text-sm text-gray-600">
                  <li
                    v-for="tip in recommendation.tips"
                    :key="tip"
                  >
                    {{ tip }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
          <!-- AI Analysis Card -->
          <div class="bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium mb-4">
              AI Scenario Analysis
            </h3>

            <div
              v-if="target.recommended_scenario"
              class="mb-4 p-3 bg-green-50 rounded-lg"
            >
              <div class="text-sm text-gray-500">
                Current Recommendation
              </div>
              <div class="text-lg font-medium text-green-800">
                {{ target.recommended_scenario }}
              </div>
              <p class="text-sm text-gray-600 mt-1">
                {{ target.scenario_reasoning }}
              </p>
            </div>

            <button
              :disabled="analyzing"
              class="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-md hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 flex items-center justify-center"
              @click="analyzeTarget"
            >
              <svg
                v-if="analyzing"
                class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              {{ analyzing ? 'Analyzing...' : (target.recommended_scenario ? 'Re-analyze with AI' : 'Analyze with AI') }}
            </button>

            <p class="text-xs text-gray-500 mt-2 text-center">
              Uses GPT-4 to recommend optimal USB drop profiles based on target characteristics.
            </p>
          </div>

          <!-- Suggested Labels -->
          <div
            v-if="target.suggested_labels?.length"
            class="bg-white shadow rounded-lg p-6"
          >
            <h3 class="text-lg font-medium mb-4">
              Suggested Labels
            </h3>
            <div class="space-y-2">
              <div
                v-for="label in target.suggested_labels"
                :key="label"
                class="px-3 py-2 bg-yellow-50 border border-yellow-200 rounded text-sm"
              >
                {{ label }}
              </div>
            </div>
          </div>

          <!-- Campaigns -->
          <div class="bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium mb-4">
              Associated Campaigns
            </h3>
            <div
              v-if="target.campaign_count === 0"
              class="text-sm text-gray-500"
            >
              No campaigns linked to this target yet.
            </div>
            <div
              v-else
              class="text-sm"
            >
              <span class="text-2xl font-bold text-primary-600">{{ target.campaign_count }}</span>
              <span class="text-gray-500 ml-1">campaign(s)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">
          Delete Target?
        </h2>
        <p class="text-gray-600 mb-4">
          Are you sure you want to delete "{{ target?.company_name }}"? This action cannot be undone.
        </p>
        <div
          v-if="target?.campaign_count > 0"
          class="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm"
        >
          This target has {{ target.campaign_count }} associated campaign(s) and cannot be deleted.
        </div>
        <div class="flex justify-end space-x-3">
          <button
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
            @click="showDeleteModal = false"
          >
            Cancel
          </button>
          <button
            :disabled="target?.campaign_count > 0"
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            @click="deleteTarget"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
