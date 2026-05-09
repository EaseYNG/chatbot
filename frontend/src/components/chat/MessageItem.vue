<template>
  <div class="msg-wrapper" :class="message.role">
    <div v-if="message.role !== 'status'" class="msg-role-label">{{ roleLabel }}</div>
    <div class="msg-content">
      <div v-if="message.role === 'status'" class="status-block" :class="message.state">
        <span v-if="message.state === 'running'" class="status-spinner"></span>
        <span v-else class="status-done-mark">&#10003;</span>
        <span class="status-label">{{ message.label }}</span>
      </div>
      <div v-else-if="message.role === 'tool'" class="tool-block">
        <div class="tool-badge" :class="message.status || 'done'">
          <span class="tool-icon">&#9881;</span>
          <span>{{ message.tool_name }}</span>
          <span v-if="message.status === 'running'" class="tool-spinner">...</span>
          <span v-else class="tool-check">&#10003;</span>
        </div>
        <div v-if="message.tool_output" class="tool-output">{{ message.tool_output }}</div>
      </div>
      <div v-else class="text-block">
        <div class="typing-indicator-row" v-if="message.role === 'ai' && isStreaming && !message.content">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
        <div v-else-if="message.role === 'ai' && !message.content && !isStreaming" />
        <div
          v-else-if="message.role === 'ai'"
          class="text-content markdown-body"
          v-html="renderedContent"
        />
        <div v-else class="text-content">{{ message.content }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../../utils/markdown.js'

const props = defineProps({
  message: { type: Object, required: true },
  isStreaming: { type: Boolean, default: false },
})

const renderedContent = computed(() => renderMarkdown(props.message.content || ''))

const roleLabel = computed(() => {
  switch (props.message.role) {
    case 'human': return 'You'
    case 'ai': return 'Assistant'
    case 'tool': return 'Tool'
    case 'system': return 'System'
    default: return props.message.role
  }
})
</script>

<style scoped>
.msg-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding: 12px 24px;
  display: flex;
  gap: 12px;
}

.msg-wrapper.human { background: #1e1e3a; }
.msg-wrapper.ai    { background: #1a1a2e; }
.msg-wrapper.tool  { background: #1a1a1a; border-left: 3px solid #6a6a30; }

.msg-role-label {
  width: 72px;
  min-width: 72px;
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  padding-top: 2px;
  text-align: right;
}

.msg-content { flex: 1; min-width: 0; }

.text-content {
  font-size: 15px;
  line-height: 1.6;
  color: #d0d0e0;
  white-space: pre-wrap;
  word-break: break-word;
}

.typing-indicator-row {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.markdown-body {
  white-space: normal;
}
.markdown-body h1, .markdown-body h2, .markdown-body h3,
.markdown-body h4, .markdown-body h5, .markdown-body h6 {
  margin: 16px 0 8px;
  font-weight: 600;
  line-height: 1.4;
  color: #e8e0ff;
}
.markdown-body h1 { font-size: 1.5em; border-bottom: 1px solid #3a3a5a; padding-bottom: 8px; }
.markdown-body h2 { font-size: 1.3em; }
.markdown-body h3 { font-size: 1.1em; }
.markdown-body p { margin: 8px 0; }
.markdown-body ul, .markdown-body ol { margin: 8px 0; padding-left: 24px; }
.markdown-body li { margin: 4px 0; }
.markdown-body a { color: #80a0e0; text-decoration: none; }
.markdown-body a:hover { text-decoration: underline; }
.markdown-body blockquote {
  margin: 8px 0;
  padding: 4px 14px;
  border-left: 3px solid #5a5a8a;
  background: #1e1e36;
  color: #b0b0d0;
}
.markdown-body code {
  font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 0.9em;
  padding: 2px 6px;
  border-radius: 4px;
  background: #2a2a40;
  color: #d0b0ff;
}
.markdown-body pre {
  margin: 12px 0;
  border-radius: 8px;
  overflow: hidden;
}
.markdown-body pre code {
  display: block;
  padding: 14px 16px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
  background: #1e1e30;
  color: #c0c0d0;
  border: 1px solid #2a2a4a;
}
.markdown-body table {
  border-collapse: collapse;
  margin: 12px 0;
  width: 100%;
}
.markdown-body th, .markdown-body td {
  border: 1px solid #3a3a5a;
  padding: 8px 12px;
  text-align: left;
}
.markdown-body th { background: #1e1e38; font-weight: 600; }
.markdown-body img { max-width: 100%; border-radius: 8px; }
.markdown-body hr { border: none; border-top: 1px solid #2a2a4a; margin: 16px 0; }
.markdown-body strong { color: #e8e0f0; }

/* highlight.js dark theme overrides */
.markdown-body :deep(.hljs) { background: #1e1e30; }
.markdown-body :deep(.hljs-keyword) { color: #c586c0; }
.markdown-body :deep(.hljs-string)  { color: #ce9178; }
.markdown-body :deep(.hljs-comment) { color: #6a9955; }
.markdown-body :deep(.hljs-function) { color: #dcdcaa; }
.markdown-body :deep(.hljs-number) { color: #b5cea8; }

.status-block {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 13px;
  color: #888;
}

.status-block.running {
  color: #8ab4f8;
}

.status-block.done {
  color: #5a8a5a;
}

.status-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #3a3a5a;
  border-top-color: #6080c0;
  border-radius: 50%;
  animation: status-spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes status-spin {
  to { transform: rotate(360deg); }
}

.status-done-mark {
  color: #5a8a5a;
  font-size: 12px;
}

.status-label {
  line-height: 1.4;
}

.tool-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  background: #2a2a1a;
  color: #c0c060;
  margin-bottom: 6px;
}


.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #666;
  animation: bounce 1.2s infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

.tool-spinner { animation: pulse 0.8s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.tool-output {
  font-size: 13px;
  color: #a0a080;
  background: #1a1a10;
  padding: 6px 10px;
  border-radius: 4px;
  margin-top: 4px;
  white-space: pre-wrap;
}
</style>
