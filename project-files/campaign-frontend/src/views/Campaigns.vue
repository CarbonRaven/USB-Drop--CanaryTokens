<script setup>
import { ref, onMounted } from 'vue'
import { campaignsApi } from '@/services/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'

const campaigns = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const newCampaign = ref({ name: '', client_name: '', description: '' })

onMounted(async () => {
  await loadCampaigns()
})

const loadCampaigns = async () => {
  loading.value = true
  try {
    const response = await campaignsApi.list()
    campaigns.value = response.data
  } finally {
    loading.value = false
  }
}

const createCampaign = async () => {
  await campaignsApi.create(newCampaign.value)
  showCreateModal.value = false
  newCampaign.value = { name: '', client_name: '', description: '' }
  await loadCampaigns()
}

const statusSeverity = {
  draft: 'secondary',
  active: 'success',
  completed: 'info',
  archived: 'warn',
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-surface-0">Campaigns</h1>
      <Button label="New Campaign" icon="pi pi-plus" @click="showCreateModal = true" />
    </div>

    <div class="bg-surface-900 border border-surface-700 rounded-lg overflow-hidden">
      <DataTable :value="campaigns" :loading="loading" stripedRows
        tableClass="w-full" :rowHover="true"
        emptyMessage="No campaigns found">
        <Column field="name" header="Name">
          <template #body="{ data }">
            <router-link :to="`/campaigns/${data.id}`" class="text-primary-400 hover:underline">
              {{ data.name }}
            </router-link>
          </template>
        </Column>
        <Column field="client_name" header="Client">
          <template #body="{ data }">
            <span class="text-surface-300">{{ data.client_name || '-' }}</span>
          </template>
        </Column>
        <Column field="status" header="Status">
          <template #body="{ data }">
            <Tag :value="data.status" :severity="statusSeverity[data.status] || 'secondary'" />
          </template>
        </Column>
        <Column field="drive_count" header="Drives">
          <template #body="{ data }">
            <span class="text-surface-300">{{ data.drive_count }}</span>
          </template>
        </Column>
        <Column field="triggered_count" header="Triggers">
          <template #body="{ data }">
            <span class="text-surface-300">{{ data.triggered_count }}</span>
          </template>
        </Column>
        <Column header="Actions">
          <template #body="{ data }">
            <router-link :to="`/campaigns/${data.id}`" class="text-primary-400 hover:underline text-sm">
              View
            </router-link>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreateModal" header="Create Campaign" modal :style="{ width: '28rem' }">
      <form @submit.prevent="createCampaign" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Name</label>
          <InputText v-model="newCampaign.name" required class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Client Name</label>
          <InputText v-model="newCampaign.client_name" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-300 mb-1">Description</label>
          <Textarea v-model="newCampaign.description" rows="3" class="w-full" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <Button label="Cancel" severity="secondary" text @click="showCreateModal = false" />
          <Button type="submit" label="Create" />
        </div>
      </form>
    </Dialog>
  </div>
</template>
