<script setup>
import { ref, computed, watch } from 'vue'
import { useProfileWizardStore } from '@/stores/profileWizard'
import FileUploader from './FileUploader.vue'
import TemplateEditor from './TemplateEditor.vue'
import { profilesApi } from '@/services/api'

const store = useProfileWizardStore()

// Content editor modal state
const showContentEditor = ref(false)
const editingFile = ref(null)
const editingFileContent = ref('')
const editingFileType = ref('template') // 'template' or 'uploaded'
const isSavingContent = ref(false)

const newFile = ref({
  name: '',
  folder: '',
  token_type: 'ms_word'
})

const editingIndex = ref(null)
const activeTab = ref('template') // 'template' or 'upload'
const selectedUploadFolder = ref('')

// Watch for profile editing mode to load uploaded files
watch(() => store.editingProfileId, async (profileId) => {
  if (profileId) {
    await store.loadUploadedFiles(profileId)
  }
}, { immediate: true })

const tokenTypes = [
  { value: 'ms_word', label: 'Word Document', icon: '📄', extension: '.docx', color: 'bg-blue-100 text-blue-800' },
  { value: 'ms_excel', label: 'Excel Spreadsheet', icon: '📊', extension: '.xlsx', color: 'bg-green-100 text-green-800' },
  { value: 'pdf', label: 'PDF Document', icon: '📕', extension: '.pdf', color: 'bg-red-100 text-red-700' },
  { value: 'text', label: 'Text File', icon: '📝', extension: '.txt', color: 'bg-gray-100 text-gray-800' },
  { value: 'windows_dir', label: 'Folder Token', icon: '📁', extension: 'desktop.ini', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'aws_keys', label: 'AWS Credentials', icon: '🔑', extension: '.txt', color: 'bg-orange-100 text-orange-800' },
  { value: 'web', label: 'Web Bug (Link)', icon: '🔗', extension: '.url', color: 'bg-purple-100 text-purple-800' },
  { value: 'qr_code', label: 'QR Code Image', icon: '📱', extension: '.png', color: 'bg-pink-100 text-pink-800' },
]

const folders = computed(() => store.folders)
const files = computed(() => store.files)
const uploadedFiles = computed(() => store.uploadedFiles)
const canUpload = computed(() => store.isEditing && store.editingProfileId)

const getTokenType = (typeValue) => {
  return tokenTypes.find(t => t.value === typeValue) || tokenTypes[0]
}

const addFile = () => {
  if (!newFile.value.name.trim()) return

  store.addFile({
    name: newFile.value.name.trim(),
    folder: newFile.value.folder,
    token_type: newFile.value.token_type
  })

  // Reset form but keep the folder selection
  newFile.value = {
    name: '',
    folder: newFile.value.folder,
    token_type: 'ms_word'
  }
}

const removeFile = (index) => {
  store.removeFile(index)
}

const startEditing = (index) => {
  editingIndex.value = index
}

const updateFile = (index, field, value) => {
  store.updateFile(index, { [field]: value })
}

const stopEditing = () => {
  editingIndex.value = null
}

// Group files by folder for display
const filesByFolder = computed(() => {
  const grouped = { '': [] }

  // Initialize groups for all folders
  folders.value.forEach(f => {
    grouped[f.path] = []
  })

  // Group files
  files.value.forEach((file, index) => {
    const folder = file.folder || ''
    if (!grouped[folder]) {
      grouped[folder] = []
    }
    grouped[folder].push({ ...file, index })
  })

  return grouped
})

// Token count summary
const tokenSummary = computed(() => {
  const summary = {}
  files.value.forEach(file => {
    if (file.token_type) {
      summary[file.token_type] = (summary[file.token_type] || 0) + 1
    }
  })
  // Add uploaded files with token types
  uploadedFiles.value.forEach(file => {
    if (file.token_type) {
      summary[file.token_type] = (summary[file.token_type] || 0) + 1
    }
  })
  return summary
})

// Uploaded file handlers
const onFileUploaded = (file) => {
  store.addUploadedFile(file)
}

const onUploadError = (error) => {
  console.error('Upload error:', error)
}

const removeUploadedFile = async (fileId) => {
  if (!confirm('Delete this uploaded file?')) return
  try {
    await store.removeUploadedFile(store.editingProfileId, fileId)
  } catch (error) {
    console.error('Failed to delete file:', error)
  }
}

// Get file type icon and color
const getFileTypeDisplay = (file) => {
  if (file.file_type === 'static') {
    return { icon: '🖼️', label: 'Static Image', color: 'bg-purple-100 text-purple-800' }
  }
  if (file.token_type) {
    return getTokenType(file.token_type)
  }
  return { icon: '📎', label: 'File', color: 'bg-gray-100 text-gray-800' }
}

