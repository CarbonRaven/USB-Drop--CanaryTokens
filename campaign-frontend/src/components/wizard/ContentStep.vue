<script setup>
import { ref, computed } from 'vue'
import { useProfileWizardStore } from '@/stores/profileWizard'
import TemplateEditor from './TemplateEditor.vue'
import { profilesApi } from '@/services/api'

const store = useProfileWizardStore()

const urlShortener = computed(() => store.content.url_shortener)
const labelSuggestions = computed(() => store.content.label_suggestions)

// Shortcut creation
const showShortcutModal = ref(false)
const newShortcut = ref({
  filename: '',
  folder: '',
  target_url: '',
  shortcut_type: 'both'
})

// Template creation
const showTemplateModal = ref(false)
const newTemplate = ref({
  filename: 'readme.txt',
  folder: '',
  content: ''
})

// Check if we can create shortcuts/templates (need a saved profile)
const canCreateFiles = computed(() => store.isEditing && store.editingProfileId)

// Create shortcut
const createShortcut = async () => {
  if (!canCreateFiles.value) return

  try {
    const response = await profilesApi.createShortcut(store.editingProfileId, {
      filename: newShortcut.value.filename,
      folder: newShortcut.value.folder,
      target_url: newShortcut.value.target_url,
      shortcut_type: newShortcut.value.shortcut_type
    })
    store.addUploadedFile(response.data)
    showShortcutModal.value = false
    newShortcut.value = { filename: '', folder: '', target_url: '', shortcut_type: 'both' }
  } catch (error) {
    console.error('Failed to create shortcut:', error)
  }
}

// Create template
const createTemplate = async () => {
  if (!canCreateFiles.value) return

  try {
    const response = await profilesApi.createTemplate(store.editingProfileId, {
      filename: newTemplate.value.filename,
      folder: newTemplate.value.folder,
      content: newTemplate.value.content
    })
    store.addUploadedFile(response.data)
    showTemplateModal.value = false
    newTemplate.value = { filename: 'readme.txt', folder: '', content: '' }
  } catch (error) {
    console.error('Failed to create template:', error)
  }
}

const suffixModes = [
  { value: 'random', label: 'Random', description: 'Generate random alphanumeric suffix (e.g., hr-docs-x7k2)' },
  { value: 'sequential', label: 'Sequential', description: 'Use sequential numbers (e.g., hr-docs-001)' },
  { value: 'drive_code', label: 'Drive Code', description: 'Use drive code as suffix (e.g., hr-docs-usba1b2c3)' },
]

const updateUrlShortener = (field, value) => {
  store.content.url_shortener[field] = value
}

const addLabelSuggestion = () => {
  const input = document.getElementById('newLabelInput')
  const value = input?.value?.trim()
  if (value && !store.content.label_suggestions.includes(value)) {
    store.content.label_suggestions.push(value)
    input.value = ''
  }
}

const removeLabelSuggestion = (index) => {
  store.content.label_suggestions.splice(index, 1)
}

