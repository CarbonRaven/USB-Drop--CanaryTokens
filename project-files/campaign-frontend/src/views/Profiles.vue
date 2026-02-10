<script setup>
import { ref, onMounted } from 'vue'
import { profilesApi } from '@/services/api'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import ConfirmDialog from 'primevue/confirmdialog'
import { useConfirm } from 'primevue/useconfirm'

const confirm = useConfirm()

const profiles = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const showPreviewModal = ref(false)
const previewData = ref(null)
const newProfile = ref({
  name: '',
  description: '',
  scenario_type: 'hr',
  theme: 'corporate',
  file_structure: [],
  token_config: { types: ['dns', 'word'] },
  ai_prompts: {},
  label_suggestions: []
})

const scenarioTypes = [
  { value: 'hr', label: 'HR / Payroll' },
  { value: 'it', label: 'IT / Technical' },
  { value: 'executive', label: 'Executive / Financial' },
  { value: 'marketing', label: 'Marketing / Sales' },
  { value: 'legal', label: 'Legal / Compliance' },
  { value: 'generic', label: 'Generic / Mixed' }
]

const tokenTypes = [
  { value: 'dns', label: 'DNS Token' },
  { value: 'word', label: 'Word Document' },
  { value: 'excel', label: 'Excel Spreadsheet' },
  { value: 'pdf', label: 'PDF Document' },
  { value: 'folder', label: 'Windows Folder' },
  { value: 'qr', label: 'QR Code' }
]

onMounted(async () => {
  await loadProfiles()
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

const createProfile = async () => {
  await profilesApi.create(newProfile.value)
  showCreateModal.value = false
  resetForm()
  await loadProfiles()
}

const deleteProfile = (id) => {
  confirm.require({
    message: 'Are you sure you want to delete this profile?',
    header: 'Delete Profile',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptClass: 'p-button-danger',
    accept: async () => {
      await profilesApi.delete(id)
      await loadProfiles()
    }
  })
}

const previewProfile = async (id) => {
  const response = await profilesApi.preview(id)
  previewData.value = response.data
  showPreviewModal.value = true
}

const resetForm = () => {
  newProfile.value = {
    name: '',
    description: '',
    scenario_type: 'hr',
    theme: 'corporate',
    file_structure: [],
    token_config: { types: ['dns', 'word'] },
    ai_prompts: {},
    label_suggestions: []
  }
}

const toggleTokenType = (type) => {
  const types = newProfile.value.token_config.types
  const index = types.indexOf(type)
  if (index === -1) {
    types.push(type)
  } else {
    types.splice(index, 1)
  }
}
</script>

<template>
  <div>
    <ConfirmDialog />

    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-surface-0">USB Profiles</h1>
      <Button label="New Profile" icon="pi pi-plus" @click="showCreateModal = true" />
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="profile in profiles"
        :key="profile.id"
        class="bg-surface-900 border border-surface-700 rounded-lg hover:border-surface-600 transition-colors"
      >
        <div class="p-6">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="text-lg font-medium text-surface-0">{{ profile.name }}</h3>
              <Tag :value="profile.scenario_type" class="mt-1" severity="info" />
            </div>
          </div>

          <p class="mt-3 text-sm text-surface-400 line-clamp-2">
            {{ profile.description || 'No description' }}
          </p>

          <div class="mt-4">
            <div class="text-xs text-surface-400 mb-2">Token Types:</div>
            <div class="flex flex-wrap gap-1">
              <Tag
                v-for="type in profile.token_config?.types || []"
                :key="type"
                :value="type"
                severity="secondary"
              />
            </div>
          </div>

          <div class="mt-4 pt-4 border-t border-surface-700 flex justify-between">
            <Button label="Preview" text size="small" @click="previewProfile(profile.id)" />
            <Button label="Delete" text size="small" severity="danger" @click="deleteProfile(profile.id)" />
          </div>
        </div>
      </div>

      <div v-if="profiles.length === 0" class="col-span-full text-center py-12 text-surface-400">
        No profiles yet. Create your first one!
      </div>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreateModal" header="Create Profile" modal :style="{ width: '32rem' }"
      @hide="resetForm">
      <form @submit.prevent="createProfile" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Name</label>
          <InputText v-model="newProfile.name" required class="w-full" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Scenario Type</label>
          <Select v-model="newProfile.scenario_type" :options="scenarioTypes" optionLabel="label" optionValue="value" class="w-full" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Description</label>
          <Textarea v-model="newProfile.description" rows="2" class="w-full" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-2">Token Types</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="type in tokenTypes"
              :key="type.value"
              type="button"
              @click="toggleTokenType(type.value)"
              :class="[
                'px-3 py-1 text-sm rounded-full border transition-colors',
                newProfile.token_config.types.includes(type.value)
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-surface-800 text-surface-300 border-surface-600 hover:border-primary-400'
              ]"
            >
              {{ type.label }}
            </button>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Label Suggestions (comma-separated)</label>
          <InputText
            :modelValue="newProfile.label_suggestions.join(', ')"
            @update:modelValue="newProfile.label_suggestions = $event.split(',').map(s => s.trim()).filter(Boolean)"
            placeholder="Payroll Q4, HR Confidential, ..."
            class="w-full"
          />
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <Button label="Cancel" severity="secondary" text @click="showCreateModal = false; resetForm()" />
          <Button type="submit" label="Create" />
        </div>
      </form>
    </Dialog>

    <!-- Preview Dialog -->
    <Dialog v-model:visible="showPreviewModal" header="Profile Preview" modal :style="{ width: '32rem' }">
      <div v-if="previewData" class="space-y-4">
        <div>
          <div class="text-sm font-medium text-surface-300">File Structure:</div>
          <pre class="mt-1 p-3 bg-surface-800 border border-surface-700 rounded text-sm text-surface-200 overflow-auto max-h-48">{{ JSON.stringify(previewData.files, null, 2) }}</pre>
        </div>

        <div>
          <div class="text-sm font-medium text-surface-300">Token Types:</div>
          <div class="mt-1 flex flex-wrap gap-1">
            <Tag v-for="type in previewData.tokens" :key="type" :value="type" severity="info" />
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Close" severity="secondary" @click="showPreviewModal = false" />
      </template>
    </Dialog>
  </div>
</template>
