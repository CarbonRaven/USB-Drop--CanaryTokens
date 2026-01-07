<script setup>
import { ref, computed, watch, defineProps, defineEmits } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  filename: {
    type: String,
    default: 'template.txt'
  },
  urlShortenerEnabled: {
    type: Boolean,
    default: false
  },
  urlShortenerConfig: {
    type: Object,
    default: () => ({})
  },
  placeholders: {
    type: Array,
    default: () => [
      { tag: '{canary_token-URL}', label: 'Web Token', description: 'Web bug tracking URL - triggers on click/load', icon: '🔗', color: 'bg-blue-100 text-blue-800' },
      { tag: '{canary_token-DNS}', label: 'DNS Token', description: 'DNS-based token - triggers on DNS lookup', icon: '🌐', color: 'bg-green-100 text-green-800' },
      { tag: '{canary_token-WORD}', label: 'Word Token', description: 'Word doc token URL - triggers on open', icon: '📄', color: 'bg-blue-100 text-blue-700' },
      { tag: '{canary_token-EXCEL}', label: 'Excel Token', description: 'Excel sheet token URL - triggers on open', icon: '📊', color: 'bg-green-100 text-green-700' },
      { tag: '{canary_token-PDF}', label: 'PDF Token', description: 'PDF document token URL - triggers on open', icon: '📕', color: 'bg-red-100 text-red-700' },
      { tag: '{canary_token-QR}', label: 'QR Code URL', description: 'URL for QR code generation', icon: '📱', color: 'bg-pink-100 text-pink-800' },
      { tag: '{short_url}', label: 'Short URL', description: 'Shortened tracking URL (requires URL Shortener enabled in Step 4)', icon: '📎', color: 'bg-purple-100 text-purple-800', requiresShortener: true },
      { tag: '{drive_code}', label: 'Drive Code', description: 'Unique drive identifier', icon: '💾', color: 'bg-gray-100 text-gray-800' },
    ]
  },
  previewMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'save', 'preview'])

const textareaRef = ref(null)
const cursorPosition = ref(0)
const showPreview = ref(false)

// Local content for editing
const content = ref(props.modelValue)

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  content.value = newVal
})

// Emit changes
watch(content, (newVal) => {
  emit('update:modelValue', newVal)
})

// Insert placeholder at cursor position
const insertPlaceholder = (placeholder) => {
  const textarea = textareaRef.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = content.value

  // Insert the placeholder tag
  content.value = text.substring(0, start) + placeholder.tag + text.substring(end)

  // Set cursor position after the inserted placeholder
  const newPosition = start + placeholder.tag.length
  setTimeout(() => {
    textarea.focus()
    textarea.setSelectionRange(newPosition, newPosition)
  }, 0)
}

// Track cursor position
const updateCursorPosition = (event) => {
  cursorPosition.value = event.target.selectionStart
}

// Generate preview content
const previewContent = computed(() => {
  let preview = content.value
  // New token placeholders
  preview = preview.replace(/{canary_token-URL}/g, 'https://canarytokens.com/t/abc123/web.gif')
  preview = preview.replace(/{canary_token-DNS}/g, 'abc123.canarytokens.com')
  preview = preview.replace(/{canary_token-WORD}/g, 'https://canarytokens.com/t/def456/document.docx')
  preview = preview.replace(/{canary_token-EXCEL}/g, 'https://canarytokens.com/t/ghi789/spreadsheet.xlsx')
  preview = preview.replace(/{canary_token-PDF}/g, 'https://canarytokens.com/t/jkl012/document.pdf')
  preview = preview.replace(/{canary_token-QR}/g, 'https://canarytokens.com/t/mno345/qr')
  // Legacy placeholders (for backwards compatibility)
  preview = preview.replace(/{canary_url}/g, 'https://canarytokens.com/t/abc123/web.gif')
  // Short URL - use preview if shortener enabled, otherwise show disabled message
  if (props.urlShortenerEnabled && shortUrlPreview.value) {
    preview = preview.replace(/{short_url}/g, shortUrlPreview.value)
  } else {
    preview = preview.replace(/{short_url}/g, '[URL Shortener disabled]')
  }
  preview = preview.replace(/{drive_code}/g, 'USB-2024-001')
  return preview
})

