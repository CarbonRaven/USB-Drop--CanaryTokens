<script setup>
import { ref, onMounted, computed } from 'vue'
import { usersApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const users = ref([])
const roles = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showResetPasswordModal = ref(false)
const showChangePasswordModal = ref(false)
const editingUser = ref(null)
const saving = ref(false)
const error = ref('')

const newUser = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'viewer'
})

const editForm = ref({
  email: '',
  role: '',
  is_active: true
})

const resetPasswordForm = ref({
  new_password: '',
  confirm_password: ''
})

const changePasswordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordRequirements = [
  { test: (p) => p.length >= 12, label: 'At least 12 characters' },
  { test: (p) => /[A-Z]/.test(p), label: 'One uppercase letter' },
  { test: (p) => /[a-z]/.test(p), label: 'One lowercase letter' },
  { test: (p) => /\d/.test(p), label: 'One digit' },
  { test: (p) => /[!@#$%^&*(),.?":{}|<>]/.test(p), label: 'One special character' }
]

const passwordValid = computed(() => {
  const p = newUser.value.password
  return passwordRequirements.every(r => r.test(p))
})

const passwordsMatch = computed(() => {
  return newUser.value.password === newUser.value.confirmPassword
})

const resetPasswordValid = computed(() => {
  const p = resetPasswordForm.value.new_password
  return passwordRequirements.every(r => r.test(p)) &&
         resetPasswordForm.value.new_password === resetPasswordForm.value.confirm_password
})

const changePasswordValid = computed(() => {
  const p = changePasswordForm.value.new_password
  return changePasswordForm.value.current_password.length > 0 &&
         passwordRequirements.every(r => r.test(p)) &&
         changePasswordForm.value.new_password === changePasswordForm.value.confirm_password
})

onMounted(async () => {
  await Promise.all([loadUsers(), loadRoles()])
})

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await usersApi.list()
    users.value = response.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to load users'
  } finally {
    loading.value = false
  }
}

const loadRoles = async () => {
  try {
    const response = await usersApi.roles()
    roles.value = response.data.roles
  } catch (e) {
    console.error('Failed to load roles', e)
  }
}

const createUser = async () => {
  if (!passwordValid.value || !passwordsMatch.value) {
    error.value = 'Please fix password errors'
    return
  }

  saving.value = true
  error.value = ''
  try {
    await usersApi.create({
      username: newUser.value.username,
      email: newUser.value.email,
      password: newUser.value.password,
      role: newUser.value.role
    })
    showCreateModal.value = false
    newUser.value = { username: '', email: '', password: '', confirmPassword: '', role: 'viewer' }
    await loadUsers()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to create user'
  } finally {
    saving.value = false
  }
}

const openEditModal = (user) => {
  editingUser.value = user
  editForm.value = {
    email: user.email,
    role: user.role,
    is_active: user.is_active
  }
  error.value = ''
  showEditModal.value = true
}

const updateUser = async () => {
  saving.value = true
  error.value = ''
  try {
    await usersApi.update(editingUser.value.id, editForm.value)
    showEditModal.value = false
    editingUser.value = null
    await loadUsers()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to update user'
  } finally {
    saving.value = false
  }
}

const openResetPasswordModal = (user) => {
  editingUser.value = user
  resetPasswordForm.value = { new_password: '', confirm_password: '' }
  error.value = ''
  showResetPasswordModal.value = true
}

const resetPassword = async () => {
  if (!resetPasswordValid.value) {
    error.value = 'Please fix password errors'
    return
  }

  saving.value = true
  error.value = ''
  try {
    await usersApi.resetPassword(editingUser.value.id, {
      new_password: resetPasswordForm.value.new_password
    })
    showResetPasswordModal.value = false
    editingUser.value = null
    resetPasswordForm.value = { new_password: '', confirm_password: '' }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to reset password'
  } finally {
    saving.value = false
  }
}

const openChangePasswordModal = () => {
  changePasswordForm.value = { current_password: '', new_password: '', confirm_password: '' }
  error.value = ''
  showChangePasswordModal.value = true
}

const changePassword = async () => {
  if (!changePasswordValid.value) {
    error.value = 'Please fix password errors'
    return
  }

  saving.value = true
  error.value = ''
  try {
    await usersApi.changePassword({
      current_password: changePasswordForm.value.current_password,
      new_password: changePasswordForm.value.new_password
    })
    showChangePasswordModal.value = false
    changePasswordForm.value = { current_password: '', new_password: '', confirm_password: '' }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to change password'
  } finally {
    saving.value = false
  }
}

