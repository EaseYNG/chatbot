<template>
  <div
    class="conv-item"
    :class="{ active: isActive }"
    @click="$emit('select')"
  >
    <div class="conv-title">{{ conv.title || 'New Chat' }}</div>
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
</script>

<style scoped>
.conv-item {
  position: relative;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 2px;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}
.conv-item:hover {
  background: #1e1e3a;
}
.conv-item.active {
  background: #25254a;
  border-left-color: #7a6aff;
}

.conv-title {
  font-size: 14px;
  color: #c8c8e8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 24px;
  line-height: 1.4;
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
