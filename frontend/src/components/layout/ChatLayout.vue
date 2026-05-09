<template>
  <div class="layout">
    <aside class="sidebar-shell">
      <Sidebar />
    </aside>
    <main class="chat-shell">
      <ChatPanel />
    </main>
  </div>
</template>

<script setup>
import Sidebar from '../sidebar/Sidebar.vue'
import ChatPanel from '../chat/ChatPanel.vue'
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar-shell {
  width: 280px;
  min-width: 280px;
  border-right: 1px solid #2a2a4a;
  display: flex;
  flex-direction: column;
}

.chat-shell {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
</style>
