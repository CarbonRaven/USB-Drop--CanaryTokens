<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue'

const props = defineProps({
  folders: {
    type: Array,
    default: () => []
  },
  files: {
    type: Array,
    default: () => []
  },
  uploadedFiles: {
    type: Array,
    default: () => []
  },
  selectedFile: {
    type: Object,
    default: null
  },
  tokenTypes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'select-file',
  'select-folder',
  'update-file-token',
  'remove-file',
  'reorder-files',
  'drop-token'
])

const expandedFolders = ref(new Set())
const dragOverTarget = ref(null)
const draggedItem = ref(null)

// Toggle folder expansion
const toggleFolder = (folderPath) => {
  if (expandedFolders.value.has(folderPath)) {
    expandedFolders.value.delete(folderPath)
  } else {
    expandedFolders.value.add(folderPath)
  }
}

// Check if folder is expanded
const isFolderExpanded = (folderPath) => {
  return expandedFolders.value.has(folderPath)
}

// Get files in a specific folder
const getFilesInFolder = (folderPath) => {
  const templateFiles = props.files.filter(f => (f.folder || '') === folderPath)
  const uploaded = props.uploadedFiles.filter(f => (f.folder || '') === folderPath)
  return [...templateFiles.map((f, i) => ({ ...f, _type: 'template', _index: i })),
          ...uploaded.map(f => ({ ...f, _type: 'uploaded' }))]
}

// Get files in root (no folder)
const rootFiles = computed(() => getFilesInFolder(''))

// Get token type display info
const getTokenDisplay = (tokenType) => {
  const type = props.tokenTypes.find(t => t.value === tokenType)
  return type || { icon: '📄', label: 'File', color: 'bg-gray-100 text-gray-800' }
}

// Get file icon based on type
const getFileIcon = (file) => {
  if (file._type === 'uploaded') {
    if (file.file_type === 'static') return '🖼️'
    if (file.file_type === 'shortcut') return '🔗'
    if (file.file_type === 'template') return '📝'
  }
  if (file.token_type) {
    return getTokenDisplay(file.token_type).icon
  }
  return '📄'
}

// Handle file selection
const selectFile = (file) => {
  emit('select-file', file)
}

// Handle folder selection
const selectFolder = (folder) => {
  emit('select-folder', folder)
}

// Handle drag start
const onDragStart = (event, item, type) => {
  draggedItem.value = { item, type }
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({ item, type }))
}

// Handle drag over
const onDragOver = (event, target) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  dragOverTarget.value = target
}

// Handle drag leave
const onDragLeave = () => {
  dragOverTarget.value = null
}

// Handle drop on file (assign token)
const onDropOnFile = (event, file) => {
  event.preventDefault()
  dragOverTarget.value = null

  try {
    const data = JSON.parse(event.dataTransfer.getData('text/plain'))
    if (data.type === 'token') {
      emit('drop-token', { file, tokenType: data.item.value })
    }
  } catch (e) {
    // Check if it's from TokenPalette
    const tokenType = event.dataTransfer.getData('token-type')
    if (tokenType) {
      emit('drop-token', { file, tokenType })
    }
  }

  draggedItem.value = null
}

// Handle drop on folder (move file to folder)
const onDropOnFolder = (event, folder) => {
  event.preventDefault()
  dragOverTarget.value = null
  draggedItem.value = null
}

// Remove token from file
const removeToken = (file, event) => {
  event.stopPropagation()
  emit('update-file-token', { file, tokenType: null })
}

// Remove file
const removeFile = (file, event) => {
  event.stopPropagation()
  emit('remove-file', file)
}
</script>

