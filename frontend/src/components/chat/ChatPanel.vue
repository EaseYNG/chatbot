<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span class="chat-title" :class="{ 'new-chat': !title }">{{ title || 'New Conversation' }}</span>
    </div>

    <WorkflowTimeline />

    <div class="chat-body">
      <MessageList
        :messages="chatStore.messages"
        :is-streaming="chatStore.isStreaming"
      />
    </div>

    <div v-if="conversations.error" class="chat-error">
      Store: {{ conversations.error }}
      <button class="err-close" @click="conversations.error = ''">&times;</button>
    </div>

    <div v-if="chatStore.errorMessage" class="chat-error">
      {{ chatStore.errorMessage }}
      <button class="err-close" @click="chatStore.errorMessage = ''">&times;</button>
    </div>

    <ChatInput
      :disabled="chatStore.isStreaming"
      @send="chatStore.sendMessage($event)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '../../stores/chat.js'
import { useConversationsStore } from '../../stores/conversations.js'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'
import WorkflowTimeline from './WorkflowTimeline.vue'

const chatStore = useChatStore()
const conversations = useConversationsStore()

const title = computed(() => {
  if (!conversations.activeId) return ''
  const conv = conversations.list.find(c => c.thread_id === conversations.activeId)
  return conv?.title || 'Chat'
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a2e;
}

.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid #2a2a4a;
  background: #16162a;
}

.chat-title {
  font-size: 15px;
  font-weight: 500;
  color: #c0c0e0;
}
.chat-title.new-chat {
  color: #888;
  font-style: italic;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.chat-error {
  margin: 0 16px 8px;
  padding: 8px 12px;
  background: #4a2020;
  border: 1px solid #6a3030;
  border-radius: 6px;
  color: #e08080;
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.err-close {
  background: none;
  border: none;
  color: #e08080;
  font-size: 18px;
  cursor: pointer;
}
</style>
