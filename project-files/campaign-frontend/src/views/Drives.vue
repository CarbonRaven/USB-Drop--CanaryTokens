<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { drivesApi, campaignsApi, profilesApi } from '@/services/api'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'

const router = useRouter()
const toast = useToast()
const drives = ref([])
const campaigns = ref([])
const profiles = ref([])
const loading = ref(true)
const showCreateModal = ref(false)

const filters = ref({
  campaign_id: '',
  status: ''
})

const newDrive = ref({
  campaign_id: '',
  profile_id: '',
  label: ''
})

const driveStatusSeverity = {
  created: 'secondary',
  prepared: 'info',
  deployed: 'success',
  triggered: 'danger',
  recovered: 'warn',
}

const statusFilterOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Created', value: 'created' },
  { label: 'Prepared', value: 'prepared' },
  { label: 'Deployed', value: 'deployed' },
  { label: 'Triggered', value: 'triggered' },
  { label: 'Recovered', value: 'recovered' },
]

onMounted(async () => {
  await Promise.all([
    loadDrives(),
    loadCampaigns(),
    loadProfiles()
  ])
})

const loadDrives = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.campaign_id) params.campaign_id = filters.value.campaign_id
    if (filters.value.status) params.status = filters.value.status

    const response = await drivesApi.list(params)
    drives.value = response.data
  } finally {
    loading.value = false
  }
}

const loadCampaigns = async () => {
  const response = await campaignsApi.list()
  campaigns.value = response.data
}

const loadProfiles = async () => {
  const response = await profilesApi.list()
  profiles.value = response.data
}

const createDrive = async () => {
  try {
    await drivesApi.create(newDrive.value)
    showCreateModal.value = false
    resetForm()
    toast.add({ severity: 'success', summary: 'Drive Created', life: 3000 })
    await loadDrives()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to create drive', life: 5000 })
  }
}

const prepareDrive = async (id) => {
  try {
    await drivesApi.prepare(id)
    toast.add({ severity: 'success', summary: 'Drive Prepared', detail: 'Tokens generated successfully', life: 3000 })
    await loadDrives()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to prepare drive', life: 5000 })
  }
}

const downloadDrive = async (id) => {
  try {
    const response = await drivesApi.download(id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `drive-${id}.zip`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    toast.add({ severity: 'success', summary: 'Download Started', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to download drive', life: 5000 })
  }
}

const resetForm = () => {
  newDrive.value = {
    campaign_id: '',
    profile_id: '',
    label: ''
  }
}

const applyFilters = () => {
  loadDrives()
}

const clearFilters = () => {
  filters.value = { campaign_id: '', status: '' }
  loadDrives()
}

const campaignFilterOptions = computed(() => [
  { label: 'All Campaigns', value: '' },
  ...campaigns.value.map(c => ({ label: c.name, value: c.id }))
])

const campaignOptions = computed(() =>
  campaigns.value.map(c => ({ label: c.name, value: c.id }))
)

const profileOptions = computed(() =>
  profiles.value.map(p => ({ label: p.name, value: p.id }))
)

const getCampaignName = (id) => {
  const campaign = campaigns.value.find(c => c.id === id)
  return campaign?.name || '-'
}

const getProfileName = (id) => {
  const profile = profiles.value.find(p => p.id === id)
  return profile?.name || '-'
}

const filteredDrives = computed(() => {
  return drives.value
})
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-surface-0">USB Drives</h1>
      <Button label="New Drive" icon="pi pi-plus" @click="showCreateModal = true" />
    </div>

    <!-- Filters -->
    <div class="bg-surface-900 border border-surface-700 rounded-lg p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Campaign</label>
          <Select v-model="filters.campaign_id" :options="campaignFilterOptions"
            optionLabel="label" optionValue="value" class="w-48" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Status</label>
          <Select v-model="filters.status" :options="statusFilterOptions"
            optionLabel="label" optionValue="value" class="w-40" />
        </div>

        <Button label="Filter" icon="pi pi-filter" @click="applyFilters" />
        <Button label="Clear" severity="secondary" text @click="clearFilters" />
      </div>
    </div>

    <!-- Drives Table -->
    <div class="bg-surface-900 border border-surface-700 rounded-lg overflow-hidden">
      <DataTable :value="filteredDrives" :loading="loading" :rowHover="true"
        emptyMessage="No drives found">
        <Column field="unique_code" header="Code">
          <template #body="{ data }">
            <router-link :to="`/drives/${data.id}`" class="text-primary-400 hover:underline font-mono">
              {{ data.unique_code }}
            </router-link>
          </template>
        </Column>
        <Column field="label" header="Label">
          <template #body="{ data }">
            <span class="text-surface-300">{{ data.label || '-' }}</span>
          </template>
        </Column>
        <Column field="campaign_id" header="Campaign">
          <template #body="{ data }">
            <span class="text-surface-300">{{ getCampaignName(data.campaign_id) }}</span>
          </template>
        </Column>
        <Column field="profile_id" header="Profile">
          <template #body="{ data }">
            <span class="text-surface-300">{{ getProfileName(data.profile_id) }}</span>
          </template>
        </Column>
        <Column field="status" header="Status">
          <template #body="{ data }">
            <Tag :value="data.status" :severity="driveStatusSeverity[data.status] || 'secondary'" />
          </template>
        </Column>
        <Column field="token_count" header="Tokens">
          <template #body="{ data }">
            <span class="text-surface-300">{{ data.token_count || 0 }}</span>
          </template>
        </Column>
        <Column header="Actions">
          <template #body="{ data }">
            <div class="flex gap-2">
              <Button v-if="data.status === 'created'" label="Prepare" text size="small"
                @click="prepareDrive(data.id)" />
              <Button v-if="data.status === 'prepared'" label="Download" text size="small" severity="success"
                @click="downloadDrive(data.id)" />
              <router-link v-if="data.status === 'prepared'" :to="`/drives/${data.id}?action=deploy`">
                <Button label="Deploy" text size="small" severity="info" />
              </router-link>
              <router-link :to="`/drives/${data.id}`">
                <Button label="View" text size="small" severity="secondary" />
              </router-link>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreateModal" header="Create Drive" modal :style="{ width: '28rem' }"
      @hide="resetForm">
      <form @submit.prevent="createDrive" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Campaign</label>
          <Select v-model="newDrive.campaign_id" :options="campaignOptions"
            optionLabel="label" optionValue="value" placeholder="Select a campaign" class="w-full" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Profile</label>
          <Select v-model="newDrive.profile_id" :options="profileOptions"
            optionLabel="label" optionValue="value" placeholder="Select a profile" class="w-full" />
        </div>

        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Label (optional)</label>
          <InputText v-model="newDrive.label" placeholder="e.g., HR Payroll Q4" class="w-full" />
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <Button label="Cancel" severity="secondary" text @click="showCreateModal = false; resetForm()" />
          <Button type="submit" label="Create" />
        </div>
      </form>
    </Dialog>
  </div>
</template>
