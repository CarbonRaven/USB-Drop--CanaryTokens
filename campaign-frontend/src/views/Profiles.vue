<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { profilesApi } from '@/services/api'

const router = useRouter()

const profiles = ref([])
const templates = ref([])
const textTemplates = ref([])
const tokenTypes = ref([])
const loading = ref(true)
const togglingId = ref(null)
const showCreateModal = ref(false)
const showTemplateModal = ref(false)
const showPreviewModal = ref(false)
const showEditModal = ref(false)
const previewData = ref(null)
const editingProfile = ref(null)
const selectedTemplate = ref(null)

const newProfile = ref({
  name: '',
  description: '',
  scenario_type: 'it',
  theme: 'corporate',
  file_structure: {
    folders: [],
    files: []
  },
  token_config: {},
  ai_prompts: {},
  label_suggestions: []
})

// New file being added
const newFile = ref({
  folder: '',
  name: '',
  type: 'ms_word',
  template: ''
})

const newFolder = ref('')

const scenarioTypes = [
  { value: 'it_department', label: 'IT Department', icon: '💻' },
  { value: 'hr_documents', label: 'HR / Payroll', icon: '👥' },
  { value: 'finance', label: 'Finance', icon: '💰' },
  { value: 'executive', label: 'Executive', icon: '👔' },
  { value: 'developer', label: 'Developer', icon: '🔧' },
  { value: 'network_admin', label: 'Network Admin', icon: '🌐' },
  { value: 'security_audit', label: 'Security Audit', icon: '🔒' },
  { value: 'contractor', label: 'Contractor', icon: '📋' },
]

// Token type display config
const tokenTypeConfig = {
  ms_word: { label: 'Word Document', icon: '📄', color: 'bg-blue-100 text-blue-800' },
  ms_excel: { label: 'Excel Spreadsheet', icon: '📊', color: 'bg-green-100 text-green-800' },
  text: { label: 'Text File', icon: '📝', color: 'bg-gray-100 text-gray-800' },
  dns: { label: 'DNS Token', icon: '🌐', color: 'bg-purple-100 text-purple-800' },
  web: { label: 'Web Bug', icon: '🔗', color: 'bg-orange-100 text-orange-800' },
  windows_dir: { label: 'Windows Folder', icon: '📁', color: 'bg-yellow-100 text-yellow-800' },
  aws_keys: { label: 'AWS Credentials', icon: '🔑', color: 'bg-red-100 text-red-800' },
  qr_code: { label: 'QR Code', icon: '📱', color: 'bg-pink-100 text-pink-800' },
  pdf: { label: 'PDF Document', icon: '📕', color: 'bg-red-100 text-red-700' },
}

onMounted(async () => {
  await Promise.all([
    loadProfiles(),
    loadTemplates(),
    loadTextTemplates(),
    loadTokenTypes()
  ])
})

const loadProfiles = async () => {
  loading.value = true
  try {
    const response = await profilesApi.list()
    profiles.value = response.data
  } finally {
    loading.value = false
  }
}

const loadTemplates = async () => {
  try {
    const response = await profilesApi.templates()
    templates.value = response.data
  } catch (e) {
    console.error('Failed to load templates:', e)
  }
}

const loadTextTemplates = async () => {
  try {
    const response = await profilesApi.textTemplates()
    textTemplates.value = response.data
  } catch (e) {
    console.error('Failed to load text templates:', e)
  }
}

const loadTokenTypes = async () => {
  try {
    const response = await profilesApi.tokenTypes()
    tokenTypes.value = response.data
  } catch (e) {
    console.error('Failed to load token types:', e)
  }
}

// Computed file count for profiles
const getFileCount = (profile) => {
  return profile.file_structure?.files?.length || 0
}

const getFolderCount = (profile) => {
  return profile.file_structure?.folders?.length || 0
}

// Template selection
const openTemplateModal = () => {
  showTemplateModal.value = true
}

const selectTemplate = async (template) => {
  try {
    const response = await profilesApi.getTemplate(template.id)
    const templateData = response.data

    selectedTemplate.value = template
    newProfile.value = {
      name: templateData.name,
      description: templateData.description,
      scenario_type: template.id,
      theme: 'corporate',
      file_structure: {
        folders: templateData.folders || [],
        files: templateData.files || []
      },
      token_config: {},
      ai_prompts: {},
      label_suggestions: []
    }

    showTemplateModal.value = false
    showCreateModal.value = true
  } catch (e) {
    console.error('Failed to load template:', e)
  }
}

