import { defineStore } from 'pinia'
import { ref } from 'vue'

const DARK_KEY = 'jf_dark_mode'
const SIDEBAR_KEY = 'jf_sidebar_collapsed'

export function initTheme() {
  // “暗夜工业”方向：默认深色，除非用户显式切到浅色（存 '0'）
  const dark = localStorage.getItem(DARK_KEY) !== '0'
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  return dark
}

export const useAppStore = defineStore('app', () => {
  const isDark = ref(localStorage.getItem(DARK_KEY) !== '0')
  const sidebarCollapsed = ref(localStorage.getItem(SIDEBAR_KEY) === '1')
  const loading = ref(false)

  function toggleDark() {
    isDark.value = !isDark.value
    document.documentElement.setAttribute(
      'data-theme',
      isDark.value ? 'dark' : 'light'
    )
    localStorage.setItem(DARK_KEY, isDark.value ? '1' : '0')
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem(SIDEBAR_KEY, sidebarCollapsed.value ? '1' : '0')
  }
  function setSidebar(val) {
    sidebarCollapsed.value = val
    localStorage.setItem(SIDEBAR_KEY, val ? '1' : '0')
  }

  function setDark(val) {
    isDark.value = val
    document.documentElement.setAttribute(
      'data-theme',
      val ? 'dark' : 'light'
    )
    localStorage.setItem(DARK_KEY, val ? '1' : '0')
  }

  function setLoading(val) {
    loading.value = val
  }

  return { isDark, sidebarCollapsed, loading, toggleDark, setDark, toggleSidebar, setSidebar, setLoading }
})
