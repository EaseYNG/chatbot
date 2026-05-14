<template>
  <div class="message-list" ref="listRef">
    <div v-if="messages.length === 0" class="list-empty">
      <div class="empty-logo">ChatBot</div>
      <p class="empty-hint">Type a message to start a conversation</p>
    </div>
    <MessageItem
      v-for="(msg, idx) in messages"
      :key="idx + '-' + msg.role"
      :message="msg"
      :is-streaming="isStreaming && idx === messages.length - 1 && msg.role === 'ai'"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import MessageItem from './MessageItem.vue'

const props = defineProps({
  messages: { type: Array, required: true },
  isStreaming: { type: Boolean, default: false },
})

const listRef = ref(null)
let rafId = null

function isNearBottom() {
  const el = listRef.value
  if (!el) return true
  return el.scrollHeight - el.scrollTop - el.clientHeight < 60
}

function scrollToBottom(force = false) {
  if (!force && !isNearBottom()) return
  if (rafId) return
  rafId = requestAnimationFrame(() => {
    rafId = null
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, () => nextTick(() => scrollToBottom(true)))
watch(
  () => props.messages[props.messages.length - 1]?.content,
  () => { if (props.isStreaming) scrollToBottom() },
)
</script>

<style scoped>
.message-list {
  padding: 16px 0;
  overflow-y: auto;
  height: 100%;
}

.list-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #555;
  gap: 16px;
  user-select: none;
}

.empty-logo {
  font-size: 36px;
  font-weight: 700;
  color: #3a3a6a;
  letter-spacing: 2px;
}

.empty-hint {
  font-size: 14px;
  color: #555;
}
</style>