const createFromTemplate = async (templateId) => {
  try {
    await profilesApi.createFromTemplate(templateId)
    showTemplateModal.value = false
    await loadProfiles()
  } catch (e) {
    console.error('Failed to create from template:', e)
  }
}

// File structure management
const addFolder = () => {
  if (newFolder.value && !newProfile.value.file_structure.folders.includes(newFolder.value)) {
    newProfile.value.file_structure.folders.push(newFolder.value)
    newFolder.value = ''
  }
}

const removeFolder = (folder) => {
  const index = newProfile.value.file_structure.folders.indexOf(folder)
  if (index > -1) {
    newProfile.value.file_structure.folders.splice(index, 1)
    // Also remove files in this folder
    newProfile.value.file_structure.files = newProfile.value.file_structure.files.filter(
      f => f.folder !== folder
    )
  }
}

const addFile = () => {
  if (newFile.value.name) {
    newProfile.value.file_structure.files.push({ ...newFile.value })
    newFile.value = {
      folder: newFile.value.folder,
      name: '',
      type: 'ms_word',
      template: ''
    }
  }
}

const removeFile = (index) => {
  newProfile.value.file_structure.files.splice(index, 1)
}

const createProfile = async () => {
  try {
    await profilesApi.create(newProfile.value)
    showCreateModal.value = false
    resetForm()
    await loadProfiles()
  } catch (e) {
    console.error('Failed to create profile:', e)
  }
}

const deleteProfile = async (id) => {
  if (confirm('Are you sure you want to delete this profile?')) {
    await profilesApi.delete(id)
    await loadProfiles()
  }
}

const toggleProfile = async (profile) => {
  togglingId.value = profile.id
  try {
    await profilesApi.toggle(profile.id)
    await loadProfiles()
  } catch (e) {
    console.error('Failed to toggle profile:', e)
  } finally {
    togglingId.value = null
  }
}

const previewProfile = async (id) => {
  const response = await profilesApi.preview(id)
  previewData.value = response.data
  showPreviewModal.value = true
}

const saveProfile = async () => {
  try {
    await profilesApi.update(editingProfile.value.id, editingProfile.value)
    showEditModal.value = false
    editingProfile.value = null
    await loadProfiles()
  } catch (e) {
    console.error('Failed to update profile:', e)
  }
}

const resetForm = () => {
  newProfile.value = {
    name: '',
    description: '',
    scenario_type: 'it',
    theme: 'corporate',
    file_structure: {
      folders: [],
      files: []
    },
    token_config: {},
    ai_prompts: {},
    label_suggestions: []
  }
  selectedTemplate.value = null
}

const getTokenTypeLabel = (type) => {
  return tokenTypeConfig[type]?.label || type
}

const getTokenTypeIcon = (type) => {
  return tokenTypeConfig[type]?.icon || '📄'
}

const getTokenTypeColor = (type) => {
  return tokenTypeConfig[type]?.color || 'bg-gray-100 text-gray-800'
}

