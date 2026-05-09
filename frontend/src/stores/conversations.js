import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  fetchConversations,
  fetchConversation,
  deleteConversation as apiDelete,
} from '../api/client.js'

export const useConversationsStore = defineStore('conversations', () => {
  const list = ref([])
  const activeId = ref(null)
  const loading = ref(false)
  const error = ref('')
  const lastFetchedMessages = ref([])

  async function fetchList() {
    loading.value = true
    error.value = ''
    try {
      list.value = await fetchConversations()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function retryFetchList() {
    fetchList()
  }

  function setActiveId(id) {
    activeId.value = id
  }

  function clearError() {
    error.value = ''
  }

  async function selectConversation(id) {
    error.value = ''
    try {
      const detail = await fetchConversation(id)
      activeId.value = id
      lastFetchedMessages.value = detail.messages || []
      return true
    } catch (e) {
      error.value = e.message
      return false
    }
  }

  async function deleteConversation(id) {
    try {
      await apiDelete(id)
      list.value = list.value.filter((c) => c.thread_id !== id)
      if (activeId.value === id) {
        activeId.value = null
        lastFetchedMessages.value = []
      }
    } catch (e) {
      error.value = e.message
    }
  }

  function newConversation() {
    activeId.value = null
    lastFetchedMessages.value = []
  }

  return {
    list,
    activeId,
    loading,
    error,
    lastFetchedMessages,
    fetchList,
    retryFetchList,
    setActiveId,
    clearError,
    selectConversation,
    deleteConversation,
    newConversation,
  }
})