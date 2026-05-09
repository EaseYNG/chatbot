<template>
  <div v-if="visible" class="timeline" :class="{ expanded: showDetail }">
    <div class="timeline-bar" @click="showDetail = hasSteps && !showDetail">
      <div class="bar-left">
        <span class="badge-mode" :class="modeClass">{{ modeLabel }}</span>

        <span v-if="hasSteps" class="step-dots">
          <span
            v-for="step in planSteps"
            :key="step.step_id"
            class="dot"
            :class="step.status"
            :title="step.title + ' (' + step.agent + ')'"
          ></span>
        </span>

        <span class="bar-agent">{{ activeAgent || '...' }}</span>
      </div>

      <div class="bar-right">
        <span v-if="qualityScore !== null" class="badge-q" :class="qualityClass">
          {{ qualityScore }}
        </span>
        <button
          v-if="hasSteps"
          class="btn-toggle"
          @click.stop="showDetail = !showDetail"
        >{{ showDetail ? '收起' : '步骤' }}</button>
      </div>
    </div>

    <div v-if="showDetail && hasSteps" class="timeline-detail">
      <div
        v-for="step in planSteps"
        :key="step.step_id"
        class="step-row"
        :class="step.status"
      >
        <span class="step-mark">
          <span v-if="step.status === 'running'" class="spinner"></span>
          <span v-else-if="step.status === 'done'" class="check">&#10003;</span>
          <span v-else class="pending-mark"></span>
        </span>
        <span class="step-name">{{ step.title }}</span>
        <span class="step-by">{{ step.agent }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useChatStore } from '../../stores/chat.js'

const chatStore = useChatStore()
const showDetail = ref(false)

const visible = computed(() => {
  return chatStore.workflowEvents.length > 0
})

const planSteps = computed(() => {
  const planEvent = chatStore.workflowEvents.find(e => e.kind === 'plan')
  if (!planEvent || !Array.isArray(planEvent.steps)) return []

  const stepStarts = new Set(chatStore.workflowEvents.filter(e => e.kind === 'step_start').map(e => e.step_id))
  const stepEnds = new Set(chatStore.workflowEvents.filter(e => e.kind === 'step_end').map(e => e.step_id))

  return planEvent.steps.map(step => {
    let status = 'pending'
    if (stepEnds.has(step.step_id)) status = 'done'
    else if (stepStarts.has(step.step_id)) status = 'running'
    return { ...step, status }
  })
})

const hasSteps = computed(() => planSteps.value.length > 0)

const modeLabel = computed(() => {
  const routeEvent = chatStore.workflowEvents.find(e => e.kind === 'route')
  const mode = routeEvent?.mode
  const labels = { REACT: '快速回答', PLAN_EXECUTE: '计划执行', WORKFLOW: '协作' }
  return labels[mode] || mode || '...'
})

const modeClass = computed(() => {
  const routeEvent = chatStore.workflowEvents.find(e => e.kind === 'route')
  const mode = routeEvent?.mode
  return { REACT: 'c-react', PLAN_EXECUTE: 'c-plan', WORKFLOW: 'c-flow' }[mode] || ''
})

const activeAgent = computed(() => {
  const starts = chatStore.workflowEvents.filter(e => e.kind === 'agent_start')
  const ends = chatStore.workflowEvents.filter(e => e.kind === 'agent_end')
  if (starts.length > ends.length) {
    return starts[starts.length - 1].label || starts[starts.length - 1].agent
  }
  const routeEvent = chatStore.workflowEvents.find(e => e.kind === 'route')
  return routeEvent?.agent || null
})

const qualityScore = computed(() => {
  const q = chatStore.workflowEvents.find(e => e.kind === 'quality')
  return q?.score ?? null
})

const qualityClass = computed(() => {
  const q = chatStore.workflowEvents.find(e => e.kind === 'quality')
  return q?.passed ? 'q-pass' : 'q-fail'
})

watch(() => chatStore.isStreaming, (val) => {
  if (!val) {
    const doneEvent = chatStore.workflowEvents.find(e => e.kind === 'done')
    if (doneEvent) {
      setTimeout(() => { showDetail.value = false }, 4000)
    }
  }
})
</script>

<style scoped>
.timeline {
  background: #12122a;
  border-bottom: 1px solid #22224a;
  font-size: 12px;
  user-select: none;
}

.timeline-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 16px;
  min-height: 28px;
  gap: 10px;
}

.bar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.badge-mode {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
  letter-spacing: 0.3px;
  flex-shrink: 0;
}

.c-react { background: #1a2a1a; color: #60c060; }
.c-plan  { background: #1a1a2a; color: #6080c0; }
.c-flow  { background: #2a1a2a; color: #c080c0; }

.step-dots {
  display: flex;
  gap: 3px;
  align-items: center;
}

.step-dots .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #333;
  transition: background 0.2s;
}

.step-dots .dot.running {
  background: #6080c0;
  box-shadow: 0 0 4px #6080c0;
}

.step-dots .dot.done {
  background: #4a8a4a;
}

.bar-agent {
  color: #777;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge-q {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
}

.q-pass { background: #1a2a1a; color: #60c060; }
.q-fail { background: #2a1a1a; color: #e06060; }

.btn-toggle {
  background: none;
  border: 1px solid #333;
  color: #666;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
  cursor: pointer;
}

.btn-toggle:hover {
  border-color: #555;
  color: #aaa;
}

.timeline-detail {
  padding: 2px 16px 8px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.step-row {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #161630;
  border: 1px solid #222;
  font-size: 11px;
}

.step-row.running {
  border-color: #405080;
}

.step-row.done {
  border-color: #2a4a2a;
  opacity: 0.7;
}

.step-mark {
  width: 12px;
  height: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pending-mark {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #333;
}

.spinner {
  width: 10px;
  height: 10px;
  border: 2px solid #6080c0;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.check {
  color: #60c060;
  font-size: 9px;
}

.step-name {
  color: #c0c0d0;
}

.step-by {
  color: #555;
}
</style>
