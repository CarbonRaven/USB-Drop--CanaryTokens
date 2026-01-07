<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue'
import { profilesApi } from '@/services/api'

const props = defineProps({
  profileId: {
    type: String,
    required: true
  },
  folder: {
    type: String,
    default: ''
  },
  acceptedTypes: {
    type: Array,
    default: () => ['.docx', '.xlsx', '.pdf', '.png', '.jpg', '.jpeg', '.gif']
  },
  maxFileSize: {
    type: Number,
    default: 10 * 1024 * 1024 // 10MB
  }
})

const emit = defineEmits(['file-uploaded', 'error'])

const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadError = ref(null)
const fileInput = ref(null)

const acceptString = computed(() => props.acceptedTypes.join(','))

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getFileIcon = (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  switch (ext) {
    case 'docx':
    case 'doc':
      return { icon: 'W', color: 'bg-blue-600' }
    case 'xlsx':
    case 'xls':
      return { icon: 'X', color: 'bg-green-600' }
    case 'pdf':
      return { icon: 'P', color: 'bg-red-600' }
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
      return { icon: 'I', color: 'bg-purple-600' }
    default:
      return { icon: 'F', color: 'bg-gray-600' }
  }
}

const validateFile = (file) => {
  // Check file extension
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!props.acceptedTypes.includes(ext) && !props.acceptedTypes.includes(ext.replace('.jpeg', '.jpg'))) {
    return `File type "${ext}" is not allowed. Accepted types: ${props.acceptedTypes.join(', ')}`
  }

  // Check file size
  if (file.size > props.maxFileSize) {
    return `File is too large. Maximum size is ${formatFileSize(props.maxFileSize)}`
  }

  return null
}

const handleDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  isDragging.value = false
}

const handleDrop = async (e) => {
  e.preventDefault()
  isDragging.value = false

  const files = Array.from(e.dataTransfer.files)
  for (const file of files) {
    await uploadFile(file)
  }
}

const handleFileSelect = async (e) => {
  const files = Array.from(e.target.files)
  for (const file of files) {
    await uploadFile(file)
  }
  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const uploadFile = async (file) => {
  // Validate
  const error = validateFile(file)
  if (error) {
    uploadError.value = error
    emit('error', error)
    return
  }

  uploadError.value = null
  isUploading.value = true
  uploadProgress.value = 0

  try {
    const response = await profilesApi.uploadFile(props.profileId, file, props.folder)
    emit('file-uploaded', response.data)
    uploadProgress.value = 100
  } catch (err) {
    const errorMsg = err.response?.data?.detail || 'Failed to upload file'
    uploadError.value = errorMsg
    emit('error', errorMsg)
  } finally {
    isUploading.value = false
    setTimeout(() => {
      uploadProgress.value = 0
    }, 1000)
  }
}

const triggerFileSelect = () => {
  fileInput.value?.click()
}
</script>

<template>
  <div class="file-uploader">
    <!-- Drop zone -->
    <div
      class="border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer"
      :class="{
        'border-primary-500 bg-primary-50': isDragging,
        'border-gray-300 hover:border-gray-400': !isDragging && !isUploading,
        'border-gray-200 bg-gray-50': isUploading
      }"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
      @click="triggerFileSelect"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="acceptString"
        multiple
        class="hidden"
        @change="handleFileSelect"
      >

      <!-- Uploading state -->
      <div v-if="isUploading" class="py-4">
        <svg class="animate-spin h-8 w-8 mx-auto text-primary-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p class="mt-2 text-sm text-gray-600">Uploading...</p>
        <div class="mt-2 w-48 mx-auto bg-gray-200 rounded-full h-2">
          <div
            class="bg-primary-600 h-2 rounded-full transition-all"
            :style="{ width: uploadProgress + '%' }"
          />
        </div>
      </div>

      <!-- Default state -->
      <div v-else>
        <svg
          class="w-10 h-10 mx-auto text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p class="mt-2 text-sm text-gray-600">
          <span class="font-medium text-primary-600">Click to upload</span> or drag and drop
        </p>
        <p class="mt-1 text-xs text-gray-500">
          {{ acceptedTypes.join(', ') }} up to {{ formatFileSize(maxFileSize) }}
        </p>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="uploadError" class="mt-2 flex items-center text-sm text-red-600">
      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {{ uploadError }}
    </div>

    <!-- File type hints -->
    <div class="mt-3 flex flex-wrap gap-2">
      <div class="flex items-center text-xs text-gray-500">
        <span class="w-4 h-4 rounded bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold mr-1">W</span>
        Word
      </div>
      <div class="flex items-center text-xs text-gray-500">
        <span class="w-4 h-4 rounded bg-green-600 text-white flex items-center justify-center text-[10px] font-bold mr-1">X</span>
        Excel
      </div>
      <div class="flex items-center text-xs text-gray-500">
        <span class="w-4 h-4 rounded bg-red-600 text-white flex items-center justify-center text-[10px] font-bold mr-1">P</span>
        PDF
      </div>
      <div class="flex items-center text-xs text-gray-500">
        <span class="w-4 h-4 rounded bg-purple-600 text-white flex items-center justify-center text-[10px] font-bold mr-1">I</span>
        Images
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-uploader {
  @apply w-full;
}
</style>
