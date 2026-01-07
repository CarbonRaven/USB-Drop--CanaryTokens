<script setup>
import { ref, computed } from 'vue'
import { useProfileWizardStore } from '@/stores/profileWizard'

const store = useProfileWizardStore()
const showPreviewModal = ref(false)
const previewTemplate = ref(null)

const scenarioTypes = [
  { id: 'hr_documents', name: 'HR Department', icon: '👥', description: 'Payroll, benefits, and employee documents' },
  { id: 'it_department', name: 'IT Department', icon: '💻', description: 'Network configs, software, and credentials' },
  { id: 'finance', name: 'Finance', icon: '💰', description: 'Invoices, budgets, and financial reports' },
  { id: 'executive', name: 'Executive', icon: '👔', description: 'Board materials and strategic documents' },
  { id: 'developer', name: 'Developer', icon: '🔧', description: 'Source code, API keys, and configs' },
  { id: 'network_admin', name: 'Network Admin', icon: '🌐', description: 'Network diagrams and credentials' },
  { id: 'security_audit', name: 'Security Audit', icon: '🔒', description: 'Audit reports and vulnerability data' },
  { id: 'contractor', name: 'Contractor', icon: '📋', description: 'Project files and NDA documents' },
]


const profileName = computed({
  get: () => store.scenario.name,
  set: (value) => {
    store.scenario.name = value
  }
})

const profileDescription = computed({
  get: () => store.scenario.description,
  set: (value) => {
    store.scenario.description = value
  }
})

const selectTemplate = async (templateId) => {
  try {
    await store.loadTemplate(templateId)
  } catch (error) {
    console.error('Failed to load template:', error)
  }
}

const selectFromScratch = () => {
  store.scenario.type = 'custom'
  store.scenario.template_id = null
}

const openPreview = (template) => {
  previewTemplate.value = template
  showPreviewModal.value = true
}

const useTemplate = () => {
  if (previewTemplate.value) {
    selectTemplate(previewTemplate.value.id)
    showPreviewModal.value = false
  }
}

const getTemplateStats = (templateId) => {
  const template = store.templates.find(t => t.id === templateId)
  if (template) {
    return {
      files: template.file_count || 0,
      folders: template.folder_count || 0
    }
  }
  return { files: 0, folders: 0 }
}

const isSelected = (typeId) => {
  return store.scenario.type === typeId || store.scenario.template_id === typeId
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-lg font-medium text-gray-900">
        Step 1: Choose a Scenario
      </h2>
      <p class="mt-1 text-sm text-gray-500">
        Select a template that matches your target environment, or start from scratch.
      </p>
    </div>

    <!-- Template Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      <!-- Template cards -->
      <div
        v-for="type in scenarioTypes"
        :key="type.id"
        class="relative border rounded-lg transition-all hover:shadow-md"
        :class="isSelected(type.id) ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500' : 'border-gray-200 hover:border-primary-300'"
      >
        <!-- Main clickable area -->
        <button
          type="button"
          class="w-full p-4 text-left focus:outline-none"
          @click="selectTemplate(type.id)"
        >
          <!-- Selected indicator -->
          <div
            v-if="isSelected(type.id)"
            class="absolute top-2 right-2"
          >
            <svg
              class="w-5 h-5 text-primary-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clip-rule="evenodd"
              />
            </svg>
          </div>

          <div class="flex items-start">
            <span class="text-2xl mr-3">{{ type.icon }}</span>
            <div class="flex-1 min-w-0">
              <h3 class="font-medium text-gray-900">
                {{ type.name }}
              </h3>
              <p class="text-sm text-gray-500 mt-1">
                {{ type.description }}
              </p>
              <div class="flex items-center space-x-3 mt-2 text-xs text-gray-400">
                <span>{{ getTemplateStats(type.id).folders }} folders</span>
                <span>{{ getTemplateStats(type.id).files }} files</span>
              </div>
            </div>
          </div>
        </button>

        <!-- Preview link -->
        <div class="px-4 pb-3">
          <button
            type="button"
            class="text-xs text-primary-600 hover:text-primary-700"
            @click="openPreview(type)"
          >
            Preview template
          </button>
        </div>
      </div>

      <!-- Start from scratch option -->
      <button
        type="button"
        class="p-4 text-left border-2 border-dashed rounded-lg transition-all hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
        :class="store.scenario.type === 'custom' ? 'border-primary-500 bg-primary-50' : 'border-gray-300'"
        @click="selectFromScratch"
      >
        <div class="flex items-start">
          <span class="text-2xl mr-3">➕</span>
          <div class="flex-1">
            <h3 class="font-medium text-gray-900">
              Start from Scratch
            </h3>
            <p class="text-sm text-gray-500 mt-1">
              Create a custom profile with no pre-populated content
            </p>
          </div>
        </div>
      </button>
    </div>

    <!-- Profile Name and Description -->
    <div class="space-y-4 pt-6 border-t border-gray-200">
      <div>
        <label
          for="profile-name"
          class="block text-sm font-medium text-gray-700"
        >
          Profile Name <span class="text-red-500">*</span>
        </label>
        <input
          id="profile-name"
          v-model="profileName"
          type="text"
          placeholder="e.g., HR Documents - Q4 Campaign"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
        >
      </div>

      <div>
        <label
          for="profile-description"
          class="block text-sm font-medium text-gray-700"
        >
          Description
        </label>
        <textarea
          id="profile-description"
          v-model="profileDescription"
          rows="2"
          placeholder="Brief description of this profile's purpose..."
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
        />
      </div>
    </div>

    <!-- Preview Modal -->
    <div
      v-if="showPreviewModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium">
            {{ previewTemplate?.icon }} {{ previewTemplate?.name }} Template
          </h3>
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

        <p class="text-sm text-gray-500 mb-4">
          {{ previewTemplate?.description }}
        </p>

        <!-- Template contents would be shown here -->
        <div class="bg-gray-50 rounded-lg p-4 mb-4">
          <p class="text-sm text-gray-500 text-center">
            Template preview content will be loaded from the API.
          </p>
        </div>

        <div class="flex justify-end space-x-3">
          <button
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
            @click="showPreviewModal = false"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            @click="useTemplate"
          >
            Use This Template
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
