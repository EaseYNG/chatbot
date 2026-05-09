<template>
  <div
    class="conv-item"
    :class="{ active: isActive }"
    @click="$emit('select')"
  >
    <div class="conv-title">{{ conv.title || 'New Chat' }}</div>
    <div class="conv-meta">{{ formatDate(conv.updated_at) }}</div>
    <button
      class="btn-delete"
      title="Delete"
      @click.stop="$emit('delete')"
    >&times;</button>
  </div>
</template>

<script setup>
defineProps({
  conv: { type: Object, required: true },
  isActive: { type: Boolean, default: false },
})
defineEmits(['select', 'delete'])

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const diff = Date.now() - d
  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago'
  if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago'
  return d.toLocaleDateString()
}
</script>

<style scoped>
.conv-item {
  position: relative;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 2px;
  transition: background 0.15s;
}
.conv-item:hover {
  background: #1e1e3a;
}
.conv-item.active {
  background: #2a2a5a;
}

.conv-title {
  font-size: 14px;
  color: #c8c8e8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 24px;
}

.conv-meta {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
}

.btn-delete {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  display: none;
  align-items: center;
  justify-content: center;
}
.conv-item:hover .btn-delete {
  display: flex;
}
.btn-delete:hover {
  background: #4a2030;
  color: #e05050;
}
</style>
