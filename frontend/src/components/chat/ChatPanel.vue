<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span v-if="conversations.activeId" class="chat-title">
        Thread #{{ conversations.activeId }}
      </span>
      <span v-else class="chat-title new-chat">New Conversation</span>
    </div>

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
import { useChatStore } from '../../stores/chat.js'
import { useConversationsStore } from '../../stores/conversations.js'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'

const chatStore = useChatStore()
const conversations = useConversationsStore()
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
