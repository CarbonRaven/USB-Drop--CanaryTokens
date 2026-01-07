<script setup>
import { computed } from 'vue'
import { useProfileWizardStore } from '@/stores/profileWizard'

const store = useProfileWizardStore()

const tokenTypes = {
  ms_word: { label: 'Word Document', icon: '📄', color: 'bg-blue-100 text-blue-800' },
  ms_excel: { label: 'Excel Spreadsheet', icon: '📊', color: 'bg-green-100 text-green-800' },
  pdf: { label: 'PDF Document', icon: '📕', color: 'bg-red-100 text-red-700' },
  text: { label: 'Text File', icon: '📝', color: 'bg-gray-100 text-gray-800' },
  windows_dir: { label: 'Folder Token', icon: '📁', color: 'bg-yellow-100 text-yellow-800' },
  aws_keys: { label: 'AWS Credentials', icon: '🔑', color: 'bg-orange-100 text-orange-800' },
  web: { label: 'Web Bug', icon: '🔗', color: 'bg-purple-100 text-purple-800' },
  qr_code: { label: 'QR Code', icon: '📱', color: 'bg-pink-100 text-pink-800' },
}

const scenarioTypes = {
  hr_documents: { name: 'HR Department', icon: '👥' },
  it_department: { name: 'IT Department', icon: '💻' },
  finance: { name: 'Finance', icon: '💰' },
  executive: { name: 'Executive', icon: '👔' },
  developer: { name: 'Developer', icon: '🔧' },
  network_admin: { name: 'Network Admin', icon: '🌐' },
  security_audit: { name: 'Security Audit', icon: '🔒' },
  contractor: { name: 'Contractor', icon: '📋' },
  custom: { name: 'Custom', icon: '➕' },
}

const getTokenType = (typeValue) => {
  return tokenTypes[typeValue] || { label: typeValue, icon: '📄', color: 'bg-gray-100 text-gray-800' }
}

const getScenarioType = (typeValue) => {
  return scenarioTypes[typeValue] || { name: typeValue, icon: '📁' }
}

// Summary data
const summary = computed(() => store.profileSummary)
const folders = computed(() => store.folders)
const files = computed(() => store.files)
const urlShortener = computed(() => store.content.url_shortener)
const labelSuggestions = computed(() => store.content.label_suggestions)

const suffixModeLabels = {
  random: 'Random',
  sequential: 'Sequential',
  drive_code: 'Drive Code'
}

// Token type counts
const tokenCounts = computed(() => {
  const counts = {}
  files.value.forEach(file => {
    if (file.token_type) {
      counts[file.token_type] = (counts[file.token_type] || 0) + 1
    }
  })
  return counts
})

// Build file tree structure for display
const fileTree = computed(() => {
  const tree = []

  // Add root-level files
  files.value
    .filter(f => !f.folder)
    .forEach(file => {
      tree.push({
        type: 'file',
        name: file.name,
        tokenType: file.token_type,
        path: file.name
      })
    })

  // Add folders with their files
  folders.value.forEach(folder => {
    const folderFiles = files.value.filter(f => f.folder === folder.path)
    tree.push({
      type: 'folder',
      name: folder.path,
      hasToken: folder.has_folder_token,
      files: folderFiles.map(f => ({
        type: 'file',
        name: f.name,
        tokenType: f.token_type,
        path: `${folder.path}/${f.name}`
      }))
    })
  })

  return tree
})