// Get unique token types used in a profile
const getUsedTokenTypes = (profile) => {
  const files = profile.file_structure?.files || []
  const types = [...new Set(files.map(f => f.type).filter(Boolean))]
  return types
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        USB Profiles
      </h1>
      <div class="flex space-x-3">
        <button
          class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          @click="openTemplateModal"
        >
          Quick Create
        </button>
        <button
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          @click="router.push('/profiles/new')"
        >
          New Profile
        </button>
      </div>
    </div>

    <div
      v-if="loading"
      class="text-center py-12"
    >
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
    </div>

    <div
      v-else
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      <div
        v-for="profile in profiles"
        :key="profile.id"
        :class="[
          'bg-white rounded-lg shadow hover:shadow-md transition-shadow',
          !profile.is_active && 'opacity-60'
        ]"
      >
        <div class="p-6">
          <div class="flex items-start justify-between">
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-medium text-gray-900">
                  {{ profile.name }}
                </h3>
                <span
                  v-if="!profile.is_active"
                  class="px-2 py-0.5 text-xs rounded-full bg-gray-200 text-gray-600"
                >
                  Disabled
                </span>
              </div>
              <span class="inline-flex items-center mt-1 px-2 py-1 text-xs rounded-full bg-primary-100 text-primary-800">
                {{ scenarioTypes.find(s => s.value === profile.scenario_type)?.icon || '📁' }}
                {{ profile.scenario_type }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span
                v-if="profile.is_system === 'true'"
                class="text-xs text-gray-400"
              >System</span>
              <!-- Toggle Switch -->
              <button
                :disabled="togglingId === profile.id"
                class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                :class="profile.is_active ? 'bg-primary-600' : 'bg-gray-200'"
                @click="toggleProfile(profile)"
              >
                <span
                  class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                  :class="profile.is_active ? 'translate-x-5' : 'translate-x-0'"
                />
              </button>
            </div>
          </div>

          <p class="mt-3 text-sm text-gray-500 line-clamp-2">
            {{ profile.description || 'No description' }}
          </p>

          <!-- File/Folder counts -->
          <div class="mt-3 flex space-x-4 text-sm text-gray-500">
            <span>📁 {{ getFolderCount(profile) }} folders</span>
            <span>📄 {{ getFileCount(profile) }} files</span>
          </div>

          <!-- Token Types Used -->
          <div class="mt-4">
            <div class="text-xs text-gray-500 mb-2">
              Token Types:
            </div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="type in getUsedTokenTypes(profile)"
                :key="type"
                :class="['px-2 py-0.5 text-xs rounded', getTokenTypeColor(type)]"
              >
                {{ getTokenTypeIcon(type) }} {{ getTokenTypeLabel(type) }}
              </span>
              <span
                v-if="getUsedTokenTypes(profile).length === 0"
                class="text-xs text-gray-400"
              >
                None configured
              </span>
            </div>
          </div>

          <div class="mt-4 pt-4 border-t flex justify-between">
            <div class="flex space-x-3">
              <button
                class="text-sm text-primary-600 hover:text-primary-700"
                @click="previewProfile(profile.id)"
              >
                Preview
              </button>
              <button
                class="text-sm text-gray-600 hover:text-gray-700"
                :disabled="profile.is_system === 'true'"
                :class="{ 'opacity-50 cursor-not-allowed': profile.is_system === 'true' }"
                @click="router.push(`/profiles/${profile.id}/edit`)"
              >
                Edit
              </button>
            </div>
            <button
              class="text-sm text-red-600 hover:text-red-700"
              :disabled="profile.is_system === 'true'"
              :class="{ 'opacity-50 cursor-not-allowed': profile.is_system === 'true' }"
              @click="deleteProfile(profile.id)"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="profiles.length === 0"
        class="col-span-full text-center py-12 text-gray-500"
      >
        No profiles yet. Create one from a template or build your own!
      </div>
    </div>

    <!-- Template Gallery Modal -->
    <div
      v-if="showTemplateModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-medium">
            Select a Template
          </h2>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="showTemplateModal = false"
          >
            <svg
              class="w-6 h-6"
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
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="template in templates"
            :key="template.id"
            class="border rounded-lg p-4 hover:border-primary-500 hover:shadow-md cursor-pointer transition-all"
            @click="selectTemplate(template)"
          >
            <div class="flex items-center mb-2">
              <span class="text-2xl mr-2">{{ scenarioTypes.find(s => s.value === template.id)?.icon || '📁' }}</span>
              <h3 class="font-medium">
                {{ template.name }}
              </h3>
            </div>
            <p class="text-sm text-gray-500 mb-3">
              {{ template.description }}
            </p>
            <div class="flex space-x-3 text-xs text-gray-400">
              <span>📁 {{ template.folder_count }} folders</span>
              <span>📄 {{ template.file_count }} files</span>
            </div>
            <button
              class="mt-3 w-full text-sm px-3 py-1.5 bg-primary-100 text-primary-700 rounded hover:bg-primary-200"
              @click.stop="createFromTemplate(template.id)"
            >
              Quick Create
            </button>
          </div>
        </div>

        <div
          v-if="templates.length === 0"
          class="text-center py-8 text-gray-500"
        >
          No templates available
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div class="p-6 border-b">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-medium">
              {{ selectedTemplate ? `Create from ${selectedTemplate.name}` : 'Create Profile' }}
            </h2>
            <button
              class="text-gray-400 hover:text-gray-600"
              @click="showCreateModal = false; resetForm()"
            >
              <svg
                class="w-6 h-6"
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
          </div>
        </div>

        <div class="p-6 overflow-y-auto flex-1">
          <form
            class="space-y-6"
            @submit.prevent="createProfile"
          >
            <!-- Basic Info -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Profile Name</label>
                <input
                  v-model="newProfile.name"
                  type="text"
                  required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                >
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Scenario Type</label>
                <select
                  v-model="newProfile.scenario_type"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option
                    v-for="type in scenarioTypes"
                    :key="type.value"
                    :value="type.value"
                  >
                    {{ type.icon }} {{ type.label }}
                  </option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                v-model="newProfile.description"
                rows="2"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <!-- Folder Structure -->
            <div class="border rounded-lg p-4 bg-gray-50">
              <h3 class="font-medium mb-3">
                Folder Structure
              </h3>

              <div class="flex gap-2 mb-3">
                <input
                  v-model="newFolder"
                  type="text"
                  placeholder="New folder name..."
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                  @keyup.enter="addFolder"
                >
                <button
                  type="button"
                  class="px-3 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-sm"
                  @click="addFolder"
                >
                  Add Folder
                </button>
              </div>

              <div class="flex flex-wrap gap-2">
                <span
                  v-for="folder in newProfile.file_structure.folders"
                  :key="folder"
                  class="inline-flex items-center px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm"
                >
                  📁 {{ folder }}
                  <button
                    type="button"
                    class="ml-2 text-yellow-600 hover:text-yellow-800"
                    @click="removeFolder(folder)"
                  >
                    &times;
                  </button>
                </span>
                <span
                  v-if="newProfile.file_structure.folders.length === 0"
                  class="text-sm text-gray-400"
                >
                  No folders defined
                </span>
              </div>
            </div>

            <!-- File Configuration -->
            <div class="border rounded-lg p-4">
              <h3 class="font-medium mb-3">
                Files &amp; Tokens
              </h3>

              <!-- Add new file -->
              <div class="grid grid-cols-4 gap-2 mb-4 p-3 bg-gray-50 rounded">
                <select
                  v-model="newFile.folder"
                  class="px-2 py-1.5 border border-gray-300 rounded text-sm"
                >
                  <option value="">
                    (Root)
                  </option>
                  <option
                    v-for="folder in newProfile.file_structure.folders"
                    :key="folder"
                    :value="folder"
                  >
                    {{ folder }}
                  </option>
                </select>
                <input
                  v-model="newFile.name"
                  type="text"
                  placeholder="filename.docx"
                  class="px-2 py-1.5 border border-gray-300 rounded text-sm"
                >
                <select
                  v-model="newFile.type"
                  class="px-2 py-1.5 border border-gray-300 rounded text-sm"
                >
                  <option value="ms_word">
                    Word Document
                  </option>
                  <option value="ms_excel">
                    Excel Spreadsheet
                  </option>
                  <option value="text">
                    Text File
                  </option>
                  <option value="pdf">
                    PDF Document
                  </option>
                  <option value="windows_dir">
                    Windows Folder
                  </option>
                  <option value="aws_keys">
                    AWS Credentials
                  </option>
                  <option value="qr_code">
                    QR Code
                  </option>
                </select>
                <button
                  type="button"
                  class="px-3 py-1.5 bg-primary-600 text-white rounded hover:bg-primary-700 text-sm"
                  @click="addFile"
                >
                  Add File
                </button>
              </div>

              <!-- Text template selection (shows when text type selected) -->
              <div
                v-if="newFile.type === 'text'"
                class="mb-4 p-3 bg-blue-50 rounded"
              >
                <label class="block text-sm font-medium text-gray-700 mb-2">Text Template</label>
                <select
                  v-model="newFile.template"
                  class="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                >
                  <option value="">
                    Select a template...
                  </option>
                  <option
                    v-for="tmpl in textTemplates"
                    :key="tmpl.id"
                    :value="tmpl.id"
                  >
                    {{ tmpl.filename }} - {{ tmpl.preview }}
                  </option>
                </select>
              </div>

              <!-- Files list -->
              <div class="space-y-2 max-h-64 overflow-y-auto">
                <div
                  v-for="(file, index) in newProfile.file_structure.files"
                  :key="index"
                  class="flex items-center justify-between p-2 bg-white border rounded"
                >
                  <div class="flex items-center space-x-3">
                    <span :class="['px-2 py-0.5 text-xs rounded', getTokenTypeColor(file.type)]">
                      {{ getTokenTypeIcon(file.type) }}
                    </span>
                    <span class="text-sm">
                      <span class="text-gray-400">{{ file.folder ? file.folder + '/' : '' }}</span>
                      <span class="font-medium">{{ file.name }}</span>
                    </span>
                    <span
                      v-if="file.template"
                      class="text-xs text-gray-400"
                    >({{ file.template }})</span>
                  </div>
                  <button
                    type="button"
                    class="text-red-500 hover:text-red-700"
                    @click="removeFile(index)"
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
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
                <div
                  v-if="newProfile.file_structure.files.length === 0"
                  class="text-center py-4 text-sm text-gray-400"
                >
                  No files configured. Add files above.
                </div>
              </div>
            </div>

            <!-- Label Suggestions -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Label Suggestions (for USB drives)</label>
              <input
                type="text"
                :value="newProfile.label_suggestions.join(', ')"
                placeholder="IT Backup, Network Config, Confidential..."
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                @input="newProfile.label_suggestions = $event.target.value.split(',').map(s => s.trim()).filter(Boolean)"
              >
            </div>
          </form>
        </div>

        <div class="p-6 border-t bg-gray-50 flex justify-end space-x-3">
          <button
            type="button"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
            @click="showCreateModal = false; resetForm()"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            @click="createProfile"
          >
            Create Profile
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div
      v-if="showEditModal && editingProfile"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div class="p-6 border-b">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-medium">
              Edit Profile: {{ editingProfile.name }}
            </h2>
            <button
              class="text-gray-400 hover:text-gray-600"
              @click="showEditModal = false"
            >
              <svg
                class="w-6 h-6"
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
          </div>
        </div>

        <div class="p-6 overflow-y-auto flex-1">
          <div class="space-y-6">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Profile Name</label>
                <input
                  v-model="editingProfile.name"
                  type="text"
                  required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                >
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Scenario Type</label>
                <select
                  v-model="editingProfile.scenario_type"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option
                    v-for="type in scenarioTypes"
                    :key="type.value"
                    :value="type.value"
                  >
                    {{ type.icon }} {{ type.label }}
                  </option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                v-model="editingProfile.description"
                rows="2"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <!-- Current Files Display -->
            <div class="border rounded-lg p-4">
              <h3 class="font-medium mb-3">
                Current Files
              </h3>
              <div class="space-y-2">
                <div
                  v-for="(file, index) in editingProfile.file_structure?.files || []"
                  :key="index"
                  class="flex items-center justify-between p-2 bg-gray-50 rounded"
                >
                  <div class="flex items-center space-x-3">
                    <span :class="['px-2 py-0.5 text-xs rounded', getTokenTypeColor(file.type)]">
                      {{ getTokenTypeIcon(file.type) }} {{ getTokenTypeLabel(file.type) }}
                    </span>
                    <span class="text-sm">
                      {{ file.folder ? file.folder + '/' : '' }}{{ file.name }}
                    </span>
                  </div>
                </div>
                <div
                  v-if="!editingProfile.file_structure?.files?.length"
                  class="text-sm text-gray-400 text-center py-4"
                >
                  No files configured
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t bg-gray-50 flex justify-end space-x-3">
          <button
            type="button"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
            @click="showEditModal = false"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            @click="saveProfile"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <div
      v-if="showPreviewModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-medium">
            Profile Preview
          </h2>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="showPreviewModal = false"
          >
            <svg
              class="w-6 h-6"
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
        </div>

        <div
          v-if="previewData"
          class="space-y-4"
        >
          <!-- File tree visualization -->
          <div>
            <div class="text-sm font-medium text-gray-700 mb-2">
              File Structure:
            </div>
            <div class="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm">
              <div
                v-for="file in previewData.files"
                :key="file.path"
                class="flex items-center space-x-2"
              >
                <span
                  v-if="file.type === 'folder'"
                  class="text-yellow-400"
                >📁</span>
                <span
                  v-else
                  :class="{'text-blue-400': file.token_type === 'ms_word', 'text-green-400': file.token_type === 'ms_excel', 'text-gray-400': file.token_type === 'text'}"
                >
                  {{ getTokenTypeIcon(file.token_type) }}
                </span>
                <span>{{ file.path }}</span>
                <span
                  v-if="file.token_type"
                  class="text-xs text-gray-500"
                >[{{ file.token_type }}]</span>
              </div>
              <div
                v-if="previewData.files.length === 0"
                class="text-gray-500"
              >
                No files
              </div>
            </div>
          </div>

          <!-- Token summary -->
          <div>
            <div class="text-sm font-medium text-gray-700 mb-2">
              Token Summary:
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(count, type) in previewData.token_summary"
                :key="type"
                :class="['px-3 py-1 rounded-full text-sm', getTokenTypeColor(type)]"
              >
                {{ getTokenTypeIcon(type) }} {{ type }}: {{ count }}
              </span>
              <span
                v-if="Object.keys(previewData.token_summary || {}).length === 0"
                class="text-sm text-gray-400"
              >
                No tokens configured
              </span>
            </div>
          </div>
        </div>

        <div class="mt-6 flex justify-end">
          <button
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            @click="showPreviewModal = false"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
