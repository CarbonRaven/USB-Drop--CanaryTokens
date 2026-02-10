<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  error.value = ''
  loading.value = true

  try {
    await authStore.login(username.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface-950 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-bold text-surface-0">
          USB Drop Campaign Manager
        </h2>
        <p class="mt-2 text-center text-sm text-surface-400">
          Sign in to manage your campaigns
        </p>
      </div>

      <div class="bg-surface-900 border border-surface-700 rounded-lg p-8">
        <form class="space-y-6" @submit.prevent="handleLogin">
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

          <div class="space-y-4">
            <div>
              <label for="username" class="block text-sm font-medium text-surface-300 mb-1">Username</label>
              <InputText
                id="username"
                v-model="username"
                type="text"
                required
                class="w-full"
                placeholder="Enter username"
              />
            </div>

            <div>
              <label for="password" class="block text-sm font-medium text-surface-300 mb-1">Password</label>
              <InputText
                id="password"
                v-model="password"
                type="password"
                required
                class="w-full"
                placeholder="Enter password"
              />
            </div>
          </div>

          <Button
            type="submit"
            label="Sign in"
            :loading="loading"
            class="w-full"
          />
        </form>
      </div>
    </div>
  </div>
</template>
