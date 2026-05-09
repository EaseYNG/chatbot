<template>
  <div v-if="visible" class="workflow-bar">
    <div class="stages">
      <template v-for="(stage, idx) in stages" :key="stage.key">
        <div class="stage-node" :class="stageStatus(stage.key)">
          <span class="stage-dot">
            <span v-if="stageStatus(stage.key) === 'active'" class="pulse"></span>
            <span v-else-if="stageStatus(stage.key) === 'done'" class="check-mark">&#10003;</span>
            <span v-else class="empty-dot"></span>
          </span>
          <span class="stage-label">{{ stage.label }}</span>
        </div>
        <span v-if="idx < stages.length - 1" class="stage-connector" :class="connectorClass(idx)"></span>
      </template>
    </div>

    <div class="bar-meta">
      <span v-if="modeLabel" class="badge-mode" :class="modeClass">{{ modeLabel }}</span>
      <span v-if="qualityScore !== null" class="badge-q" :class="qualityClass">{{ qualityScore }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '../../stores/chat.js'

const chatStore = useChatStore()

const stages = [
  { key: 'INIT', label: '初始化' },
  { key: 'INPUT', label: '意图识别' },
  { key: 'COMPLEXITY', label: '复杂度' },
  { key: 'ROUTING', label: '路由' },
  { key: 'EXECUTION', label: '执行' },
  { key: 'OUTPUT', label: '输出整合' },
  { key: 'QUALITY', label: '质量检查' },
]

const visible = computed(() => {
  return chatStore.workflowEvents.length > 0
})

const startedStages = computed(() => {
  const started = new Map()
  const ended = new Map()
  for (const e of chatStore.workflowEvents) {
    if (e.kind === 'stage_start' && e.stage) {
      started.set(e.stage, true)
    }
    if (e.kind === 'stage_end' && e.stage) {
      ended.set(e.stage, true)
    }
  }
  return { started, ended }
})

function stageStatus(stageKey) {
  const { started, ended } = startedStages.value
  if (ended.has(stageKey)) return 'done'
  if (started.has(stageKey)) return 'active'
  return 'pending'
}

function connectorClass(idx) {
  const currentStage = stages[idx]
  const nextStage = stages[idx + 1]
  if (stageStatus(currentStage.key) === 'done' && stageStatus(nextStage.key) === 'active') return 'half'
  if (stageStatus(currentStage.key) === 'done') return 'done'
  return 'pending'
}

const modeLabel = computed(() => {
  const routeEvent = chatStore.workflowEvents.find(e => e.kind === 'route')
  const mode = routeEvent?.mode
  const labels = { REACT: '快速回答', PLAN_EXECUTE: '计划执行', WORKFLOW: '协作模式' }
  return labels[mode] || null
})

const modeClass = computed(() => {
  const routeEvent = chatStore.workflowEvents.find(e => e.kind === 'route')
  const mode = routeEvent?.mode
  return { REACT: 'c-react', PLAN_EXECUTE: 'c-plan', WORKFLOW: 'c-flow' }[mode] || ''
})

const qualityScore = computed(() => {
  const q = chatStore.workflowEvents.find(e => e.kind === 'quality')
  return q?.score ?? null
})

const qualityClass = computed(() => {
  const q = chatStore.workflowEvents.find(e => e.kind === 'quality')
  return q?.passed ? 'q-pass' : 'q-fail'
})
</script>

<style scoped>
.workflow-bar {
  background: #12122a;
  border-bottom: 1px solid #22224a;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  user-select: none;
  flex-shrink: 0;
}

.stages {
  display: flex;
  align-items: center;
  gap: 0;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
}

.stage-node {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  white-space: nowrap;
}

.stage-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.stage-node.pending .stage-dot {
  background: #1e1e38;
  border: 2px solid #2a2a4a;
}

.stage-node.active .stage-dot {
  background: #1a2a3a;
  border: 2px solid #4a8af4;
  box-shadow: 0 0 6px rgba(74, 138, 244, 0.4);
}

.stage-node.done .stage-dot {
  background: #1a2a1a;
  border: 2px solid #4a8a4a;
}

.stage-label {
  font-size: 10px;
  color: #444;
  transition: color 0.3s ease;
}

.stage-node.active .stage-label {
  color: #8ab4f8;
  font-weight: 500;
}

.stage-node.done .stage-label {
  color: #6a9a6a;
}

.stage-connector {
  width: 24px;
  height: 2px;
  flex-shrink: 0;
  margin: 0 2px;
  background: #1e1e38;
  border-radius: 1px;
  transition: background 0.5s ease;
}

.stage-connector.done {
  background: #3a6a3a;
}

.stage-connector.half {
  background: linear-gradient(to right, #3a6a3a 50%, #1e1e38 50%);
}

.empty-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #2a2a4a;
}

.check-mark {
  color: #60c060;
  font-size: 9px;
  font-weight: 700;
}

.pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4a8af4;
  animation: pulse-anim 1.2s ease-in-out infinite;
}

@keyframes pulse-anim {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}

.bar-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.badge-mode {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
  letter-spacing: 0.3px;
}

.c-react { background: #1a2a1a; color: #60c060; }
.c-plan  { background: #1a1a2a; color: #6080c0; }
.c-flow  { background: #2a1a2a; color: #c080c0; }

.badge-q {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
}

.q-pass { background: #1a2a1a; color: #60c060; }
.q-fail { background: #2a1a1a; color: #e06060; }
</style>