// Count placeholders
const placeholderCounts = computed(() => {
  const counts = {}
  props.placeholders.forEach(p => {
    const regex = new RegExp(p.tag.replace(/[{}]/g, '\\$&'), 'g')
    const matches = content.value.match(regex)
    counts[p.tag] = matches ? matches.length : 0
  })
  return counts
})

// Filter/modify placeholders based on URL shortener status
const displayPlaceholders = computed(() => {
  return props.placeholders.map(p => {
    if (p.requiresShortener && !props.urlShortenerEnabled) {
      return {
        ...p,
        disabled: true,
        color: 'bg-gray-100 text-gray-400 border-dashed',
        description: p.description + ' - DISABLED: Enable URL Shortener in Step 4'
      }
    }
    return p
  })
})

// Short URL preview based on config
const shortUrlPreview = computed(() => {
  if (!props.urlShortenerEnabled || !props.urlShortenerConfig) {
    return null
  }
  const config = props.urlShortenerConfig
  const base = config.base_slug || 'docs'
  const domain = config.domain || 'links.example.com'
  let suffix = 'xxxx'
  if (config.suffix_mode === 'sequential') suffix = '001'
  else if (config.suffix_mode === 'drive_code') suffix = 'usb...'
  return `https://${domain}/${base}-${suffix}`
})

// Highlight placeholders in content for display
const highlightedContent = computed(() => {
  let html = content.value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Highlight placeholders
  props.placeholders.forEach(p => {
    const escaped = p.tag.replace(/[{}]/g, '\\$&')
    const regex = new RegExp(escaped, 'g')
    html = html.replace(regex, `<span class="bg-yellow-200 text-yellow-900 px-1 rounded">${p.tag}</span>`)
  })

  return html
})

// Toggle preview
const togglePreview = () => {
  showPreview.value = !showPreview.value
}

// Save template
const saveTemplate = () => {
  emit('save', { filename: props.filename, content: content.value })
}

// Template presets
const presets = [
  {
    name: 'Password List',
    content: `WiFi Passwords - Updated {drive_code}
================================

Office WiFi: SecurePass2024!
Guest Network: Welcome123
Server Room: Admin@2024#
VPN: Corp_VPN_2024

Click here to view more: {canary_token-URL}
`
  },
  {
    name: 'Credentials File',
    content: `=== CONFIDENTIAL ===
System: Corporate Portal
URL: {canary_token-URL}
Username: admin
Password: P@ssw0rd123!

Last Updated: See {short_url} for changes
Drive ID: {drive_code}
`
  },
  {
    name: 'IT Notes',
    content: `IT Department Notes
-------------------
For updated documentation: {canary_token-URL}

Server credentials saved to secure location.
Contact IT for access.

Reference: {drive_code}
`
  },
  {
    name: 'AWS Credentials',
    content: `# AWS Credentials - {drive_code}
# DO NOT SHARE

[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# For credential rotation: {canary_token-URL}
`
  }
]

// Apply preset
const applyPreset = (preset) => {
  if (content.value && !confirm('Replace current content with preset?')) return
  content.value = preset.content
}
</script>