const goToStep = (step) => {
  store.goToStep(step)
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-lg font-medium text-gray-900">
        Step 5: Review &amp; Create
      </h2>
      <p class="mt-1 text-sm text-gray-500">
        Review your profile configuration before creating. Click on any section to make changes.
      </p>
    </div>

    <div class="space-y-6">
      <!-- Profile Info -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-sm font-medium text-gray-700">
            Profile Information
          </h3>
          <button
            type="button"
            class="text-xs text-primary-600 hover:text-primary-700"
            @click="goToStep(1)"
          >
            Edit
          </button>
        </div>
        <div class="p-4">
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Name
              </dt>
              <dd class="mt-1 text-sm text-gray-900">
                {{ summary.name || 'Not set' }}
              </dd>
            </div>
            <div>
              <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Scenario Type
              </dt>
              <dd class="mt-1 text-sm text-gray-900">
                <span class="inline-flex items-center">
                  <span class="mr-1">{{ getScenarioType(summary.scenario_type).icon }}</span>
                  {{ getScenarioType(summary.scenario_type).name }}
                </span>
              </dd>
            </div>
            <div class="sm:col-span-2">
              <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Description
              </dt>
              <dd class="mt-1 text-sm text-gray-900">
                {{ summary.description || 'No description' }}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Structure Summary -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-yellow-700">
            {{ summary.folders }}
          </div>
          <div class="text-sm text-yellow-600">
            Folders
          </div>
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-blue-700">
            {{ summary.files }}
          </div>
          <div class="text-sm text-blue-600">
            Files
          </div>
        </div>
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-green-700">
            {{ summary.tokens }}
          </div>
          <div class="text-sm text-green-600">
            Tokens
          </div>
        </div>
      </div>

      <!-- Token Types -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-sm font-medium text-gray-700">
            Token Types
          </h3>
          <button
            type="button"
            class="text-xs text-primary-600 hover:text-primary-700"
            @click="goToStep(3)"
          >
            Edit
          </button>
        </div>
        <div class="p-4">
          <div
            v-if="Object.keys(tokenCounts).length > 0"
            class="flex flex-wrap gap-2"
          >
            <span
              v-for="(count, type) in tokenCounts"
              :key="type"
              :class="['inline-flex items-center px-3 py-1.5 rounded-full text-sm', getTokenType(type).color]"
            >
              <span class="mr-1">{{ getTokenType(type).icon }}</span>
              {{ getTokenType(type).label }}: {{ count }}
            </span>
          </div>
          <p
            v-else
            class="text-sm text-gray-500"
          >
            No tokens configured
          </p>
        </div>
      </div>

      <!-- URL Shortener Config -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-sm font-medium text-gray-700">
            URL Shortener
          </h3>
          <button
            type="button"
            class="text-xs text-primary-600 hover:text-primary-700"
            @click="goToStep(4)"
          >
            Edit
          </button>
        </div>
        <div class="p-4">
          <div v-if="urlShortener.enabled">
            <div class="flex items-center mb-3">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Enabled
              </span>
            </div>
            <dl class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <div>
                <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Base Slug
                </dt>
                <dd class="mt-1 text-gray-900">
                  {{ urlShortener.base_slug || '(not set)' }}
                </dd>
              </div>
              <div>
                <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Suffix Mode
                </dt>
                <dd class="mt-1 text-gray-900">
                  {{ suffixModeLabels[urlShortener.suffix_mode] || urlShortener.suffix_mode }}
                </dd>
              </div>
              <div>
                <dt class="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Domain
                </dt>
                <dd class="mt-1 text-gray-900">
                  {{ urlShortener.domain || '(default)' }}
                </dd>
              </div>
            </dl>
            <div class="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
              Example: <code class="text-primary-600">https://{{ urlShortener.domain || 'links.example.com' }}/{{ urlShortener.base_slug || 'docs' }}-{{ urlShortener.suffix_mode === 'random' ? 'x7k2' : urlShortener.suffix_mode === 'sequential' ? '001' : 'usba1b2c3' }}</code>
            </div>
          </div>
          <div
            v-else
            class="flex items-center text-gray-500"
          >
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 mr-2">
              Disabled
            </span>
            <span class="text-sm">Token URLs will use default CanaryTokens format</span>
          </div>
        </div>
      </div>

      <!-- Label Suggestions -->
      <div
        v-if="labelSuggestions.length > 0"
        class="border border-gray-200 rounded-lg overflow-hidden"
      >
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-sm font-medium text-gray-700">
            USB Label Suggestions
          </h3>
          <button
            type="button"
            class="text-xs text-primary-600 hover:text-primary-700"
            @click="goToStep(4)"
          >
            Edit
          </button>
        </div>
        <div class="p-4">
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(label, index) in labelSuggestions"
              :key="index"
              class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700"
            >
              {{ label }}
            </span>
          </div>
        </div>
      </div>

      <!-- File Structure Preview -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-sm font-medium text-gray-700">
            File Structure Preview
          </h3>
          <button
            type="button"
            class="text-xs text-primary-600 hover:text-primary-700"
            @click="goToStep(2)"
          >
            Edit
          </button>
        </div>
        <div class="p-4">
          <div class="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm overflow-x-auto">
            <!-- USB Drive root -->
            <div class="flex items-center text-gray-400 mb-1">
              <svg
                class="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
              USB Drive
            </div>

            <!-- Tree structure -->
            <div class="ml-4">
              <template
                v-for="(item, index) in fileTree"
                :key="index"
              >
                <!-- File at root -->
                <div
                  v-if="item.type === 'file'"
                  class="flex items-center py-0.5"
                >
                  <span class="text-gray-600 mr-2">├──</span>
                  <span
                    :class="getTokenType(item.tokenType).color.replace('bg-', 'text-').replace('-100', '-400')"
                    class="mr-2"
                  >
                    {{ getTokenType(item.tokenType).icon }}
                  </span>
                  <span>{{ item.name }}</span>
                  <span class="text-gray-500 ml-2 text-xs">[{{ getTokenType(item.tokenType).label }}]</span>
                </div>

                <!-- Folder -->
                <template v-if="item.type === 'folder'">
                  <div class="flex items-center py-0.5">
                    <span class="text-gray-600 mr-2">├──</span>
                    <span class="text-yellow-400 mr-2">📁</span>
                    <span>{{ item.name }}</span>
                    <span
                      v-if="item.hasToken"
                      class="text-yellow-500 ml-2 text-xs"
                    >[folder token]</span>
                  </div>
                  <!-- Files in folder -->
                  <div
                    v-for="(file, fileIndex) in item.files"
                    :key="`${index}-${fileIndex}`"
                    class="flex items-center py-0.5 ml-6"
                  >
                    <span class="text-gray-600 mr-2">{{ fileIndex === item.files.length - 1 ? '└──' : '├──' }}</span>
                    <span
                      :class="getTokenType(file.tokenType).color.replace('bg-', 'text-').replace('-100', '-400')"
                      class="mr-2"
                    >
                      {{ getTokenType(file.tokenType).icon }}
                    </span>
                    <span>{{ file.name }}</span>
                    <span class="text-gray-500 ml-2 text-xs">[{{ getTokenType(file.tokenType).label }}]</span>
                  </div>
                </template>
              </template>

              <!-- Empty state -->
              <div
                v-if="fileTree.length === 0"
                class="text-gray-500 py-2"
              >
                (empty)
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Ready to Create -->
      <div class="bg-green-50 border border-green-200 rounded-lg p-4">
        <div class="flex">
          <svg
            class="w-5 h-5 text-green-500 mr-3 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <h4 class="text-sm font-medium text-green-800">
              Ready to Create
            </h4>
            <p class="mt-1 text-sm text-green-700">
              Your profile is configured and ready to be created. Click "Create Profile" below to save.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
