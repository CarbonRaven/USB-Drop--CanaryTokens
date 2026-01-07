import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { profilesApi } from '@/services/api'

export const useProfileWizardStore = defineStore('profileWizard', () => {
  // Step management
  const currentStep = ref(1)
  const totalSteps = 5

  // Step 1: Scenario
  const scenario = ref({
    type: null,
    template_id: null,
    name: '',
    description: ''
  })

  // Step 2: Folders
  const folders = ref([])

  // Step 3: Files/Tokens
  const files = ref([])

  // Uploaded files (from API)
  const uploadedFiles = ref([])

  // Step 4: Content (Phase 2)
  const content = ref({
    text_templates: {},
    url_shortener: {
      enabled: false,
      base_slug: '',
      suffix_mode: 'random',
      suffix_length: 4,
      domain: ''
    },
    images: {
      source: 'template',
      selected: []
    },
    label_suggestions: []
  })

  // Validation errors
  const errors = ref({})

  // Edit mode
  const isEditing = ref(false)
  const editingProfileId = ref(null)

  // Loading states
  const loading = ref(false)
  const saving = ref(false)

  // Templates cache
  const templates = ref([])
  const templatesLoaded = ref(false)

  // Computed
  const canProceed = computed(() => {
    switch (currentStep.value) {
      case 1:
        return scenario.value.name?.trim().length > 0 && scenario.value.type !== null
      case 2:
        return folders.value.length > 0
      case 3:
        return files.value.length > 0
      case 4:
        return true // Content step is optional in Phase 1
      case 5:
        return true // Review step
      default:
        return false
    }
  })

  const tokenCount = computed(() => {
    return files.value.filter(f => f.token_type).length
  })

  const folderCount = computed(() => {
    return folders.value.length
  })

  const fileCount = computed(() => {
    return files.value.length
  })

  const uploadedFileCount = computed(() => {
    return uploadedFiles.value.length
  })

  const totalFileCount = computed(() => {
    return files.value.length + uploadedFiles.value.length
  })

  const profileSummary = computed(() => ({
    name: scenario.value.name,
    description: scenario.value.description,
    scenario_type: scenario.value.type,
    folders: folderCount.value,
    files: fileCount.value,
    tokens: tokenCount.value
  }))

  // Actions
  function nextStep() {
    if (currentStep.value < totalSteps && canProceed.value) {
      currentStep.value++
    }
  }

  function prevStep() {
    if (currentStep.value > 1) {
      currentStep.value--
    }
  }

  function goToStep(step) {
    if (step >= 1 && step <= totalSteps) {
      currentStep.value = step
    }
  }

  async function loadTemplates() {
    if (templatesLoaded.value) return templates.value

    try {
      loading.value = true
      const response = await profilesApi.templates()
      templates.value = response.data
      templatesLoaded.value = true
      return templates.value
    } catch (error) {
      console.error('Failed to load templates:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function loadTemplate(templateId) {
    try {
      loading.value = true
      const response = await profilesApi.getTemplate(templateId)
      const template = response.data

      // Populate scenario
      scenario.value.type = templateId
      scenario.value.template_id = templateId
      if (!scenario.value.name) {
        scenario.value.name = template.name
      }
      scenario.value.description = template.description

      // Populate folders
      folders.value = template.folders.map(path => ({
        path,
        has_folder_token: false
      }))

      // Populate files
      files.value = template.files.map(file => ({
        name: file.name,
        folder: file.folder || '',
        token_type: file.type || null,
        token_config: {}
      }))

      return template
    } catch (error) {
      console.error('Failed to load template:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function loadForEditing(profileId) {
    try {
      loading.value = true
      const response = await profilesApi.get(profileId)
      const profile = response.data

      isEditing.value = true
      editingProfileId.value = profileId

      // Populate from profile
      scenario.value = {
        type: profile.scenario_type,
        template_id: null,
        name: profile.name,
        description: profile.description || ''
      }

      // Parse file_structure
      const fileStructure = profile.file_structure || {}
      folders.value = (fileStructure.folders || []).map(path => ({
        path,
        has_folder_token: false
      }))

      files.value = (fileStructure.files || []).map(file => ({
        name: file.name,
        folder: file.folder || '',
        token_type: file.type || null,
        token_config: {},
        custom_content: file.custom_content || null
      }))

      // Parse other config
      content.value.label_suggestions = profile.label_suggestions || []

      // Parse url_config
      if (profile.url_config) {
        content.value.url_shortener = {
          enabled: profile.url_config.enabled || false,
          base_slug: profile.url_config.base_slug || '',
          suffix_mode: profile.url_config.suffix_mode || 'random',
          suffix_length: profile.url_config.suffix_length || 4,
          domain: profile.url_config.domain || ''
        }
      }

      return profile
    } catch (error) {
      console.error('Failed to load profile for editing:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function saveProfile() {
    try {
      saving.value = true

      // Build url_config from content settings
      const urlConfig = content.value.url_shortener.enabled ? {
        enabled: true,
        base_slug: content.value.url_shortener.base_slug || '',
        suffix_mode: content.value.url_shortener.suffix_mode || 'random',
        suffix_length: content.value.url_shortener.suffix_length || 4,
        domain: content.value.url_shortener.domain || null
      } : { enabled: false }

      const profileData = {
        name: scenario.value.name,
        description: scenario.value.description,
        scenario_type: scenario.value.type,
        file_structure: {
          folders: folders.value.map(f => f.path),
          files: files.value.map(f => ({
            name: f.name,
            folder: f.folder,
            type: f.token_type,
            custom_content: f.custom_content || f.content || null
          }))
        },
        token_config: {},
        url_config: urlConfig,
        label_suggestions: content.value.label_suggestions
      }

      let response
      if (isEditing.value && editingProfileId.value) {
        response = await profilesApi.update(editingProfileId.value, profileData)
      } else {
        response = await profilesApi.create(profileData)
      }

      return response.data
    } catch (error) {
      console.error('Failed to save profile:', error)
      throw error
    } finally {
      saving.value = false
    }
  }

  function addFolder(path) {
    if (!folders.value.find(f => f.path === path)) {
      folders.value.push({
        path,
        has_folder_token: false
      })
    }
  }

  function removeFolder(path) {
    const index = folders.value.findIndex(f => f.path === path)
    if (index !== -1) {
      folders.value.splice(index, 1)
      // Also remove files in this folder
      files.value = files.value.filter(f => f.folder !== path)
    }
  }

  function updateFolder(oldPath, newPath) {
    const folder = folders.value.find(f => f.path === oldPath)
    if (folder) {
      folder.path = newPath
      // Update files in this folder
      files.value.forEach(f => {
        if (f.folder === oldPath) {
          f.folder = newPath
        }
      })
    }
  }

  function addFile(file) {
    files.value.push({
      name: file.name,
      folder: file.folder || '',
      token_type: file.token_type || null,
      token_config: file.token_config || {}
    })
  }

  function removeFile(index) {
    if (index >= 0 && index < files.value.length) {
      files.value.splice(index, 1)
    }
  }

  function updateFile(index, updates) {
    if (index >= 0 && index < files.value.length) {
      Object.assign(files.value[index], updates)
    }
  }

  // Uploaded file management
  async function loadUploadedFiles(profileId) {
    if (!profileId) return []
    try {
      const response = await profilesApi.listFiles(profileId)
      uploadedFiles.value = response.data
      return uploadedFiles.value
    } catch (error) {
      console.error('Failed to load uploaded files:', error)
      return []
    }
  }

  function addUploadedFile(file) {
    uploadedFiles.value.push(file)
  }

  async function removeUploadedFile(profileId, fileId) {
    try {
      await profilesApi.deleteFile(profileId, fileId)
      const index = uploadedFiles.value.findIndex(f => f.id === fileId)
      if (index !== -1) {
        uploadedFiles.value.splice(index, 1)
      }
      return true
    } catch (error) {
      console.error('Failed to delete uploaded file:', error)
      throw error
    }
  }

  async function updateUploadedFile(profileId, fileId, updates) {
    try {
      const response = await profilesApi.updateFile(profileId, fileId, updates)
      const index = uploadedFiles.value.findIndex(f => f.id === fileId)
      if (index !== -1) {
        uploadedFiles.value[index] = response.data
      }
      return response.data
    } catch (error) {
      console.error('Failed to update uploaded file:', error)
      throw error
    }
  }

  function reset() {
    currentStep.value = 1
    scenario.value = {
      type: null,
      template_id: null,
      name: '',
      description: ''
    }
    folders.value = []
    files.value = []
    uploadedFiles.value = []
    content.value = {
      text_templates: {},
      url_shortener: {
        enabled: false,
        base_slug: '',
        suffix_mode: 'random',
        suffix_length: 4,
        domain: ''
      },
      images: {
        source: 'template',
        selected: []
      },
      label_suggestions: []
    }
    errors.value = {}
    isEditing.value = false
    editingProfileId.value = null
  }

  return {
    // State
    currentStep,
    totalSteps,
    scenario,
    folders,
    files,
    uploadedFiles,
    content,
    errors,
    isEditing,
    editingProfileId,
    loading,
    saving,
    templates,

    // Computed
    canProceed,
    tokenCount,
    folderCount,
    fileCount,
    uploadedFileCount,
    totalFileCount,
    profileSummary,

    // Actions
    nextStep,
    prevStep,
    goToStep,
    loadTemplates,
    loadTemplate,
    loadForEditing,
    saveProfile,
    addFolder,
    removeFolder,
    updateFolder,
    addFile,
    removeFile,
    updateFile,
    loadUploadedFiles,
    addUploadedFile,
    removeUploadedFile,
    updateUploadedFile,
    reset
  }
})
