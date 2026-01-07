<script setup>
import { ref, onMounted } from 'vue'
import { targetsApi } from '@/services/api'

const targets = ref([])
const options = ref({ industries: [], company_sizes: [], departments: [], regions: [] })
const loading = ref(true)
const showCreateModal = ref(false)
const newTarget = ref({
  name: '',
  company_name: '',
  industry: 'technology',
  company_size: 'mid_market',
  target_department: '',
  geographic_region: 'us_east',
  email_domain: '',
  website: '',
  osint_notes: ''
})

onMounted(async () => {
  await Promise.all([loadTargets(), loadOptions()])
})

const loadTargets = async () => {
  loading.value = true
  try {
    const response = await targetsApi.list()
    targets.value = response.data
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

const createTarget = async () => {
  await targetsApi.create(newTarget.value)
  showCreateModal.value = false
  newTarget.value = {
    name: '',
    company_name: '',
    industry: 'technology',
    company_size: 'mid_market',
    target_department: '',
    geographic_region: 'us_east',
    email_domain: '',
    website: '',
    osint_notes: ''
  }
  await loadTargets()
}

const sizeLabels = {
  startup: 'Startup (<50)',
  smb: 'SMB (50-200)',
  mid_market: 'Mid-Market (200-1k)',
  enterprise: 'Enterprise (1k+)',
}

const industryColors = {
  technology: 'bg-blue-100 text-blue-800',
  finance: 'bg-green-100 text-green-800',
  healthcare: 'bg-red-100 text-red-800',
  government: 'bg-purple-100 text-purple-800',
  education: 'bg-yellow-100 text-yellow-800',
  default: 'bg-gray-100 text-gray-800',
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          Target Organizations
        </h1>
        <p class="text-sm text-gray-500 mt-1">
          Manage target profiles for AI-powered scenario recommendations
        </p>
      </div>
      <button
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        @click="showCreateModal = true"
      >
        New Target
      </button>
    </div>

    <div
      v-if="loading"
      class="text-center py-8 text-gray-500"
    >
      Loading targets...
    </div>

    <div
      v-else-if="targets.length === 0"
      class="bg-white shadow rounded-lg p-8 text-center"
    >
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
        />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">
        No targets
      </h3>
      <p class="mt-1 text-sm text-gray-500">
        Get started by creating a new target organization.
      </p>
      <div class="mt-6">
        <button
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          @click="showCreateModal = true"
        >
          New Target
        </button>
      </div>
    </div>

    <div
      v-else
      class="bg-white shadow rounded-lg overflow-hidden"
    >
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Organization
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Industry
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Size
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Department
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Recommended
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Campaigns
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="target in targets"
            :key="target.id"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4">
              <router-link
                :to="`/targets/${target.id}`"
                class="text-primary-600 hover:underline font-medium"
              >
                {{ target.company_name }}
              </router-link>
              <div class="text-xs text-gray-500">
                {{ target.name }}
              </div>
            </td>
            <td class="px-6 py-4">
              <span :class="[industryColors[target.industry] || industryColors.default, 'px-2 py-1 text-xs rounded-full capitalize']">
                {{ target.industry }}
              </span>
            </td>
            <td class="px-6 py-4 text-gray-500 text-sm">
              {{ sizeLabels[target.company_size] || target.company_size }}
            </td>
            <td class="px-6 py-4 text-gray-500 text-sm capitalize">
              {{ target.target_department || '-' }}
            </td>
            <td class="px-6 py-4">
              <span
                v-if="target.recommended_scenario"
                class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800"
              >
                {{ target.recommended_scenario }}
              </span>
              <span
                v-else
                class="text-gray-400 text-xs"
              >Not analyzed</span>
            </td>
            <td class="px-6 py-4 text-gray-500">
              {{ target.campaign_count }}
            </td>
            <td class="px-6 py-4">
              <router-link
                :to="`/targets/${target.id}`"
                class="text-primary-600 hover:underline text-sm"
              >
                View
              </router-link>
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
      <div class="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-medium mb-4">
          Create Target Organization
        </h2>
        <form
          class="space-y-4"
          @submit.prevent="createTarget"
        >
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Internal Name</label>
              <input
                v-model="newTarget.name"
                type="text"
                required
                placeholder="acme-q1-2024"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Company Name</label>
              <input
                v-model="newTarget.company_name"
                type="text"
                required
                placeholder="Acme Corporation"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Industry</label>
              <select
                v-model="newTarget.industry"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option
                  v-for="ind in options.industries"
                  :key="ind"
                  :value="ind"
                  class="capitalize"
                >
                  {{ ind }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Company Size</label>
              <select
                v-model="newTarget.company_size"
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
                v-model="newTarget.target_department"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="">
                  Any / Not specified
                </option>
                <option
                  v-for="dept in options.departments"
                  :key="dept"
                  :value="dept"
                  class="capitalize"
                >
                  {{ dept }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Region</label>
              <select
                v-model="newTarget.geographic_region"
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
                v-model="newTarget.email_domain"
                type="text"
                placeholder="@acme.com"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Website</label>
              <input
                v-model="newTarget.website"
                type="text"
                placeholder="https://acme.com"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">OSINT Notes</label>
            <textarea
              v-model="newTarget.osint_notes"
              rows="3"
              placeholder="Research notes, LinkedIn findings, tech stack, etc."
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>

          <div class="flex justify-end space-x-3 pt-4">
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
              Create Target
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
