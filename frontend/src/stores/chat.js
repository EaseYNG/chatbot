import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { streamChat } from '../api/client.js'
import { useConversationsStore } from './conversations.js'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isStreaming = ref(false)
  const errorMessage = ref('')
  const workflowEvents = ref([])

  const convStore = useConversationsStore()
  watch(() => convStore.activeId, () => {
    if (isStreaming.value) {
      isStreaming.value = false
    }
    errorMessage.value = ''
  })

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

  function addWorkflowEvent(kind, payload = {}) {
    workflowEvents.value.push({ kind, ...payload })
  }

  function setMessages(msgs) {
    messages.value = msgs
  }

  function clearMessages() {
    messages.value = []
    errorMessage.value = ''
    workflowEvents.value = []
  }

  async function sendMessage(text) {
    if (!text.trim() || isStreaming.value) return

    errorMessage.value = ''
    workflowEvents.value = []
    addMessage('human', text)

    const convStore = useConversationsStore()
    const threadId = convStore.activeId
    const isNewConv = !threadId

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
            addWorkflowEvent('done', event)
            if (isNewConv && event.thread_id) {
              convStore.setActiveId(event.thread_id)
              convStore.fetchList()
            } else if (isNewConv) {
              convStore.fetchList()
            }
            break

          case 'stage_start':
            addWorkflowEvent('stage_start', event)
            break

          case 'stage_end':
            addWorkflowEvent('stage_end', event)
            break

          case 'route':
            addWorkflowEvent('route', event)
            break

          case 'plan':
            addWorkflowEvent('plan', event)
            break

          case 'step_start':
            addWorkflowEvent('step_start', event)
            break

          case 'step_end':
            addWorkflowEvent('step_end', event)
            break

          case 'agent_start':
            addWorkflowEvent('agent_start', event)
            break

          case 'agent_end':
            addWorkflowEvent('agent_end', event)
            break

          case 'quality':
            addWorkflowEvent('quality', event)
            break

          case 'warning':
            addWorkflowEvent('warning', event)
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
    workflowEvents,
    addMessage,
    setMessages,
    clearMessages,
    sendMessage,
  }
})