<template>
  <div class="visual-file-tree border border-gray-200 rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
      <div class="flex items-center">
        <svg class="w-5 h-5 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
        <span class="text-sm font-medium text-gray-700">USB Drive Structure</span>
      </div>
      <span class="text-xs text-gray-500">
        {{ files.length + uploadedFiles.length }} files
      </span>
    </div>

    <!-- Tree Content -->
    <div class="p-2 max-h-[400px] overflow-y-auto">
      <!-- Root level -->
      <div class="space-y-1">
        <!-- Root indicator -->
        <div class="flex items-center px-2 py-1 text-sm text-gray-600 font-medium">
          <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
          </svg>
          USB Drive (root)
        </div>

        <!-- Root files -->
        <div
          v-for="file in rootFiles"
          :key="file._type + '-' + (file.id || file._index)"
          class="ml-6 flex items-center px-2 py-1.5 rounded cursor-pointer group transition-colors"
          :class="{
            'bg-primary-50 border border-primary-200': selectedFile === file,
            'hover:bg-gray-50': selectedFile !== file,
            'bg-blue-50 border-2 border-blue-300 border-dashed': dragOverTarget === file
          }"
          draggable="true"
          @click="selectFile(file)"
          @dragstart="onDragStart($event, file, 'file')"
          @dragover="onDragOver($event, file)"
          @dragleave="onDragLeave"
          @drop="onDropOnFile($event, file)"
        >
          <!-- File icon -->
          <span class="mr-2 text-sm">{{ getFileIcon(file) }}</span>

          <!-- File name -->
          <span class="flex-1 text-sm text-gray-700 truncate">
            {{ file.name || file.filename }}
          </span>

          <!-- Token badge -->
          <span
            v-if="file.token_type"
            :class="['px-1.5 py-0.5 text-xs rounded mr-2', getTokenDisplay(file.token_type).color]"
          >
            {{ getTokenDisplay(file.token_type).label }}
          </span>

          <!-- Uploaded badge -->
          <span
            v-if="file._type === 'uploaded'"
            class="px-1.5 py-0.5 text-xs rounded bg-green-100 text-green-700 mr-2"
          >
            uploaded
          </span>

          <!-- Actions -->
          <div class="opacity-0 group-hover:opacity-100 flex items-center space-x-1">
            <button
              v-if="file.token_type && file._type === 'template'"
              type="button"
              class="p-1 text-gray-400 hover:text-orange-500"
              title="Remove token"
              @click="removeToken(file, $event)"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </button>
            <button
              type="button"
              class="p-1 text-gray-400 hover:text-red-500"
              title="Remove file"
              @click="removeFile(file, $event)"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Folders -->
        <div
          v-for="folder in folders"
          :key="folder.path"
          class="ml-4"
        >
          <!-- Folder header -->
          <div
            class="flex items-center px-2 py-1.5 rounded cursor-pointer hover:bg-gray-50 group"
            :class="{
              'bg-yellow-50 border-2 border-yellow-300 border-dashed': dragOverTarget === folder
            }"
            @click="toggleFolder(folder.path)"
            @dragover="onDragOver($event, folder)"
            @dragleave="onDragLeave"
            @drop="onDropOnFolder($event, folder)"
          >
            <!-- Expand/collapse icon -->
            <svg
              class="w-4 h-4 mr-1 text-gray-400 transition-transform"
              :class="{ 'rotate-90': isFolderExpanded(folder.path) }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>

            <!-- Folder icon -->
            <span class="mr-2">{{ isFolderExpanded(folder.path) ? '📂' : '📁' }}</span>

            <!-- Folder name -->
            <span class="flex-1 text-sm font-medium text-gray-700">{{ folder.path }}</span>

            <!-- Folder token indicator -->
            <span
              v-if="folder.has_folder_token"
              class="px-1.5 py-0.5 text-xs rounded bg-yellow-100 text-yellow-800"
            >
              token
            </span>

            <!-- File count -->
            <span class="ml-2 text-xs text-gray-400">
              {{ getFilesInFolder(folder.path).length }} files
            </span>
          </div>

          <!-- Folder contents -->
          <div
            v-show="isFolderExpanded(folder.path)"
            class="ml-4 mt-1 space-y-1"
          >
            <div
              v-for="file in getFilesInFolder(folder.path)"
              :key="file._type + '-' + (file.id || file._index)"
              class="flex items-center px-2 py-1.5 rounded cursor-pointer group transition-colors"
              :class="{
                'bg-primary-50 border border-primary-200': selectedFile === file,
                'hover:bg-gray-50': selectedFile !== file,
                'bg-blue-50 border-2 border-blue-300 border-dashed': dragOverTarget === file
              }"
              draggable="true"
              @click="selectFile(file)"
              @dragstart="onDragStart($event, file, 'file')"
              @dragover="onDragOver($event, file)"
              @dragleave="onDragLeave"
              @drop="onDropOnFile($event, file)"
            >
              <!-- File icon -->
              <span class="mr-2 text-sm">{{ getFileIcon(file) }}</span>

              <!-- File name -->
              <span class="flex-1 text-sm text-gray-700 truncate">
                {{ file.name || file.filename }}
              </span>

              <!-- Token badge -->
              <span
                v-if="file.token_type"
                :class="['px-1.5 py-0.5 text-xs rounded mr-2', getTokenDisplay(file.token_type).color]"
              >
                {{ getTokenDisplay(file.token_type).label }}
              </span>

              <!-- Uploaded badge -->
              <span
                v-if="file._type === 'uploaded'"
                class="px-1.5 py-0.5 text-xs rounded bg-green-100 text-green-700 mr-2"
              >
                uploaded
              </span>

              <!-- Actions -->
              <div class="opacity-0 group-hover:opacity-100 flex items-center space-x-1">
                <button
                  v-if="file.token_type && file._type === 'template'"
                  type="button"
                  class="p-1 text-gray-400 hover:text-orange-500"
                  title="Remove token"
                  @click="removeToken(file, $event)"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="p-1 text-gray-400 hover:text-red-500"
                  title="Remove file"
                  @click="removeFile(file, $event)"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Empty folder message -->
            <div
              v-if="getFilesInFolder(folder.path).length === 0"
              class="px-2 py-2 text-xs text-gray-400 italic"
            >
              Empty folder - drag files here
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div
          v-if="folders.length === 0 && rootFiles.length === 0"
          class="px-4 py-8 text-center text-gray-400"
        >
          <svg class="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="text-sm">No files yet</p>
          <p class="text-xs mt-1">Add folders and files to build your USB structure</p>
        </div>
      </div>
    </div>

    <!-- Drop zone hint -->
    <div class="px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
      Drag tokens from the palette onto files to assign them
    </div>
  </div>
</template>

<style scoped>
.visual-file-tree {
  @apply bg-white;
}
</style>
