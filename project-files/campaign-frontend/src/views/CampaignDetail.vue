<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { campaignsApi, drivesApi, reportsApi } from '@/services/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ConfirmDialog from 'primevue/confirmdialog'
import ProgressSpinner from 'primevue/progressspinner'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const campaign = ref(null)
const drives = ref([])
const stats = ref(null)
const loading = ref(true)
const showEditModal = ref(false)
const editForm = ref({})

const statusOptions = [
  { label: 'Draft', value: 'draft' },
  { label: 'Active', value: 'active' },
  { label: 'Completed', value: 'completed' },
  { label: 'Archived', value: 'archived' },
]

const statusSeverity = {
  draft: 'secondary',
  active: 'success',
  completed: 'info',
  archived: 'warn',
}

const driveStatusSeverity = {
  created: 'secondary',
  prepared: 'info',
  deployed: 'success',
  triggered: 'danger',
  recovered: 'warn',
}

onMounted(async () => {
  await loadCampaign()
})

const loadCampaign = async () => {
  loading.value = true
  try {
    const [campaignRes, statsRes] = await Promise.all([
      campaignsApi.get(route.params.id),
      campaignsApi.stats(route.params.id)
    ])
    campaign.value = campaignRes.data
    stats.value = statsRes.data
    drives.value = campaign.value.drives || []

    editForm.value = {
      name: campaign.value.name,
      client_name: campaign.value.client_name,
      description: campaign.value.description,
      status: campaign.value.status
    }
  } catch (error) {
    console.error('Failed to load campaign:', error)
    router.push('/campaigns')
  } finally {
    loading.value = false
  }
}

const updateCampaign = async () => {
  try {
    await campaignsApi.update(campaign.value.id, editForm.value)
    showEditModal.value = false
    toast.add({ severity: 'success', summary: 'Campaign Updated', life: 3000 })
    await loadCampaign()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update campaign', life: 5000 })
  }
}

const deleteCampaign = () => {
  confirm.require({
    message: 'Are you sure you want to delete this campaign? This cannot be undone.',
    header: 'Delete Campaign',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await campaignsApi.delete(campaign.value.id)
        toast.add({ severity: 'success', summary: 'Campaign Deleted', life: 3000 })
        router.push('/campaigns')
      } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete campaign', life: 5000 })
      }
    }
  })
}

const exportCsv = async () => {
  try {
    const response = await reportsApi.exportCsv(campaign.value.id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `campaign-${campaign.value.id}-report.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    toast.add({ severity: 'success', summary: 'CSV Exported', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to export CSV', life: 5000 })
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div>
    <ConfirmDialog />

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <div v-else-if="campaign">
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center space-x-4">
          <router-link to="/campaigns" class="text-surface-400 hover:text-surface-200">
            &larr; Back to Campaigns
          </router-link>
        </div>
        <div class="mt-4 flex justify-between items-start">
          <div>
            <h1 class="text-2xl font-bold text-surface-0">{{ campaign.name }}</h1>
            <p v-if="campaign.client_name" class="mt-1 text-surface-400">
              Client: {{ campaign.client_name }}
            </p>
          </div>
          <div class="flex items-center space-x-3">
            <Tag :value="campaign.status" :severity="statusSeverity[campaign.status]" />
            <Button label="Edit" severity="secondary" size="small" @click="showEditModal = true" />
          </div>
        </div>
        <p v-if="campaign.description" class="mt-3 text-surface-300">
          {{ campaign.description }}
        </p>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Total Drives</div>
          <div class="text-2xl font-bold text-surface-0">{{ stats?.total_drives || 0 }}</div>
        </div>
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Deployed</div>
          <div class="text-2xl font-bold text-green-400">{{ stats?.deployed || 0 }}</div>
        </div>
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Triggered</div>
          <div class="text-2xl font-bold text-red-400">{{ stats?.triggered || 0 }}</div>
        </div>
        <div class="bg-surface-900 border border-surface-700 rounded-lg p-4">
          <div class="text-sm text-surface-400">Success Rate</div>
          <div class="text-2xl font-bold text-surface-0">
            {{ stats?.deployed ? Math.round((stats.triggered / stats.deployed) * 100) : 0 }}%
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mb-6 flex gap-3">
        <router-link :to="`/drives?campaign_id=${campaign.id}`">
          <Button label="View All Drives" icon="pi pi-database" />
        </router-link>
        <router-link :to="`/map?campaign_id=${campaign.id}`">
          <Button label="View on Map" icon="pi pi-map" severity="info" />
        </router-link>
        <Button label="Export CSV" icon="pi pi-download" severity="secondary" @click="exportCsv" />
      </div>

      <!-- Drives Table -->
      <div class="bg-surface-900 border border-surface-700 rounded-lg overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-700 flex justify-between items-center">
          <h2 class="text-lg font-medium text-surface-0">Drives</h2>
          <router-link :to="`/drives?action=new&campaign_id=${campaign.id}`"
            class="text-sm text-primary-400 hover:text-primary-300">
            + Add Drive
          </router-link>
        </div>
        <DataTable :value="drives" :rowHover="true" emptyMessage="No drives in this campaign yet">
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
          <Column field="trigger_count" header="Triggers">
            <template #body="{ data }">
              <span class="text-surface-300">{{ data.trigger_count || 0 }}</span>
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <!-- Edit Dialog -->
    <Dialog v-model:visible="showEditModal" header="Edit Campaign" modal :style="{ width: '28rem' }">
      <form @submit.prevent="updateCampaign" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Name</label>
          <InputText v-model="editForm.name" required class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Client Name</label>
          <InputText v-model="editForm.client_name" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Status</label>
          <Select v-model="editForm.status" :options="statusOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Description</label>
          <Textarea v-model="editForm.description" rows="3" class="w-full" />
        </div>
        <div class="flex justify-between pt-4">
          <Button label="Delete" severity="danger" text @click="deleteCampaign" />
          <div class="flex gap-3">
            <Button label="Cancel" severity="secondary" text @click="showEditModal = false" />
            <Button type="submit" label="Save" />
          </div>
        </div>
      </form>
    </Dialog>
  </div>
</template>