// Generate slug preview
const slugPreview = computed(() => {
  if (!urlShortener.value.enabled) return null
  const base = urlShortener.value.base_slug || 'docs'
  const mode = urlShortener.value.suffix_mode
  let suffix = ''
  if (mode === 'random') {
    suffix = 'x7k2'
  } else if (mode === 'sequential') {
    suffix = '001'
  } else if (mode === 'drive_code') {
    suffix = 'usba1b2c3'
  }
  return `${base}-${suffix}`
})
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-lg font-medium text-gray-900">
        Step 4: Content &amp; Configuration
      </h2>
      <p class="mt-1 text-sm text-gray-500">
        Configure URL shortening, label suggestions, and other content options.
      </p>
    </div>

    <div class="space-y-8">
      <!-- URL Shortener Section -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-medium text-gray-900">
                URL Shortener
              </h3>
              <p class="text-xs text-gray-500 mt-0.5">
                Create short, branded URLs for token tracking links
              </p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="urlShortener.enabled"
                class="sr-only peer"
                @change="updateUrlShortener('enabled', $event.target.checked)"
              >
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600" />
            </label>
          </div>
        </div>

        <div
          v-if="urlShortener.enabled"
          class="p-4 space-y-4"
        >
          <!-- Base Slug -->
          <div>
            <label class="block text-sm font-medium text-gray-700">
              Base Slug
            </label>
            <div class="mt-1 flex rounded-md shadow-sm">
              <span class="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                links.example.com/
              </span>
              <input
                type="text"
                :value="urlShortener.base_slug"
                placeholder="hr-docs"
                class="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md text-sm border border-gray-300 focus:ring-primary-500 focus:border-primary-500"
                @input="updateUrlShortener('base_slug', $event.target.value)"
              >
            </div>
            <p class="mt-1 text-xs text-gray-500">
              Use lowercase letters, numbers, and hyphens only
            </p>
          </div>

          <!-- Suffix Mode -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Suffix Mode
            </label>
            <div class="space-y-2">
              <label
                v-for="mode in suffixModes"
                :key="mode.value"
                class="flex items-start p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                :class="urlShortener.suffix_mode === mode.value ? 'border-primary-500 bg-primary-50' : 'border-gray-200'"
              >
                <input
                  type="radio"
                  :value="mode.value"
                  :checked="urlShortener.suffix_mode === mode.value"
                  class="mt-0.5 h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                  @change="updateUrlShortener('suffix_mode', mode.value)"
                >
                <div class="ml-3">
                  <span class="text-sm font-medium text-gray-900">{{ mode.label }}</span>
                  <p class="text-xs text-gray-500">{{ mode.description }}</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Suffix Length (for random mode) -->
          <div v-if="urlShortener.suffix_mode === 'random'">
            <label class="block text-sm font-medium text-gray-700">
              Suffix Length
            </label>
            <select
              :value="urlShortener.suffix_length"
              class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              @change="updateUrlShortener('suffix_length', parseInt($event.target.value))"
            >
              <option :value="3">
                3 characters
              </option>
              <option :value="4">
                4 characters (recommended)
              </option>
              <option :value="5">
                5 characters
              </option>
              <option :value="6">
                6 characters
              </option>
            </select>
          </div>

          <!-- Custom Domain (optional) -->
          <div>
            <label class="block text-sm font-medium text-gray-700">
              Custom Domain (optional)
            </label>
            <input
              type="text"
              :value="urlShortener.domain"
              placeholder="Leave empty to use default"
              class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              @input="updateUrlShortener('domain', $event.target.value)"
            >
            <p class="mt-1 text-xs text-gray-500">
              Override the default short link domain
            </p>
          </div>

          <!-- Preview -->
          <div
            v-if="slugPreview"
            class="p-3 bg-gray-50 rounded-lg"
          >
            <p class="text-xs text-gray-500 mb-1">
              Example URL:
            </p>
            <code class="text-sm text-primary-600">
              https://{{ urlShortener.domain || 'links.example.com' }}/{{ slugPreview }}
            </code>
          </div>
        </div>

        <div
          v-else
          class="p-4 text-center text-gray-500 text-sm"
        >
          <p>URL shortening is disabled. Token URLs will use the default CanaryTokens format.</p>
        </div>
      </div>

      <!-- URL Shortcuts Section -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-medium text-gray-900">URL Shortcuts</h3>
            <p class="text-xs text-gray-500 mt-0.5">Create clickable shortcut files (.url, .webloc)</p>
          </div>
          <button
            type="button"
            :disabled="!canCreateFiles"
            class="px-3 py-1.5 text-xs font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            @click="showShortcutModal = true"
          >
            + Add Shortcut
          </button>
        </div>
        <div class="p-4">
          <div v-if="!canCreateFiles" class="text-center py-4 text-gray-500">
            <p class="text-sm">Save profile first to add shortcuts</p>
          </div>
          <div v-else class="text-sm text-gray-600">
            <p>Shortcuts created will appear in the Files list. They link to tracking URLs that trigger alerts when clicked.</p>
          </div>
        </div>
      </div>

      <!-- Custom Templates Section -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-medium text-gray-900">Custom Text Templates</h3>
            <p class="text-xs text-gray-500 mt-0.5">Create text files with embedded tracking URLs</p>
          </div>
          <button
            type="button"
            :disabled="!canCreateFiles"
            class="px-3 py-1.5 text-xs font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            @click="showTemplateModal = true"
          >
            + Add Template
          </button>
        </div>
        <div class="p-4">
          <div v-if="!canCreateFiles" class="text-center py-4 text-gray-500">
            <p class="text-sm">Save profile first to add templates</p>
          </div>
          <div v-else class="text-sm text-gray-600">
            <p>Templates allow you to create custom text files with <code class="bg-gray-100 px-1 rounded">{canary_url}</code> placeholders that get replaced with tracking URLs.</p>
          </div>
        </div>
      </div>

      <!-- Label Suggestions Section -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 class="text-sm font-medium text-gray-900">
            USB Drive Label Suggestions
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">
            Suggested labels to write on USB drives for this profile
          </p>
        </div>

        <div class="p-4">
          <!-- Add new label -->
          <div class="flex gap-2 mb-4">
            <input
              id="newLabelInput"
              type="text"
              placeholder="e.g., HR Confidential"
              class="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              @keyup.enter="addLabelSuggestion"
            >
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700"
              @click="addLabelSuggestion"
            >
              Add
            </button>
          </div>

          <!-- Label list -->
          <div
            v-if="labelSuggestions.length > 0"
            class="flex flex-wrap gap-2"
          >
            <span
              v-for="(label, index) in labelSuggestions"
              :key="index"
              class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700"
            >
              {{ label }}
              <button
                type="button"
                class="ml-2 text-gray-400 hover:text-red-500"
                @click="removeLabelSuggestion(index)"
              >
                <svg
                  class="w-4 h-4"
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
            </span>
          </div>

          <p
            v-else
            class="text-sm text-gray-500 text-center py-4"
          >
            No label suggestions added yet
          </p>
        </div>
      </div>

      <!-- Info Box -->
      <div class="p-4 bg-blue-50 rounded-lg">
        <div class="flex">
          <svg
            class="w-5 h-5 text-blue-400 mr-3 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div class="text-sm text-blue-700">
            <p class="font-medium">
              About URL Shortening
            </p>
            <p class="mt-1">
              Short URLs make token links look more professional and less suspicious.
              When enabled, drives created from this profile will automatically generate
              shortened URLs for web-based tokens (text files, QR codes, etc.).
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Shortcut Modal -->
    <div
      v-if="showShortcutModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      @click.self="showShortcutModal = false"
    >
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Create URL Shortcut</h3>
        </div>
        <div class="px-6 py-4 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Filename</label>
            <input
              v-model="newShortcut.filename"
              type="text"
              placeholder="e.g., Important_Link"
              class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
            <p class="mt-1 text-xs text-gray-500">Extension will be added automatically (.url, .webloc)</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Target Folder</label>
            <select
              v-model="newShortcut.folder"
              class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">(Root)</option>
              <option v-for="folder in store.folders" :key="folder.path" :value="folder.path">
                {{ folder.path }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Target URL</label>
            <input
              v-model="newShortcut.target_url"
              type="url"
              placeholder="https://..."
              class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
            <p class="mt-1 text-xs text-gray-500">This URL will be tracked. Use a landing page or redirect URL.</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Shortcut Type</label>
            <div class="mt-2 space-y-2">
              <label class="flex items-center">
                <input v-model="newShortcut.shortcut_type" type="radio" value="both" class="h-4 w-4 text-primary-600">
                <span class="ml-2 text-sm text-gray-700">Both (.url + .webloc)</span>
              </label>
              <label class="flex items-center">
                <input v-model="newShortcut.shortcut_type" type="radio" value="windows" class="h-4 w-4 text-primary-600">
                <span class="ml-2 text-sm text-gray-700">Windows only (.url)</span>
              </label>
              <label class="flex items-center">
                <input v-model="newShortcut.shortcut_type" type="radio" value="macos" class="h-4 w-4 text-primary-600">
                <span class="ml-2 text-sm text-gray-700">macOS only (.webloc)</span>
              </label>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            @click="showShortcutModal = false"
          >
            Cancel
          </button>
          <button
            type="button"
            :disabled="!newShortcut.filename || !newShortcut.target_url"
            class="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:bg-gray-300"
            @click="createShortcut"
          >
            Create Shortcut
          </button>
        </div>
      </div>
    </div>

    <!-- Template Modal -->
    <div
      v-if="showTemplateModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      @click.self="showTemplateModal = false"
    >
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Create Custom Template</h3>
        </div>
        <div class="px-6 py-4 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Filename</label>
              <input
                v-model="newTemplate.filename"
                type="text"
                placeholder="e.g., passwords.txt"
                class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Target Folder</label>
              <select
                v-model="newTemplate.folder"
                class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">(Root)</option>
                <option v-for="folder in store.folders" :key="folder.path" :value="folder.path">
                  {{ folder.path }}
                </option>
              </select>
            </div>
          </div>
          <TemplateEditor
            v-model="newTemplate.content"
            :filename="newTemplate.filename"
            :url-shortener-enabled="urlShortener.enabled"
            :url-shortener-config="urlShortener"
          />
        </div>
        <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            @click="showTemplateModal = false"
          >
            Cancel
          </button>
          <button
            type="button"
            :disabled="!newTemplate.filename || !newTemplate.content"
            class="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:bg-gray-300"
            @click="createTemplate"
          >
            Create Template
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
