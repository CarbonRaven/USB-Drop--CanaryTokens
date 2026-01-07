<script setup>
const props = defineProps({
  currentStep: {
    type: Number,
    required: true
  },
  totalSteps: {
    type: Number,
    default: 5
  },
  canProceed: {
    type: Boolean,
    default: true
  },
  saving: {
    type: Boolean,
    default: false
  },
  isEditing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['back', 'next', 'cancel', 'save'])

const isFirstStep = () => props.currentStep === 1
const isLastStep = () => props.currentStep === props.totalSteps

const onBack = () => {
  if (!isFirstStep()) {
    emit('back')
  }
}

const onNext = () => {
  if (isLastStep()) {
    emit('save')
  } else if (props.canProceed) {
    emit('next')
  }
}

const onCancel = () => {
  emit('cancel')
}
</script>

<template>
  <div class="flex items-center justify-between pt-6 border-t border-gray-200 mt-6">
    <!-- Cancel button (left side) -->
    <button
      type="button"
      class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
      @click="onCancel"
    >
      Cancel
    </button>

    <!-- Navigation buttons (right side) -->
    <div class="flex items-center space-x-3">
      <!-- Back button -->
      <button
        v-if="!isFirstStep()"
        type="button"
        class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        @click="onBack"
      >
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
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back
      </button>

      <!-- Next / Save button -->
      <button
        type="button"
        :disabled="!canProceed || saving"
        class="inline-flex items-center px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        :class="[
          canProceed && !saving
            ? 'bg-primary-600 hover:bg-primary-700'
            : 'bg-gray-400 cursor-not-allowed'
        ]"
        @click="onNext"
      >
        <template v-if="saving">
          <svg
            class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Saving...
        </template>
        <template v-else-if="isLastStep()">
          {{ isEditing ? 'Save Changes' : 'Create Profile' }}
        </template>
        <template v-else>
          Next
          <svg
            class="w-4 h-4 ml-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </template>
      </button>
    </div>
  </div>
</template>
