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
  padding: 12px 48px;
  display: flex;
  gap: 12px;
}

.msg-wrapper:not(.status) {
  animation: msg-in 0.18s ease-out;
}

@keyframes msg-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-wrapper.human { background: #1e1e3a; }
.msg-wrapper.ai    { background: #1a1a2e; }
.msg-wrapper.tool  { background: #1a1a1a; border-left: 3px solid #6a6a30; }

.msg-role-label {
  width: 64px;
  min-width: 64px;
  font-size: 11px;
  font-weight: 700;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-top: 3px;
  text-align: right;
}

.msg-wrapper.human .msg-role-label { color: #7aacf0; }
.msg-wrapper.ai .msg-role-label    { color: #b890e0; }

.msg-content { flex: 1; min-width: 0; }

.text-content {
  font-size: 16px;
  line-height: 1.7;
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
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3),
.markdown-body :deep(h4), .markdown-body :deep(h5), .markdown-body :deep(h6) {
  margin: 20px 0 10px;
  font-weight: 600;
  line-height: 1.4;
  color: #e8e0ff;
}
.markdown-body :deep(h1) { font-size: 1.6em; border-bottom: 1px solid #3a3a5a; padding-bottom: 8px; }
.markdown-body :deep(h2) { font-size: 1.35em; }
.markdown-body :deep(h3) { font-size: 1.15em; }
.markdown-body :deep(p) { margin: 10px 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin: 10px 0; padding-left: 24px; }
.markdown-body :deep(li) { margin: 4px 0; }
.markdown-body :deep(a) { color: #80a0e0; text-decoration: none; }
.markdown-body :deep(a:hover) { text-decoration: underline; }
.markdown-body :deep(blockquote) {
  margin: 10px 0;
  padding: 6px 16px;
  border-left: 3px solid #5a5a8a;
  background: #1e1e36;
  color: #b0b0d0;
}

/* Inline code */
.markdown-body :deep(code) {
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace;
  font-size: 0.85em;
  padding: 2px 7px;
  border-radius: 4px;
  background: #2a2a45;
  color: #d0b0ff;
}

/* Code block wrapper */
.markdown-body :deep(.code-block) {
  margin: 16px 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #3a3a6a;
  background: #12122a;
}

.markdown-body :deep(.code-header) {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  background: #1a1a38;
  border-bottom: 1px solid #2a2a4a;
}

.markdown-body :deep(.code-lang) {
  font-size: 11px;
  font-weight: 600;
  color: #7a7aaa;
  text-transform: lowercase;
  letter-spacing: 0.3px;
}

.markdown-body :deep(.code-block pre) {
  margin: 0;
  overflow-x: auto;
}

.markdown-body :deep(.code-block pre code) {
  display: block;
  padding: 16px 18px;
  font-size: 14px;
  line-height: 1.6;
  background: transparent;
  color: #d0d0e0;
  border: none;
}

/* Tables */
.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 16px 0;
  width: 100%;
  font-size: 14px;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid #3a3a6a;
  padding: 10px 14px;
  text-align: left;
}
.markdown-body :deep(th) {
  background: #1e1e3a;
  font-weight: 600;
  color: #c0b0e0;
  border-bottom-width: 2px;
}
.markdown-body :deep(tbody tr:nth-child(even)) {
  background: #16162e;
}
.markdown-body :deep(tbody tr:hover) {
  background: #1e1e3e;
}

.markdown-body :deep(img) { max-width: 100%; border-radius: 8px; }
.markdown-body :deep(hr) { border: none; border-top: 1px solid #2a2a4a; margin: 20px 0; }
.markdown-body :deep(strong) { color: #e8e0f0; }

/* highlight.js dark theme overrides */
.markdown-body :deep(.hljs) { background: transparent; }
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
