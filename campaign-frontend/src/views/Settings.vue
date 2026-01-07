<script setup>
import { ref, onMounted, computed } from 'vue'
import { settingsApi } from '@/services/api'

const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const error = ref(null)
const success = ref(null)

// Shlink status
const shlinkStatus = ref({
  connected: false,
  domain: '',
  api_url: '',
  error: null,
  short_url_count: 0
})

// Test result
const testResult = ref(null)

// Domain management
const domains = ref([])
const caddyDomains = ref([])
const caddyStatus = ref({ healthy: false })
const newDomain = ref('')
const addingDomain = ref(false)
const verifyingDomain = ref(null)
const dnsResults = ref({})

// Profile URL configs
const profiles = ref([])
const editedConfigs = ref({})

// Suffix mode options
const suffixModes = [
  { value: 'random', label: 'Random' },
  { value: 'drive_code', label: 'Drive Code' },
  { value: 'sequential', label: 'Sequential' },
  { value: 'custom', label: 'Custom' }
]

// Check if there are unsaved changes
const hasChanges = computed(() => {
  return Object.keys(editedConfigs.value).length > 0
})

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  error.value = null

  try {
    const [statusRes, configsRes, domainsRes, caddyRes] = await Promise.all([
      settingsApi.shlinkStatus(),
      settingsApi.getUrlConfigs(),
      settingsApi.listDomains().catch(() => ({ data: { domains: [] } })),
      settingsApi.caddyStatus().catch(() => ({ data: { healthy: false, shlink_domains: [] } }))
    ])

    shlinkStatus.value = statusRes.data
    profiles.value = configsRes.data
    domains.value = domainsRes.data.domains || []
    caddyStatus.value = caddyRes.data
    caddyDomains.value = caddyRes.data.shlink_domains || []
    editedConfigs.value = {}
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to load settings'
  } finally {
    loading.value = false
  }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  error.value = null

  try {
    const response = await settingsApi.shlinkTest()
    testResult.value = response.data

    // Refresh status after test
    const statusRes = await settingsApi.shlinkStatus()
    shlinkStatus.value = statusRes.data
  } catch (err) {
    testResult.value = {
      success: false,
      error: err.response?.data?.detail || err.message || 'Test failed'
    }
  } finally {
    testing.value = false
  }
}

async function verifyDomainDNS(domain) {
  verifyingDomain.value = domain
  dnsResults.value[domain] = null

  try {
    const response = await settingsApi.verifyDomainDNS(domain)
    dnsResults.value[domain] = response.data
  } catch (err) {
    dnsResults.value[domain] = {
      domain,
      resolves: false,
      reachable: false,
      https_works: false,
      error: err.response?.data?.detail || err.message || 'Verification failed'
    }
  } finally {
    verifyingDomain.value = null
  }
}

