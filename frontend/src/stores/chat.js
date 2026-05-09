import { defineStore } from 'pinia'
import { ref } from 'vue'
import { streamChat } from '../api/client.js'
import { useConversationsStore } from './conversations.js'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isStreaming = ref(false)
  const errorMessage = ref('')

  function appendToLastMessage(content) {
    const last = messages.value[messages.value.length - 1]
    if (!last || last.role !== 'ai') {
      addMessage('ai', '')
    }
    const ai = messages.value[messages.value.length - 1]
    ai.content = (ai.content || '') + content
  }

  function addMessage(role, content, extra = {}) {
    messages.value.push({ role, content, ...extra })
  }

  function setMessages(msgs) {
    messages.value = msgs
  }

  function clearMessages() {
    messages.value = []
    errorMessage.value = ''
  }

  async function sendMessage(text) {
    if (!text.trim() || isStreaming.value) return

    errorMessage.value = ''
    addMessage('human', text)

    const convStore = useConversationsStore()
    const threadId = convStore.activeId
    const isNewConv = !threadId

    addMessage('ai', '')
    isStreaming.value = true

    try {
      for await (const event of streamChat(threadId, text)) {
        switch (event.type) {
          case 'token':
            appendToLastMessage(event.content || '')
            break

          case 'tool_start':
            addMessage('tool', `Calling ${event.tool_name}...`, {
              tool_name: event.tool_name,
              tool_input: event.tool_input,
              status: 'running',
            })
            break

          case 'tool_end': {
            for (let i = messages.value.length - 1; i >= 0; i--) {
              const m = messages.value[i]
              if (m.role === 'tool' && m.tool_name === event.tool_name && m.status === 'running') {
                m.content = `Tool ${event.tool_name}: ${event.tool_output}`
                m.status = 'done'
                m.tool_output = event.tool_output
                break
              }
            }
            break
          }

          case 'done':
            if (isNewConv && event.thread_id) {
              convStore.setActiveId(event.thread_id)
              convStore.fetchList()
            } else if (isNewConv) {
              convStore.fetchList()
            }
            break

          case 'error':
            errorMessage.value = event.message || 'Unknown error'
            break
        }
      }
    } catch (e) {
      errorMessage.value = e.message
      if (!messages.value[messages.value.length - 1]?.content) {
        appendToLastMessage('Error: ' + e.message)
      }
    } finally {
      isStreaming.value = false
    }
  }

  return {
    messages,
    isStreaming,
    errorMessage,
    addMessage,
    setMessages,
    clearMessages,
    sendMessage,
  }
})
