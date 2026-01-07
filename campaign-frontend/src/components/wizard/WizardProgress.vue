<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentStep: {
    type: Number,
    required: true
  },
  totalSteps: {
    type: Number,
    default: 5
  }
})

const emit = defineEmits(['step-click'])

const steps = computed(() => [
  { number: 1, label: 'Scenario', description: 'Choose template' },
  { number: 2, label: 'Folders', description: 'Organize structure' },
  { number: 3, label: 'Tokens', description: 'Configure files' },
  { number: 4, label: 'Content', description: 'Customize content' },
  { number: 5, label: 'Review', description: 'Confirm & create' }
])

const getStepStatus = (stepNumber) => {
  if (stepNumber < props.currentStep) return 'completed'
  if (stepNumber === props.currentStep) return 'current'
  return 'upcoming'
}

const onStepClick = (stepNumber) => {
  if (stepNumber < props.currentStep) {
    emit('step-click', stepNumber)
  }
}
</script>

<template>
  <nav
    aria-label="Progress"
    class="mb-8"
  >
    <ol class="flex items-center justify-between">
      <li
        v-for="(step, index) in steps"
        :key="step.number"
        class="relative flex-1"
        :class="{ 'pr-8 sm:pr-20': index < steps.length - 1 }"
      >
        <!-- Connector line -->
        <div
          v-if="index < steps.length - 1"
          class="absolute top-4 left-7 -right-3 sm:left-9 sm:-right-11 h-0.5"
          :class="getStepStatus(step.number) === 'completed' ? 'bg-primary-600' : 'bg-gray-200'"
        />

        <!-- Step circle and label -->
        <button
          type="button"
          class="group flex flex-col items-center relative"
          :class="getStepStatus(step.number) === 'completed' ? 'cursor-pointer' : 'cursor-default'"
          @click="onStepClick(step.number)"
        >
          <!-- Circle -->
          <span
            class="flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors"
            :class="{
              'bg-primary-600 text-white': getStepStatus(step.number) === 'completed',
              'border-2 border-primary-600 bg-white text-primary-600': getStepStatus(step.number) === 'current',
              'border-2 border-gray-300 bg-white text-gray-500': getStepStatus(step.number) === 'upcoming'
            }"
          >
            <!-- Checkmark for completed -->
            <svg
              v-if="getStepStatus(step.number) === 'completed'"
              class="h-5 w-5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
            <!-- Number for current/upcoming -->
            <span v-else>{{ step.number }}</span>
          </span>

          <!-- Label -->
          <span
            class="mt-2 text-xs font-medium hidden sm:block"
            :class="{
              'text-primary-600': getStepStatus(step.number) === 'current',
              'text-gray-900': getStepStatus(step.number) === 'completed',
              'text-gray-500': getStepStatus(step.number) === 'upcoming'
            }"
          >
            {{ step.label }}
          </span>

          <!-- Description (visible on larger screens) -->
          <span
            class="text-xs text-gray-400 hidden lg:block"
          >
            {{ step.description }}
          </span>
        </button>
      </li>
    </ol>
  </nav>
</template>