async function addDomain() {
  if (!newDomain.value.trim()) return

  addingDomain.value = true
  error.value = null
  success.value = null

  try {
    // First verify DNS
    await verifyDomainDNS(newDomain.value.trim())

    const dnsResult = dnsResults.value[newDomain.value.trim()]
    if (!dnsResult?.resolves) {
      error.value = `DNS verification failed for ${newDomain.value}: ${dnsResult?.error || 'Domain does not resolve'}`
      return
    }

    // Full domain setup: Caddy + Shlink
    const response = await settingsApi.fullDomainSetup(newDomain.value.trim())

    if (response.data.success) {
      success.value = response.data.message || `Domain ${newDomain.value} added successfully`
      newDomain.value = ''
      dnsResults.value = {}

      // Reload all domain data
      await loadData()
    } else {
      error.value = response.data.error || 'Failed to add domain'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to add domain'
  } finally {
    addingDomain.value = false
  }
}

function updateConfig(profileId, field, value) {
  const profile = profiles.value.find(p => p.id === profileId)
  if (!profile) return

  // Initialize edited config if not exists
  if (!editedConfigs.value[profileId]) {
    editedConfigs.value[profileId] = { ...profile.url_config }
  }

  editedConfigs.value[profileId][field] = value
}

function getConfigValue(profileId, field) {
  if (editedConfigs.value[profileId]?.[field] !== undefined) {
    return editedConfigs.value[profileId][field]
  }
  const profile = profiles.value.find(p => p.id === profileId)
  return profile?.url_config?.[field]
}

function isEdited(profileId) {
  return !!editedConfigs.value[profileId]
}

async function saveChanges() {
  if (!hasChanges.value) return

  saving.value = true
  error.value = null
  success.value = null

  try {
    const updates = Object.entries(editedConfigs.value).map(([id, config]) => ({
      id,
      enabled: config.enabled ?? false,
      base_slug: config.base_slug ?? '',
      suffix_mode: config.suffix_mode ?? 'random',
      suffix_length: config.suffix_length ?? 4
    }))

    await settingsApi.bulkUpdateUrlConfigs(updates)

    success.value = `Updated ${updates.length} profile(s) successfully`
    editedConfigs.value = {}

    // Reload data
    await loadData()
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to save changes'
  } finally {
    saving.value = false
  }
}

function discardChanges() {
  editedConfigs.value = {}
}

async function toggleAll(enabled) {
  for (const profile of profiles.value) {
    updateConfig(profile.id, 'enabled', enabled)
  }
}
</script>

<template>
  <div class="px-4 sm:px-6 lg:px-8 py-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

    <!-- Error Alert -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
      {{ error }}
    </div>

    <!-- Success Alert -->
    <div v-if="success" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
      {{ success }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>

    <div v-else class="space-y-6">
      <!-- Shlink Connection Status -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Shlink URL Shortener</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Status -->
          <div>
            <div class="flex items-center gap-3 mb-4">
              <span
                :class="[
                  'w-3 h-3 rounded-full',
                  shlinkStatus.connected ? 'bg-green-500' : 'bg-red-500'
                ]"
              ></span>
              <span class="font-medium">
                {{ shlinkStatus.connected ? 'Connected' : 'Disconnected' }}
              </span>
            </div>

            <div class="space-y-2 text-sm text-gray-600">
              <div>
                <span class="font-medium">Domain:</span>
                {{ shlinkStatus.domain || 'Not configured' }}
              </div>
              <div>
                <span class="font-medium">API URL:</span>
                {{ shlinkStatus.api_url }}
              </div>
              <div v-if="shlinkStatus.connected">
                <span class="font-medium">Short URLs:</span>
                {{ shlinkStatus.short_url_count }}
              </div>
              <div v-if="shlinkStatus.error" class="text-red-600">
                <span class="font-medium">Error:</span>
                {{ shlinkStatus.error }}
              </div>
            </div>
          </div>

          <!-- Test Connection -->
          <div>
            <button
              @click="testConnection"
              :disabled="testing"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {{ testing ? 'Testing...' : 'Test Connection' }}
            </button>

            <div v-if="testResult" class="mt-4 p-3 rounded-md" :class="testResult.success ? 'bg-green-50' : 'bg-red-50'">
              <div class="flex items-center gap-2">
                <span v-if="testResult.success" class="text-green-600">Test passed</span>
                <span v-else class="text-red-600">Test failed</span>
              </div>
              <div v-if="testResult.short_url" class="text-sm text-gray-600 mt-1">
                Created: {{ testResult.short_url }}
              </div>
              <div v-if="testResult.error" class="text-sm text-red-600 mt-1">
                {{ testResult.error }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Domain Management -->
      <div v-if="shlinkStatus.connected" class="bg-white shadow rounded-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Domain Management</h2>
          <div class="flex items-center gap-2 text-sm">
            <span
              :class="[
                'w-2 h-2 rounded-full',
                caddyStatus.healthy ? 'bg-green-500' : 'bg-red-500'
              ]"
            ></span>
            <span class="text-gray-600">Caddy: {{ caddyStatus.healthy ? 'Connected' : 'Disconnected' }}</span>
          </div>
        </div>

        <p class="text-sm text-gray-500 mb-4">
          Add domains for short URL generation. Domains are automatically configured in Caddy with SSL certificates.
        </p>

        <!-- Current Domains -->
        <div class="mb-6">
          <h3 class="text-sm font-medium text-gray-700 mb-3">Configured Domains</h3>

          <div v-if="domains.length === 0" class="text-sm text-gray-500 italic">
            No domains configured yet.
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="domain in domains"
              :key="domain.domain"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div class="flex items-center gap-3">
                <span
                  :class="[
                    'w-2 h-2 rounded-full',
                    domain.is_default ? 'bg-green-500' : 'bg-blue-500'
                  ]"
                ></span>
                <div>
                  <span class="font-medium text-gray-900">{{ domain.domain }}</span>
                  <span v-if="domain.is_default" class="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                    Default
                  </span>
                  <span
                    v-if="caddyDomains.includes(domain.domain)"
                    class="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded"
                    title="Configured in Caddy with SSL"
                  >
                    Caddy
                  </span>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <!-- DNS Status -->
                <div v-if="dnsResults[domain.domain]" class="flex items-center gap-1 text-xs">
                  <span
                    :class="dnsResults[domain.domain].resolves ? 'text-green-600' : 'text-red-600'"
                  >
                    DNS: {{ dnsResults[domain.domain].resolves ? 'OK' : 'FAIL' }}
                  </span>
                  <span
                    v-if="dnsResults[domain.domain].resolves"
                    :class="dnsResults[domain.domain].https_works ? 'text-green-600' : (dnsResults[domain.domain].reachable ? 'text-yellow-600' : 'text-red-600')"
                    :title="dnsResults[domain.domain].error || ''"
                  >
                    | HTTPS: {{ dnsResults[domain.domain].https_works ? 'OK' : (dnsResults[domain.domain].reachable ? 'OK*' : 'FAIL') }}
                  </span>
                </div>

                <button
                  @click="verifyDomainDNS(domain.domain)"
                  :disabled="verifyingDomain === domain.domain"
                  class="px-3 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded disabled:opacity-50"
                >
                  {{ verifyingDomain === domain.domain ? 'Checking...' : 'Verify DNS' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Add New Domain -->
        <div class="border-t pt-4">
          <h3 class="text-sm font-medium text-gray-700 mb-3">Add New Domain</h3>

          <div class="flex items-start gap-4">
            <div class="flex-1">
              <input
                v-model="newDomain"
                type="text"
                placeholder="e.g., short.example.com"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              />
              <p class="text-xs text-gray-500 mt-1">
                Make sure DNS is configured before adding. Domain should resolve to your Caddy server IP.
              </p>
            </div>

            <button
              @click="addDomain"
              :disabled="addingDomain || !newDomain.trim()"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {{ addingDomain ? 'Adding...' : 'Add Domain' }}
            </button>
          </div>

          <!-- DNS Result for new domain -->
          <div
            v-if="newDomain && dnsResults[newDomain.trim()]"
            class="mt-3 p-3 rounded-md text-sm"
            :class="dnsResults[newDomain.trim()].resolves ? 'bg-green-50' : 'bg-red-50'"
          >
            <div class="font-medium" :class="dnsResults[newDomain.trim()].resolves ? 'text-green-700' : 'text-red-700'">
              {{ dnsResults[newDomain.trim()].resolves ? 'DNS Resolution: OK' : 'DNS Resolution: Failed' }}
            </div>
            <div v-if="dnsResults[newDomain.trim()].ip_addresses?.length" class="text-gray-600 mt-1">
              IPs: {{ dnsResults[newDomain.trim()].ip_addresses.join(', ') }}
            </div>
            <div v-if="dnsResults[newDomain.trim()].resolves" class="mt-1">
              <span :class="dnsResults[newDomain.trim()].https_works ? 'text-green-600' : 'text-yellow-600'">
                HTTPS: {{ dnsResults[newDomain.trim()].https_works ? 'Working' : 'Not working' }}
              </span>
            </div>
            <div v-if="dnsResults[newDomain.trim()].error" class="text-red-600 mt-1">
              {{ dnsResults[newDomain.trim()].error }}
            </div>
          </div>
        </div>

        <!-- Verification Note -->
        <div class="mt-4 p-3 bg-gray-50 rounded-md text-xs text-gray-600">
          <strong>*</strong> HTTPS verification may show "OK*" due to hairpin NAT limitations when testing from inside Docker.
          This typically means the domain works correctly for external users.
        </div>

        <!-- Auto-configuration Notice -->
        <div class="mt-4 p-3 bg-green-50 rounded-md text-sm text-green-800">
          <strong>Automatic Setup:</strong> When you add a domain, it is automatically:
          <ul class="list-disc list-inside mt-1 text-xs">
            <li>Added to Caddy configuration</li>
            <li>SSL certificate provisioned via Let's Encrypt</li>
            <li>Registered with Shlink for short URL creation</li>
          </ul>
        </div>
      </div>

      <!-- Profile URL Configurations -->
      <div class="bg-white shadow rounded-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Profile URL Configurations</h2>

          <div class="flex items-center gap-4">
            <button
              @click="toggleAll(true)"
              class="text-sm text-primary-600 hover:text-primary-800"
            >
              Enable All
            </button>
            <button
              @click="toggleAll(false)"
              class="text-sm text-gray-600 hover:text-gray-800"
            >
              Disable All
            </button>
          </div>
        </div>

        <p class="text-sm text-gray-500 mb-4">
          Configure how short URLs are generated for each profile. When enabled, new drives using these profiles will automatically create short URLs via Shlink.
        </p>

        <!-- Table -->
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Profile</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Enabled</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Base Slug</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Suffix Mode</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Length</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="profile in profiles"
                :key="profile.id"
                :class="{ 'bg-yellow-50': isEdited(profile.id) }"
              >
                <td class="px-4 py-3">
                  <div class="font-medium text-gray-900">{{ profile.name }}</div>
                  <div class="text-xs text-gray-500">{{ profile.scenario_type }}</div>
                </td>
                <td class="px-4 py-3">
                  <input
                    type="checkbox"
                    :checked="getConfigValue(profile.id, 'enabled')"
                    @change="updateConfig(profile.id, 'enabled', $event.target.checked)"
                    class="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                </td>
                <td class="px-4 py-3">
                  <input
                    type="text"
                    :value="getConfigValue(profile.id, 'base_slug')"
                    @input="updateConfig(profile.id, 'base_slug', $event.target.value)"
                    placeholder="e.g., hr-docs"
                    class="w-32 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-primary-500 focus:border-primary-500"
                  />
                </td>
                <td class="px-4 py-3">
                  <select
                    :value="getConfigValue(profile.id, 'suffix_mode') || 'random'"
                    @change="updateConfig(profile.id, 'suffix_mode', $event.target.value)"
                    class="w-28 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option v-for="mode in suffixModes" :key="mode.value" :value="mode.value">
                      {{ mode.label }}
                    </option>
                  </select>
                </td>
                <td class="px-4 py-3">
                  <input
                    type="number"
                    :value="getConfigValue(profile.id, 'suffix_length') || 4"
                    @input="updateConfig(profile.id, 'suffix_length', parseInt($event.target.value))"
                    min="2"
                    max="12"
                    class="w-16 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-primary-500 focus:border-primary-500"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Save/Discard buttons -->
        <div v-if="hasChanges" class="mt-4 flex items-center gap-4 pt-4 border-t">
          <button
            @click="saveChanges"
            :disabled="saving"
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
          <button
            @click="discardChanges"
            :disabled="saving"
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Discard
          </button>
          <span class="text-sm text-yellow-600">
            {{ Object.keys(editedConfigs).length }} profile(s) modified
          </span>
        </div>
      </div>

      <!-- Example URLs -->
      <div class="bg-gray-50 rounded-lg p-6">
        <h3 class="text-sm font-medium text-gray-900 mb-2">Example Short URLs</h3>
        <p class="text-sm text-gray-600 mb-3">
          Based on your configuration, short URLs will look like:
        </p>
        <div class="space-y-1 text-sm font-mono text-gray-700">
          <div>https://{{ shlinkStatus.domain }}/hr-docs-a7k2</div>
          <div>https://{{ shlinkStatus.domain }}/finance-report-m9p4</div>
          <div>https://{{ shlinkStatus.domain }}/it-resources-x3b8</div>
        </div>
      </div>
    </div>
  </div>
</template>
