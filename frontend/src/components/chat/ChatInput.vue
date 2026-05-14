<template>
  <div class="chat-input-area">
    <div class="input-row">
      <textarea
        ref="inputRef"
        v-model="text"
        class="input-field"
        placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
        :disabled="disabled"
        rows="1"
        @keydown="onKeydown"
        @input="autoResize"
      />
      <button
        class="btn-send"
        :disabled="disabled || !text.trim()"
        @click="doSend"
      >
        <span v-if="disabled">&#9632;</span>
        <span v-else>&#9654;</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['send'])

const text = ref('')
const inputRef = ref(null)

function autoResize() {
  nextTick(() => {
    const el = inputRef.value
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 200) + 'px'
    }
  })
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    doSend()
  }
}

function doSend() {
  const msg = text.value.trim()
  if (!msg || props.disabled) return
  emit('send', msg)
  text.value = ''
  nextTick(() => {
    const el = inputRef.value
    if (el) {
      el.style.height = 'auto'
    }
  })
}
</script>

<style scoped>
.chat-input-area {
  padding: 12px 20px 16px;
  border-top: 1px solid #2a2a4a;
  background: #16162a;
}

.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  max-width: 900px;
  margin: 0 48px;
}

.input-field {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #3a3a6a;
  border-radius: 10px;
  background: #1a1a32;
  color: #d0d0e0;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  max-height: 200px;
  transition: border-color 0.15s;
}
.input-field:focus {
  border-color: #5a5aaa;
}
.input-field:disabled {
  opacity: 0.5;
}

.btn-send {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 10px;
  background: #4a4aaa;
  color: white;
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.btn-send:hover:not(:disabled) {
  background: #5a5acc;
}
.btn-send:disabled {
  background: #2a2a4a;
  color: #666;
  cursor: not-allowed;
}
</style>