// Format file size
const formatFileSize = (bytes) => {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Check if file type supports content editing
const canEditContent = (file, fileType) => {
  if (fileType === 'template') {
    // Template files can always have content edited
    const tokenType = file.token_type
    return ['text', 'ms_word', 'ms_excel', 'pdf', 'aws_keys'].includes(tokenType)
  }
  if (fileType === 'uploaded') {
    // Uploaded files with template or document type can be edited
    return file.file_type === 'template' ||
           ['text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/pdf'].includes(file.mime_type)
  }
  return false
}

// Open content editor for a file
const openContentEditor = (file, fileType) => {
  editingFile.value = file
  editingFileType.value = fileType

  if (fileType === 'template') {
    // Get content from template file or use default
    editingFileContent.value = file.content || file.custom_content || ''
  } else if (fileType === 'uploaded') {
    // Get content from uploaded file's custom_content
    editingFileContent.value = file.custom_content || ''
  }

  showContentEditor.value = true
}

// Save content from editor
const saveFileContent = async () => {
  if (!editingFile.value) return

  isSavingContent.value = true

  try {
    if (editingFileType.value === 'template') {
      // Update template file content in store
      const index = editingFile.value.index !== undefined ? editingFile.value.index :
                    files.value.findIndex(f => f.name === editingFile.value.name && f.folder === editingFile.value.folder)
      if (index >= 0) {
        store.updateFile(index, {
          content: editingFileContent.value,
          custom_content: editingFileContent.value
        })
      }
    } else if (editingFileType.value === 'uploaded' && store.editingProfileId) {
      // Update uploaded file content via API
      await profilesApi.updateFile(store.editingProfileId, editingFile.value.id, {
        custom_content: editingFileContent.value
      })
      // Refresh uploaded files
      await store.loadUploadedFiles(store.editingProfileId)
    }

    showContentEditor.value = false
    editingFile.value = null
    editingFileContent.value = ''
  } catch (error) {
    console.error('Failed to save content:', error)
    alert('Failed to save content: ' + (error.message || 'Unknown error'))
  } finally {
    isSavingContent.value = false
  }
}

// Close content editor without saving
const closeContentEditor = () => {
  if (editingFileContent.value && !confirm('Discard unsaved changes?')) return
  showContentEditor.value = false
  editingFile.value = null
  editingFileContent.value = ''
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-lg font-medium text-gray-900">
        Step 3: Files &amp; Tokens
      </h2>
      <p class="mt-1 text-sm text-gray-500">
        Add files and configure token types for each. These tokens will trigger alerts when accessed.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Add File Form -->
      <div class="lg:col-span-1">
        <div class="border border-gray-200 rounded-lg">
          <!-- Tabs -->
          <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <div class="flex space-x-4">
              <button
                type="button"
                class="text-sm font-medium pb-1 border-b-2 transition-colors"
                :class="activeTab === 'template' ? 'text-primary-600 border-primary-600' : 'text-gray-500 border-transparent hover:text-gray-700'"
                @click="activeTab = 'template'"
              >
                Template File
              </button>
              <button
                type="button"
                class="text-sm font-medium pb-1 border-b-2 transition-colors"
                :class="activeTab === 'upload' ? 'text-primary-600 border-primary-600' : 'text-gray-500 border-transparent hover:text-gray-700'"
                @click="activeTab = 'upload'"
              >
                Upload File
              </button>
            </div>
          </div>

          <!-- Template File Tab -->
          <div v-show="activeTab === 'template'" class="p-4 space-y-4">
            <!-- File name -->
            <div>
              <label class="block text-sm font-medium text-gray-700">File Name</label>
              <input
                v-model="newFile.name"
                type="text"
                placeholder="e.g., Salaries_2024.xlsx"
                class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                @keyup.enter="addFile"
              >
            </div>

            <!-- Folder selection -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Folder</label>
              <select
                v-model="newFile.folder"
                class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">
                  (Root)
                </option>
                <option
                  v-for="folder in folders"
                  :key="folder.path"
                  :value="folder.path"
                >
                  {{ folder.path }}
                </option>
              </select>
            </div>

            <!-- Token type -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Token Type</label>
              <select
                v-model="newFile.token_type"
                class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option
                  v-for="type in tokenTypes"
                  :key="type.value"
                  :value="type.value"
                >
                  {{ type.icon }} {{ type.label }}
                </option>
              </select>
              <p class="mt-1 text-xs text-gray-500">
                {{ getTokenType(newFile.token_type).extension }}
              </p>
            </div>

            <button
              type="button"
              :disabled="!newFile.name.trim()"
              class="w-full px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              @click="addFile"
            >
              Add File
            </button>
          </div>

          <!-- Upload File Tab -->
          <div v-show="activeTab === 'upload'" class="p-4 space-y-4">
            <template v-if="canUpload">
              <!-- Target folder -->
              <div>
                <label class="block text-sm font-medium text-gray-700">Target Folder</label>
                <select
                  v-model="selectedUploadFolder"
                  class="mt-1 block w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">
                    (Root)
                  </option>
                  <option
                    v-for="folder in folders"
                    :key="folder.path"
                    :value="folder.path"
                  >
                    {{ folder.path }}
                  </option>
                </select>
              </div>

              <!-- File uploader -->
              <FileUploader
                :profile-id="store.editingProfileId"
                :folder="selectedUploadFolder"
                @file-uploaded="onFileUploaded"
                @error="onUploadError"
              />

              <p class="text-xs text-gray-500">
                Documents (.docx, .xlsx, .pdf) will have tokens automatically embedded.
                Images (.png, .jpg, .gif) are included as-is.
              </p>
            </template>

            <template v-else>
              <div class="text-center py-6 text-gray-500">
                <svg class="w-12 h-12 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p class="mt-2 text-sm font-medium">Save profile first</p>
                <p class="text-xs">You need to save this profile before uploading files.</p>
              </div>
            </template>
          </div>
        </div>

        <!-- Token Summary -->
        <div
          v-if="Object.keys(tokenSummary).length > 0"
          class="mt-4 border border-gray-200 rounded-lg"
        >
          <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h3 class="text-sm font-medium text-gray-700">
              Token Summary
            </h3>
          </div>
          <div class="p-4">
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(count, type) in tokenSummary"
                :key="type"
                :class="['px-2 py-1 text-xs rounded-full', getTokenType(type).color]"
              >
                {{ getTokenType(type).icon }} {{ getTokenType(type).label }}: {{ count }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- File List -->
      <div class="lg:col-span-2">
        <div class="border border-gray-200 rounded-lg">
          <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
            <h3 class="text-sm font-medium text-gray-700">
              Files ({{ files.length + uploadedFiles.length }})
            </h3>
            <div v-if="uploadedFiles.length > 0" class="text-xs text-gray-500">
              {{ uploadedFiles.length }} uploaded
            </div>
          </div>

          <div class="divide-y divide-gray-200 max-h-[500px] overflow-y-auto">
            <!-- Files grouped by folder -->
            <template
              v-for="(folderFiles, folderPath) in filesByFolder"
              :key="folderPath"
            >
              <div v-if="folderFiles.length > 0">
                <!-- Folder header -->
                <div class="px-4 py-2 bg-gray-50 text-sm font-medium text-gray-600 sticky top-0">
                  <span class="mr-2">📁</span>
                  {{ folderPath || '(Root)' }}
                </div>

                <!-- Files in folder -->
                <div
                  v-for="file in folderFiles"
                  :key="file.index"
                  class="px-4 py-3 hover:bg-gray-50 group"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center flex-1 min-w-0">
                      <!-- Token type badge -->
                      <span
                        :class="['px-2 py-1 text-xs rounded mr-3', getTokenType(file.token_type).color]"
                      >
                        {{ getTokenType(file.token_type).icon }}
                      </span>

                      <!-- File info -->
                      <div class="flex-1 min-w-0">
                        <template v-if="editingIndex === file.index">
                          <div class="flex items-center gap-2">
                            <input
                              :value="file.name"
                              class="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                              @input="updateFile(file.index, 'name', $event.target.value)"
                              @keyup.enter="stopEditing"
                              @blur="stopEditing"
                            >
                            <select
                              :value="file.token_type"
                              class="px-2 py-1 text-sm border border-gray-300 rounded"
                              @change="updateFile(file.index, 'token_type', $event.target.value)"
                            >
                              <option
                                v-for="type in tokenTypes"
                                :key="type.value"
                                :value="type.value"
                              >
                                {{ type.icon }} {{ type.label }}
                              </option>
                            </select>
                          </div>
                        </template>
                        <template v-else>
                          <p class="text-sm font-medium text-gray-900 truncate">
                            {{ file.name }}
                          </p>
                          <p class="text-xs text-gray-500">
                            {{ getTokenType(file.token_type).label }}
                          </p>
                        </template>
                      </div>
                    </div>

                    <!-- Actions -->
                    <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        v-if="canEditContent(file, 'template')"
                        type="button"
                        class="p-1 text-gray-400 hover:text-primary-600"
                        title="Edit Content & Tokens"
                        @click="openContentEditor(file, 'template')"
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
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                      </button>
                      <button
                        v-if="editingIndex !== file.index"
                        type="button"
                        class="p-1 text-gray-400 hover:text-gray-600"
                        title="Edit Name/Type"
                        @click="startEditing(file.index)"
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
                            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                          />
                        </svg>
                      </button>
                      <button
                        type="button"
                        class="p-1 text-gray-400 hover:text-red-600"
                        title="Remove"
                        @click="removeFile(file.index)"
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
                  </div>
                </div>
              </div>
            </template>

            <!-- Uploaded Files Section -->
            <template v-if="uploadedFiles.length > 0">
              <div class="px-4 py-2 bg-green-50 text-sm font-medium text-green-700 sticky top-0 border-t border-green-100">
                <span class="mr-2">📤</span>
                Uploaded Files ({{ uploadedFiles.length }})
              </div>

              <div
                v-for="file in uploadedFiles"
                :key="file.id"
                class="px-4 py-3 hover:bg-gray-50 group"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center flex-1 min-w-0">
                    <!-- File type badge -->
                    <span
                      :class="['px-2 py-1 text-xs rounded mr-3', getFileTypeDisplay(file).color]"
                    >
                      {{ getFileTypeDisplay(file).icon }}
                    </span>

                    <!-- File info -->
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-900 truncate">
                        {{ file.filename }}
                      </p>
                      <p class="text-xs text-gray-500">
                        {{ getFileTypeDisplay(file).label }}
                        <span v-if="file.file_size_bytes" class="ml-2">
                          {{ formatFileSize(file.file_size_bytes) }}
                        </span>
                        <span v-if="file.folder" class="ml-2 text-gray-400">
                          in {{ file.folder }}
                        </span>
                      </p>
                    </div>
                  </div>

                  <!-- Actions -->
                  <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      v-if="canEditContent(file, 'uploaded')"
                      type="button"
                      class="p-1 text-gray-400 hover:text-primary-600"
                      title="Edit Content & Tokens"
                      @click="openContentEditor(file, 'uploaded')"
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
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="p-1 text-gray-400 hover:text-red-600"
                      title="Remove"
                      @click="removeUploadedFile(file.id)"
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
                </div>
              </div>
            </template>

            <!-- Empty state -->
            <div
              v-if="files.length === 0 && uploadedFiles.length === 0"
              class="px-4 py-12 text-center text-gray-500"
            >
              <svg
                class="w-12 h-12 mx-auto text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p class="mt-2 text-sm">
                No files configured
              </p>
              <p class="text-xs text-gray-400">
                Add files using the form on the left
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tip -->
    <div class="mt-4 p-3 bg-blue-50 rounded-lg">
      <div class="flex">
        <svg
          class="w-5 h-5 text-blue-400 mr-2 flex-shrink-0"
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
        <p class="text-sm text-blue-700">
          <strong>Tip:</strong> Click the document icon on a file to edit its content and insert token placeholders like
          <code class="bg-blue-100 px-1 rounded">{canary_token-URL}</code>.
        </p>
      </div>
    </div>

    <!-- Content Editor Modal -->
    <Teleport to="body">
      <div
        v-if="showContentEditor"
        class="fixed inset-0 z-50 overflow-y-auto"
        aria-labelledby="modal-title"
        role="dialog"
        aria-modal="true"
      >
        <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <!-- Background overlay -->
          <div
            class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
            aria-hidden="true"
            @click="closeContentEditor"
          />

          <!-- Modal panel -->
          <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
            <!-- Header -->
            <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-medium text-gray-900">
                    Edit Content & Tokens
                  </h3>
                  <p class="mt-1 text-sm text-gray-500">
                    {{ editingFile?.name || editingFile?.filename || 'File' }}
                  </p>
                </div>
                <button
                  type="button"
                  class="text-gray-400 hover:text-gray-600"
                  @click="closeContentEditor"
                >
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Content -->
            <div class="px-6 py-4 max-h-[70vh] overflow-y-auto">
              <TemplateEditor
                v-model="editingFileContent"
                :filename="editingFile?.name || editingFile?.filename || 'file.txt'"
                :url-shortener-enabled="store.content.url_shortener.enabled"
                :url-shortener-config="store.content.url_shortener"
              />
            </div>

            <!-- Footer -->
            <div class="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                type="button"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                @click="closeContentEditor"
              >
                Cancel
              </button>
              <button
                type="button"
                class="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:bg-gray-400"
                :disabled="isSavingContent"
                @click="saveFileContent"
              >
                <span v-if="isSavingContent">Saving...</span>
                <span v-else>Save Content</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