const deleteUser = async (user) => {
  if (!confirm(`Are you sure you want to deactivate user "${user.username}"?`)) {
    return
  }

  try {
    await usersApi.delete(user.id)
    await loadUsers()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to delete user'
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'Never'
  return new Date(dateStr).toLocaleString()
}

const roleColors = {
  admin: 'bg-red-100 text-red-800',
  operator: 'bg-blue-100 text-blue-800',
  viewer: 'bg-gray-100 text-gray-800',
  ADMIN: 'bg-red-100 text-red-800',
  OPERATOR: 'bg-blue-100 text-blue-800',
  VIEWER: 'bg-gray-100 text-gray-800'
}

const roleLabels = {
  admin: 'Admin',
  operator: 'Operator',
  viewer: 'Viewer',
  ADMIN: 'Admin',
  OPERATOR: 'Operator',
  VIEWER: 'Viewer'
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        User Management
      </h1>
      <div class="space-x-3">
        <button
          class="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          @click="openChangePasswordModal"
        >
          Change My Password
        </button>
        <button
          class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          @click="showCreateModal = true"
        >
          New User
        </button>
      </div>
    </div>

    <!-- Role Legend -->
    <div class="mb-4 flex items-center space-x-4 text-sm">
      <span class="text-gray-500">Roles:</span>
      <span
        v-for="role in roles"
        :key="role.value"
        class="flex items-center space-x-1"
      >
        <span :class="[roleColors[role.value], 'px-2 py-0.5 text-xs rounded-full']">{{ role.label }}</span>
        <span class="text-gray-500">- {{ role.description }}</span>
      </span>
    </div>

    <!-- Error Alert -->
    <div
      v-if="error"
      class="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded"
    >
      {{ error }}
      <button
        class="float-right text-red-700 hover:text-red-900"
        @click="error = ''"
      >
        &times;
      </button>
    </div>

    <!-- Users Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Username
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Email
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Role
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Last Login
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-if="loading">
            <td
              colspan="6"
              class="px-6 py-4 text-center text-gray-500"
            >
              Loading...
            </td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td
              colspan="6"
              class="px-6 py-4 text-center text-gray-500"
            >
              No users found
            </td>
          </tr>
          <tr
            v-for="user in users"
            :key="user.id"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4 font-medium">
              {{ user.username }}
              <span
                v-if="user.id === authStore.user?.id"
                class="ml-2 text-xs text-gray-500"
              >(you)</span>
            </td>
            <td class="px-6 py-4 text-gray-500">
              {{ user.email }}
            </td>
            <td class="px-6 py-4">
              <span :class="[roleColors[user.role] || roleColors.viewer, 'px-2 py-1 text-xs rounded-full']">
                {{ roleLabels[user.role] || user.role }}
              </span>
            </td>
            <td class="px-6 py-4">
              <span
                v-if="user.is_active"
                class="text-green-600"
              >Active</span>
              <span
                v-else
                class="text-red-600"
              >Inactive</span>
            </td>
            <td class="px-6 py-4 text-gray-500 text-sm">
              {{ formatDate(user.last_login) }}
            </td>
            <td class="px-6 py-4 space-x-2">
              <button
                class="text-primary-600 hover:underline text-sm"
                @click="openEditModal(user)"
              >
                Edit
              </button>
              <button
                class="text-blue-600 hover:text-blue-800 hover:underline text-sm"
                @click="openResetPasswordModal(user)"
              >
                Reset PW
              </button>
              <button
                v-if="user.id !== authStore.user?.id"
                class="text-red-600 hover:underline text-sm"
                @click="deleteUser(user)"
              >
                {{ user.is_active ? 'Deactivate' : 'Delete' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create User Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">
          Create User
        </h2>
        <form
          class="space-y-4"
          @submit.prevent="createUser"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700">Username</label>
            <input
              v-model="newUser.username"
              type="text"
              required
              pattern="[a-zA-Z0-9_-]+"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
            <p class="mt-1 text-xs text-gray-500">
              Letters, numbers, underscores, hyphens only
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Email</label>
            <input
              v-model="newUser.email"
              type="email"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Role</label>
            <select
              v-model="newUser.role"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option
                v-for="role in roles"
                :key="role.value"
                :value="role.value"
              >
                {{ role.label }} - {{ role.description }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Password</label>
            <input
              v-model="newUser.password"
              type="password"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
            <div class="mt-2 space-y-1">
              <p
                v-for="req in passwordRequirements"
                :key="req.label"
                :class="req.test(newUser.password) ? 'text-green-600' : 'text-gray-400'"
                class="text-xs flex items-center"
              >
                <span class="mr-1">{{ req.test(newUser.password) ? '&#10003;' : '&#9675;' }}</span>
                {{ req.label }}
              </p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Confirm Password</label>
            <input
              v-model="newUser.confirmPassword"
              type="password"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
            <p
              v-if="newUser.confirmPassword && !passwordsMatch"
              class="mt-1 text-xs text-red-600"
            >
              Passwords do not match
            </p>
          </div>
          <div
            v-if="error"
            class="text-red-600 text-sm"
          >
            {{ error }}
          </div>
          <div class="flex justify-end space-x-3">
            <button
              type="button"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="showCreateModal = false; error = ''"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saving || !passwordValid || !passwordsMatch"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {{ saving ? 'Creating...' : 'Create User' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit User Modal -->
    <div
      v-if="showEditModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">
          Edit User: {{ editingUser?.username }}
        </h2>
        <form
          class="space-y-4"
          @submit.prevent="updateUser"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700">Email</label>
            <input
              v-model="editForm.email"
              type="email"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Role</label>
            <select
              v-model="editForm.role"
              required
              :disabled="editingUser?.id === authStore.user?.id"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md disabled:bg-gray-100"
            >
              <option
                v-for="role in roles"
                :key="role.value"
                :value="role.value"
              >
                {{ role.label }}
              </option>
            </select>
            <p
              v-if="editingUser?.id === authStore.user?.id"
              class="mt-1 text-xs text-gray-500"
            >
              You cannot change your own role
            </p>
          </div>
          <div class="flex items-center">
            <input
              id="is_active"
              v-model="editForm.is_active"
              type="checkbox"
              :disabled="editingUser?.id === authStore.user?.id"
              class="h-4 w-4 text-primary-600 rounded border-gray-300"
            >
            <label
              for="is_active"
              class="ml-2 text-sm text-gray-700"
            >Active</label>
            <p
              v-if="editingUser?.id === authStore.user?.id"
              class="ml-2 text-xs text-gray-500"
            >
              (Cannot deactivate yourself)
            </p>
          </div>
          <div
            v-if="error"
            class="text-red-600 text-sm"
          >
            {{ error }}
          </div>
          <div class="flex justify-end space-x-3">
            <button
              type="button"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="showEditModal = false; error = ''"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Reset Password Modal (Admin) -->
    <div
      v-if="showResetPasswordModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">
          Reset Password: {{ editingUser?.username }}
        </h2>
        <form
          class="space-y-4"
          @submit.prevent="resetPassword"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700">New Password</label>
            <input
              v-model="resetPasswordForm.new_password"
              type="password"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
            <div class="mt-2 space-y-1">
              <p
                v-for="req in passwordRequirements"
                :key="req.label"
                :class="req.test(resetPasswordForm.new_password) ? 'text-green-600' : 'text-gray-400'"
                class="text-xs flex items-center"
              >
                <span class="mr-1">{{ req.test(resetPasswordForm.new_password) ? '&#10003;' : '&#9675;' }}</span>
                {{ req.label }}
              </p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Confirm Password</label>
            <input
              v-model="resetPasswordForm.confirm_password"
              type="password"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
            <p
              v-if="resetPasswordForm.confirm_password && resetPasswordForm.new_password !== resetPasswordForm.confirm_password"
              class="mt-1 text-xs text-red-600"
            >
              Passwords do not match
            </p>
          </div>
          <div
            v-if="error"
            class="text-red-600 text-sm"
          >
            {{ error }}
          </div>
          <div class="flex justify-end space-x-3">
            <button
              type="button"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="showResetPasswordModal = false; error = ''"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saving || !resetPasswordValid"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {{ saving ? 'Resetting...' : 'Reset Password' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Change My Password Modal -->
    <div
      v-if="showChangePasswordModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 class="text-lg font-medium mb-4">
          Change Your Password
        </h2>
        <form
          class="space-y-4"
          @submit.prevent="changePassword"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700">Current Password</label>
            <input
              v-model="changePasswordForm.current_password"
              type="password"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">New Password</label>
            <input
              v-model="changePasswordForm.new_password"
              type="password"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
            <div class="mt-2 space-y-1">
              <p
                v-for="req in passwordRequirements"
                :key="req.label"
                :class="req.test(changePasswordForm.new_password) ? 'text-green-600' : 'text-gray-400'"
                class="text-xs flex items-center"
              >
                <span class="mr-1">{{ req.test(changePasswordForm.new_password) ? '&#10003;' : '&#9675;' }}</span>
                {{ req.label }}
              </p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Confirm New Password</label>
            <input
              v-model="changePasswordForm.confirm_password"
              type="password"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
            >
            <p
              v-if="changePasswordForm.confirm_password && changePasswordForm.new_password !== changePasswordForm.confirm_password"
              class="mt-1 text-xs text-red-600"
            >
              Passwords do not match
            </p>
          </div>
          <div
            v-if="error"
            class="text-red-600 text-sm"
          >
            {{ error }}
          </div>
          <div class="flex justify-end space-x-3">
            <button
              type="button"
              class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              @click="showChangePasswordModal = false; error = ''"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saving || !changePasswordValid"
              class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {{ saving ? 'Changing...' : 'Change Password' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
