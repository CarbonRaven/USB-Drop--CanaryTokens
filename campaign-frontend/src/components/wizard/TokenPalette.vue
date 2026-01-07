<script setup>
import { ref, defineProps, defineEmits } from 'vue'

const props = defineProps({
  tokenTypes: {
    type: Array,
    default: () => [
      { value: 'ms_word', label: 'Word', icon: '📄', extension: '.docx', color: 'bg-blue-100 text-blue-800 border-blue-200', description: 'Word document with embedded web bug' },
      { value: 'ms_excel', label: 'Excel', icon: '📊', extension: '.xlsx', color: 'bg-green-100 text-green-800 border-green-200', description: 'Excel spreadsheet with external data connection' },
      { value: 'pdf', label: 'PDF', icon: '📕', extension: '.pdf', color: 'bg-red-100 text-red-700 border-red-200', description: 'PDF with embedded tracking' },
      { value: 'text', label: 'Text', icon: '📝', extension: '.txt', color: 'bg-gray-100 text-gray-800 border-gray-200', description: 'Text file with tracking URLs' },
      { value: 'windows_dir', label: 'Folder', icon: '📁', extension: 'desktop.ini', color: 'bg-yellow-100 text-yellow-800 border-yellow-200', description: 'Folder token triggers on browse' },
      { value: 'aws_keys', label: 'AWS Keys', icon: '🔑', extension: '.txt', color: 'bg-orange-100 text-orange-800 border-orange-200', description: 'Fake AWS credentials file' },
      { value: 'web', label: 'Web Link', icon: '🔗', extension: '.url', color: 'bg-purple-100 text-purple-800 border-purple-200', description: 'URL shortcut with tracking' },
      { value: 'qr_code', label: 'QR Code', icon: '📱', extension: '.png', color: 'bg-pink-100 text-pink-800 border-pink-200', description: 'QR code image with tracking URL' },
    ]
  },
  selectedToken: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['select-token', 'drag-start', 'drag-end'])

const draggingToken = ref(null)

// Handle drag start
const onDragStart = (event, token) => {
  draggingToken.value = token.value
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('text/plain', JSON.stringify({ item: token, type: 'token' }))
  event.dataTransfer.setData('token-type', token.value)

  // Create a custom drag image
  const dragImage = document.createElement('div')
  dragImage.className = 'px-3 py-2 rounded-lg shadow-lg text-sm font-medium ' + token.color
  dragImage.textContent = token.icon + ' ' + token.label
  dragImage.style.position = 'absolute'
  dragImage.style.top = '-1000px'
  document.body.appendChild(dragImage)
  event.dataTransfer.setDragImage(dragImage, 0, 0)
  setTimeout(() => document.body.removeChild(dragImage), 0)

  emit('drag-start', token)
}

// Handle drag end
const onDragEnd = () => {
  draggingToken.value = null
  emit('drag-end')
}

// Handle click selection
const selectToken = (token) => {
  emit('select-token', token)
}
</script>

<template>
  <div class="token-palette">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-medium text-gray-700">Token Types</h3>
      <span class="text-xs text-gray-400">Drag to assign</span>
    </div>

    <!-- Token Grid -->
    <div class="grid grid-cols-2 gap-2">
      <div
        v-for="token in tokenTypes"
        :key="token.value"
        class="token-chip group relative"
        :class="[
          token.color,
          'border rounded-lg px-3 py-2 cursor-grab transition-all',
          draggingToken === token.value ? 'opacity-50 scale-95' : 'hover:shadow-md hover:scale-105',
          selectedToken === token.value ? 'ring-2 ring-primary-500 ring-offset-1' : ''
        ]"
        draggable="true"
        @dragstart="onDragStart($event, token)"
        @dragend="onDragEnd"
        @click="selectToken(token)"
      >
        <!-- Token content -->
        <div class="flex items-center">
          <span class="text-lg mr-2">{{ token.icon }}</span>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium truncate">{{ token.label }}</div>
            <div class="text-xs opacity-70">{{ token.extension }}</div>
          </div>
        </div>

        <!-- Tooltip on hover -->
        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
          {{ token.description }}
          <div class="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
        </div>

        <!-- Drag indicator -->
        <div class="absolute top-1 right-1 opacity-0 group-hover:opacity-50 transition-opacity">
          <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 6a2 2 0 11-4 0 2 2 0 014 0zM8 12a2 2 0 11-4 0 2 2 0 014 0zM8 18a2 2 0 11-4 0 2 2 0 014 0zM14 6a2 2 0 11-4 0 2 2 0 014 0zM14 12a2 2 0 11-4 0 2 2 0 014 0zM14 18a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
      </div>
    </div>

    <!-- Usage hint -->
    <div class="mt-4 p-3 bg-blue-50 rounded-lg">
      <div class="flex items-start">
        <svg class="w-4 h-4 text-blue-400 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div class="text-xs text-blue-700">
          <p class="font-medium">How to use:</p>
          <ul class="mt-1 space-y-1 list-disc list-inside">
            <li>Drag a token onto a file to assign it</li>
            <li>Click a token to see its details</li>
            <li>Each file can have one token type</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Token details panel -->
    <div
      v-if="selectedToken"
      class="mt-4 p-3 border border-gray-200 rounded-lg"
    >
      <h4 class="text-sm font-medium text-gray-700 mb-2">Selected Token</h4>
      <div
        v-for="token in tokenTypes.filter(t => t.value === selectedToken)"
        :key="token.value"
        class="space-y-2"
      >
        <div class="flex items-center">
          <span class="text-2xl mr-3">{{ token.icon }}</span>
          <div>
            <div class="font-medium text-gray-900">{{ token.label }}</div>
            <div class="text-xs text-gray-500">{{ token.extension }}</div>
          </div>
        </div>
        <p class="text-sm text-gray-600">{{ token.description }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.token-chip {
  @apply select-none;
}

.token-chip:active {
  cursor: grabbing;
}
</style>
