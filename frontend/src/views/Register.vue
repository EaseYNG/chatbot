<template>
  <div class="auth-container">
    <form class="auth-form" @submit.prevent="handleRegister">
      <h2>Register</h2>
      <p v-if="error" class="auth-error">{{ error }}</p>
      <input
        v-model="username"
        type="text"
        placeholder="Username (3-50 chars, a-z, 0-9, _)"
        required
        autocomplete="username"
      />
      <input
        v-model="password"
        type="password"
        placeholder="Password (min 6 chars)"
        required
        autocomplete="new-password"
      />
      <input
        v-model="confirmPassword"
        type="password"
        placeholder="Confirm password"
        required
        autocomplete="new-password"
      />
      <button type="submit" :disabled="loading">
        {{ loading ? 'Registering...' : 'Register' }}
      </button>
      <p class="auth-link">
        Already have an account?
        <button type="button" class="link-btn" @click="$emit('switch')">
          Login
        </button>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'

const emit = defineEmits(['switch', 'done'])
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.register(username.value, password.value)
    emit('done')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
}
.auth-form {
  background: #16213e;
  padding: 2.5rem;
  border-radius: 12px;
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.auth-form h2 {
  text-align: center;
  margin-bottom: 0.5rem;
}
.auth-error {
  color: #ff6b6b;
  font-size: 0.875rem;
  text-align: center;
}
input {
  padding: 0.75rem;
  border: 1px solid #0f3460;
  border-radius: 8px;
  background: #1a1a2e;
  color: #e0e0e0;
  font-size: 1rem;
}
button[type='submit'] {
  padding: 0.75rem;
  background: #0f3460;
  color: #e0e0e0;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
}
button[type='submit']:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.auth-link {
  text-align: center;
  font-size: 0.875rem;
}
.link-btn {
  background: none;
  border: none;
  color: #4fc3f7;
  text-decoration: underline;
  cursor: pointer;
  font-size: inherit;
}
</style>
