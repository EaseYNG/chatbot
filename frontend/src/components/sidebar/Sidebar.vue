<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <h2 class="logo">ChatBot</h2>
      <button class="btn-new" @click="handleNewChat()">+ New Chat</button>
    </div>

    <div v-if="conversations.error" class="sidebar-error-bar">
      <span>{{ conversations.error }}</span>
      <button class="err-dismiss" @click="conversations.clearError()">&times;</button>
    </div>

    <div class="sidebar-list">
      <div v-if="conversations.loading && conversations.list.length === 0" class="sidebar-empty">Loading...</div>

      <div v-else-if="!conversations.loading && conversations.list.length === 0 && !conversations.error" class="sidebar-empty">
        No conversations yet
      </div>

      <div v-else-if="!conversations.loading && conversations.list.length === 0 && conversations.error" class="sidebar-error">
        <button class="btn-retry" @click="conversations.retryFetchList()">Retry</button>
      </div>

      <ConversationItem
        v-for="conv in conversations.list"
        :key="conv.thread_id"
        :conv="conv"
        :is-active="conv.thread_id === conversations.activeId"
        @select="handleSelect(conv.thread_id)"
        @delete="handleDelete(conv.thread_id)"
      />
    </div>

    <div class="sidebar-footer">
      <button class="btn-logout" @click="handleLogout">Logout</button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useConversationsStore } from '../../stores/conversations.js'
import { useChatStore } from '../../stores/chat.js'
import { useAuthStore } from '../../stores/auth.js'
import ConversationItem from './ConversationItem.vue'

const conversations = useConversationsStore()
const chatStore = useChatStore()
const auth = useAuthStore()

function handleLogout() {
  auth.clear()
  chatStore.clearMessages()
  conversations.list = []
  conversations.activeId = null
}

async function handleSelect(id) {
  const prevActiveId = conversations.activeId
  const prevMessages = [...chatStore.messages]

  const ok = await conversations.selectConversation(id)
  if (ok) {
    chatStore.setMessages(conversations.lastFetchedMessages)
  } else {
    conversations.setActiveId(prevActiveId)
    chatStore.setMessages(prevMessages)
  }
}

function handleNewChat() {
  conversations.newConversation()
  chatStore.clearMessages()
}

async function handleDelete(id) {
  await conversations.deleteConversation(id)
  if (!conversations.activeId) {
    chatStore.clearMessages()
  }
}

onMounted(() => {
  conversations.fetchList()
})
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #16162a;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #2a2a4a;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #c8b0ff;
  letter-spacing: 1px;
  margin-bottom: 14px;
  text-align: center;
}

.btn-new {
  width: 100%;
  padding: 8px 16px;
  border: 1px solid #4a4a8a;
  border-radius: 8px;
  background: #252550;
  color: #c0c0ff;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-new:hover {
  background: #353570;
}

.sidebar-error-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  margin: 0;
  background: #3a1a1a;
  border-bottom: 1px solid #5a3030;
  color: #e08080;
  font-size: 12px;
}

.err-dismiss {
  background: none;
  border: none;
  color: #e08080;
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
}
.err-dismiss:hover {
  color: #ff8080;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.sidebar-empty {
  padding: 24px 16px;
  text-align: center;
  color: #666;
  font-size: 14px;
}

.sidebar-error {
  padding: 24px 16px;
  text-align: center;
}

.btn-retry {
  padding: 6px 16px;
  border: 1px solid #5a3030;
  border-radius: 6px;
  background: #3a2020;
  color: #e08080;
  font-size: 13px;
  cursor: pointer;
}
.btn-retry:hover {
  background: #4a2828;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #2a2a4a;
}

.btn-logout {
  width: 100%;
  padding: 8px 16px;
  border: 1px solid #5a3030;
  border-radius: 8px;
  background: #3a2020;
  color: #e08080;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-logout:hover {
  background: #4a2828;
}
</style>