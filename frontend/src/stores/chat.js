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

  // ---- 状态消息管理 ----

  const stageLabels = {
    INIT: '初始化',
    INPUT: '分析用户意图',
    COMPLEXITY: '评估任务复杂度',
    ROUTING: '选择执行模式',
    EXECUTION: '执行任务',
    OUTPUT: '整理输出结果',
    QUALITY: '检查输出质量',
  }

  function upsertStatus(statusId, label, state = 'running') {
    const existing = messages.value.find(
      m => m.role === 'status' && m.status_id === statusId
    )
    if (existing) {
      existing.label = label
      existing.state = state
      return
    }
    messages.value.push({
      role: 'status',
      status_id: statusId,
      label,
      state,
      ts: Date.now(),
    })
  }

  function finishStatus(statusId) {
    const existing = messages.value.find(
      m => m.role === 'status' && m.status_id === statusId
    )
    if (existing) {
      existing.state = 'done'
    }
  }

  // 清理所有 running 状态消息（done 时调用）
  function finishAllStatuses() {
    for (const m of messages.value) {
      if (m.role === 'status' && m.state === 'running') {
        m.state = 'done'
      }
    }
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
    let pendingAiContent = ''

    try {
      for await (const event of streamChat(threadId, text)) {
        switch (event.type) {
          case 'token':
            pendingAiContent += (event.content || '')
            break

          case 'tool_start':
            upsertStatus(`tool:${event.tool_name}`, `调用工具: ${event.tool_name}`)
            break

          case 'tool_end':
            finishStatus(`tool:${event.tool_name}`)
            addMessage('tool', `工具 ${event.tool_name} 执行完成`, {
              tool_name: event.tool_name,
              tool_output: event.tool_output,
              status: 'done',
            })
            break

          case 'done':
            finishAllStatuses()
            if (pendingAiContent) {
              addMessage('ai', pendingAiContent)
            }
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
            if (event.stage && event.stage !== 'INIT' && event.stage !== 'DONE') {
              upsertStatus(
                `stage:${event.stage}`,
                event.label || stageLabels[event.stage] || event.stage
              )
            }
            break

          case 'stage_end':
            addWorkflowEvent('stage_end', event)
            if (event.stage && event.stage !== 'INIT' && event.stage !== 'DONE') {
              finishStatus(`stage:${event.stage}`)
            }
            break

          case 'route':
            addWorkflowEvent('route', event)
            break

          case 'plan':
            addWorkflowEvent('plan', event)
            if (event.steps && Array.isArray(event.steps)) {
              const names = event.steps.map(s => s.title).join(' → ')
              upsertStatus('plan', `计划: ${names}`, 'done')
            }
            break

          case 'step_start':
            addWorkflowEvent('step_start', event)
            upsertStatus(
              `step:${event.step_id}`,
              `执行步骤: ${event.title || event.step_id}`
            )
            break

          case 'step_end':
            addWorkflowEvent('step_end', event)
            finishStatus(`step:${event.step_id}`)
            break

          case 'agent_start':
            addWorkflowEvent('agent_start', event)
            upsertStatus(
              `agent:${event.agent}`,
              `${event.label || event.agent} 工作中`
            )
            break

          case 'agent_end':
            addWorkflowEvent('agent_end', event)
            finishStatus(`agent:${event.agent}`)
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
      if (pendingAiContent) {
        addMessage('ai', pendingAiContent)
      } else if (!messages.value[messages.value.length - 1]?.content) {
        addMessage('ai', 'Error: ' + e.message)
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
