<script setup>
import { onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useProfileWizardStore } from '@/stores/profileWizard'
import WizardProgress from '@/components/wizard/WizardProgress.vue'
import WizardNavigation from '@/components/wizard/WizardNavigation.vue'
import ScenarioStep from '@/components/wizard/ScenarioStep.vue'
import FolderStep from '@/components/wizard/FolderStep.vue'
import TokenStep from '@/components/wizard/TokenStep.vue'
import ContentStep from '@/components/wizard/ContentStep.vue'
import ReviewStep from '@/components/wizard/ReviewStep.vue'

const router = useRouter()
const route = useRoute()
const store = useProfileWizardStore()

const isEditing = computed(() => store.isEditing)
const profileId = computed(() => route.params.id)

onMounted(async () => {
  // Check if we're editing an existing profile
  if (profileId.value) {
    try {
      await store.loadForEditing(profileId.value)
    } catch (error) {
      console.error('Failed to load profile:', error)
      router.push('/profiles')
    }
  } else {
    // Fresh wizard - load templates for selection
    await store.loadTemplates()
  }
})

onBeforeUnmount(() => {
  // Reset store when leaving the wizard
  store.reset()
})

const handleBack = () => {
  store.prevStep()
}

const handleNext = () => {
  store.nextStep()
}

const handleStepClick = (step) => {
  store.goToStep(step)
}

const handleCancel = () => {
  if (confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) {
    store.reset()
    router.push('/profiles')
  }
}

const handleSave = async () => {
  try {
    await store.saveProfile()
    store.reset()
    router.push('/profiles')
  } catch (error) {
    console.error('Failed to save profile:', error)
    alert('Failed to save profile. Please try again.')
  }
}

// Get the title based on editing mode
const pageTitle = computed(() => {
  if (store.loading) return 'Loading...'
  if (isEditing.value) return `Edit Profile: ${store.scenario.name}`
  return 'Create New Profile'
})
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ pageTitle }}
      </h1>
      <p class="mt-1 text-sm text-gray-500">
        {{ isEditing ? 'Modify your USB drive profile configuration.' : 'Configure a new USB drive profile for your campaigns.' }}
      </p>
    </div>

    <!-- Loading state -->
    <div
      v-if="store.loading"
      class="text-center py-12"
    >
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
      <p class="mt-4 text-gray-500">
        Loading...
      </p>
    </div>

    <!-- Wizard content -->
    <div
      v-else
      class="bg-white rounded-lg shadow-sm border border-gray-200"
    >
      <div class="p-6">
        <!-- Progress indicator -->
        <WizardProgress
          :current-step="store.currentStep"
          :total-steps="store.totalSteps"
          @step-click="handleStepClick"
        />

        <!-- Step content -->
        <div class="min-h-[400px]">
          <ScenarioStep v-if="store.currentStep === 1" />
          <FolderStep v-else-if="store.currentStep === 2" />
          <TokenStep v-else-if="store.currentStep === 3" />
          <ContentStep v-else-if="store.currentStep === 4" />
          <ReviewStep v-else-if="store.currentStep === 5" />
        </div>

        <!-- Navigation -->
        <WizardNavigation
          :current-step="store.currentStep"
          :total-steps="store.totalSteps"
          :can-proceed="store.canProceed"
          :saving="store.saving"
          :is-editing="isEditing"
          @back="handleBack"
          @next="handleNext"
          @cancel="handleCancel"
          @save="handleSave"
        />
      </div>
    </div>
  </div>
</template>
