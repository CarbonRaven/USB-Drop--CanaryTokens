<script setup>
import { ref, computed } from 'vue'
import { useProfileWizardStore } from '@/stores/profileWizard'

const store = useProfileWizardStore()
const newFolderName = ref('')
const editingFolder = ref(null)
const editingName = ref('')
const selectedFolder = ref(null)

const folders = computed(() => store.folders)

const addFolder = () => {
  const name = newFolderName.value.trim()
  if (name && !folders.value.find(f => f.path === name)) {
    store.addFolder(name)
    newFolderName.value = ''
  }
}

const startEditing = (folder) => {
  editingFolder.value = folder.path
  editingName.value = folder.path
}

const saveEdit = (folder) => {
  const newName = editingName.value.trim()
  if (newName && newName !== folder.path) {
    store.updateFolder(folder.path, newName)
  }
  editingFolder.value = null
  editingName.value = ''
}

const cancelEdit = () => {
  editingFolder.value = null
  editingName.value = ''
}

const removeFolder = (path) => {
  if (confirm(`Delete folder "${path}" and all its files?`)) {
    store.removeFolder(path)
    if (selectedFolder.value === path) {
      selectedFolder.value = null
    }
  }
}

const selectFolder = (folder) => {
  selectedFolder.value = folder.path
}

const toggleFolderToken = (folder) => {
  folder.has_folder_token = !folder.has_folder_token
}

// Get files in the selected folder
const filesInFolder = computed(() => {
  if (!selectedFolder.value) return []
  return store.files.filter(f => f.folder === selectedFolder.value)
})

// Folder icon based on token status
const getFolderIcon = (folder) => {
  return folder.has_folder_token ? '📁' : '📂'
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-lg font-medium text-gray-900">
        Step 2: Folder Structure
      </h2>
      <p class="mt-1 text-sm text-gray-500">
        Organize folders as they will appear on the USB drive.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Folder Tree -->
      <div class="border border-gray-200 rounded-lg">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 class="text-sm font-medium text-gray-700">
            Folder Tree
          </h3>
        </div>

        <div class="p-4">
          <!-- Add new folder -->
          <div class="flex gap-2 mb-4">
            <input
              v-model="newFolderName"
              type="text"
              placeholder="New folder name..."
              class="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              @keyup.enter="addFolder"
            >
            <button
              type="button"
              :disabled="!newFolderName.trim()"
              class="px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              @click="addFolder"
            >
              Add
            </button>
          </div>

          <!-- Folder list -->
          <div class="space-y-1">
            <!-- Root indicator -->
            <div class="flex items-center px-2 py-1 text-sm text-gray-500">
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
              USB Drive (root)
            </div>

            <!-- Folders -->
            <div
              v-for="folder in folders"
              :key="folder.path"
              class="group"
            >
              <div
                class="flex items-center justify-between px-2 py-2 ml-4 rounded-md cursor-pointer transition-colors"
                :class="selectedFolder === folder.path ? 'bg-primary-100' : 'hover:bg-gray-100'"
                @click="selectFolder(folder)"
              >
                <div class="flex items-center flex-1 min-w-0">
                  <span class="mr-2">{{ getFolderIcon(folder) }}</span>

                  <!-- Editing mode -->
                  <template v-if="editingFolder === folder.path">
                    <input
                      v-model="editingName"
                      type="text"
                      class="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                      @keyup.enter="saveEdit(folder)"
                      @keyup.escape="cancelEdit"
                      @click.stop
                    >
                    <button
                      class="ml-2 text-green-600 hover:text-green-700"
                      @click.stop="saveEdit(folder)"
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
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </button>
                    <button
                      class="ml-1 text-gray-400 hover:text-gray-600"
                      @click.stop="cancelEdit"
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
                  </template>

                  <!-- Display mode -->
                  <template v-else>
                    <span class="text-sm text-gray-700 truncate">{{ folder.path }}</span>
                    <span
                      v-if="folder.has_folder_token"
                      class="ml-2 px-1.5 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded"
                    >
                      token
                    </span>
                  </template>
                </div>

                <!-- Action buttons (visible on hover) -->
                <div
                  v-if="editingFolder !== folder.path"
                  class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <button
                    class="p-1 text-gray-400 hover:text-gray-600"
                    title="Rename"
                    @click.stop="startEditing(folder)"
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
                    class="p-1 text-gray-400 hover:text-red-600"
                    title="Delete"
                    @click.stop="removeFolder(folder.path)"
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

            <!-- Empty state -->
            <div
              v-if="folders.length === 0"
              class="text-center py-8 text-gray-500"
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
                  d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                />
              </svg>
              <p class="mt-2 text-sm">
                No folders yet
              </p>
              <p class="text-xs text-gray-400">
                Add folders above to get started
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Folder Properties -->
      <div class="border border-gray-200 rounded-lg">
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 class="text-sm font-medium text-gray-700">
            Folder Properties
          </h3>
        </div>

        <div class="p-4">
          <template v-if="selectedFolder">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Selected Folder</label>
                <p class="mt-1 text-sm text-gray-900">
                  {{ selectedFolder }}
                </p>
              </div>

              <!-- Folder token toggle -->
              <div class="flex items-start">
                <div class="flex items-center h-5">
                  <input
                    :id="`folder-token-${selectedFolder}`"
                    type="checkbox"
                    :checked="folders.find(f => f.path === selectedFolder)?.has_folder_token"
                    class="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                    @change="toggleFolderToken(folders.find(f => f.path === selectedFolder))"
                  >
                </div>
                <div class="ml-3">
                  <label
                    :for="`folder-token-${selectedFolder}`"
                    class="text-sm font-medium text-gray-700"
                  >
                    Add folder token (desktop.ini)
                  </label>
                  <p class="text-xs text-gray-500 mt-1">
                    Creates a hidden desktop.ini file that triggers when the folder is opened in Windows Explorer.
                  </p>
                </div>
              </div>

              <!-- Files in this folder -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Files in this folder</label>
                <div
                  v-if="filesInFolder.length > 0"
                  class="space-y-1"
                >
                  <div
                    v-for="(file, index) in filesInFolder"
                    :key="index"
                    class="flex items-center text-sm text-gray-600 py-1"
                  >
                    <span class="mr-2">📄</span>
                    {{ file.name }}
                  </div>
                </div>
                <p
                  v-else
                  class="text-sm text-gray-400"
                >
                  No files in this folder yet
                </p>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="text-center py-8 text-gray-500">
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
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p class="mt-2 text-sm">
                Select a folder
              </p>
              <p class="text-xs text-gray-400">
                Click on a folder to view and edit its properties
              </p>
            </div>
          </template>
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
          <strong>Tip:</strong> Use realistic folder names that match your target organization's naming conventions.
          Click on a folder to configure folder tokens.
        </p>
      </div>
    </div>
  </div>
</template>