<template>
  <div class="template-editor">
    <!-- Toolbar -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center space-x-2">
        <span class="text-sm font-medium text-gray-700">Template Editor</span>
        <span class="text-xs text-gray-400">{{ filename }}</span>
      </div>
      <div class="flex items-center space-x-2">
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
          :class="showPreview ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
          @click="togglePreview"
        >
          {{ showPreview ? 'Edit' : 'Preview' }}
        </button>
      </div>
    </div>

    <!-- Placeholder buttons -->
    <div class="mb-3 p-3 bg-gray-50 rounded-lg">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-gray-600">Insert Placeholder:</span>
        <div class="flex items-center space-x-2">
          <span
            v-for="(count, tag) in placeholderCounts"
            :key="tag"
            class="text-xs text-gray-400"
          >
            {{ tag }}: {{ count }}
          </span>
        </div>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="placeholder in displayPlaceholders"
          :key="placeholder.tag"
          type="button"
          class="inline-flex items-center px-3 py-1.5 text-xs font-medium border rounded-md transition-all group"
          :class="[
            placeholder.color || 'bg-white border-gray-200',
            placeholder.disabled ? 'cursor-not-allowed opacity-60' : 'hover:shadow-sm'
          ]"
          :title="placeholder.description"
          :disabled="placeholder.disabled"
          @click="!placeholder.disabled && insertPlaceholder(placeholder)"
        >
          <span class="mr-1.5">{{ placeholder.icon }}</span>
          {{ placeholder.label }}
          <code class="ml-2 px-1.5 py-0.5 bg-white/50 rounded text-[10px] opacity-75 group-hover:opacity-100">
            {{ placeholder.tag }}
          </code>
          <span v-if="placeholder.disabled" class="ml-1 text-red-400" title="Requires URL Shortener">
            ⚠
          </span>
        </button>
      </div>
      <!-- URL Shortener status indicator -->
      <div v-if="shortUrlPreview" class="mt-2 text-xs text-purple-600">
        Short URLs will look like: <code class="bg-purple-50 px-1 rounded">{{ shortUrlPreview }}</code>
      </div>
    </div>

    <!-- Preset templates -->
    <div class="mb-3">
      <div class="flex items-center space-x-2">
        <span class="text-xs text-gray-500">Quick start:</span>
        <div class="flex flex-wrap gap-1">
          <button
            v-for="preset in presets"
            :key="preset.name"
            type="button"
            class="px-2 py-1 text-xs text-gray-600 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- Editor / Preview -->
    <div class="border border-gray-200 rounded-lg overflow-hidden">
      <!-- Edit mode -->
      <div v-show="!showPreview" class="relative">
        <textarea
          ref="textareaRef"
          v-model="content"
          class="w-full h-64 p-4 font-mono text-sm text-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
          placeholder="Enter your template content here...&#10;&#10;Use placeholders like {canary_url} for tracking URLs."
          @click="updateCursorPosition"
          @keyup="updateCursorPosition"
        />

        <!-- Character count -->
        <div class="absolute bottom-2 right-2 text-xs text-gray-400">
          {{ content.length }} characters
        </div>
      </div>

      <!-- Preview mode -->
      <div v-show="showPreview" class="p-4 bg-gray-50 min-h-[256px]">
        <div class="mb-2 text-xs text-gray-500 flex items-center">
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          Preview with sample values
        </div>
        <pre class="font-mono text-sm text-gray-800 whitespace-pre-wrap break-words">{{ previewContent }}</pre>
      </div>
    </div>

    <!-- Help text -->
    <div class="mt-3 p-3 bg-blue-50 rounded-lg">
      <div class="flex items-start">
        <svg class="w-4 h-4 text-blue-400 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div class="text-xs text-blue-700">
          <p class="font-medium mb-1">Token Placeholders:</p>
          <ul class="space-y-1 list-disc list-inside">
            <li><code class="bg-blue-100 px-1 rounded">{canary_token-URL}</code> - Web tracking URL (triggers on click/load)</li>
            <li><code class="bg-blue-100 px-1 rounded">{canary_token-DNS}</code> - DNS token (triggers on lookup)</li>
            <li><code class="bg-blue-100 px-1 rounded">{canary_token-WORD}</code> - Word document token URL</li>
            <li><code class="bg-blue-100 px-1 rounded">{canary_token-EXCEL}</code> - Excel spreadsheet token URL</li>
            <li><code class="bg-blue-100 px-1 rounded">{canary_token-PDF}</code> - PDF document token URL</li>
            <li><code class="bg-blue-100 px-1 rounded">{drive_code}</code> - Unique drive identifier</li>
          </ul>
          <p class="mt-2 text-blue-600">Use multiple token types to track different interactions!</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.template-editor {
  @apply w-full;
}

textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
}
</style>
