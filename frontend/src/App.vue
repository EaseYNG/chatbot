<template>
  <div v-if="!auth.isAuthenticated" class="auth-wrapper">
    <Login
      v-if="authView === 'login'"
      @done="authReady"
      @switch="authView = 'register'"
    />
    <Register
      v-else
      @done="authReady"
      @switch="authView = 'login'"
    />
  </div>
  <ChatLayout v-else />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from './stores/auth.js'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import ChatLayout from './components/layout/ChatLayout.vue'

const auth = useAuthStore()
const authView = ref('login')

onMounted(async () => {
  if (auth.isAuthenticated) {
    await auth.fetchUser()
  }
})

function authReady() {
  auth.fetchUser()
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #1a1a2e;
  color: #e0e0e0;
}

.auth-wrapper {
  height: 100vh;
}
</style>
